"""qr_code_handler: генерация QR-кодов (PNG base64) и разбор скана."""
import base64, io, json
import qrcode

def generate_qr(batch_id: str) -> str:
    """Генерирует PNG QR-кода, содержащего ТОЛЬКО batch_id. Возвращает base64."""
    payload = json.dumps({"batch_id": batch_id})
    img = qrcode.make(payload, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def decode_qr(scan_data: str) -> str:
    """Извлекает batch_id из данных скана. Бросает ValueError, если QR чужой."""
    try:
        return json.loads(scan_data)["batch_id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("QR-код не является этикеткой Склад-Бота")
