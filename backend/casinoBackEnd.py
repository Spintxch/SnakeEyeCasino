"""Backend logic for Snake Eye Casino.

This module contains pure game/wallet logic that operates on a generic
session object. The frontend imports these functions and provides
UI bindings for the native GUI.
"""

LUCK_MIN = 0
LUCK_MAX = 100


def _clamp_luck(value):
    return max(LUCK_MIN, min(LUCK_MAX, int(value)))


def get_luck(session_state):
    """Return the current player luck level (0-100)."""
    if "luck" not in session_state:
        session_state.luck = 0
    session_state.luck = _clamp_luck(session_state.luck)
    return session_state.luck


def _get_game_specific_luck_bonuses(session_state):
    """Return summed game-specific luck bonuses from owned items."""
    _ensure_inventory(session_state)
    totals = {"slots": 0, "blackjack": 0, "poker": 0}
    for owned in session_state.inventory:
        item_id = owned.get("id")
        for game_name, bonus in ITEM_GAME_LUCK_BONUS.get(item_id, {}).items():
            if game_name in totals:
                totals[game_name] += int(bonus)
    return totals


def get_game_effects(session_state, game_name):
    """Return aggregated non-luck effects for a specific game."""
    key = str(game_name).strip().lower()
    effects = {
        "slots_symbol_multipliers": {},
        "preferred_ranks": [],
    }
    if key not in {"slots", "blackjack", "poker"}:
        return effects

    _ensure_inventory(session_state)
    _ensure_custom_effect_settings(session_state)
    preferred = []
    for owned in session_state.inventory:
        item_id = owned.get("id")
        item_effect = ITEM_GAME_EFFECTS.get(item_id, {}).get(key, {})

        for symbol, mult in item_effect.get("slots_symbol_multipliers", {}).items():
            current = effects["slots_symbol_multipliers"].get(symbol, 1.0)
            effects["slots_symbol_multipliers"][symbol] = current * float(mult)

        for rank in item_effect.get("preferred_ranks", []):
            if rank not in preferred:
                preferred.append(rank)

    custom_slot_owned = _count_item_in_inventory(session_state, "custom_slot_focus")
    custom_bj_owned = _count_item_in_inventory(session_state, "custom_blackjack_focus")
    custom_poker_owned = _count_item_in_inventory(session_state, "custom_poker_focus")

    if key == "slots" and custom_slot_owned > 0:
        chosen_symbol = session_state.custom_slot_symbol
        current = effects["slots_symbol_multipliers"].get(chosen_symbol, 1.0)
        effects["slots_symbol_multipliers"][chosen_symbol] = current * (1.5 ** custom_slot_owned)
    if key == "blackjack" and custom_bj_owned > 0:
        chosen_rank = session_state.custom_blackjack_rank
        if chosen_rank not in preferred:
            preferred.append(chosen_rank)
    if key == "poker" and custom_poker_owned > 0:
        chosen_rank = session_state.custom_poker_rank
        if chosen_rank not in preferred:
            preferred.append(chosen_rank)

    effects["preferred_ranks"] = preferred
    return effects


def get_game_luck(session_state, game_name):
    """Return effective luck for a game (base luck + game-specific bonuses)."""
    key = str(game_name).strip().lower()
    base_luck = get_luck(session_state)
    if key not in {"slots", "blackjack", "poker"}:
        return base_luck
    bonuses = _get_game_specific_luck_bonuses(session_state)
    return _clamp_luck(base_luck + bonuses.get(key, 0))


def get_active_bonus_effects(session_state):
    """Return active bonus values for UI display."""
    effects = {
        "global_luck": get_luck(session_state),
        "slots_luck": 0,
        "blackjack_luck": 0,
        "poker_luck": 0,
        "slots_symbols": {},
        "blackjack_preferred_ranks": [],
        "poker_preferred_ranks": [],
    }
    bonuses = _get_game_specific_luck_bonuses(session_state)
    effects["slots_luck"] = bonuses["slots"]
    effects["blackjack_luck"] = bonuses["blackjack"]
    effects["poker_luck"] = bonuses["poker"]

    slots_effects = get_game_effects(session_state, "slots")
    blackjack_effects = get_game_effects(session_state, "blackjack")
    poker_effects = get_game_effects(session_state, "poker")
    effects["slots_symbols"] = {
        symbol: mult
        for symbol, mult in slots_effects.get("slots_symbol_multipliers", {}).items()
        if mult > 1.0
    }
    effects["blackjack_preferred_ranks"] = blackjack_effects.get("preferred_ranks", [])
    effects["poker_preferred_ranks"] = poker_effects.get("preferred_ranks", [])
    return effects


