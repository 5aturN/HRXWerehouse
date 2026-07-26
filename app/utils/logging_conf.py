"""Логирование: файл + консоль, ротация по 5 МБ."""
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_dir: str = "C:/sklad-bot/logs"):
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = RotatingFileHandler(f"{log_dir}/sklad.log", maxBytes=5_000_000,
                             backupCount=10, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(ch)
