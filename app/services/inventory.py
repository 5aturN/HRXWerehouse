"""inventory_engine: вся математика остатков. Каждая операция — одна транзакция БД."""
import uuid, logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Batch, Item, Transaction

log = logging.getLogger("inventory")

class InsufficientStockError(Exception):
    def __init__(self, item: Item, need: int, have: int):
        self.item, self.need, self.have = item, need, have
        super().__init__(f"Недостаточно «{item.name}»: нужно {need}, есть {have}")

async def get_balance(db: AsyncSession, item_id: str) -> int:
    """Текущий остаток товара = сумма remaining по всем партиям."""
    from sqlalchemy import func
    return (await db.scalar(
        select(func.coalesce(func.sum(Batch.remaining), 0)).where(Batch.item_id == item_id)
    )) or 0

async def write_off_fifo(
    db: AsyncSession, item_id: str, qty: int, tx_type: str, user_id: int,
    reason: str | None = None, project_id: str | None = None,
    assembly_group: str | None = None, qr_code_id: str | None = None,
) -> list[Transaction]:
    """
    Списывает qty единиц товара по FIFO (старые партии первыми).
    НЕ коммитит — вызывающий код управляет транзакцией (важно для атомарной сборки).
    """
    batches = (await db.scalars(
        select(Batch).where(Batch.item_id == item_id, Batch.remaining > 0)
        .order_by(Batch.delivery_date, Batch.created_at)
        .with_for_update()  # для SQLite фактически no-op, но переносимо
    )).all()

    total = sum(b.remaining for b in batches)
    if total < qty:
        item = await db.get(Item, item_id)
        raise InsufficientStockError(item, qty, total)

    txs, left = [], qty
    for b in batches:
        if left == 0:
            break
        take = min(b.remaining, left)
        b.remaining -= take
        left -= take
        tx = Transaction(
            id=str(uuid.uuid4()), batch_id=b.id, qr_code_id=qr_code_id,
            transaction_type=tx_type, quantity=take, reason=reason,
            project_id=project_id, assembly_group=assembly_group, user_id=user_id,
        )
        db.add(tx)
        txs.append(tx)
        log.info("Списание: item=%s batch=%s qty=%s type=%s user=%s",
                 item_id, b.id, take, tx_type, user_id)
    return txs

async def return_to_stock(db: AsyncSession, tx_id: str, user_id: int) -> Transaction:
    """Возврат по исходной операции списания: восстанавливает remaining той же партии."""
    src = await db.get(Transaction, tx_id)
    if not src or src.transaction_type in ("receipt", "return"):
        raise ValueError("Операция для возврата не найдена или не является списанием")
    batch = await db.get(Batch, src.batch_id)
    batch.remaining += src.quantity
    tx = Transaction(
        id=str(uuid.uuid4()), batch_id=batch.id, transaction_type="return",
        quantity=src.quantity, reason=f"Возврат операции {tx_id}", user_id=user_id,
    )
    db.add(tx)
    log.info("Возврат: batch=%s qty=%s user=%s", batch.id, src.quantity, user_id)
    return tx