def get_active_bonus_item_counts(session_state):
    """Return counts of owned items that currently provide bonus effects."""
    _ensure_inventory(session_state)
    counts = {}
    for owned in session_state.inventory:
        item_id = owned.get("id")
        has_bonus = (
            ITEM_LUCK_BONUS.get(item_id, 0) > 0
            or bool(ITEM_GAME_LUCK_BONUS.get(item_id))
            or bool(ITEM_GAME_EFFECTS.get(item_id))
        )
        if not has_bonus:
            continue
        item_name = owned.get("name", item_id)
        counts[item_name] = counts.get(item_name, 0) + 1
    return counts


def _ensure_custom_effect_settings(session_state):
    if "custom_slot_symbol" not in session_state:
        session_state.custom_slot_symbol = "seven"
    if "custom_blackjack_rank" not in session_state:
        session_state.custom_blackjack_rank = "A"
    if "custom_poker_rank" not in session_state:
        session_state.custom_poker_rank = "A"


def get_custom_focus_options():
    return {
        "slots_symbols": ["cherry", "lemon", "watermelon", "bell", "heart", "horseShoe", "bar", "diamond", "seven"],
        "card_ranks": ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"],
    }


def get_custom_focus_settings(session_state):
    _ensure_custom_effect_settings(session_state)
    return {
        "slot_symbol": session_state.custom_slot_symbol,
        "blackjack_rank": session_state.custom_blackjack_rank,
        "poker_rank": session_state.custom_poker_rank,
    }


def set_custom_focus(session_state, game_name, choice):
    _ensure_custom_effect_settings(session_state)
    options = get_custom_focus_options()
    game_key = str(game_name).strip().lower()

    if game_key == "slots":
        valid = options["slots_symbols"]
        if choice not in valid:
            return False, "Invalid slots symbol choice."
        session_state.custom_slot_symbol = choice
        return True, f"Slots custom focus set to {choice}."
    if game_key == "blackjack":
        valid = options["card_ranks"]
        if choice not in valid:
            return False, "Invalid blackjack rank choice."
        session_state.custom_blackjack_rank = choice
        return True, f"Blackjack custom focus set to {choice}."
    if game_key == "poker":
        valid = options["card_ranks"]
        if choice not in valid:
            return False, "Invalid poker rank choice."
        session_state.custom_poker_rank = choice
        return True, f"Poker custom focus set to {choice}."

    return False, "Unsupported game for custom focus."

def initialize_account(session_state):
    if "digital_balance" not in session_state:
        session_state.digital_balance = 0
    if "cash_on_hand" not in session_state:
        session_state.cash_on_hand = 100
    if "page" not in session_state:
        session_state.page = "hub"
    if "wallet_message" not in session_state:
        session_state.wallet_message = ""
    if "luck" not in session_state:
        session_state.luck = 0


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
    {"id": "lucky_hat", "tier": 1, "name": "Lucky Hat", "price": 10, "description": "Adds style and +10 global luck."},
    {"id": "rabbit_foot", "tier": 1, "name": "Rabbit Foot Charm", "price": 20, "description": "A classic charm worth +20 global luck."},
    {"id": "slot_oil", "tier": 2, "name": "Reel Oil", "price": 15, "description": "Slots only: +20 luck."},
    {"id": "card_guard", "tier": 2, "name": "Card Guard", "price": 15, "description": "Blackjack only: +20 luck."},
    {"id": "poker_tells", "tier": 2, "name": "Poker Tells Guide", "price": 15, "description": "Poker only: +20 luck."},
    {"id": "seven_charm", "tier": 2, "name": "Seven Charm", "price": 25, "description": "Slots only: increases seven symbol frequency."},
    {"id": "ace_sleeve", "tier": 2, "name": "Ace Sleeve", "price": 20, "description": "Blackjack only: aces appear more often in your draws."},
    {"id": "face_read", "tier": 2, "name": "Face Read Notes", "price": 20, "description": "Poker only: face cards appear more often in your hole cards."},
    {"id": "custom_slot_focus", "tier": 3, "name": "Slot Totem", "price": 35, "description": "Slots only: choose one symbol to appear more often."},
    {"id": "custom_blackjack_focus", "tier": 3, "name": "Blackjack Sigil", "price": 35, "description": "Blackjack only: choose one rank to appear more often in your draws."},
    {"id": "custom_poker_focus", "tier": 3, "name": "Poker Lens", "price": 35, "description": "Poker only: choose one rank to appear more often in your hole cards."},
]


