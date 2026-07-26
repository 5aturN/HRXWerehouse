/** Печать QR-этикеток (58×40 мм) после приемки. */
import { ReceiveResponse } from '../types';

export function PrintLabels({ result, onDone }: { result: ReceiveResponse; onDone: () => void }) {
  return (
    <div>
      <h2>🖨 Этикетки: {result.item_name}</h2>
      <p className="hint">Этикеток: {result.qr_codes.length}. Нажмите «Печать», затем наклейте на товар/коробки.</p>
      <div className="print-area">
        {result.qr_codes.map(qr => (
          <div className="label" key={qr.qr_id}>
            <img src={`data:image/png;base64,${qr.png_base64}`} alt="QR" />
            <div className="cap">{result.sku} · {result.item_name} · {qr.quantity} шт.</div>
          </div>
        ))}
      </div>
      <button className="big-btn primary" onClick={() => window.print()}>🖨 Печать</button>
      <button className="big-btn" onClick={onDone}>✅ Готово, к следующей приемке</button>
    </div>
  );
}
