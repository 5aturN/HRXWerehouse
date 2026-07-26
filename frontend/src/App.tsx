/** Корневой компонент: авторизация, меню, роутинг экранов, BackButton. */
import { useEffect, useState, useCallback } from 'react';
import { api } from './lib/api';
import { initTelegram, haptic, tg } from './lib/telegram';
import { Screen, UserProfile } from './types';
import { Receive } from './components/Receive';
import { Scanner } from './components/Scanner';
import { Assembly } from './components/Assembly';
import { RdProjects } from './components/RdProjects';
import { Balances } from './components/Balances';
import { AdminPanel } from './components/admin/AdminPanel';

export default function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    initTelegram();
    api<UserProfile>('/auth/telegram', { method: 'POST' })
      .then(setUser)
      .catch(e => setAuthError(e.message));
  }, []);

  // Кнопка «Назад» Telegram возвращает в меню
  const goMenu = useCallback(() => setScreen('menu'), []);
  useEffect(() => {
    if (screen === 'menu') tg.BackButton.hide();
    else { tg.BackButton.show(); tg.BackButton.onClick(goMenu); }
    return () => tg.BackButton.offClick(goMenu);
  }, [screen, goMenu]);

  if (authError) return <div className="card red">⛔ {authError}</div>;
  if (!user) return <div className="card">⏳ Загрузка…</div>;

  if (screen === 'menu') {
    const menu: [Screen, string, string, boolean][] = [
      ['receive', '📥', 'Приемка', true],
      ['scan', '📷', 'Сканировать QR', true],
      ['assembly', '🔧', 'Сборка', true],
      ['rd', '🔬', 'R&D проекты', true],
      ['balances', '📊', 'Остатки', true],
      ['admin', '⚙️', 'Админ-панель', user.role === 'admin'],
    ];
    return (
      <div>
        <h2>📦 Склад-Бот</h2>
        <p className="hint">Здравствуйте, {user.full_name ?? 'коллега'}!</p>
        {menu.filter(m => m[3]).map(([s, icon, label]) => (
          <button key={s} className="menu-btn"
                  onClick={() => { haptic.tap(); setScreen(s); }}>
            <span className="icon">{icon}</span>{label}
          </button>
        ))}
      </div>
    );
  }

  switch (screen) {
    case 'receive': return <Receive />;
    case 'scan': return <Scanner />;
    case 'assembly': return <Assembly />;
    case 'rd': return <RdProjects />;
    case 'balances': return <Balances />;
    case 'admin': return <AdminPanel />;
  }
}
