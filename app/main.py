from pathlib import Path
import logging
import time
import uuid

from fastapi import FastAPI, Request
from sqlalchemy import text
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.database import Base, SessionLocal, engine
from app.core.events import event_bus
from app.models.entities import Achievement, Subject
from app.services.test_service import TestService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SkillFlow MVP", version="0.1.0")
app.include_router(router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
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


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_data()
    setup_event_handlers()
    logger.info("startup_completed")


def setup_event_handlers():
    event_bus.subscribe("TEST_COMPLETED", TestService._handle_rating_update)
    event_bus.subscribe("TEST_COMPLETED", TestService._handle_achievement_update)
    event_bus.subscribe("TEST_PUBLISHED", TestService._handle_creator_achievement)


@app.get("/")
def root():
    return FileResponse(static_dir / "index.html")


@app.get("/auth")
def auth_page():
    return FileResponse(static_dir / "auth.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse(static_dir / "dashboard.html")


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
        subjects = [
            ("Программирование", "PROG"),
            ("Математика", "MATH"),
            ("Физика", "PHYS"),
        ]
        for name, code in subjects:
            if not db.query(Subject).filter(Subject.code == code).first():
                db.add(Subject(name=name, code=code))
        achievements = [
            ("FIRST_TEST", "Первый тест", "Пройти хотя бы один тест"),
            ("STREAK_3", "Серия побед", "Три идеальных результата подряд"),
            ("SUBJECT_MASTER", "Эксперт предмета", "Попасть в топ-3 предмета"),
            ("TEST_CREATOR", "Создатель", "Опубликовать первый тест"),
            ("PERFECT_SCORE", "Идеальный результат", "Пройти тест без ошибок"),
        ]
        for code, name, description in achievements:
            if not db.query(Achievement).filter(Achievement.code == code).first():
                db.add(Achievement(code=code, name=name, description=description))
        db.commit()
    finally:
        db.close()
