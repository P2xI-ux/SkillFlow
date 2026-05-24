from pathlib import Path
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.events import event_bus
from app.core.seed import seed_core_data
from app.services.test_service import TestService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SkillFlow MVP", version="0.1.0")
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
from fastapi.templating import Jinja2Templates

app.include_router(router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=templates_dir)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            "http_request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-Id"] = request_id
    logger.info(
        "http_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        message = detail.get("message", str(detail))
    else:
        code = "HTTP_ERROR"
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": message, "request_id": request_id},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    messages = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error.get("loc", []))
        messages.append(f"{location}: {error.get('msg')}")
    return JSONResponse(
        status_code=422,
        content={
            "code": "REQUEST_VALIDATION_ERROR",
            "message": "; ".join(messages) or "Некорректные данные запроса",
            "request_id": request_id,
        },
    )


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_data()
    setup_event_handlers()
    from app.services.notification_subscriber import init_arq_pool, setup_notification_subscriptions
    setup_notification_subscriptions()
    await init_arq_pool()
    logger.info("startup_completed")


@app.on_event("shutdown")
async def shutdown_event():
    from app.services.notification_subscriber import close_arq_pool
    await close_arq_pool()
    logger.info("shutdown_completed")



def setup_event_handlers():
    event_bus.subscribe("TEST_COMPLETED", TestService._handle_rating_update)
    event_bus.subscribe("TEST_COMPLETED", TestService._handle_achievement_update)
    event_bus.subscribe("TEST_PUBLISHED", TestService._handle_creator_achievement)


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/auth")
def auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        logger.exception("health_ready_failed", extra={"error": str(exc)})
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "error"})


def seed_data():
    db = SessionLocal()
    try:
        seed_core_data(db)
    finally:
        db.close()
