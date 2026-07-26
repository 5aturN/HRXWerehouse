/** Настройка порогов уведомлений по позициям. */
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { tg, haptic } from '../../lib/telegram';
import { Item } from '../../types';

export function ThresholdsTab() {
  const [items, setItems] = useState<Item[]>([]);
  const [search, setSearch] = useState('');
  const [managerId, setManagerId] = useState('');

  useEffect(() => { api<Item[]>('/items').then(setItems); }, []);

  const save = async (itemId: string, threshold: number) => {
    if (!managerId) { tg.showAlert('Сначала укажите Telegram ID менеджера'); return; }
    try {
      await api('/admin/thresholds', {
        method: 'POST',
        body: JSON.stringify({
          item_id: itemId,
          manager_telegram_id: +managerId,
          threshold,
          is_active: true,
        }),
      });
      haptic.success();
    } catch (e: any) {
      haptic.error();
      tg.showAlert(e.message);
    }
  };

  const filtered = items.filter(i =>
    (i.name + i.sku).toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="card">
        <label>Telegram ID менеджера по закупкам (получатель уведомлений)</label>
        <input type="number" value={managerId}
               onChange={e => setManagerId(e.target.value)} placeholder="123456789" />
      </div>
      <input placeholder="🔍 Поиск позиции" value={search}
             onChange={e => setSearch(e.target.value)} />
      {filtered.slice(0, 30).map(i => (
        <ThresholdRow key={i.id} item={i} onSave={save} />
      ))}
    </div>
  );
}

/** Строка позиции: остаток + редактируемый порог. */
function ThresholdRow({ item, onSave }: {
  item: Item;
  onSave: (itemId: string, threshold: number) => void;
}) {
  const [value, setValue] = useState(item.threshold);
  return (
    <div className="card" style={{ padding: 10 }}>
      <b>{item.name}</b> ({item.sku}) — остаток: {item.balance}
      <div className="row">
        <input type="number" min={0} value={value}
               onChange={e => setValue(+e.target.value)} style={{ marginBottom: 0 }} />
        <button style={{ width: 'auto', padding: '0 20px', marginBottom: 0 }}
                onClick={() => onSave(item.id, value)}>💾</button>
      </div>
    </div>
  );
}
