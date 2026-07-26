/** Админ-панель: вкладки. */
import { useState } from 'react';
import { UsersTab } from './UsersTab';
import { BomTab } from './BomTab';
import { ThresholdsTab } from './ThresholdsTab';
import { AuditTab } from './AuditTab';
import { FoldersTab } from './FoldersTab';

const TABS = [
  ['users', '👥 Пользователи'],
  ['boms', '📋 Спецификации'],
  ['folders', '📁 Папки/Проекты'],
  ['thresholds', '🔔 Пороги'],
  ['audit', '📜 Журнал'],
] as const;

export function AdminPanel() {
  const [tab, setTab] = useState<string>('users');
  return (
    <div>
      <h2>⚙️ Админ-панель</h2>
      <div className="tabs">
        {TABS.map(([id, label]) => (
          <button key={id} className={tab === id ? 'active' : ''}
                  onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      {tab === 'users' && <UsersTab />}
      {tab === 'boms' && <BomTab />}
      {tab === 'folders' && <FoldersTab />}
      {tab === 'thresholds' && <ThresholdsTab />}
      {tab === 'audit' && <AuditTab />}
    </div>
  );
}
