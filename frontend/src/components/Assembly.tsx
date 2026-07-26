// src/components/Assembly.tsx
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { haptic, tg } from '../lib/telegram';

interface Product { id: string; name: string; }
interface Shortage { sku: string; name: string; required: number; available: number; missing: number; }

export function Assembly() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Product | null>(null);
  const [count, setCount] = useState(1);
  const [shortages, setShortages] = useState<Shortage[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api<Product[]>('/items?is_product=1').then(setProducts); }, []);

  const assemble = async () => {
    if (!selected) return;
    setBusy(true); setShortages([]);
    try {
      const res = await api<any>('/boms/assemble', {
        method: 'POST',
        body: JSON.stringify({ product_item_id: selected.id, count }),
      });
      if (res.success) {
        haptic.success();
        tg.showPopup({ title: '✅ Готово', message: res.message, buttons: [{ type: 'ok' }] });
      } else {
        haptic.error();
        setShortages(res.shortages);   // показать список недостающего
      }
    } catch (e: any) {
      haptic.error();
      tg.showAlert(e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="screen">
      <h2>🔧 Сборка изделия</h2>

      {products.map(p => (
        <button key={p.id}
          className={`select-btn ${selected?.id === p.id ? 'active' : ''}`}
          onClick={() => { haptic.tap(); setSelected(p); }}>
          {p.name}
        </button>
      ))}

      {selected && (
        <>
          <div className="counter">
            <button onClick={() => setCount(Math.max(1, count - 1))}>−</button>
            <span>{count} шт.</span>
            <button onClick={() => setCount(count + 1)}>+</button>
          </div>
          <button className="big-btn primary" disabled={busy} onClick={assemble}>
            {busy ? '⏳ Списываем…' : `🔧 Собрать ${count} шт.`}
          </button>
        </>
      )}

      {shortages.length > 0 && (
        <div className="shortage-card">
          <h3>❌ Не хватает деталей:</h3>
          {shortages.map(s => (
            <div key={s.sku} className="shortage-row">
              <b>{s.name}</b> ({s.sku})<br/>
              Нужно: {s.required} · На складе: {s.available} ·
              <span className="red"> Не хватает: {s.missing}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
