/** Управление доступом к боту. */
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { tg, haptic } from '../../lib/telegram';

interface U { telegram_id: number; username: string | null; full_name: string | null; role: string; is_active: boolean; }

export function UsersTab() {
  const [users, setUsers] = useState<U[]>([]);
  const [form, setForm] = useState({ telegram_id: '', full_name: '', role: 'user' });

  const load = () => api<U[]>('/admin/users').then(setUsers);
  useEffect(() => { load(); }, []);

  const save = async (u: Partial<U> & { telegram_id: number }) => {
    try {
      await api('/admin/users', { method: 'POST', body: JSON.stringify(u) });
      haptic.success(); load();
    } catch (e: any) { tg.showAlert(e.message); }
  };

  return (
    <div>
      <div className="card">
        <label>Telegram ID нового пользователя</label>
        <input type="number" value={form.telegram_id}
               onChange={e => setForm({ ...form, telegram_id: e.target.value })} />
        <label>ФИО</label>
        <input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
        <label>Роль</label>
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
          <option value="user">Сборщик/Кладовщик</option>
          <option value="manager">Менеджер по закупкам</option>
          <option value="admin">Администратор</option>
        </select>
        <button className="big-btn primary" disabled={!form.telegram_id}
                onClick={() => save({ telegram_id: +form.telegram_id, full_name: form.full_name, role: form.role, is_active: true } as any)}>
          ➕ Выдать доступ
        </button>
        <p className="hint">ID можно узнать через бота @userinfobot</p>
      </div>
      {users.map(u => (
        <div key={u.telegram_id} className="card" style={{ padding: 10 }}>
          <b>{u.full_name ?? u.username ?? u.telegram_id}</b> — {u.role}
          {!u.is_active && <span className="red"> (отключен)</span>}
          <button onClick={() => save({ ...u, is_active: !u.is_active })}>
            {u.is_active ? '🚫 Отключить' : '✅ Включить'}
          </button>
        </div>
      ))}
    </div>
  );
}
