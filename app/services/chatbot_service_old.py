import re
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.enums.user_role import UserRole
from app.utils.security import hash_password

from app.repositories.user_repository import get_user_by_phone, create_user
from app.services.stall_service import get_stalls
from app.services.menu_item_service import get_menu_items, get_menu_item_by_id_service
from app.services.pickup_slot_service import get_available_pickup_slots
from app.services.order_service import create_order, get_my_orders, cancel_order
from app.schemas.order import OrderCreate, OrderItemCreate
from app.enums.cancelled_by import CancelledBy

# In-memory draft orders per phone number
# Format: { phone_number: { "items": { menu_item_id: quantity }, "slot_id": int | None } }
USER_DRAFTS: dict[str, dict] = {}


def get_or_create_user_by_phone(db: Session, phone_number: str, name: str = "Student") -> User:
    """Ensure user exists by phone number; create guest student account if missing."""
    clean_phone = phone_number.replace("whatsapp:", "").strip()
    user = get_user_by_phone(db, clean_phone)

    if not user:
        reg_num = f"WA{clean_phone[-8:]}" if len(clean_phone) >= 8 else f"WA{clean_phone}"
        user = User(
            registration_number=reg_num,
            name=name,
            email=f"{clean_phone}@munchbot.local",
            phone_number=clean_phone,
            password_hash=hash_password("WhatsAppDefault1!"),
            role=UserRole.STUDENT
        )
        create_user(db, user)
    
    return user


