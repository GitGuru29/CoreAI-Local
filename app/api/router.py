from fastapi import APIRouter

from app.api.routes import analyze_code, chat, health, info, models, summarize

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(info.router)
api_router.include_router(models.router)
api_router.include_router(chat.router)
api_router.include_router(summarize.router)
api_router.include_router(analyze_code.router)
