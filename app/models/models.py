"""ORM-модели SQLAlchemy 2.0. Все PK — TEXT (UUID строкой)."""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def _uuid() -> str:
    return str(uuid.uuid4())

def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


class Base(DeclarativeBase):
    pass


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("parent_id", "name"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(Text)  # root/serial/consumable/rd/project/generic
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class Item(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    sku: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    decimal_number: Mapped[str | None] = mapped_column(Text)
    folder_id: Mapped[str] = mapped_column(ForeignKey("folders.id", ondelete="RESTRICT"))
    unit_type: Mapped[str] = mapped_column(Text)  # single/bulk
    threshold: Mapped[int] = mapped_column(Integer, default=5)
    is_product: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class Bom(Base):
    __tablename__ = "boms"
    __table_args__ = (UniqueConstraint("product_item_id", "component_item_id"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    product_item_id: Mapped[str] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    component_item_id: Mapped[str] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"))
    supplier: Mapped[str] = mapped_column(Text)
    invoice_number: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer)
    quantity_per_qr: Mapped[int | None] = mapped_column(Integer)
    delivery_date: Mapped[str] = mapped_column(Text)
    remaining: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class QrCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"))
    qr_code_data: Mapped[str] = mapped_column(Text, unique=True)
    quantity: Mapped[int] = mapped_column(Integer)
    is_used: Mapped[int] = mapped_column(Integer, default=0)
    printed_at: Mapped[str] = mapped_column(Text, default=_now)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id", ondelete="RESTRICT"))
    qr_code_id: Mapped[str | None] = mapped_column(ForeignKey("qr_codes.id"))
    transaction_type: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(Text)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("folders.id"))
    assembly_group: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, default="user")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(Text, default=_now)


class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    __table_args__ = (UniqueConstraint("manager_telegram_id", "item_id"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    manager_telegram_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    threshold: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    last_notified_at: Mapped[str | None] = mapped_column(Text)
