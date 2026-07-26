"""
Валидация Telegram.WebApp.initData по официальному алгоритму:
secret_key = HMAC_SHA256("WebAppData", bot_token)
hash       = HMAC_SHA256(secret_key, data_check_string)
"""
import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.models import User

def validate_init_data(init_data: str) -> dict:
    """Проверяет подпись initData. Возвращает распарсенные данные пользователя."""
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            raise ValueError("Отсутствует hash")

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calc_hash, received_hash):
            raise ValueError("Неверная подпись")

        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > settings.AUTH_MAX_AGE_SECONDS:
            raise ValueError("Сессия устарела, перезапустите приложение")

        return json.loads(parsed["user"])
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=401, detail=f"Ошибка авторизации Telegram: {e}")


async def get_current_user(
    x_telegram_init_data: str = Header("", alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: валидирует initData на каждом запросе.
    В DEV_MODE (только локальная разработка!) авторизация подменяется
    фиктивным пользователем DEV_USER_ID — чтобы отлаживать в обычном браузере.
    """
    if settings.DEV_MODE:
        user = await db.scalar(select(User).where(User.telegram_id == settings.DEV_USER_ID))
        if not user:
            raise HTTPException(403, "DEV_MODE: запустите scripts/seed.py — там создается тестовый админ")
        return user

    tg_user = validate_init_data(x_telegram_init_data)
    user = await db.scalar(select(User).where(User.telegram_id == tg_user["id"]))
    if not user or not user.is_active:
        raise HTTPException(403, "Доступ не выдан. Обратитесь к администратору.")
    return user


async def get_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: только для админов."""
    if user.role != "admin":
        raise HTTPException(403, "Требуются права администратора")
    return user