"""Все Pydantic-схемы приложения."""
from pydantic import BaseModel, Field

# ---------- Папки ----------
class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: str | None = None
    type: str = Field("generic", pattern="^(serial|consumable|rd|project|generic)$")

class FolderNode(BaseModel):
    id: str
    name: str
    parent_id: str | None
    type: str
    children: list["FolderNode"] = []

# ---------- Товары ----------
class ItemCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    decimal_number: str | None = None
    folder_id: str
    unit_type: str = Field(..., pattern="^(single|bulk)$")
    threshold: int = Field(5, ge=0)
    is_product: bool = False

class ItemOut(ItemCreate):
    id: str
    balance: int = 0

# ---------- Приемка ----------
class ReceiveRequest(BaseModel):
    folder_id: str
    sku: str
    name: str
    decimal_number: str | None = None
    supplier: str = Field(..., min_length=1)
    invoice_number: str = Field(..., min_length=1)
    delivery_date: str                       # YYYY-MM-DD
    quantity: int = Field(..., ge=1)
    unit_type: str = Field(..., pattern="^(single|bulk)$")
    quantity_per_qr: int | None = Field(None, ge=1)

class QrOut(BaseModel):
    qr_id: str
    quantity: int
    png_base64: str                          # для печати этикетки

class ReceiveResponse(BaseModel):
    batch_id: str
    item_name: str
    sku: str
    qr_codes: list[QrOut]

# ---------- Операции ----------
class WriteOffRequest(BaseModel):
    item_id: str
    quantity: int = Field(..., ge=1)
    project_id: str | None = None            # обязателен для rd_issue
    reason: str | None = None

class ScrapRequest(BaseModel):
    batch_id: str
    quantity: int = Field(..., ge=1)
    reason: str = Field(..., min_length=3, max_length=500)

class ReturnRequest(BaseModel):
    transaction_id: str

# ---------- Отчеты ----------
class ExportRequest(BaseModel):
    date_from: str                           # YYYY-MM-DD
    date_to: str

# ---------- Админ ----------
class UserUpsert(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str | None = None
    role: str = Field("user", pattern="^(user|manager|admin)$")
    is_active: bool = True

class ThresholdSet(BaseModel):
    item_id: str
    manager_telegram_id: int
    threshold: int = Field(..., ge=0)
    is_active: bool = True
