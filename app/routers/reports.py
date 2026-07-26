"""Отчеты: остатки, движения, Excel."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import ExportRequest
from app.services.excel import export_report
from app.services.telegram_auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/balances")
async def balances(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Остатки по всем позициям с признаком «ниже порога»."""
    rows = (await db.execute(text("""
        SELECT i.id, i.sku, i.name, i.decimal_number, f.name AS folder_name,
               COALESCE(SUM(b.remaining),0) AS balance, i.threshold,
               CASE WHEN COALESCE(SUM(b.remaining),0) <= i.threshold THEN 1 ELSE 0 END AS is_low
        FROM items i JOIN folders f ON f.id = i.folder_id
        LEFT JOIN batches b ON b.item_id = i.id
        GROUP BY i.id ORDER BY is_low DESC, f.name, i.name
    """))).mappings().all()
    return [dict(r) for r in rows]

@router.get("/movements")
async def movements(date_from: str, date_to: str,
                    db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Движения за период."""
    rows = (await db.execute(text("""
        SELECT t.created_at, t.transaction_type, i.sku, i.name, t.quantity,
               COALESCE(t.reason, pf.name, '') AS detail,
               COALESCE(u.full_name, CAST(t.user_id AS TEXT)) AS user_name
        FROM transactions t
        JOIN batches b ON b.id = t.batch_id JOIN items i ON i.id = b.item_id
        LEFT JOIN folders pf ON pf.id = t.project_id
        LEFT JOIN users u ON u.telegram_id = t.user_id
        WHERE t.created_at BETWEEN :df AND :dt || ' 23:59:59'
        ORDER BY t.created_at DESC
    """), {"df": date_from, "dt": date_to})).mappings().all()
    return [dict(r) for r in rows]

@router.post("/export-excel")
async def export_excel(req: ExportRequest, db: AsyncSession = Depends(get_db),
                       _: User = Depends(get_current_user)):
    """Excel-файл: листы «Остатки» и «Движения за период»."""
    data = await export_report(db, req.date_from, req.date_to)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":
                 f'attachment; filename="sklad_{req.date_from}_{req.date_to}.xlsx"'})
