/** Создание папок и R&D проектов. */
import { useState } from 'react';
import { api } from '../../lib/api';
import { tg, haptic } from '../../lib/telegram';
import { FolderNode } from '../../types';
import { FolderTree } from '../FolderTree';

export function FoldersTab() {
  const [parent, setParent] = useState<FolderNode | null>(null);
  const [name, setName] = useState('');
  const [key, setKey] = useState(0); // перерисовка дерева после создания

  const create = async () => {
    const type = parent?.type === 'rd' ? 'project' : 'generic';
    try {
      await api('/folders/create', {
        method: 'POST',
        body: JSON.stringify({ name, parent_id: parent?.id ?? null, type }),
      });
      haptic.success(); setName(''); setKey(k => k + 1);
    } catch (e: any) { tg.showAlert(e.message); }
  };

  return (
    <div>
      <p className="hint">1. Выберите родительскую папку. 2. Введите имя новой.</p>
      <FolderTree key={key} onSelect={setParent} selectedId={parent?.id} />
      <div className="card">
        <label>Имя новой папки {parent?.type === 'rd' && '(будет создан R&D проект)'}</label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Проект Z" />
        <button className="big-btn primary" disabled={!name || !parent} onClick={create}>
          ➕ Создать в «{parent?.name ?? '—'}»
        </button>
      </div>
    </div>
  );
}
