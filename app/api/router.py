from fastapi import APIRouter

from app.api.routes import chat, health, models

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(models.router)
api_router.include_router(chat.router)