ITEM_PURCHASE_LIMITS = {
    "lucky_hat": 1,
    "rabbit_foot": 3,
    "slot_oil": 2,
    "card_guard": 2,
    "poker_tells": 2,
    "seven_charm": 2,
    "ace_sleeve": 2,
    "face_read": 2,
    "custom_slot_focus": 1,
    "custom_blackjack_focus": 1,
    "custom_poker_focus": 1,
}


ITEM_LUCK_BONUS = {
    "lucky_hat": 10,
    "rabbit_foot": 20,
}


ITEM_GAME_LUCK_BONUS = {
    "slot_oil": {"slots": 20},
    "card_guard": {"blackjack": 20},
    "poker_tells": {"poker": 20},
}


ITEM_GAME_EFFECTS = {
    "seven_charm": {
        "slots": {
            "slots_symbol_multipliers": {"seven": 2.0},
        }
    },
    "ace_sleeve": {
        "blackjack": {
            "preferred_ranks": ["A"],
        }
    },
    "face_read": {
        "poker": {
            "preferred_ranks": ["K", "Q", "J"],
        }
    },
}


def get_shop_items():
    """Return the list of shop items (copy to avoid accidental mutation)."""
    items = []
    for item in SHOP_ITEMS:
        copied = item.copy()
        copied["purchase_limit"] = ITEM_PURCHASE_LIMITS.get(item["id"])
        items.append(copied)
    return items


def _ensure_inventory(session_state):
    if "inventory" not in session_state:
        session_state.inventory = []


def get_inventory(session_state):
    _ensure_inventory(session_state)
    return list(session_state.inventory)


def _count_item_in_inventory(session_state, item_id):
    _ensure_inventory(session_state)
    return sum(1 for owned in session_state.inventory if owned.get("id") == item_id)


def buy_item(session_state, item_id):
    """Attempt to purchase an item by `item_id`.

    Payment order: `digital_balance` first, then `cash_on_hand`.
    Returns (success: bool, message: str).
    """
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if item is None:
        return False, "Item not found."

    purchase_limit = ITEM_PURCHASE_LIMITS.get(item_id)
    if purchase_limit is not None:
        owned_count = _count_item_in_inventory(session_state, item_id)
        if owned_count >= purchase_limit:
            return False, f"Purchase limit reached for {item['name']} ({purchase_limit})."

    price = float(item["price"])

    if getattr(session_state, "digital_balance", 0) < price:
        return False, "Insufficient digital balance to purchase item."

    session_state.digital_balance -= price
    payment_source = "digital"

    _ensure_inventory(session_state)
    session_state.inventory.append({"id": item["id"], "name": item["name"]})

    luck_bonus = ITEM_LUCK_BONUS.get(item_id, 0)
    game_bonus = ITEM_GAME_LUCK_BONUS.get(item_id, {})
    game_effects = ITEM_GAME_EFFECTS.get(item_id, {})
    if luck_bonus or game_bonus or game_effects:
        previous_luck = get_luck(session_state)
        session_state.luck = _clamp_luck(previous_luck + luck_bonus)
        gained = session_state.luck - previous_luck
        bonus_parts = []
        if gained > 0:
            bonus_parts.append(f"Global luck +{gained} (now {session_state.luck}/{LUCK_MAX})")
        elif luck_bonus > 0:
            bonus_parts.append(f"Global luck already maxed at {LUCK_MAX}")
        for game_name, amount in game_bonus.items():
            bonus_parts.append(f"{game_name.title()} luck +{amount}")
        for game_name, effect_data in game_effects.items():
            for symbol, mult in effect_data.get("slots_symbol_multipliers", {}).items():
                bonus_parts.append(f"{game_name.title()} {symbol} frequency x{mult}")
            preferred_ranks = effect_data.get("preferred_ranks", [])
            if preferred_ranks:
                shown_ranks = ", ".join(preferred_ranks)
                bonus_parts.append(f"{game_name.title()} favored cards: {shown_ranks}")
        bonus_text = " | ".join(bonus_parts)
        session_state.wallet_message = (
            f"Purchased {item['name']} for ${price} from {payment_source} balance. {bonus_text}."
        )
    else:
        session_state.wallet_message = f"Purchased {item['name']} for ${price} from {payment_source} balance."

    return True, session_state.wallet_message
