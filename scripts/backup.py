"""Бэкап SQLite через API .backup (безопасно при работающем приложении, WAL).
Запускать по расписанию Task Scheduler, например каждые 6 часов."""
import sqlite3, datetime, pathlib

SRC = r"C:\sklad-bot\data\warehouse.db"
DST_DIR = pathlib.Path(r"C:\sklad-bot\backups")
DST_DIR.mkdir(parents=True, exist_ok=True)

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
dst = DST_DIR / f"warehouse_{stamp}.db"

src_conn = sqlite3.connect(SRC)
dst_conn = sqlite3.connect(dst)
with dst_conn:
    src_conn.backup(dst_conn)   # онлайн-бэкап, не блокирует приложение
src_conn.close()
dst_conn.close()

# Ротация: храним 60 последних копий
backups = sorted(DST_DIR.glob("warehouse_*.db"))
for old in backups[:-60]:
    old.unlink()

print(f"✅ Бэкап создан: {dst}")
