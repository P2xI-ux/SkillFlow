from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.database import Base, SessionLocal, engine
from app.models.entities import Achievement, Subject

app = FastAPI(title="SkillFlow MVP", version="0.1.0")
app.include_router(router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_data()


@app.get("/")
def root():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}



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
