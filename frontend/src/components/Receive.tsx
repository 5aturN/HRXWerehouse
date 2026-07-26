/** Экран «Приемка»: мастер из 3 шагов → печать этикеток. */
import { useState } from 'react';
import { api } from '../lib/api';
import { haptic, tg } from '../lib/telegram';
import { FolderNode, ReceiveResponse } from '../types';
import { FolderTree } from './FolderTree';
import { PrintLabels } from './PrintLabels';

export function Receive() {
  const [step, setStep] = useState(1);
  const [folder, setFolder] = useState<FolderNode | null>(null);
  const [form, setForm] = useState({
    sku: '', name: '', decimal_number: '', supplier: '', invoice_number: '',
    delivery_date: new Date().toISOString().slice(0, 10),
    quantity: 1, unit_type: 'single' as 'single' | 'bulk', quantity_per_qr: 10,
  });
  const [result, setResult] = useState<ReceiveResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: string, v: unknown) => setForm({ ...form, [k]: v });

  const submit = async () => {
    if (!folder) return;
    setBusy(true);
    try {
      const res = await api<ReceiveResponse>('/batches/receive', {
        method: 'POST',
        body: JSON.stringify({
          folder_id: folder.id, ...form,
          decimal_number: form.decimal_number || null,
          quantity_per_qr: form.unit_type === 'bulk' ? form.quantity_per_qr : null,
        }),
      });
      haptic.success();
      setResult(res);
    } catch (e: any) {
      haptic.error();
      tg.showAlert(e.message);
    } finally { setBusy(false); }
  };

  if (result) return <PrintLabels result={result} onDone={() => { setResult(null); setStep(1); }} />;

  return (
    <div>
      <h2>📥 Приемка — шаг {step} из 3</h2>

      {step === 1 && (<>
        <p className="hint">Куда положить товар?</p>
        <FolderTree onSelect={setFolder} selectedId={folder?.id} />
        <button className="big-btn primary" disabled={!folder}
                onClick={() => setStep(2)}>Далее → {folder ? `(${folder.name})` : ''}</button>
      </>)}

      {step === 2 && (<>
        <label>Артикул (SKU)</label>
        <input value={form.sku} onChange={e => set('sku', e.target.value)} placeholder="D-1234-01" />
        <label>Наименование</label>
        <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="Деталь 1" />
        <label>Децимальный номер {folder?.type === 'serial' ? '(обязательно)' : '(если есть)'}</label>
        <input value={form.decimal_number} onChange={e => set('decimal_number', e.target.value)} />
        <label>Поставщик</label>
        <input value={form.supplier} onChange={e => set('supplier', e.target.value)} />
        <label>Номер УПД</label>
        <input value={form.invoice_number} onChange={e => set('invoice_number', e.target.value)} />
        <label>Дата поставки</label>
        <input type="date" value={form.delivery_date} onChange={e => set('delivery_date', e.target.value)} />
        <button className="big-btn primary"
                disabled={!form.sku || !form.name || !form.supplier || !form.invoice_number}
                onClick={() => setStep(3)}>Далее →</button>
      </>)}

      {step === 3 && (<>
        <label>Тип учета</label>
        <div className="row">
          <button className={`select-btn ${form.unit_type === 'single' ? 'active' : ''}`}
                  onClick={() => set('unit_type', 'single')}>Штучный (1 QR = 1 шт.)</button>
          <button className={`select-btn ${form.unit_type === 'bulk' ? 'active' : ''}`}
                  onClick={() => set('unit_type', 'bulk')}>Россыпь (1 QR = N шт.)</button>
        </div>
        <label>Общее количество</label>
        <input type="number" min={1} value={form.quantity}
               onChange={e => set('quantity', +e.target.value)} />
        {form.unit_type === 'bulk' && (<>
          <label>Штук в одной коробке (на 1 QR)</label>
          <input type="number" min={1} value={form.quantity_per_qr}
                 onChange={e => set('quantity_per_qr', +e.target.value)} />
        </>)}
        <button className="big-btn primary" disabled={busy} onClick={submit}>
          {busy ? '⏳ Сохраняем…' : '✅ Принять и напечатать этикетки'}
        </button>
      </>)}
    </div>
  );
}
