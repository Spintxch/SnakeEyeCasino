"""Backend logic for Snake Eye Casino.

This module contains pure game/wallet logic that operates on a generic
session object. The frontend imports these functions and provides
UI bindings for the native GUI.
"""

def initialize_account(session_state):
    if "digital_balance" not in session_state:
        session_state.digital_balance = 0
    if "cash_on_hand" not in session_state:
        session_state.cash_on_hand = 100
    if "page" not in session_state:
        session_state.page = "hub"
    if "wallet_message" not in session_state:
        session_state.wallet_message = ""


def get_total_value(session_state):
    return session_state.digital_balance + session_state.cash_on_hand


def transfer_to_digital(session_state):
    """Move `transfer_amount` from cash_on_hand to digital_balance.

    Reads `transfer_amount` from `session_state.transfer_amount` and updates
    balances and `session_state.wallet_message` accordingly.
    """
    amount = getattr(session_state, "transfer_amount", 0)
    try:
        amount = float(amount)
    except Exception:
        session_state.wallet_message = "Invalid transfer amount."
        return False

    if amount <= 0:
        session_state.wallet_message = "Enter a transfer amount above $0."
        return False
    if amount > session_state.cash_on_hand:
        session_state.wallet_message = "You do not have that much cash on hand."
        return False

    session_state.cash_on_hand -= amount
    session_state.digital_balance += amount
    session_state.wallet_message = f"Transferred ${amount} to your digital balance."
    return True


def withdraw_to_cash(session_state):
    """Move `withdraw_amount` from digital_balance to cash_on_hand.

    Reads `withdraw_amount` from `session_state.withdraw_amount` and updates
    balances and `session_state.wallet_message` accordingly.
    """
    amount = getattr(session_state, "withdraw_amount", 0)
    try:
        amount = float(amount)
    except Exception:
        session_state.wallet_message = "Invalid withdraw amount."
        return False

    if amount <= 0:
        session_state.wallet_message = "Enter a withdraw amount above $0."
        return False
    if amount > session_state.digital_balance:
        session_state.wallet_message = "You do not have that much digital balance."
        return False

    session_state.digital_balance -= amount
    session_state.cash_on_hand += amount
    session_state.wallet_message = f"Withdrew ${amount} from digital balance to cash on hand."
    return True


def go_to_page(session_state, page_name):
    session_state.page = page_name


# --- Shop support ---
SHOP_ITEMS = [
    {"id": "lucky_hat", "name": "Lucky Hat", "price": 10, "description": "Adds style and +1 luck."},
    {"id": "coffee", "name": "Energy Coffee", "price": 5, "description": "Gives +1 energy for quick plays."},
    {"id": "token_pack", "name": "Token Pack (5)", "price": 20, "description": "Provides 5 play tokens."},
]


def get_shop_items():
    """Return the list of shop items (copy to avoid accidental mutation)."""
    return [item.copy() for item in SHOP_ITEMS]


def _ensure_inventory(session_state):
    if "inventory" not in session_state:
        session_state.inventory = []


def get_inventory(session_state):
    _ensure_inventory(session_state)
    return list(session_state.inventory)


def buy_item(session_state, item_id):
    """Attempt to purchase an item by `item_id`.

    Payment order: `digital_balance` first, then `cash_on_hand`.
    Returns (success: bool, message: str).
    """
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if item is None:
        return False, "Item not found."

    price = float(item["price"])

    # prefer digital balance
    if getattr(session_state, "digital_balance", 0) >= price:
        session_state.digital_balance -= price
        payment_source = "digital"
    elif getattr(session_state, "cash_on_hand", 0) >= price:
        session_state.cash_on_hand -= price
        payment_source = "cash"
    else:
        return False, "Insufficient funds to purchase item."

    _ensure_inventory(session_state)
    session_state.inventory.append({"id": item["id"], "name": item["name"]})
    session_state.wallet_message = f"Purchased {item['name']} for ${price} from {payment_source} balance."
    return True, session_state.wallet_message
