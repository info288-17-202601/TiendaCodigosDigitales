import os
import smtplib
from email.message import EmailMessage


import socket

SMTP_HOST = os.environ.get("NOTIFICATIONS_SMTP_HOST")
SMTP_PORT = int(os.environ.get("NOTIFICATIONS_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("NOTIFICATIONS_SMTP_USER")
SMTP_PASS = os.environ.get("NOTIFICATIONS_SMTP_PASS")
SMTP_FROM = os.environ.get("NOTIFICATIONS_SMTP_FROM", SMTP_USER or "no-reply@localhost")
SMTP_USE_TLS = os.environ.get("NOTIFICATIONS_SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "si"}

# Parche para error de DNS en Docker Desktop con Alpine Linux
if SMTP_HOST == "smtp.gmail.com":
    try:
        socket.gethostbyname(SMTP_HOST)
    except socket.gaierror:
        print("[Notificaciones] Fallo el DNS de Docker. Usando IP directa de Gmail...")
        SMTP_HOST = "172.217.192.109"


def armar_mensaje_compra(id_orden_compra, juego_id, codigos_entregados):
    codigos_formateados = "\n".join(f"- {codigo}" for codigo in codigos_entregados)
    return (
        f"Tu compra fue completada con exito.\n\n"
        f"Orden: {id_orden_compra}\n"
        f"Juego: {juego_id or 'No especificado'}\n"
        f"Codigos entregados:\n{codigos_formateados}\n\n"
        f"Gracias por tu compra."
    )


def armar_mensaje_generico(asunto, mensaje_cuerpo):
    return f"{mensaje_cuerpo}\n\nGracias por usar KittenZtore."

def enviar_notificacion(email, asunto, cuerpo):
    if not SMTP_HOST:
        print(f"[Notificaciones] Modo simulacion: correo a {email}")
        print(f"Asunto: {asunto}")
        print(cuerpo)
        return {
            "estado": "SIMULADA",
            "destinatario": email,
        }

    mensaje = EmailMessage()
    mensaje["From"] = SMTP_FROM
    mensaje["To"] = email
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as servidor:
        if SMTP_USE_TLS:
            servidor.starttls()
        if SMTP_USER and SMTP_PASS:
            servidor.login(SMTP_USER, SMTP_PASS)
        servidor.send_message(mensaje)

    print(f"[Notificaciones] Correo enviado a {email}")
    return {
        "estado": "ENVIADA",
        "destinatario": email,
    }

def enviar_notificacion_compra(email, id_orden_compra, juego_id, codigos_entregados):
    """
    Envía la notificación de compra por correo.

    Si las credenciales SMTP no están configuradas, deja la operación en modo simulación
    para que el módulo siga siendo usable durante el desarrollo.
    """
    asunto = f"Tu compra {id_orden_compra} fue completada"
    cuerpo = armar_mensaje_compra(id_orden_compra, juego_id, codigos_entregados)

    if not SMTP_HOST:
        print(f"[Notificaciones] Modo simulacion: correo a {email}")
        print(cuerpo)
        return {
            "estado": "SIMULADA",
            "destinatario": email,
            "id_orden_compra": id_orden_compra,
        }

    mensaje = EmailMessage()
    mensaje["From"] = SMTP_FROM
    mensaje["To"] = email
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as servidor:
        if SMTP_USE_TLS:
            servidor.starttls()
        if SMTP_USER and SMTP_PASS:
            servidor.login(SMTP_USER, SMTP_PASS)
        servidor.send_message(mensaje)

    print(f"[Notificaciones] Correo enviado a {email}")
    return {
        "estado": "ENVIADA",
        "destinatario": email,
        "id_orden_compra": id_orden_compra,
    }