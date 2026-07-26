/** Выбор изделия → редактор BOM (BomEditor из предыдущего ответа). */
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Item } from '../../types';
import { BomEditor } from './BomEditor';

export function BomTab() {
  const [products, setProducts] = useState<Item[]>([]);
  const [selected, setSelected] = useState<Item | null>(null);

  useEffect(() => { api<Item[]>('/items?is_product=1').then(setProducts); }, []);

  if (!selected) return (
    <div>
      <p className="hint">Выберите изделие для редактирования спецификации:</p>
      {products.map(p => (
        <button key={p.id} className="menu-btn" onClick={() => setSelected(p)}>🔧 {p.name}</button>
      ))}
    </div>
  );
  return (
    <div>
      <button onClick={() => setSelected(null)}>← К списку изделий</button>
      <h2>📋 BOM: {selected.name}</h2>
      <BomEditor productId={selected.id} />
    </div>
  );
}