def handle_whatsapp_message(db: Session, sender_phone: str, message_text: str) -> str:
    """
    Process incoming text message from a WhatsApp phone number and return response text.
    """
    clean_phone = sender_phone.replace("whatsapp:", "").strip()
    user = get_or_create_user_by_phone(db, clean_phone)
    text = message_text.strip()
    text_upper = text.upper()

    if clean_phone not in USER_DRAFTS:
        USER_DRAFTS[clean_phone] = {"items": {}, "slot_id": None}

    draft = USER_DRAFTS[clean_phone]

    # RESET / CLEAR
    if text_upper in ["RESET", "CLEAR"]:
        USER_DRAFTS[clean_phone] = {"items": {}, "slot_id": None}
        return "🔄 Your current order draft has been cleared. Send `MENU` to view the menu."

    # STATUS / MY ORDERS
    if text_upper in ["STATUS", "MY ORDERS", "MYORDERS", "ORDERS"]:
        orders = get_my_orders(db, user.id)
        if not orders:
            return "📝 You have no active or past orders. Reply `MENU` to place an order!"
        
        resp = "📋 *YOUR RECENT ORDERS*\n"
        for o in orders[:5]:
            resp += f"\n• *{o.order_number}* — ₹{o.total_amount}\n  Status: *{o.status.value}*"
            if o.status.value == "READY":
                resp += "\n  🚨 *OTP for Pickup:* (Check WhatsApp notification)"
        return resp

    # CANCEL
    if text_upper.startswith("CANCEL"):
        parts = text.split()
        if len(parts) > 1 and parts[1].isdigit():
            order_id = int(parts[1])
            try:
                cancelled = cancel_order(db, order_id, "Cancelled via WhatsApp", CancelledBy.USER, user.id)
                return f"❌ Order *{cancelled.order_number}* has been successfully cancelled."
            except Exception as e:
                return f"⚠️ Could not cancel order: {str(e)}"
        else:
            return "To cancel an order, reply with `CANCEL <order_id>` (e.g. `CANCEL 1`)."

    # CONFIRM ORDER
    if text_upper in ["CONFIRM", "YES", "CHECKOUT"]:
        if not draft["items"]:
            return "⚠️ Your order draft is empty! Reply `MENU` to select food items."
        if not draft["slot_id"]:
            return "⚠️ Please select a pickup slot first! Reply `SLOT` to view available slots."

        items_payload = [
            OrderItemCreate(menu_item_id=item_id, quantity=qty)
            for item_id, qty in draft["items"].items()
        ]
        order_create_data = OrderCreate(
            pickup_slot_id=draft["slot_id"],
            items=items_payload
        )

        try:
            order = create_order(db, user.id, order_create_data)
            # Clear draft
            USER_DRAFTS[clean_phone] = {"items": {}, "slot_id": None}
            return (
                f"🎉 *ORDER PLACED SUCCESSFULLY!*\n\n"
                f"• Order Number: *{order.order_number}*\n"
                f"• Total Amount: *₹{order.total_amount}*\n"
                f"• Status: *PENDING* (Awaiting canteen confirmation)\n\n"
                f"We will notify you here as soon as the canteen accepts and prepares your food! 📲"
            )
        except Exception as e:
            return f"❌ Order creation failed: {str(e)}"

    # SLOT SELECTION
    if text_upper.startswith("SLOT"):
        try:
            slots = get_available_pickup_slots(db)
        except Exception as e:
            return f"ℹ️ {getattr(e, 'detail', str(e))}"

        if not slots:
            return "⏳ No pickup slots currently available for today. Please try again later."

        parts = text.split()
        if len(parts) > 1 and parts[1].isdigit():
            slot_id = int(parts[1])
            selected_slot = next((s for s in slots if s.id == slot_id), None)
            if not selected_slot:
                # If slot_id directly matches a slot in DB even if filtered out by time check
                from app.repositories.pickup_slot_repository import get_pickup_slot_by_id
                slot_obj = get_pickup_slot_by_id(db, slot_id)
                if not slot_obj:
                    return f"⚠️ Invalid slot ID {slot_id}. Please reply `SLOT` to view valid options."
                selected_slot = slot_obj

            draft["slot_id"] = slot_id

            # Show draft summary
            if not draft["items"]:
                return f"✅ Pickup slot set to *{selected_slot.start_time.strftime('%H:%M')} - {selected_slot.end_time.strftime('%H:%M')}*.\n\nNow add items to your cart by sending `ORDER <item_id> x<qty>`!"

            total = Decimal("0.00")
            summary = "📋 *ORDER SUMMARY*\n"
            for item_id, qty in draft["items"].items():
                item = get_menu_item_by_id_service(db, item_id)
                subtotal = item.current_price * qty
                total += subtotal
                summary += f"• {qty}x {item.name} = ₹{subtotal}\n"
            
            summary += f"\n*Total Amount:* ₹{total}\n"
            summary += f"*Pickup Slot:* {selected_slot.start_time.strftime('%H:%M')} - {selected_slot.end_time.strftime('%H:%M')}\n\n"
            summary += "Reply `CONFIRM` to place this order now!"
            return summary
        else:
            resp = "⏰ *AVAILABLE PICKUP SLOTS*\n\n"
            for s in slots:
                resp += f"• *[Slot ID: {s.id}]* {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')} (Wait: ~{s.estimated_wait_minutes}m)\n"
            resp += "\nTo select a slot, reply `SLOT <slot_id>` (e.g., `SLOT 1`)."
            return resp

    # ORDER ITEM PARSING (e.g., "ORDER 1 x2, 2 x1" or "1 x2" or "ORDER 1")
    order_match = re.findall(r'(\d+)\s*(?:x|\*|\s)?\s*(\d+)?', text, re.IGNORECASE)
    if (text_upper.startswith("ORDER") or order_match) and not text_upper.startswith("SLOT"):
        if order_match:
            added_text = ""
            for item_str, qty_str in order_match:
                item_id = int(item_str)
                qty = int(qty_str) if qty_str else 1
                try:
                    menu_item = get_menu_item_by_id_service(db, item_id)
                    if not menu_item.is_available:
                        return f"⚠️ Sorry, *{menu_item.name}* is currently out of stock."
                    
                    draft["items"][item_id] = draft["items"].get(item_id, 0) + qty
                    added_text += f"• Added {qty}x *{menu_item.name}* (₹{menu_item.current_price * qty})\n"
                except Exception:
                    return f"⚠️ Menu item ID {item_id} not found. Send `MENU` to view item IDs."

            resp = f"🛒 *ITEMS ADDED TO CART*\n{added_text}\n"
            if not draft["slot_id"]:
                resp += "Next step: Send `SLOT` to select your pickup time!"
            else:
                resp += "Send `CONFIRM` to complete your order, or `SLOT` to view/change pickup time."
            return resp

    

# DEFAULT / MENU / GREETING RESPONSE

    if text_upper in ["HI", "HELLO", "START", "MENU"]:
    
        stalls = get_stalls(db, only_open=True)
    
        if not stalls:
            return "⚠️ No food stalls are currently open."
    
        resp = f"👋 Hello *{user.name}*! Welcome to *MunchBot* 🍕\n\n"
        resp += "🏪 *Choose a Stall*\n\n"
    
        for stall in stalls:
            resp += f"{stall.id}. {stall.name}\n"
    
        resp += "\nReply with the stall number."
    
        return resp
    
    return (
        "❓ I didn't understand that.\n\n"
        "Reply with:\n"
        "• MENU\n"
        "• STATUS\n"
        "• RESET"
    )
