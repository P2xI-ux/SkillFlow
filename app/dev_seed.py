from app.core.database import Base, SessionLocal, engine
from app.core.seed import seed_demo_data


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    print("Demo data ready: student@skillflow.local / Demo12345, teacher@skillflow.local / Demo12345")


if __name__ == "__main__":
    main()
