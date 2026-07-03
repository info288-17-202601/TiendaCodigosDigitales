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

if SMTP_HOST == "smtp.gmail.com":
    try:
        socket.gethostbyname(SMTP_HOST)
    except socket.gaierror:
        print("[Notificaciones] Fallo el DNS de Docker. Usando IP directa de Gmail...")
        SMTP_HOST = "172.217.192.109"


AVISO_SEGURIDAD = """
<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:12px 16px;margin:20px 32px 0;">
  <p style="font-size:12px;color:#92400e;line-height:1.6;margin:0;">
    <strong style="color:#78350f;">Aviso de seguridad:</strong> KittenZtore nunca te pedirá información personal, 
    contraseñas, datos bancarios ni códigos a través de correo electrónico. Si recibes un mensaje que solicita 
    estos datos, ignóralo y revisa siempre la comunicación en nuestra web oficial.
  </p>
</div>
"""

def _armar_html(contenido):
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f0;font-family:Arial,sans-serif;">
  <div style="max-width:520px;margin:40px auto;background:#ffffff;border-radius:12px;overflow:hidden;">

    <div style="background:#1a1a2e;padding:28px 32px;text-align:center;">
      <span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1px;">
        Kitten<span style="color:#a78bfa;">Ztore</span>
      </span>
    </div>

    <div style="padding:32px;">
      {contenido}
    </div>

    {AVISO_SEGURIDAD}

    <div style="background:#f8f8f8;padding:20px 32px;text-align:center;">
      <p style="font-size:14px;font-weight:700;color:#1a1a2e;margin:0 0 6px;">
        Kitten<span style="color:#7c3aed;">Ztore</span>
      </p>
      <p style="font-size:12px;color:#999;margin:0;line-height:1.6;">
        Este correo fue generado automáticamente, por favor no respondas.
      </p>
    </div>

  </div>
