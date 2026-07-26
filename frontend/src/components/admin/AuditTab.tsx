/** Журнал операций: кто, когда, что сделал. */
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

interface AuditRow {
  created_at: string;
  transaction_type: string;
  quantity: number;
  reason: string | null;
  sku: string;
  name: string;
  user_name: string;
}

const TYPE_LABELS: Record<string, string> = {
  receipt: '📥 Приход',
  assembly: '🔧 Сборка',
  write_off: '📤 Списание',
  rd_issue: '🔬 На проект',
  scrap: '🗑 Брак',
  return: '↩️ Возврат',
};

export function AuditTab() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => { api<AuditRow[]>('/admin/audit?limit=200').then(setRows); }, []);

  const filtered = typeFilter ? rows.filter(r => r.transaction_type === typeFilter) : rows;

  return (
    <div>
      <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
        <option value="">Все операции</option>
        {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
      </select>
      {filtered.map((r, idx) => (
        <div key={idx} className="card" style={{ padding: 10 }}>
          <b>{TYPE_LABELS[r.transaction_type] ?? r.transaction_type}</b> · {r.created_at}<br />
          {r.name} ({r.sku}) × {r.quantity}<br />
          {r.reason && <span className="hint">{r.reason}<br /></span>}
          <span className="hint">👤 {r.user_name}</span>
        </div>
      ))}
    </div>
  );
}
