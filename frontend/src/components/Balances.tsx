/** Остатки: критические сверху, поиск, экспорт в Excel. */
import { useEffect, useState } from 'react';
import { api, apiDownload } from '../lib/api';
import { tg } from '../lib/telegram';
import { BalanceRow } from '../types';

export function Balances() {
  const [rows, setRows] = useState<BalanceRow[]>([]);
  const [search, setSearch] = useState('');
  const [from, setFrom] = useState(new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10));
  const [to, setTo] = useState(new Date().toISOString().slice(0, 10));

  useEffect(() => { api<BalanceRow[]>('/reports/balances').then(setRows); }, []);

  const filtered = rows.filter(r =>
    (r.name + r.sku + (r.decimal_number ?? '')).toLowerCase().includes(search.toLowerCase()));

  const download = () =>
    apiDownload('/reports/export-excel', { date_from: from, date_to: to },
      `sklad_${from}_${to}.xlsx`).catch(e => tg.showAlert(e.message));

  return (
    <div>
      <h2>📊 Остатки</h2>
      <input placeholder="🔍 Поиск" value={search} onChange={e => setSearch(e.target.value)} />
      {filtered.map(r => (
        <div key={r.id} className="card" style={{ padding: 10 }}>
          <b>{r.name}</b> ({r.sku}) <span className="hint">· {r.folder_name}</span><br />
          Остаток: <span className={r.is_low ? 'red' : 'green'}>{r.balance}</span>
          <span className="hint"> / порог {r.threshold}</span>
          {!!r.is_low && ' ⚠️'}
        </div>
      ))}
      <div className="card">
        <label>Экспорт в Excel — период</label>
        <div className="row">
          <input type="date" value={from} onChange={e => setFrom(e.target.value)} />
          <input type="date" value={to} onChange={e => setTo(e.target.value)} />
        </div>
        <button className="big-btn primary" onClick={download}>📤 Выгрузить Excel</button>
      </div>
    </div>
  );
}
