/** R&D: выбор проекта → выбор детали из каталога → списание. И возврат ошибочных списаний. */
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { haptic, tg } from '../lib/telegram';
import { FolderNode, Item } from '../types';
import { FolderTree } from './FolderTree';

interface RecentTx {
  id: string; transaction_type: string; quantity: number;
  reason: string | null; created_at: string; name: string; sku: string;
}

export function RdProjects() {
  const [project, setProject] = useState<FolderNode | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Item | null>(null);
  const [qty, setQty] = useState(1);
  const [recent, setRecent] = useState<RecentTx[]>([]);

  useEffect(() => {
    const t = setTimeout(() =>
      api<Item[]>(`/items?search=${encodeURIComponent(search)}&is_product=0`).then(setItems), 300);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => { api<RecentTx[]>('/transactions/recent').then(setRecent); }, []);

  const issue = async () => {
    try {
      await api('/transactions/write-off', {
        method: 'POST',
        body: JSON.stringify({ item_id: selected!.id, quantity: qty, project_id: project!.id }),
      });
      haptic.success();
      tg.showAlert(`«${selected!.name}» ×${qty} выдано на «${project!.name}»`);
      setSelected(null); setQty(1);
    } catch (e: any) { haptic.error(); tg.showAlert(e.message); }
  };

  const returnTx = (tx: RecentTx) => {
    tg.showPopup({
      title: 'Возврат',
      message: `Вернуть на склад «${tx.name}» ×${tx.quantity}?`,
      buttons: [{ id: 'yes', type: 'default', text: 'Вернуть' }, { type: 'cancel' }],
    }, async id => {
      if (id !== 'yes') return;
      try {
        await api('/transactions/return', {
          method: 'POST', body: JSON.stringify({ transaction_id: tx.id }),
        });
        haptic.success();
        setRecent(await api<RecentTx[]>('/transactions/recent'));
      } catch (e: any) { tg.showAlert(e.message); }
    });
  };

  if (!project) return (
    <div>
      <h2>🔬 R&D проекты</h2>
      <p className="hint">Выберите проект:</p>
      <FolderTree filterType="project" onSelect={setProject} />
    </div>
  );

  return (
    <div>
      <h2>🔬 {project.name}</h2>
      <input placeholder="🔍 Поиск детали (название, артикул, дец. №)"
             value={search} onChange={e => setSearch(e.target.value)} />

      {!selected && items.slice(0, 20).map(i => (
        <div key={i.id} className="tree-node" onClick={() => { haptic.tap(); setSelected(i); }}>
          <b>{i.name}</b> ({i.sku}) — остаток: {i.balance}
        </div>
      ))}

      {selected && (
        <div className="card">
          <b>{selected.name}</b> — на складе {selected.balance} шт.
          <div className="counter">
            <button onClick={() => setQty(Math.max(1, qty - 1))}>−</button>
            <span>{qty}</span>
            <button onClick={() => setQty(Math.min(selected.balance, qty + 1))}>+</button>
          </div>
          <button className="big-btn primary" disabled={selected.balance < 1}
                  onClick={issue}>✅ Выдать на проект</button>
          <button onClick={() => setSelected(null)}>← Другая деталь</button>
        </div>
      )}

      <h2 style={{ marginTop: 24 }}>↩️ Последние списания (для возврата)</h2>
      {recent.map(tx => (
        <div key={tx.id} className="tree-node" onClick={() => returnTx(tx)}>
          {tx.name} ×{tx.quantity} — {tx.created_at}
          <div className="hint">{tx.reason ?? tx.transaction_type} · нажмите для возврата</div>
        </div>
      ))}
    </div>
  );
}
