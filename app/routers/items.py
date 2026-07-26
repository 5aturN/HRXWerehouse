"""Номенклатура: список с остатками, создание."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import Folder, Item, User
from app.schemas.schemas import ItemCreate
from app.services.telegram_auth import get_current_user

router = APIRouter(prefix="/api/items", tags=["Items"])

@router.get("")
async def list_items(
    folder_id: str | None = None,
    is_product: int | None = Query(None),
    search: str | None = None,
    db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user),
):
    """Список товаров с текущим остатком. Фильтры: папка, готовые изделия, поиск."""
    sql = """
        SELECT i.id, i.sku, i.name, i.decimal_number, i.folder_id, i.unit_type,
               i.threshold, i.is_product, COALESCE(SUM(b.remaining), 0) AS balance
        FROM items i LEFT JOIN batches b ON b.item_id = i.id
        WHERE 1=1
    """
    params: dict = {}
    if folder_id:
        sql += " AND i.folder_id = :fid"; params["fid"] = folder_id
    if is_product is not None:
        sql += " AND i.is_product = :ip"; params["ip"] = is_product
    if search:
        sql += " AND (i.name LIKE :q OR i.sku LIKE :q OR i.decimal_number LIKE :q)"
        params["q"] = f"%{search}%"
    sql += " GROUP BY i.id ORDER BY i.name"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return [dict(r) for r in rows]

@router.post("/create")
async def create_item(req: ItemCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """Создание позиции. Правило: в серийных папках децимальный номер обязателен."""
    folder = await db.get(Folder, req.folder_id)
    if not folder:
        raise HTTPException(404, "Папка не найдена")
    if folder.type == "serial" and not req.decimal_number:
        raise HTTPException(400, "Для деталей серийной продукции децимальный номер обязателен")
    item = Item(**req.model_dump(exclude={"is_product"}), is_product=int(req.is_product))
    db.add(item)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(409, f"Артикул «{req.sku}» уже существует")
    return {"success": True, "id": item.id}
