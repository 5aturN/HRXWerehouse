"""Заполнение БД тестовыми данными: структура папок, 3 изделия с BOM, расходники, R&D."""
import asyncio, sys
sys.path.insert(0, ".")
from app.database import SessionLocal
from app.models.models import Folder, Item, Bom, Batch, User

async def seed():
    async with SessionLocal() as db:
        # Папки
        root = Folder(name="Корень склада", type="root")
        serial = Folder(name="Серийная продукция", type="serial")
        cons = Folder(name="Расходники", type="consumable")
        rd = Folder(name="R&D проекты", type="rd")
        db.add_all([root, serial, cons, rd]); await db.flush()
        serial.parent_id = cons.parent_id = rd.parent_id = root.id

        f_a = Folder(name="Изделие А", parent_id=serial.id, type="serial")
        f_b = Folder(name="Изделие Б", parent_id=serial.id, type="serial")
        f_v = Folder(name="Изделие В", parent_id=serial.id, type="serial")
        metiz = Folder(name="Метизы", parent_id=cons.id, type="consumable")
        chem = Folder(name="Химия", parent_id=cons.id, type="consumable")
        glue = Folder(name="Клеи", parent_id=cons.id, type="consumable")
        proj_x = Folder(name="Проект X", parent_id=rd.id, type="project")
        db.add_all([f_a, f_b, f_v, metiz, chem, glue, proj_x]); await db.flush()

        # Готовые изделия + детали изделия А
        prod_a = Item(sku="PROD-A", name="Изделие А", decimal_number="АБВГ.0001",
                      folder_id=f_a.id, unit_type="single", is_product=1)
        d1 = Item(sku="D-1234-01", name="Деталь 1", decimal_number="1234-01",
                  folder_id=f_a.id, unit_type="single", threshold=10)
        d2 = Item(sku="D-1234-02", name="Деталь 2", decimal_number="1234-02",
                  folder_id=f_a.id, unit_type="single", threshold=20)
        d3 = Item(sku="D-1234-03", name="Деталь 3", decimal_number="1234-03",
                  folder_id=f_a.id, unit_type="single", threshold=5)
        prod_b = Item(sku="PROD-B", name="Изделие Б", decimal_number="АБВГ.0002",
                      folder_id=f_b.id, unit_type="single", is_product=1)
        prod_v = Item(sku="PROD-V", name="Изделие В", decimal_number="АБВГ.0003",
                      folder_id=f_v.id, unit_type="single", is_product=1)
        bolt = Item(sku="M4-BOLT", name="Болт М4х12", folder_id=metiz.id,
                    unit_type="bulk", threshold=200)
        kley = Item(sku="GLUE-EP", name="Клей эпоксидный", folder_id=glue.id,
                    unit_type="bulk", threshold=3)
        db.add_all([prod_a, d1, d2, d3, prod_b, prod_v, bolt, kley]); await db.flush()

        # BOM изделия А: Д1×2, Д2×4, Д3×1, болты×8
        db.add_all([
            Bom(product_item_id=prod_a.id, component_item_id=d1.id, quantity=2),
            Bom(product_item_id=prod_a.id, component_item_id=d2.id, quantity=4),
            Bom(product_item_id=prod_a.id, component_item_id=d3.id, quantity=1),
            Bom(product_item_id=prod_a.id, component_item_id=bolt.id, quantity=8),
        ])

        # Стартовые партии
        for item, qty, per in [(d1, 50, None), (d2, 100, None), (d3, 25, None),
                               (bolt, 1000, 100), (kley, 10, 10)]:
            db.add(Batch(item_id=item.id, supplier="ООО Поставщик",
                         invoice_number="УПД-001", quantity=qty, remaining=qty,
                         quantity_per_qr=per, delivery_date="2025-01-10"))

        # Первый админ — ЗАМЕНИТЕ на свой telegram_id!
        db.add(User(telegram_id=111111111, full_name="Администратор", role="admin"))
        await db.commit()
        print("✅ Тестовые данные загружены")

asyncio.run(seed())
