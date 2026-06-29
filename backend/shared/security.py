import hashlib
import hmac
import json
import os
from cryptography.fernet import Fernet

MESSAGE_SIGNING_SECRET = os.getenv("MESSAGE_SIGNING_SECRET", "IMightSeemCrazyWhatIAmBoutToSay")
MESSAGE_ENCRYPTION_KEY = os.getenv("MESSAGE_ENCRYPTION_KEY")

def _get_fernet():
    if not MESSAGE_ENCRYPTION_KEY:
        return None
    return Fernet(MESSAGE_ENCRYPTION_KEY.encode())



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
    f = _get_fernet()
    if f:
        payload_cifrado = f.encrypt(json.dumps(payload).encode()).decode()
        payload_final = {"cifrado": True, "datos": payload_cifrado}
        print(f"[Crypto] Payload cifrado: {payload_cifrado[:50]}...")
    else:
        payload_final = payload

    firma = _firmar_mensaje(event_name, payload_final)  # firmar el payload_final, no el original

    mensaje = {
        "event": event_name,
        "payload": payload_final
    }
    if firma:
        mensaje["signed_hash"] = firma
    return mensaje

def _verificar_y_desempaquetar(body):
    data = json.loads(body)
    if "payload" not in data:
        return body

    if "signed_hash" not in data:
        payload = data["payload"]
        if isinstance(payload, dict) and payload.get("cifrado"):
            f = _get_fernet()
            if f:
                payload = json.loads(f.decrypt(payload["datos"].encode()))
                print(f"[Crypto] Mensaje descifrado: {payload}")
        return json.dumps(payload).encode('utf-8')

    expected = _firmar_mensaje(data.get("event"), data.get("payload"))
    if expected is None:
        payload = data["payload"]
        if isinstance(payload, dict) and payload.get("cifrado"):
            f = _get_fernet()
            if f:
                payload = json.loads(f.decrypt(payload["datos"].encode()))
                print(f"[Crypto] Mensaje descifrado: {payload}")
        return json.dumps(payload).encode('utf-8')

    if data.get("signed_hash", {}).get("signature") != expected.get("signature"):
        raise ValueError("Mensaje modificado o no autenticado")

    payload = data["payload"]
    if isinstance(payload, dict) and payload.get("cifrado"):
        f = _get_fernet()
        if f:
            payload = json.loads(f.decrypt(payload["datos"].encode()))
            print(f"[Crypto] Mensaje descifrado: {payload}")
    return json.dumps(payload).encode('utf-8')


def envolver_callback(callback):
    def wrapped(ch,method,properties,body):
        try:
            payload = _verificar_y_desempaquetar(body)
            callback(ch,method,properties,payload)
        except Exception as e:
            print(f"[Messaging] Mensaje rechazado: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    return wrapped