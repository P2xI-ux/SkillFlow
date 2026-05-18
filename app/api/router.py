from fastapi import APIRouter

from app.api.routers import auth, catalog, profile, ratings, telegram, tests

router = APIRouter(prefix="/api")
router.include_router(auth.router)
router.include_router(catalog.router)
router.include_router(profile.router)
router.include_router(ratings.router)
router.include_router(telegram.router)
router.include_router(tests.router)
