"""Папки: дерево и создание (админ)."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import Folder, User
from app.schemas.schemas import FolderCreate
from app.services.hierarchy import get_tree
from app.services.telegram_auth import get_current_user, get_admin

router = APIRouter(prefix="/api/folders", tags=["Folders"])
log = logging.getLogger("folders")

@router.get("/tree")
async def tree(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Дерево папок склада."""
    return await get_tree(db)

@router.post("/create")
async def create_folder(req: FolderCreate, db: AsyncSession = Depends(get_db),
                        admin: User = Depends(get_admin)):
    """Создание папки (только админ). Папка type='project' — только внутри раздела R&D."""
    if req.type == "project":
        parent = await db.get(Folder, req.parent_id) if req.parent_id else None
        if not parent or parent.type != "rd":
            raise HTTPException(400, "Папку проекта можно создать только внутри раздела «R&D проекты»")
    folder = Folder(name=req.name, parent_id=req.parent_id, type=req.type)
    db.add(folder)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(409, "Папка с таким именем уже существует в этом разделе")
    log.info("Создана папка «%s» (тип %s) админом %s", req.name, req.type, admin.telegram_id)
    return {"success": True, "id": folder.id}
