/** Сканирование QR (нативный сканер Telegram) → карточка партии → действия. */
import { useState } from 'react';
import { api } from '../lib/api';
import { haptic, tg } from '../lib/telegram';
import { BatchInfo, FolderNode } from '../types';
import { FolderTree } from './FolderTree';

type Action = null | 'scrap' | 'project';

export function Scanner() {
  const [batch, setBatch] = useState<BatchInfo | null>(null);
  const [action, setAction] = useState<Action>(null);
  const [qty, setQty] = useState(1);
  const [reason, setReason] = useState('');
  const [project, setProject] = useState<FolderNode | null>(null);

  const scan = () => {
    tg.showScanQrPopup({ text: 'Наведите камеру на QR-этикетку' }, raw => {
      try {
        const { batch_id } = JSON.parse(raw);
        haptic.success();
        api<BatchInfo>(`/batches/${batch_id}`)
          .then(b => { setBatch(b); setAction(null); setQty(1); })
          .catch(e => tg.showAlert(e.message));
        return true; // закрыть попап
      } catch {
        haptic.error();
        tg.showAlert('Это не этикетка Склад-Бота');
        return false;
      }
    });
  };

  const doScrap = async () => {
    try {
      await api('/transactions/scrap', {
        method: 'POST',
        body: JSON.stringify({ batch_id: batch!.batch_id, quantity: qty, reason }),
      });
      haptic.success();
      tg.showAlert('Списано в брак');
      setBatch(null);
    } catch (e: any) { haptic.error(); tg.showAlert(e.message); }
  };

  const doProject = async () => {
    try {
      await api('/transactions/write-off', {
        method: 'POST',
        body: JSON.stringify({ item_id: batch!.item_id, quantity: qty, project_id: project!.id }),
      });
      haptic.success();
      tg.showAlert(`Выдано на «${project!.name}»`);
      setBatch(null);
    } catch (e: any) { haptic.error(); tg.showAlert(e.message); }
  };

  if (!batch) return (
    <div>
      <h2>📷 Сканирование</h2>
      <button className="big-btn primary" onClick={scan}>📷 Сканировать QR</button>
    </div>
  );

  return (
    <div>
      <div className="card">
        <b>{batch.name}</b> ({batch.sku})<br />
        {batch.decimal_number && <>Дец. №: {batch.decimal_number}<br /></>}
        Папка: {batch.folder_name}<br />
        Поставщик: {batch.supplier}, УПД {batch.invoice_number}<br />
        Остаток партии: <b>{batch.remaining}</b> шт.
        {batch.quantity_per_qr && <span className="hint"> (в коробке {batch.quantity_per_qr})</span>}
      </div>

      {!action && (<>
        <button className="big-btn" onClick={() => setAction('project')}>🔬 Списать на R&D проект</button>
        <button className="big-btn danger" onClick={() => setAction('scrap')}>🗑 Списать в брак</button>
        <button className="big-btn" onClick={scan}>📷 Сканировать другой</button>
      </>)}

      {action && (
        <div className="card">
          <label>Количество</label>
          <div className="counter">
            <button onClick={() => setQty(Math.max(1, qty - 1))}>−</button>
            <span>{qty}</span>
            <button onClick={() => setQty(Math.min(batch.remaining, qty + 1))}>+</button>
          </div>

          {action === 'scrap' && (<>
            <label>Причина брака (обязательно)</label>
            <textarea rows={2} value={reason} onChange={e => setReason(e.target.value)}
                      placeholder="Например: скол на корпусе" />
            <button className="big-btn danger" disabled={reason.trim().length < 3}
                    onClick={doScrap}>🗑 Подтвердить списание в брак</button>
          </>)}

          {action === 'project' && (<>
            <label>Выберите проект</label>
            <FolderTree filterType="project" onSelect={setProject} selectedId={project?.id} />
            <button className="big-btn primary" disabled={!project}
                    onClick={doProject}>✅ Выдать на проект</button>
          </>)}

          <button onClick={() => setAction(null)}>← Отмена</button>
        </div>
      )}
    </div>
  );
}
