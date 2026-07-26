"""Аутентификация: фронт вызывает один раз при старте, получает профиль и роль."""
from fastapi import APIRouter, Depends
from app.models.models import User
from app.services.telegram_auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/telegram")
async def auth_telegram(user: User = Depends(get_current_user)):
    """Проверяет initData (в заголовке) и возвращает профиль пользователя."""
    return {"telegram_id": user.telegram_id, "full_name": user.full_name,
            "role": user.role}
