"""Админ-панель: пользователи, аудит, пороги."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import NotificationSetting, User
from app.schemas.schemas import ThresholdSet, UserUpsert
from app.services.telegram_auth import get_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(get_admin)):
    return [{"telegram_id": u.telegram_id, "username": u.username,
             "full_name": u.full_name, "role": u.role, "is_active": bool(u.is_active)}
            for u in (await db.scalars(select(User))).all()]

@router.post("/users")
async def upsert_user(req: UserUpsert, db: AsyncSession = Depends(get_db),
                      admin: User = Depends(get_admin)):
    """Добавление/изменение пользователя. Нельзя отключить самого себя."""
    if req.telegram_id == admin.telegram_id and not req.is_active:
        raise HTTPException(400, "Нельзя отключить собственный доступ")
    user = await db.get(User, req.telegram_id)
    if user:
        user.username, user.full_name = req.username, req.full_name
        user.role, user.is_active = req.role, int(req.is_active)
    else:
        db.add(User(telegram_id=req.telegram_id, username=req.username,
                    full_name=req.full_name, role=req.role, is_active=int(req.is_active)))
    await db.commit()
    return {"success": True}

@router.get("/audit")
async def audit(limit: int = 100, db: AsyncSession = Depends(get_db),
                _: User = Depends(get_admin)):
    """Журнал операций: кто, когда, что сделал."""
    rows = (await db.execute(text("""
        SELECT t.created_at, t.transaction_type, t.quantity, t.reason,
               i.sku, i.name, COALESCE(u.full_name, CAST(t.user_id AS TEXT)) AS user_name
        FROM transactions t
        JOIN batches b ON b.id = t.batch_id JOIN items i ON i.id = b.item_id
        LEFT JOIN users u ON u.telegram_id = t.user_id
        ORDER BY t.created_at DESC LIMIT :lim
    """), {"lim": min(limit, 500)})).mappings().all()
    return [dict(r) for r in rows]

@router.post("/thresholds")
async def set_threshold(req: ThresholdSet, db: AsyncSession = Depends(get_db),
                        _: User = Depends(get_admin)):
    """Персональный порог уведомления для позиции."""
    rule = await db.scalar(select(NotificationSetting).where(
        NotificationSetting.item_id == req.item_id,
        NotificationSetting.manager_telegram_id == req.manager_telegram_id))
    if rule:
        rule.threshold, rule.is_active = req.threshold, int(req.is_active)
    else:
        db.add(NotificationSetting(manager_telegram_id=req.manager_telegram_id,
                                   item_id=req.item_id, threshold=req.threshold))
    await db.commit()
    return {"success": True}
