/** Общие типы данных (зеркалят Pydantic-схемы бэкенда). */

export type Screen = 'menu' | 'receive' | 'scan' | 'assembly' | 'rd' | 'balances' | 'admin';

export interface UserProfile {
  telegram_id: number;
  full_name: string | null;
  role: 'user' | 'manager' | 'admin';
}

export interface FolderNode {
  id: string;
  name: string;
  parent_id: string | null;
  type: 'root' | 'serial' | 'consumable' | 'rd' | 'project' | 'generic';
  children: FolderNode[];
}

export interface Item {
  id: string;
  sku: string;
  name: string;
  decimal_number: string | null;
  folder_id: string;
  unit_type: 'single' | 'bulk';
  threshold: number;
  is_product: number;
  balance: number;
}

export interface BatchInfo {
  batch_id: string;
  item_id: string;
  sku: string;
  name: string;
  decimal_number: string | null;
  supplier: string;
  invoice_number: string;
  delivery_date: string;
  quantity: number;
  remaining: number;
  quantity_per_qr: number | null;
  unit_type: 'single' | 'bulk';
  folder_name: string;
}

export interface QrLabel {
  qr_id: string;
  quantity: number;
  png_base64: string;
}

export interface ReceiveResponse {
  batch_id: string;
  item_name: string;
  sku: string;
  qr_codes: QrLabel[];
}

export interface BalanceRow {
  id: string;
  sku: string;
  name: string;
  decimal_number: string | null;
  folder_name: string;
  balance: number;
  threshold: number;
  is_low: number;
}

export interface Shortage {
  item_id: string;
  sku: string;
  name: string;
  decimal_number: string | null;
  required: number;
  available: number;
  missing: number;
}