</body>
</html>
"""


def armar_mensaje_generico(asunto, mensaje_cuerpo):
    return f"{mensaje_cuerpo}\n\nGracias por usar KittenZtore."

def _armar_html_generico(asunto, mensaje_cuerpo, badge_color="#dbeafe", badge_text_color="#1e40af", badge_label="Aviso"):
    contenido = f"""
    <div style="display:inline-block;background:{badge_color};color:{badge_text_color};font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      {badge_label}
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">{asunto}</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 16px;">{mensaje_cuerpo}</p>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0;">Gracias por usar KittenZtore.</p>
    """
    return _armar_html(contenido)

def _armar_html_bienvenida(usuario):
    contenido = f"""
    <div style="display:inline-block;background:#dbeafe;color:#1e40af;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      ✦ Nueva cuenta
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">¡Bienvenido, {usuario}!</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 20px;">
      Tu cuenta fue creada con éxito. Ya puedes explorar nuestro catálogo de juegos y empezar a comprar códigos digitales al instante.
    </p>
    <p style="font-size:13px;color:#999;margin:0;">Si no creaste esta cuenta, puedes ignorar este correo.</p>
    """
    return _armar_html(contenido)

def _armar_html_pago_rechazado(id_orden_compra, motivo):
    contenido = f"""
    <div style="display:inline-block;background:#fee2e2;color:#991b1b;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      ✕ Pago no aprobado
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">Hubo un problema con tu pago</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 16px;">
      Tu pago para la orden <strong>{id_orden_compra}</strong> no fue aprobado.
    </p>
    <div style="background:#fff5f5;border:1px solid #fecaca;border-radius:8px;padding:16px 20px;margin-bottom:16px;">
      <div style="font-size:11px;color:#dc2626;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Motivo</div>
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;">{motivo}</div>
    </div>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0;">
      Puedes intentar nuevamente con otro método de pago o verificar los datos de tu tarjeta.
    </p>
    """
    return _armar_html(contenido)

def _armar_html_sin_stock(id_orden_compra, nombres_agotados):
    contenido = f"""
    <div style="display:inline-block;background:#fee2e2;color:#991b1b;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      ⚠ Sin stock
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">No pudimos completar tu orden</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 16px;">
      Lo sentimos, los siguientes juegos de tu orden <strong>{id_orden_compra}</strong> no tienen stock disponible:
    </p>
    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px 20px;margin-bottom:16px;">
      <div style="font-size:11px;color:#c2410c;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Juegos agotados</div>
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;">{nombres_agotados}</div>
    </div>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0;">Tu pago no fue cobrado. Puedes intentar más tarde o elegir otro título.</p>
    """
    return _armar_html(contenido)

def _armar_html_recuperar_contrasena(usuario):
    contenido = f"""
    <div style="display:inline-block;background:#dbeafe;color:#1e40af;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      🔒 Seguridad
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">Recuperación de contraseña</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 20px;">
      Hola <strong>{usuario}</strong>, recibimos una solicitud para restablecer la contraseña de tu cuenta.
    </p>
    <p style="font-size:13px;color:#999;margin:0;">Si no solicitaste esto, ignora este correo. Tu contraseña no cambiará.</p>
    """
    return _armar_html(contenido)

def _armar_html_compra(id_orden_compra, juego_id, codigos_entregados):
    codigos_html = ""
    for codigo in codigos_entregados:
        codigos_html += f"""
        <div style="background:#f8f7ff;border:1px solid #ddd6fe;border-radius:8px;padding:16px 20px;margin-bottom:12px;">
          <div style="font-size:11px;color:#7c3aed;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{juego_id} — código de activación</div>
          <div style="font-size:18px;font-weight:700;color:#1a1a2e;letter-spacing:2px;font-family:monospace;">{codigo}</div>
        </div>
        """
    contenido = f"""
    <div style="display:inline-block;background:#d1fae5;color:#065f46;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:16px;">
      ✓ Compra exitosa
    </div>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 12px;">¡Tu compra está lista!</h2>
    <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 16px;">
      Tu orden <strong>{id_orden_compra}</strong> fue procesada con éxito. Aquí están tus códigos de activación:
    </p>
    {codigos_html}
    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #f0f0f0;">
      <span style="color:#888;">Orden</span><span style="font-weight:600;color:#1a1a2e;">{id_orden_compra}</span>
    </div>
    """
    return _armar_html(contenido)


def _enviar(email, asunto, cuerpo_texto, cuerpo_html):
    if not SMTP_HOST:
        print(f"[Notificaciones] Modo simulacion: correo a {email}")
        print(f"Asunto: {asunto}")
        print(cuerpo_texto)
        return {"estado": "SIMULADA", "destinatario": email}

    mensaje = EmailMessage()
    mensaje["From"] = SMTP_FROM
    mensaje["To"] = email
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo_texto)
    mensaje.add_alternative(cuerpo_html, subtype='html')

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as servidor:
        if SMTP_USE_TLS:
            servidor.starttls()
        if SMTP_USER and SMTP_PASS:
            servidor.login(SMTP_USER, SMTP_PASS)
        servidor.send_message(mensaje)

    print(f"[Notificaciones] Correo enviado a {email}")
    return {"estado": "ENVIADA", "destinatario": email}


def enviar_notificacion(email, asunto, cuerpo):
    # Detectar tipo de correo por el asunto para usar la plantilla correcta
    if "Bienvenido" in asunto or "bienvenido" in asunto:
        usuario = cuerpo.split("Hola ")[1].split(",")[0] if "Hola " in cuerpo else "Usuario"
        html = _armar_html_bienvenida(usuario)
    elif "Recuperación" in asunto or "Contrasena" in asunto or "contraseña" in asunto.lower():
        usuario = cuerpo.split("Hola ")[1].split(",")[0] if "Hola " in cuerpo else "Usuario"
        html = _armar_html_recuperar_contrasena(usuario)
    elif "pago" in asunto.lower() or "no fue aprobado" in cuerpo.lower():
        id_orden = asunto.split("orden de compra ")[-1] if "orden de compra" in asunto else "N/A"
        motivo = cuerpo.split("Motivo: ")[-1].split("\n")[0] if "Motivo:" in cuerpo else "No especificado"
        html = _armar_html_pago_rechazado(id_orden, motivo)
    elif "stock" in asunto.lower():
        id_orden = asunto.split("orden ")[-1] if "orden" in asunto else "N/A"
        juegos = cuerpo.split("juegos: ")[-1].split(".")[0] if "juegos:" in cuerpo else "N/A"
        html = _armar_html_sin_stock(id_orden, juegos)
    else:
        html = _armar_html_generico(asunto, cuerpo)

    return _enviar(email, asunto, cuerpo, html)


def enviar_notificacion_compra(email, id_orden_compra, juego_id, codigos_entregados):
    asunto = f"Tu compra {id_orden_compra} fue completada"
    codigos_formateados = "\n".join(f"- {c}" for c in codigos_entregados)
    cuerpo_texto = (
        f"Tu compra fue completada con exito.\n\n"
        f"Orden: {id_orden_compra}\n"
        f"Juego: {juego_id}\n"
        f"Codigos entregados:\n{codigos_formateados}\n\n"
        f"Gracias por tu compra."
    )
    html = _armar_html_compra(id_orden_compra, juego_id, codigos_entregados)
    return _enviar(email, asunto, cuerpo_texto, html)