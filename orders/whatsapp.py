import urllib.request
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def wa_me_link(phone: str, message: str) -> str:
    """Generate a wa.me link to open WhatsApp with a pre-filled message."""
    import urllib.parse
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"


def send_whatsapp(phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via UltraMsg API.
    Falls back to logging the wa.me link if UltraMsg is not configured.
    Returns True if sent, False otherwise.
    """
    if settings.ULTRAMSG_INSTANCE_ID and settings.ULTRAMSG_TOKEN:
        return _send_ultramsg(phone, message)

    link = wa_me_link(phone, message)
    logger.info(f"[WhatsApp] Notificacion lista. Abri manualmente: {link}")
    return False  # No se envio automaticamente, solo se genero el link


def send_group(group_id: str, message: str) -> bool:
    """Send a message to a WhatsApp group via UltraMsg API."""
    if settings.ULTRAMSG_INSTANCE_ID and settings.ULTRAMSG_TOKEN:
        return _send_ultramsg_group(group_id, message)
    link = wa_me_link(settings.WHATSAPP_NUMBER, message)
    logger.info(f"[WhatsApp] Msg para grupo. Abri manualmente: {link}")
    return False


def _send_ultramsg_group(group_id: str, message: str) -> bool:
    """Send to a WhatsApp group via UltraMsg."""
    try:
        url = f"https://api.ultramsg.com/{settings.ULTRAMSG_INSTANCE_ID}/messages/group"
        payload = {
            "token": settings.ULTRAMSG_TOKEN,
            "to": group_id,
            "body": message,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("status") == "sent":
                logger.info(f"[WhatsApp] Mensaje enviado al grupo {group_id}")
                return True
            logger.warning(f"[WhatsApp] Error al enviar al grupo: {result}")
            return False
    except Exception as e:
        logger.error(f"[WhatsApp] Error de conexion al enviar al grupo: {e}")
        return False


def _send_ultramsg(phone: str, message: str) -> bool:
    """Send via UltraMsg API."""
    try:
        url = f"https://api.ultramsg.com/{settings.ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {
            "token": settings.ULTRAMSG_TOKEN,
            "to": phone,
            "body": message,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("status") == "sent":
                logger.info(f"[WhatsApp] Mensaje enviado a {phone}")
                return True
            logger.warning(f"[WhatsApp] Error al enviar: {result}")
            return False
    except Exception as e:
        logger.error(f"[WhatsApp] Error de conexion: {e}")
        return False
