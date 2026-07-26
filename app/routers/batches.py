"""Приемка и информация о партии по QR."""
import logging, math, uuid, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import Batch, Folder, Item, QrCode, Transaction, User
from app.schemas.schemas import ReceiveRequest, ReceiveResponse, QrOut
from app.services.qr import generate_qr
from app.services.telegram_auth import get_current_user

router = APIRouter(prefix="/api/batches", tags=["Batches"])
log = logging.getLogger("receive")

@router.post("/receive", response_model=ReceiveResponse)
async def receive(req: ReceiveRequest, db: AsyncSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    """
    Приемка товара:
    1. Ищет позицию по SKU (или создает новую в выбранной папке).
    2. Создает партию (batch) с remaining = quantity.
    3. Генерирует QR: single → по 1 QR на единицу; bulk → ceil(qty / quantity_per_qr).
    4. Пишет операцию 'receipt' в журнал.
    """
    try:
        folder = await db.get(Folder, req.folder_id)
        if not folder:
            raise HTTPException(404, "Папка не найдена")
        if req.unit_type == "bulk" and not req.quantity_per_qr:
            raise HTTPException(400, "Для кратного учета укажите количество в одном QR")
        if folder.type == "serial" and not req.decimal_number:
            raise HTTPException(400, "Для серийной продукции децимальный номер обязателен")

        # 1. Позиция
        item = await db.scalar(select(Item).where(Item.sku == req.sku))
        if not item:
            item = Item(sku=req.sku, name=req.name, decimal_number=req.decimal_number,
                        folder_id=req.folder_id, unit_type=req.unit_type)
            db.add(item)
            await db.flush()

        # 2. Партия
        batch = Batch(item_id=item.id, supplier=req.supplier,
                      invoice_number=req.invoice_number, quantity=req.quantity,
                      quantity_per_qr=req.quantity_per_qr if req.unit_type == "bulk" else None,
                      delivery_date=req.delivery_date, remaining=req.quantity)
        db.add(batch)
        await db.flush()

        # 3. QR-коды
        qr_out: list[QrOut] = []
        if req.unit_type == "single":
            counts = [1] * req.quantity
        else:
            per, full = req.quantity_per_qr, req.quantity
            counts = [per] * (full // per) + ([full % per] if full % per else [])
        for qty in counts:
            qr = QrCode(batch_id=batch.id,
                        qr_code_data=json.dumps({"batch_id": batch.id, "qr": str(uuid.uuid4())}),
                        quantity=qty)
            db.add(qr)
            await db.flush()
            qr_out.append(QrOut(qr_id=qr.id, quantity=qty, png_base64=generate_qr(batch.id)))

        # 4. Журнал
        db.add(Transaction(batch_id=batch.id, transaction_type="receipt",
                           quantity=req.quantity, user_id=user.telegram_id,
                           reason=f"Приемка, УПД {req.invoice_number}, {req.supplier}"))
        await db.commit()
        log.info("Приемка: %s x%s, партия %s, пользователь %s",
                 item.sku, req.quantity, batch.id, user.telegram_id)
        return ReceiveResponse(batch_id=batch.id, item_name=item.name,
                               sku=item.sku, qr_codes=qr_out)
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        log.exception("Ошибка приемки")
        raise HTTPException(500, "Ошибка при приемке. Данные не сохранены.")

@router.get("/{batch_id}")
async def batch_info(batch_id: str, db: AsyncSession = Depends(get_db),
                     _: User = Depends(get_current_user)):
    """Карточка партии по отсканированному QR."""
    row = (await db.execute(text("""
        SELECT b.id AS batch_id, b.supplier, b.invoice_number, b.delivery_date,
               b.quantity, b.remaining, b.quantity_per_qr,
               i.id AS item_id, i.sku, i.name, i.decimal_number, i.unit_type,
               f.name AS folder_name
        FROM batches b JOIN items i ON i.id = b.item_id
        JOIN folders f ON f.id = i.folder_id
        WHERE b.id = :bid
    """), {"bid": batch_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Партия не найдена. Возможно, этикетка устарела.")
    return dict(row)
