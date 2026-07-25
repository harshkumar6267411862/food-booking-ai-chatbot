import logging
import urllib.request
import urllib.error
import json
import requests
from app.config import settings

logger = logging.getLogger("munchbot.whatsapp")

# In-memory log of sent messages (useful for mock testing and verification)
SENT_MESSAGES: list[dict] = []

# Meta Graph API version
META_API_VERSION = "v25.0"


def send_whatsapp_message(to_phone: str, text: str) -> dict:
    """
    Send a WhatsApp text message using the configured provider (mock or meta).
    """
    provider = (settings.WHATSAPP_PROVIDER or "mock").lower()

    # Normalise phone number — strip any leading "whatsapp:" prefix
    clean_phone = to_phone.replace("whatsapp:", "").strip()

    payload_record = {
        "to": clean_phone,
        "text": text,
        "provider": provider,
    }
    SENT_MESSAGES.append(payload_record)

    if provider == "meta" and settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
        return _send_via_meta(clean_phone, text)

    # Mock / fallback
    logger.info(f"[MOCK WHATSAPP] To: {clean_phone} | Message: {text}")
    return {"status": "sent", "provider": "mock", "payload": payload_record}


import requests

def _send_via_meta(to_phone: str, text: str):
    url = (
        f"https://graph.facebook.com/v25.0/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text,
        },
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10,
        )
        if response.status_code != 200:
            logger.error(
                f"[META WHATSAPP ERROR {response.status_code}]: {response.text}\n"
                f"--> ACTION REQUIRED: Check/refresh WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID in your Render environment variables!"
            )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"[META WHATSAPP FAILED] Could not deliver message to {to_phone}: {e}")
        return {"status": "error", "detail": str(e)}

def mark_message_as_read(message_id: str) -> dict:
    """
    Mark an incoming message as read (shows double blue ticks on sender's end).
    Only works in Meta provider mode.
    """
    if settings.WHATSAPP_PROVIDER.lower() != "meta":
        return {"status": "skipped", "reason": "not in meta mode"}

    url = (
        f"https://graph.facebook.com/{META_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"status": "read_marked", "message_id": message_id}
    except Exception as e:
        logger.warning(f"[META] Could not mark message as read: {e}")
        return {"status": "error", "detail": str(e)}


def clear_sent_messages():
    """Clear sent message buffer (useful for test resets)."""
    SENT_MESSAGES.clear()
