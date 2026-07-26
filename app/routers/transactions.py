"""Ручные операции: списание в проект, брак, возврат."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import Batch, Folder, User
from app.schemas.schemas import WriteOffRequest, ScrapRequest, ReturnRequest
from app.services.inventory import write_off_fifo, return_to_stock, InsufficientStockError
from app.services.notifications import check_and_notify_thresholds
from app.services.telegram_auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])
log = logging.getLogger("transactions")

@router.post("/write-off")
async def write_off(req: WriteOffRequest, db: AsyncSession = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """Ручное списание. Если указан project_id → выдача на R&D проект."""
    tx_type = "rd_issue" if req.project_id else "write_off"
    if req.project_id:
        project = await db.get(Folder, req.project_id)
        if not project or project.type != "project":
            raise HTTPException(400, "Выберите папку R&D проекта")
    try:
        await write_off_fifo(db, req.item_id, req.quantity, tx_type,
                             user.telegram_id, reason=req.reason, project_id=req.project_id)
        await db.commit()
    except InsufficientStockError as e:
        await db.rollback()
        raise HTTPException(409, str(e))
    await check_and_notify_thresholds(db, [req.item_id])
    return {"success": True, "message": "Списание выполнено"}

@router.post("/scrap")
async def scrap(req: ScrapRequest, db: AsyncSession = Depends(get_db),
                user: User = Depends(get_current_user)):
    """Списание в брак по отсканированной партии. Причина обязательна."""
    batch = await db.get(Batch, req.batch_id)
    if not batch:
        raise HTTPException(404, "Партия не найдена")
    try:
        await write_off_fifo(db, batch.item_id, req.quantity, "scrap",
                             user.telegram_id, reason=f"Брак: {req.reason}")
        await db.commit()
    except InsufficientStockError as e:
        await db.rollback()
        raise HTTPException(409, str(e))
    await check_and_notify_thresholds(db, [batch.item_id])
    return {"success": True, "message": "Списано в брак"}

@router.post("/return")
async def return_tx(req: ReturnRequest, db: AsyncSession = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """Возврат ошибочно списанного на склад (по ID исходной операции)."""
    try:
        await return_to_stock(db, req.transaction_id, user.telegram_id)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(400, str(e))
    return {"success": True, "message": "Возврат выполнен, остаток восстановлен"}

@router.get("/recent")
async def recent(item_id: str | None = None, db: AsyncSession = Depends(get_db),
                 _: User = Depends(get_current_user)):
    """Последние списания (для выбора операции при возврате)."""
    from sqlalchemy import text
    sql = """SELECT t.id, t.transaction_type, t.quantity, t.reason, t.created_at,
                    i.name, i.sku
             FROM transactions t
             JOIN batches b ON b.id = t.batch_id JOIN items i ON i.id = b.item_id
             WHERE t.transaction_type NOT IN ('receipt','return')"""
    params = {}
    if item_id:
        sql += " AND b.item_id = :iid"; params["iid"] = item_id
    sql += " ORDER BY t.created_at DESC LIMIT 30"
    return [dict(r) for r in (await db.execute(text(sql), params)).mappings().all()]
