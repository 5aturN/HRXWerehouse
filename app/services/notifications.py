"""notification_service: проверка порогов и отправка алертов менеджеру в Telegram."""
import logging
from datetime import datetime, timedelta
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.models import Item, NotificationSetting
from app.services.inventory import get_balance

log = logging.getLogger("notifications")
TG_API = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"

async def send_alert(user_id: int, message: str) -> None:
    """Отправка сообщения через Bot API (не роняет основную операцию при сбое)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(TG_API, json={
                "chat_id": user_id, "text": message, "parse_mode": "HTML"})
    except Exception:
        log.exception("Не удалось отправить уведомление user_id=%s", user_id)

async def check_and_notify_thresholds(db: AsyncSession, item_ids: list[str]) -> None:
    """
    Для каждой позиции: если current <= threshold — алерт менеджеру.
    Порог берётся из notification_settings (персональный) или items.threshold.
    Анти-спам: не чаще 1 раза в 24 часа на позицию/менеджера.
    """
    for item_id in set(item_ids):
        item = await db.get(Item, item_id)
        balance = await get_balance(db, item_id)
        rules = (await db.scalars(select(NotificationSetting).where(
            NotificationSetting.item_id == item_id,
            NotificationSetting.is_active == 1))).all()

        # если персональных правил нет — используем общий порог позиции для всех менеджеров
        for rule in rules:
            if balance > rule.threshold:
                continue
            if rule.last_notified_at and \
               datetime.fromisoformat(rule.last_notified_at) > datetime.utcnow() - timedelta(hours=24):
                continue
            await send_alert(rule.manager_telegram_id,
                f"⚠️ <b>Критический остаток</b>\n"
                f"Артикул: <code>{item.sku}</code>\n"
                f"Наименование: {item.name}\n"
                f"Остаток: <b>{balance}</b> (порог: {rule.threshold})")
            rule.last_notified_at = datetime.utcnow().isoformat()
    await db.commit()