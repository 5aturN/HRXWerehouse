/** Дерево папок с выбором. Используется в Приемке и Админке. */
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { haptic } from '../lib/telegram';
import { FolderNode } from '../types';

interface Props {
  onSelect: (folder: FolderNode) => void;
  selectedId?: string;
  filterType?: string;          // например, показывать только 'project'
}

export function FolderTree({ onSelect, selectedId, filterType }: Props) {
  const [tree, setTree] = useState<FolderNode[]>([]);
  const [open, setOpen] = useState<Set<string>>(new Set());

  useEffect(() => { api<FolderNode[]>('/folders/tree').then(setTree); }, []);

  const toggle = (id: string) => {
    const next = new Set(open);
    next.has(id) ? next.delete(id) : next.add(id);
    setOpen(next);
  };

  const renderNode = (n: FolderNode, depth: number) => {
    const selectable = !filterType || n.type === filterType;
    return (
      <div key={n.id} style={{ marginLeft: depth * 16 }}>
        <div
          className={`tree-node ${selectedId === n.id ? 'selected' : ''}`}
          onClick={() => {
            haptic.tap();
            if (n.children.length) toggle(n.id);
            if (selectable) onSelect(n);
          }}>
          {n.children.length > 0 ? (open.has(n.id) ? '📂' : '📁') : '📄'} {n.name}
        </div>
        {open.has(n.id) && n.children.map(c => renderNode(c, depth + 1))}
      </div>
    );
  };

  return <div>{tree.map(n => renderNode(n, 0))}</div>;
}
