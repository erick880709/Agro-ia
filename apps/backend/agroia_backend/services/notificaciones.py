"""Servicio de notificaciones (1.I) — WhatsApp Cloud API con degradación total."""

import json
import os
import urllib.request

from agroia.logging import get_logger

logger = get_logger(__name__)

# Variables de entorno para la integración real (Meta WhatsApp Cloud API)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v20.0")


def enviar_whatsapp(telefono: str, template_nombre: str, parametros: list[str] | None = None) -> dict:
    """Envía un mensaje de plantilla de WhatsApp.

    Sin credenciales configuradas degrada a no-op registrado en log:
    la plataforma sigue funcionando con el dashboard (regla de degradación).
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        logger.info(
            "whatsapp_no_configurado",
            telefono=telefono,
            template=template_nombre,
            estado="omitido (sin WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID)",
        )
        return {"estado": "omitido", "motivo": "credenciales_ausentes"}

    url = f"https://graph.facebook.com/{WHATSAPP_VERSION}/{WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "template",
        "template": {
            "name": template_nombre,
            "language": {"code": "es_CO"},
        },
    }
    if parametros:
        payload["template"]["components"] = [{
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in parametros],
        }]

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            respuesta = json.loads(r.read().decode("utf-8"))
        logger.info("whatsapp_enviado", telefono=telefono, template=template_nombre)
        return {"estado": "enviado", "respuesta": respuesta}
    except Exception as e:  # noqa: BLE001 — no bloquear el scheduler
        logger.warning("whatsapp_error", error=str(e), template=template_nombre)
        return {"estado": "error", "motivo": str(e)[:200]}


def enviar_sms(telefono: str, mensaje: str) -> dict:
    """Fallback SMS (Twilio/Infobip). Sin credenciales: no-op registrado."""
    logger.info("sms_no_configurado", telefono=telefono, estado="omitido")
    return {"estado": "omitido", "motivo": "credenciales_ausentes"}
