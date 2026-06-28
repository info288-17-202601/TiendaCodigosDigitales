import hashlib
import hmac
import json
import os

MESSAGE_SIGNING_SECRET = os.getenv("MESSAGE_SIGNING_SECRET", "IMightSeemCrazyWhatIAmBoutToSay")

def _canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _firmar_mensaje(event_name, payload):
    if not MESSAGE_SIGNING_SECRET:
        return None

    mensaje = {
        "event": event_name,
        "payload": payload
    }

    signature = hmac.new(
        MESSAGE_SIGNING_SECRET.encode("utf-8"),
        _canonical_json(mensaje),
        hashlib.sha256
    ).hexdigest()

    return {
        "algorithm": "HMAC-SHA256",
        "signature": signature
    }

def _envolver_mensaje(event_name, payload):
    firma = _firmar_mensaje(event_name, payload)
    mensaje = {
        "event": event_name,
        "payload": payload
    }
    if firma:
        mensaje["signed_hash"] = firma
    return mensaje

def _verificar_y_desempaquetar(body):
    data = json.loads(body)
    if "payload" not in data:
        return data

    if "signed_hash" not in data:
        return data["payload"]

    expected = _firmar_mensaje(data.get("event"), data.get("payload"))
    if expected is None:
        return data["payload"]

    if data.get("signed_hash", {}).get("signature") != expected.get("signature"):
        raise ValueError("Mensaje modificado o no autenticado")

    return data["payload"]


def envolver_callback(callback):
    def wrapped(ch,method,properties,body):
        try:
            payload = _verificar_y_desempaquetar(body)
            callback(ch,method,properties,payload)
        except Exception as e:
            print(f"[Messaging] Mensaje rechazado: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    return wrapped