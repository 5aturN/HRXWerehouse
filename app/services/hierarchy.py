"""hierarchy_manager: дерево папок."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_tree(db: AsyncSession) -> list[dict]:
    """Возвращает дерево папок (вложенные children)."""
    rows = (await db.execute(text("""
        WITH RECURSIVE tree AS (
            SELECT id, name, parent_id, type, 0 AS depth FROM folders WHERE parent_id IS NULL
            UNION ALL
            SELECT f.id, f.name, f.parent_id, f.type, t.depth + 1
            FROM folders f JOIN tree t ON f.parent_id = t.id
        )
        SELECT id, name, parent_id, type FROM tree ORDER BY depth, name
    """))).all()

    nodes = {r.id: {"id": r.id, "name": r.name, "parent_id": r.parent_id,
                    "type": r.type, "children": []} for r in rows}
    roots = []
    for n in nodes.values():
        (nodes[n["parent_id"]]["children"] if n["parent_id"] in nodes else roots).append(n)
    return roots
