import logging
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.chatbot_service import handle_whatsapp_message
from app.services.whatsapp_service import send_whatsapp_message, mark_message_as_read

logger = logging.getLogger("munchbot.webhook")

router = APIRouter(
    prefix="/webhook",
    tags=["WhatsApp Webhook"],
)


# ── Meta Webhook Verification (GET) ───────────────────────────────────────────
@router.get("")
@router.get("/")
def verify_webhook(request: Request):
    """
    Meta WhatsApp Cloud API webhook verification.
    Meta sends GET with hub.mode=subscribe, hub.verify_token, hub.challenge.
    We must echo back hub.challenge as plain text to confirm ownership.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Meta WhatsApp webhook verified successfully.")
        return Response(content=challenge, media_type="text/plain")

    logger.warning(
        f"⚠️ Webhook verification failed — mode={mode}, token_match={token == settings.WHATSAPP_VERIFY_TOKEN}"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed. Token mismatch.",
    )


# ── Meta Webhook Message Receiver (POST) ──────────────────────────────────────
@router.post("")
@router.post("/")
async def handle_incoming_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive incoming events from Meta WhatsApp Cloud API.
    Handles: text messages, status updates, and non-text types gracefully.

    Meta always expects HTTP 200 back — even if we can't process the message.
    We MUST return 200 or Meta will retry endlessly.
    """
    logger.info("🔥 WEBHOOK POST RECEIVED")
    try:
        payload = await request.json()
    except Exception:
        # Always return 200 to Meta
        return {"status": "ignored", "reason": "invalid JSON body"}

    # ── Handle direct test JSON format: {"from": "...", "text": "..."} ────────
    if "from" in payload and "text" in payload:
        sender_phone = payload["from"] #----------------------#
        incoming_text = payload["text"]
        return await _process_and_reply(db, sender_phone, incoming_text, message_id=None)

    # ── Handle Meta Cloud API payload ─────────────────────────────────────────
    # Expected structure:
    # { "object": "whatsapp_business_account", "entry": [{ "changes": [{ "value": {...} }] }] }
    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored", "reason": "not a whatsapp_business_account event"}

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
    except (KeyError, IndexError):
        return {"status": "ignored", "reason": "malformed entry/changes structure"}

    # ── Status updates (delivery, read receipts) — acknowledge and skip ────────
    if "statuses" in value:
        statuses = value["statuses"]
        for s in statuses:
            logger.info(f"[META] Message status update — id: {s.get('id')} status: {s.get('status')}")
        return {"status": "ok", "reason": "status_update_acknowledged"}

    # ── Incoming messages ──────────────────────────────────────────────────────
    messages = value.get("messages", [])
    if not messages:
        return {"status": "ignored", "reason": "no messages in payload"}

    msg = messages[0]
    sender_phone = msg.get("from")
    msg_id = msg.get("id")
    msg_type = msg.get("type", "unknown")

    if not sender_phone:
        return {"status": "ignored", "reason": "no sender phone number"}

    # Mark message as read immediately (shows blue ticks on sender's phone)
    if msg_id:
        try:
            mark_message_as_read(msg_id)
        except Exception as e:
            logger.warning(f"[META] Could not mark message as read: {e}")

    # ── Only handle text messages ──────────────────────────────────────────────
    if msg_type != "text":
        unsupported_msg = (
            "👋 Hi! MunchBot only supports text messages.\n\n"
            "Send *MENU* to see available food items and start ordering!"
        )
        send_whatsapp_message(sender_phone, unsupported_msg)
        return {"status": "ok", "reason": f"unsupported_type_{msg_type}_replied"}

    incoming_text = msg.get("text", {}).get("body", "").strip()
    if not incoming_text:
        return {"status": "ignored", "reason": "empty text body"}

    return await _process_and_reply(db, sender_phone, incoming_text, msg_id)


async def _process_and_reply(db: Session, sender_phone: str, incoming_text: str, message_id: str | None) -> dict:
    """Core: pass message to chatbot engine and dispatch reply."""
    logger.info(f"[WEBHOOK] From: {sender_phone} | Message: '{incoming_text}'")

    try:
        reply_text = handle_whatsapp_message(db, sender_phone, incoming_text)
    except Exception as e:
        logger.error(f"[WEBHOOK] Chatbot engine error for {sender_phone}: {e}")
        reply_text = "⚠️ Sorry, something went wrong. Please try again in a moment!"

    try:
        send_result = send_whatsapp_message(sender_phone, reply_text)
    except Exception as e:
        logger.error(f"[WEBHOOK] Failed to send reply: {e}")
        send_result = None

    return {
        "status": "success",
        "sender": sender_phone,
        "reply": reply_text,
        "send_result": send_result,
    }
