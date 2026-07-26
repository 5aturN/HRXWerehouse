"""Роутер BOM: создание спецификаций и сборка серийных изделий."""
import uuid, logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.models import Bom, Item, User
from app.services.telegram_auth import get_current_user, get_admin
from app.services.inventory import get_balance, write_off_fifo, InsufficientStockError
from app.services.notifications import check_and_notify_thresholds

router = APIRouter(prefix="/api/boms", tags=["BOM"])
log = logging.getLogger("assembly")

class AssembleRequest(BaseModel):
    product_item_id: str = Field(..., description="ID серийного изделия (А/Б/В)")
    count: int = Field(1, ge=1, le=100, description="Сколько изделий собрать")

@router.post("/assemble")
async def assemble(
    req: AssembleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Кнопка «Собрать N шт.»:
    1. Загружает BOM изделия.
    2. Проверяет наличие ВСЕХ компонентов (нужно = bom.qty * count).
    3. Если чего-то не хватает — возвращает список недостающего (ничего не списывает).
    4. Если всё есть — атомарно списывает все компоненты по FIFO одной транзакцией.
    5. После коммита проверяет пороги уведомлений.
    """
    product = await db.get(Item, req.product_item_id)
    if not product or not product.is_product:
        raise HTTPException(404, "Изделие не найдено")

    bom_rows = (await db.scalars(
        select(Bom).where(Bom.product_item_id == req.product_item_id)
    )).all()
    if not bom_rows:
        raise HTTPException(400, f"Для изделия «{product.name}» не задана спецификация (BOM)")

    # --- Шаг 1: проверка наличия ВСЕХ компонентов ---
    shortages, affected_items = [], []
    for row in bom_rows:
        need = row.quantity * req.count
        have = await get_balance(db, row.component_item_id)
        comp = await db.get(Item, row.component_item_id)
        affected_items.append(row.component_item_id)
        if have < need:
            shortages.append({
                "item_id": comp.id, "sku": comp.sku, "name": comp.name,
                "decimal_number": comp.decimal_number,
                "required": need, "available": have, "missing": need - have,
            })

    if shortages:
        return {
            "success": False,
            "message": "Недостаточно компонентов для сборки",
            "shortages": shortages,
        }

    # --- Шаг 2: атомарное списание ---
    assembly_group = str(uuid.uuid4())
    try:
        for row in bom_rows:
            await write_off_fifo(
                db, item_id=row.component_item_id,
                qty=row.quantity * req.count,
                tx_type="assembly", user_id=user.telegram_id,
                reason=f"Списание на сборку изделия «{product.name}», кол-во {req.count} шт.",
                assembly_group=assembly_group,
            )
        await db.commit()
    except InsufficientStockError as e:
        await db.rollback()  # состояние гонки: кто-то списал параллельно
        raise HTTPException(409, str(e))
    except Exception:
        await db.rollback()
        log.exception("Ошибка сборки изделия %s", product.name)
        raise HTTPException(500, "Ошибка при списании компонентов. Остатки не изменены.")

    log.info("Сборка: %s x%s, группа=%s, пользователь=%s",
             product.name, req.count, assembly_group, user.telegram_id)

    # --- Шаг 3: уведомления о порогах (после коммита) ---
    await check_and_notify_thresholds(db, affected_items)

    return {
        "success": True,
        "message": f"Собрано: «{product.name}» — {req.count} шт. Компоненты списаны.",
        "assembly_group": assembly_group,
    }


class BomLine(BaseModel):
    component_item_id: str
    quantity: int = Field(..., ge=1)

class BomCreateRequest(BaseModel):
    product_item_id: str
    components: list[BomLine]

@router.post("/create")
async def create_bom(req: BomCreateRequest, db: AsyncSession = Depends(get_db),
                     _: User = Depends(get_admin)):
    """Создание/замена BOM (только админ). Валидация: компонент != изделие, нет дублей."""
    ids = [c.component_item_id for c in req.components]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "В спецификации есть повторяющиеся компоненты")
    if req.product_item_id in ids:
        raise HTTPException(400, "Изделие не может быть компонентом самого себя")

    from sqlalchemy import delete
    await db.execute(delete(Bom).where(Bom.product_item_id == req.product_item_id))
    for c in req.components:
        db.add(Bom(id=str(uuid.uuid4()), product_item_id=req.product_item_id,
                   component_item_id=c.component_item_id, quantity=c.quantity))
    await db.commit()
    return {"success": True, "message": "Спецификация сохранена"}