import os
import sys
import random as _rnd
import PySimpleGUI as sg

# Package-relative imports when running as a package or standalone script.
try:
    from ..backend.casinoBackEnd import (
        initialize_account,
        get_total_value,
        get_luck,
        get_game_luck,
        get_game_effects,
        get_active_bonus_effects,
        get_active_bonus_item_counts,
        get_custom_focus_options,
        get_custom_focus_settings,
        set_custom_focus,
        transfer_to_digital,
        withdraw_to_cash,
        get_shop_items,
        get_inventory,
        buy_item,
    )
    from ..backend.slotsBackEnd import spin_slots, check_win, calculate_slot_multiplier
    from ..backend.blackjackBackEnd import (
        create_deck as bj_create_deck,
        deal_card as bj_deal_card,
        deal_biased_card as bj_deal_biased_card,
        calculate_hand_value as bj_calculate_hand_value,
        is_blackjack,
        can_split,
        format_hand as bj_format_hand,
        format_card as bj_format_card,
    )
    from ..backend.pokerBackEnd import (
        create_deck as poker_create_deck,
        deal_cards as poker_deal_cards,
        deal_biased_cards as poker_deal_biased_cards,
        get_best_hand,
        determine_winner,
        format_hand as poker_format_hand,
    )
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from backend.casinoBackEnd import (
        initialize_account,
        get_total_value,
        get_luck,
        get_game_luck,
        get_game_effects,
        get_active_bonus_effects,
        get_active_bonus_item_counts,
        get_custom_focus_options,
        get_custom_focus_settings,
        set_custom_focus,
        transfer_to_digital,
        withdraw_to_cash,
        get_shop_items,
        get_inventory,
        buy_item,
    )
    from backend.slotsBackEnd import spin_slots, check_win, calculate_slot_multiplier
    from backend.blackjackBackEnd import (
        create_deck as bj_create_deck,
        deal_card as bj_deal_card,
        deal_biased_card as bj_deal_biased_card,
        calculate_hand_value as bj_calculate_hand_value,
        is_blackjack,
        can_split,
        format_hand as bj_format_hand,
        format_card as bj_format_card,
    )
    from backend.pokerBackEnd import (
        create_deck as poker_create_deck,
        deal_cards as poker_deal_cards,
        deal_biased_cards as poker_deal_biased_cards,
        get_best_hand,
        determine_winner,
        format_hand as poker_format_hand,
    )


class SessionState:
    def __init__(self):
        self._data = {}

    def __contains__(self, key):
        return key in self._data

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def get(self, key, default=None):
        return self._data.get(key, default)


def format_money(value):
    return f"${value:.2f}"


def format_bonus_panel(session):
    effects = get_active_bonus_effects(session)
    lines = []

    if effects["global_luck"] > 0:
        lines.append(f"Global Luck: {effects['global_luck']}/100")
    if effects["slots_luck"] > 0:
        lines.append(f"Slots bonus luck: +{effects['slots_luck']}")
    if effects["blackjack_luck"] > 0:
        lines.append(f"Blackjack bonus luck: +{effects['blackjack_luck']}")
    if effects["poker_luck"] > 0:
        lines.append(f"Poker bonus luck: +{effects['poker_luck']}")
    if effects["slots_symbols"]:
        for symbol, mult in sorted(effects["slots_symbols"].items()):
            lines.append(f"Slots symbol boost: {symbol} x{mult:.2f}")
    if effects["blackjack_preferred_ranks"]:
        lines.append("Blackjack favored cards: " + ", ".join(effects["blackjack_preferred_ranks"]))
    if effects["poker_preferred_ranks"]:
        lines.append("Poker favored cards: " + ", ".join(effects["poker_preferred_ranks"]))

    if not lines:
        lines.append("No active bonuses.")

    item_counts = get_active_bonus_item_counts(session)
    if item_counts:
        lines.append("")
        lines.append("Active bonus items:")
        for name, count in sorted(item_counts.items()):
            lines.append(f"- {name} x{count}")

    return "\n".join(lines)


def get_active_bonus_lines(session):
    effects = get_active_bonus_effects(session)
    lines = []
    if effects["global_luck"] > 0:
        lines.append(f"Global Luck: {effects['global_luck']}/100")
    if effects["slots_luck"] > 0:
        lines.append(f"Slots bonus luck: +{effects['slots_luck']}")
    if effects["blackjack_luck"] > 0:
        lines.append(f"Blackjack bonus luck: +{effects['blackjack_luck']}")
    if effects["poker_luck"] > 0:
        lines.append(f"Poker bonus luck: +{effects['poker_luck']}")
    if effects["slots_symbols"]:
        for symbol, mult in sorted(effects["slots_symbols"].items()):
            lines.append(f"Slots symbol boost: {symbol} x{mult:.2f}")
    if effects["blackjack_preferred_ranks"]:
        lines.append("Blackjack favored cards: " + ", ".join(effects["blackjack_preferred_ranks"]))
    if effects["poker_preferred_ranks"]:
        lines.append("Poker favored cards: " + ", ".join(effects["poker_preferred_ranks"]))
    return lines


def set_result_banner(window, message="", is_win=None):
    # Legacy helper retained for compatibility; game-level messages are now used.
    return


def set_status_message(window, message, is_error=False):
    if is_error:
        window["-STATUS_MSG-"].update(message)
        window["-STATUS_ROW-"].update(visible=True)
    else:
        window["-STATUS_MSG-"].update("")
        window["-STATUS_ROW-"].update(visible=False)


def _set_card_row(window, keys, cards):
    for idx, key in enumerate(keys):
        if idx < len(cards):
            window[key].update(bj_format_card(cards[idx]))
            window[key].update(visible=True)
        else:
            window[key].update("")
            window[key].update(visible=False)


def refresh_blackjack_cards(window, session):
    dealer_cards = []
    if session.bj_dealer_hand:
        if session.bj_state == "playing" and len(session.bj_dealer_hand) > 1:
            dealer_cards = [session.bj_dealer_hand[0], {"rank": "?", "suit": "?"}]
        else:
            dealer_cards = session.bj_dealer_hand

    player_cards = session.bj_player_hands[0] if session.bj_player_hands else []
    _set_card_row(window, ["-BJ_DEALER_C1-", "-BJ_DEALER_C2-", "-BJ_DEALER_C3-", "-BJ_DEALER_C4-", "-BJ_DEALER_C5-"], dealer_cards)
    _set_card_row(window, ["-BJ_PLAYER_C1-", "-BJ_PLAYER_C2-", "-BJ_PLAYER_C3-", "-BJ_PLAYER_C4-", "-BJ_PLAYER_C5-"], player_cards)


def refresh_poker_cards(window, session):
    _set_card_row(window, ["-POKER_HOLE_C1-", "-POKER_HOLE_C2-"], session.he_player_hole)
    _set_card_row(window, ["-POKER_COMM_C1-", "-POKER_COMM_C2-", "-POKER_COMM_C3-", "-POKER_COMM_C4-", "-POKER_COMM_C5-"], session.he_community)


def format_blackjack_status(session):
    lines = [
        f"Blackjack - {session.bj_state.replace('_', ' ').title()}",
        f"Cash on hand: {format_money(session.cash_on_hand)}",
        f"Message: {session.bj_message}",
    ]
    if session.bj_state in ["playing", "dealer_turn", "game_over"]:
        dealer_text = (
            f"{bj_format_card(session.bj_dealer_hand[0])} | [Hidden]"
            if session.bj_state == "playing"
            else bj_format_hand(session.bj_dealer_hand)
        )
        lines.append(f"Dealer: {dealer_text}")
        for idx, hand in enumerate(session.bj_player_hands):
            score = bj_calculate_hand_value(hand)
            bet = session.bj_bets[idx]
            prefix = "-> " if idx == session.bj_active_hand and session.bj_state == "playing" else "   "
            lines.append(f"{prefix}Hand {idx + 1} [Bet ${bet}]: {bj_format_hand(hand)} ({score})")
    return "\n".join(lines)


def format_poker_status(session):
    lines = [
        f"Texas Hold'em - {session.he_state.replace('_', ' ').title()}",
        f"Cash on hand: {format_money(session.cash_on_hand)}",
        f"Pot: ${session.he_pot}",
        f"Community: {poker_format_hand(session.he_community)}",
        f"Your Hole: {poker_format_hand(session.he_player_hole)}",
    ]
    if session.he_state == "game_over":
        if session.he_result is None:
            lines.append("Result pending.")
        elif session.he_result.get("reason"):
            lines.append(session.he_result["reason"])
        else:
            lines.append(f"Winner: {session.he_result['winner']}")
            lines.append(f"Player: {poker_format_hand(session.he_result['player'][1])} ({session.he_result['player'][0][2]})")
            lines.append(f"Dealer: {poker_format_hand(session.he_result['dealer'][1])} ({session.he_result['dealer'][0][2]})")
    return "\n".join(lines)


def reset_blackjack(session):
    session.bj_state = "betting"
    session.bj_deck = bj_create_deck()
    session.bj_player_hands = []
    session.bj_bets = []
    session.bj_active_hand = 0
    session.bj_dealer_hand = []
    session.bj_message = "Place your bet to start the hand."
    session.saved_bj_bet = session.get("saved_bj_bet", 1 if session.cash_on_hand >= 1 else 0)


def reset_poker(session):
    session.he_state = "ante"
    session.he_deck = poker_create_deck()
    session.he_player_hole = []
    session.he_dealer_hole = []
    session.he_community = []
    session.he_pot = 0
    session.he_result = None
    session.saved_he_ante = session.get("saved_he_ante", 1 if session.cash_on_hand >= 1 else 0)


def ensure_slots(session):
    if "consecutive_losses" not in session:
        session.consecutive_losses = 0
    if "slots_wheels" not in session:
        slot_effects = get_game_effects(session, "slots")
        session.slots_wheels = spin_slots(
            session.consecutive_losses,
            get_game_luck(session, "slots"),
            symbol_multipliers=slot_effects.get("slots_symbol_multipliers", {}),
        )
        session.slots_winning_lines = []
        session.slot_message = "Place a bet and spin to win!"


def update_main_metrics(window, session):
    window["-DIGITAL-"].update(format_money(session.digital_balance))
    window["-CASH-"].update(format_money(session.cash_on_hand))
    window["-TOTAL-"].update(format_money(get_total_value(session)))
    window["-LUCK-"].update(str(get_luck(session)))
    bonus_lines = get_active_bonus_lines(session)
    window["-BONUS_LIST-"].update(values=bonus_lines)
    window["-BONUS_SECTION-"].update(visible=bool(bonus_lines))
    window["-STATUS_CASH-"].update(format_money(session.cash_on_hand))
    if "-SHOP_DIGITAL-" in window.AllKeysDict:
        window["-SHOP_DIGITAL-"].update(format_money(session.digital_balance))


def set_view(window, view_key):
    keys = ["-VIEW_HUB-", "-VIEW_SHOP-", "-VIEW_INVENTORY-", "-VIEW_SLOTS-", "-VIEW_BJ-", "-VIEW_POKER-", "-VIEW_CASHIER-"]
    for key in keys:
        window[key].update(visible=(key == view_key))
    if "-TOP_BACK_HUB-" in window.AllKeysDict:
        window["-TOP_BACK_HUB-"].update(visible=(view_key != "-VIEW_HUB-"))

    # Show win/loss feedback only inside the active game view.
    if view_key != "-VIEW_SLOTS-":
        window["-SLOT_MSG-"].update("")
    if view_key != "-VIEW_BJ-":
        window["-BJ_MSG_LINE-"].update("")
    if view_key != "-VIEW_POKER-":
        window["-POKER_MSG_LINE-"].update("")


def refresh_shop_list(window, session):
    items = get_shop_items()
    session.shop_items_by_id = {item["id"]: item for item in items}

    inventory = get_inventory(session)
    owned_count = {}
    for entry in inventory:
        item_id = entry.get("id")
        owned_count[item_id] = owned_count.get(item_id, 0) + 1

    for item in items:
        key = ("SHOP_CARD", item["id"])
        if key not in window.AllKeysDict:
            continue
        tier = int(item.get("tier", 1))
        limit = item.get("purchase_limit")
        count = owned_count.get(item["id"], 0)
        limit_text = f"{count}/{limit}" if limit is not None else f"{count}/inf"
        card_text = (
            f"{item['name']}  |  ${item['price']}  |  Tier {tier}  |  Owned {limit_text}\n"
            f"{item['description']}"
        )
        window[key].update(card_text)


def refresh_inventory(window, session):
    inventory = get_inventory(session)
    counts = {}
    ids_by_name = {}
    for item in inventory:
        name = item["name"]
        counts[name] = counts.get(name, 0) + 1
        ids_by_name[name] = item.get("id")

    rows = []
    for name in sorted(counts.keys()):
        rows.append([name, counts[name], ids_by_name.get(name, "")])
    window["-INV_TABLE-"].update(values=rows)

    custom_settings = get_custom_focus_settings(session)
    owned_ids = {item.get("id") for item in inventory}

    has_slot_custom = "custom_slot_focus" in owned_ids
    has_bj_custom = "custom_blackjack_focus" in owned_ids
    has_poker_custom = "custom_poker_focus" in owned_ids

    window["-INV_CUSTOM_SLOT-"].update(value=custom_settings["slot_symbol"], disabled=not has_slot_custom)
    window["-INV_APPLY_SLOT-"].update(disabled=not has_slot_custom)
    window["-INV_SLOT_HINT-"].update("Unlocked" if has_slot_custom else "Locked: need Custom Slot Totem")

    window["-INV_CUSTOM_BJ-"].update(value=custom_settings["blackjack_rank"], disabled=not has_bj_custom)
    window["-INV_APPLY_BJ-"].update(disabled=not has_bj_custom)
    window["-INV_BJ_HINT-"].update("Unlocked" if has_bj_custom else "Locked: need Custom Blackjack Sigil")

    window["-INV_CUSTOM_POKER-"].update(value=custom_settings["poker_rank"], disabled=not has_poker_custom)
    window["-INV_APPLY_POKER-"].update(disabled=not has_poker_custom)
    window["-INV_POKER_HINT-"].update("Unlocked" if has_poker_custom else "Locked: need Custom Poker Lens")


def refresh_slots(window, session):
    ensure_slots(session)
    symbol_display = {
        "cherry": "🍒",
        "lemon": "🍋",
        "watermelon": "🍉",
        "bell": "🔔",
        "heart": "♥",
        "horseShoe": "∩",
        "bar": "BAR",
        "diamond": "♦",
        "seven": "7",
    }

    graph = window["-SLOT_GRAPH-"]
    graph.erase()
    graph_width = 450
    graph_height = 360
    cols = 3
    rows = 3
    margin = 18
    gap = 10
    cell_w = int((graph_width - (2 * margin) - ((cols - 1) * gap)) / cols)
    cell_h = int((graph_height - (2 * margin) - ((rows - 1) * gap)) / rows)

    graph.draw_rectangle((0, 0), (graph_width, graph_height), fill_color="#182030", line_color="#324057", line_width=2)

    # Draw the 3 wheel columns as separate visual reels.
    for col in range(3):
        x1 = margin + col * (cell_w + gap)
        x2 = x1 + cell_w
        graph.draw_rectangle((x1 - 6, margin - 6), (x2 + 6, graph_height - margin + 6), fill_color="#111827", line_color="#FDD835", line_width=2)

    for row in range(3):
        for col in range(3):
            x1 = margin + col * (cell_w + gap)
            y1 = graph_height - margin - (row + 1) * cell_h - row * gap
            x2 = x1 + cell_w
            y2 = y1 + cell_h

            graph.draw_rectangle((x1, y1), (x2, y2), fill_color="#F3F6FB", line_color="#B7C3D7", line_width=2)

            symbol_name = session.slots_wheels[col][row]
            shown = symbol_display.get(symbol_name, "?")
            color = "#B11F2A" if symbol_name in ["seven", "cherry", "heart"] else "#182030"
            graph.draw_text(shown, ((x1 + x2) // 2, (y1 + y2) // 2), font=("Helvetica", 24, "bold"), color=color)

    window["-SLOT_MSG-"].update(session.slot_message)


def settle_blackjack_dealer(session):
    if session.bj_state != "dealer_turn":
        return

    dealer_score = bj_calculate_hand_value(session.bj_dealer_hand)
    while dealer_score < 17:
        session.bj_dealer_hand.append(bj_deal_card(session.bj_deck))
        dealer_score = bj_calculate_hand_value(session.bj_dealer_hand)

    session.bj_state = "game_over"
    results = []
    for idx, hand in enumerate(session.bj_player_hands):
        player_score = bj_calculate_hand_value(hand)
        bet = session.bj_bets[idx]
        if player_score > 21:
            results.append(f"Hand {idx + 1}: Bust (${bet} lost)")
        elif dealer_score > 21 or player_score > dealer_score:
            payout = bet * 2
            session.cash_on_hand += payout
            results.append(f"Hand {idx + 1}: Win! Payout ${payout}")
        elif player_score == dealer_score:
            session.cash_on_hand += bet
            results.append(f"Hand {idx + 1}: Push. Bet returned.")
        else:
            results.append(f"Hand {idx + 1}: Lose (${bet} lost)")
    session.bj_message = " | ".join(results)


def main():
    session = SessionState()
    initialize_account(session)
    sg.theme("DarkAmber")

    ensure_slots(session)
    reset_blackjack(session)
    reset_poker(session)

    custom_options = get_custom_focus_options()
    custom_settings = get_custom_focus_settings(session)

    shop_items = sorted(get_shop_items(), key=lambda x: (int(x.get("tier", 1)), x["name"]))
    shop_cards = []
    for item in shop_items:
        limit_text = f"Limit {item['purchase_limit']}" if item.get("purchase_limit") is not None else "No limit"
        card_text = f"{item['name']}  |  ${item['price']}  |  Tier {item.get('tier', 1)}  |  {limit_text}\n{item['description']}"
        shop_cards.append([sg.Button(card_text, key=("SHOP_CARD", item["id"]), size=(85, 2), button_color=("#111827", "#DDE6F5"))])

    layout = [
        [
            sg.Button("Back to Hub", key="-TOP_BACK_HUB-", visible=False),
            sg.Button("Shop", key="-TOP_SHOP-"),
            sg.Button("Cashier's Cage", key="-TOP_CASHIER-"),
            sg.Push(),
            sg.Button("Toggle Fullscreen", key="-TOGGLE_FS-"),
            sg.Button("Quit", button_color=("#FFFFFF", "#D32F2F")),
        ],
        [
            sg.Text("Digital:", text_color="#FFD54F"), sg.Text(format_money(session.digital_balance), key="-DIGITAL-"),
            sg.Text("   Cash:", text_color="#FFD54F"), sg.Text(format_money(session.cash_on_hand), key="-CASH-"),
            sg.Text("   Total:", text_color="#FFD54F"), sg.Text(format_money(get_total_value(session)), key="-TOTAL-"),
            sg.Text("   Luck:", text_color="#FFD54F"), sg.Text(str(get_luck(session)), key="-LUCK-"),
        ],
        [sg.Text("", key="-RESULT_BANNER-", size=(1, 1), visible=False)],
        [sg.pin(sg.Column([[sg.Text("Error:"), sg.Input("", key="-STATUS_MSG-", size=(100, 1), readonly=True), sg.Button("Copy", key="-COPY_STATUS-")]], key="-STATUS_ROW-", visible=False))],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Welcome to Snake Eye Casino", font=(None, 20, "bold"))],
                    [sg.Text("Select where you want to go from the hub.")],
                    [
                        sg.Button("Open Slots", key="-HUB_SLOTS-"),
                        sg.Button("Open Inventory", key="-HUB_INV-"),
                        sg.Button("Open Blackjack", key="-HUB_BJ-"),
                        sg.Button("Open Poker", key="-HUB_POKER-"),
                    ],
                ],
                key="-VIEW_HUB-",
                visible=True,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Shop (Digital Currency Only)", font=(None, 16, "bold"))],
                    [sg.Text("Digital available:"), sg.Text(format_money(session.digital_balance), key="-SHOP_DIGITAL-", text_color="#FFD54F")],
                    [sg.Text("Click an item card to buy", text_color="#8AA0BF")],
                    [sg.Column(shop_cards, key="-SHOP_CARDS_COL-", scrollable=False, size=(1100, 520), expand_x=True, expand_y=True, element_justification="c")],
                ],
                key="-VIEW_SHOP-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Inventory", font=(None, 16, "bold"))],
                    [
                        sg.Table(
                            values=[],
                            headings=["Item", "Count", "ID"],
                            key="-INV_TABLE-",
                            auto_size_columns=False,
                            col_widths=[30, 10, 30],
                            justification="left",
                            num_rows=10,
                        )
                    ],
                    [sg.Text("Tier 3 Custom Focus", font=(None, 14, "bold"))],
                    [
                        sg.Text("Slots symbol:"),
                        sg.Combo(custom_options["slots_symbols"], default_value=custom_settings["slot_symbol"], key="-INV_CUSTOM_SLOT-", readonly=True, size=(14, 1)),
                        sg.Button("Apply", key="-INV_APPLY_SLOT-"),
                        sg.Text("", key="-INV_SLOT_HINT-", size=(35, 1)),
                    ],
                    [
                        sg.Text("Blackjack rank:"),
                        sg.Combo(custom_options["card_ranks"], default_value=custom_settings["blackjack_rank"], key="-INV_CUSTOM_BJ-", readonly=True, size=(14, 1)),
                        sg.Button("Apply", key="-INV_APPLY_BJ-"),
                        sg.Text("", key="-INV_BJ_HINT-", size=(35, 1)),
                    ],
                    [
                        sg.Text("Poker rank:"),
                        sg.Combo(custom_options["card_ranks"], default_value=custom_settings["poker_rank"], key="-INV_CUSTOM_POKER-", readonly=True, size=(14, 1)),
                        sg.Button("Apply", key="-INV_APPLY_POKER-"),
                        sg.Text("", key="-INV_POKER_HINT-", size=(35, 1)),
                    ],
                ],
                key="-VIEW_INVENTORY-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Slots", font=(None, 16, "bold"))],
                    [sg.Text("Bet:"), sg.Input(default_text=str(session.get("slot_bet_amount", 1)), key="-SLOT_BET-", size=(8, 1)), sg.Button("Spin", key="-SLOT_SPIN-")],
                    [
                        sg.Graph(
                            canvas_size=(450, 360),
                            graph_bottom_left=(0, 0),
                            graph_top_right=(450, 360),
                            key="-SLOT_GRAPH-",
                            background_color="#182030",
                        )
                    ],
                    [sg.Text(session.slot_message, key="-SLOT_MSG-", size=(80, 2))],
                ],
                key="-VIEW_SLOTS-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Blackjack", font=(None, 16, "bold"))],
                    [sg.Text("Dealer")],
                    [sg.Text("", key="-BJ_DEALER_C1-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_DEALER_C2-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_DEALER_C3-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_DEALER_C4-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_DEALER_C5-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center")],
                    [sg.Text("Player")],
                    [sg.Text("", key="-BJ_PLAYER_C1-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_PLAYER_C2-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_PLAYER_C3-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_PLAYER_C4-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-BJ_PLAYER_C5-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center")],
                    [sg.Text("", key="-BJ_MSG_LINE-", size=(90, 2), text_color="#DDE6F5")],
                    [sg.Text("Bet amount:"), sg.Input(default_text=str(session.saved_bj_bet), key="-BJ_BET-", size=(10, 1)), sg.Button("Deal", key="-BJ_DEAL-")],
                    [sg.Button("Hit", key="-BJ_HIT-"), sg.Button("Stand", key="-BJ_STAND-"), sg.Button("Double Down", key="-BJ_DOUBLE-"), sg.Button("Split", key="-BJ_SPLIT-"), sg.Button("Play Again", key="-BJ_RESET-")],
                ],
                key="-VIEW_BJ-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],

        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Texas Hold'em", font=(None, 16, "bold"))],
                    [sg.Text("Your Hole Cards")],
                    [sg.Text("", key="-POKER_HOLE_C1-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-POKER_HOLE_C2-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center")],
                    [sg.Text("Community Cards")],
                    [sg.Text("", key="-POKER_COMM_C1-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-POKER_COMM_C2-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-POKER_COMM_C3-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-POKER_COMM_C4-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center"), sg.Text("", key="-POKER_COMM_C5-", relief=sg.RELIEF_RIDGE, size=(5, 2), justification="center")],
                    [sg.Text("", key="-POKER_MSG_LINE-", size=(90, 3), text_color="#DDE6F5")],
                    [sg.Text("Bet amount (0 to check/call):"), sg.Input(default_text=str(session.saved_he_ante), key="-POKER_BET-", size=(10, 1)), sg.Button("Action", key="-POKER_ACTION-")],
                    [sg.Button("Fold", key="-POKER_FOLD-"), sg.Button("Next Hand", key="-POKER_RESET-")],
                ],
                key="-VIEW_POKER-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.pin(sg.Column(
                [
                    [sg.Text("Cashier's Cage", font=(None, 16, "bold"))],
                    [sg.Text("Transfer to digital:"), sg.Input(key="-TRANSFER-", size=(10, 1)), sg.Button("Transfer", key="-TRANSFER_BTN-")],
                    [sg.Text("Withdraw to cash:"), sg.Input(key="-WITHDRAW-", size=(10, 1)), sg.Button("Withdraw", key="-WITHDRAW_BTN-")],
                ],
                key="-VIEW_CASHIER-",
                visible=False,
                expand_x=True,
                expand_y=True,
                element_justification="c",
            )),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.Frame(
                "Cash On Hand",
                [[sg.Text(format_money(session.cash_on_hand), key="-STATUS_CASH-", font=(None, 20, "bold"), text_color="#FFD54F")]],
            ),
            sg.Push(),
        ],
        [
            sg.Push(),
            sg.pin(sg.Frame("Bonuses", [[sg.Listbox(values=[], key="-BONUS_LIST-", size=(95, 8), no_scrollbar=False)]], key="-BONUS_SECTION-", expand_x=False)),
            sg.Push(),
        ],
    ]

    _icon_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icon.ico")
    app_icon = _icon_path if os.path.exists(_icon_path) else None
    window = sg.Window("Snake Eye Casino", layout, finalize=True, icon=app_icon, resizable=True)

    # Scale base UI with display size so controls read better on large resolutions.
    screen_h = max(window.get_screen_dimensions()[1], 720)
    scale_factor = min(1.45, max(1.0, screen_h / 1000.0))
    try:
        window.TKroot.tk.call("tk", "scaling", scale_factor)
    except Exception:
        pass
    window.maximize()

    fullscreen = False
    refresh_shop_list(window, session)
    refresh_inventory(window, session)
    refresh_slots(window, session)
    refresh_blackjack_cards(window, session)
    refresh_poker_cards(window, session)
    window["-BJ_MSG_LINE-"].update(session.bj_message)
    window["-POKER_MSG_LINE-"].update("Start a hand to play.")
    update_main_metrics(window, session)
    set_view(window, "-VIEW_HUB-")

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Quit"):
            break

        if event == "-COPY_STATUS-":
            status_text = values.get("-STATUS_MSG-", "")
            try:
                window.TKroot.clipboard_clear()
                window.TKroot.clipboard_append(status_text)
                window.TKroot.update()
                set_status_message(window, status_text, is_error=bool(status_text))
            except Exception:
                set_status_message(window, "Unable to copy error to clipboard.", is_error=True)
            continue

        if event == "-TOGGLE_FS-":
            fullscreen = not fullscreen
            window.TKroot.attributes("-fullscreen", fullscreen)
            continue

        if event == "-TOP_BACK_HUB-":
            set_view(window, "-VIEW_HUB-")
        elif event == "-TOP_SHOP-":
            set_view(window, "-VIEW_SHOP-")
            refresh_shop_list(window, session)
        elif event == "-TOP_CASHIER-":
            set_view(window, "-VIEW_CASHIER-")
        elif event == "-HUB_SLOTS-":
            set_view(window, "-VIEW_SLOTS-")
            refresh_slots(window, session)
        elif event == "-HUB_INV-":
            set_view(window, "-VIEW_INVENTORY-")
            refresh_inventory(window, session)
        elif event == "-HUB_BJ-":
            set_view(window, "-VIEW_BJ-")
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)
        elif event == "-HUB_POKER-":
            set_view(window, "-VIEW_POKER-")
            refresh_poker_cards(window, session)
            window["-POKER_MSG_LINE-"].update("Pot: ${} | State: {}".format(session.he_pot, session.he_state.replace("_", " ").title()))
        elif event == "-TRANSFER_BTN-":
            try:
                amount = float(values.get("-TRANSFER-", 0) or 0)
            except Exception:
                set_status_message(window, "Invalid transfer amount.", is_error=True)
                continue
            session.transfer_amount = amount
            ok = transfer_to_digital(session)
            set_status_message(window, session.wallet_message, is_error=(not ok))
            update_main_metrics(window, session)

        elif event == "-WITHDRAW_BTN-":
            try:
                amount = float(values.get("-WITHDRAW-", 0) or 0)
            except Exception:
                set_status_message(window, "Invalid withdraw amount.", is_error=True)
                continue
            session.withdraw_amount = amount
            ok = withdraw_to_cash(session)
            set_status_message(window, session.wallet_message, is_error=(not ok))
            update_main_metrics(window, session)

        elif isinstance(event, tuple) and event[0] == "SHOP_CARD":
            _, item_id = event
            ok, msg = buy_item(session, item_id)
            set_status_message(window, msg, is_error=(not ok))
            refresh_shop_list(window, session)
            refresh_inventory(window, session)
            update_main_metrics(window, session)

        elif event == "-INV_APPLY_SLOT-":
            ok, msg = set_custom_focus(session, "slots", values.get("-INV_CUSTOM_SLOT-"))
            set_status_message(window, msg, is_error=(not ok))
            update_main_metrics(window, session)

        elif event == "-INV_APPLY_BJ-":
            ok, msg = set_custom_focus(session, "blackjack", values.get("-INV_CUSTOM_BJ-"))
            set_status_message(window, msg, is_error=(not ok))
            update_main_metrics(window, session)

        elif event == "-INV_APPLY_POKER-":
            ok, msg = set_custom_focus(session, "poker", values.get("-INV_CUSTOM_POKER-"))
            set_status_message(window, msg, is_error=(not ok))
            update_main_metrics(window, session)

        elif event == "-SLOT_SPIN-":
            try:
                bet_amount = int(values.get("-SLOT_BET-", 0) or 0)
            except Exception:
                window["-SLOT_MSG-"].update("Invalid bet amount.")
                set_status_message(window, "Invalid slot bet amount.", is_error=True)
                continue
            if bet_amount <= 0:
                window["-SLOT_MSG-"].update("Enter a bet above $0.")
                set_status_message(window, "Enter a slot bet above $0.", is_error=True)
                continue
            if bet_amount > session.cash_on_hand:
                window["-SLOT_MSG-"].update("Not enough cash on hand.")
                set_status_message(window, "Not enough cash on hand for slot bet.", is_error=True)
                continue

            session.cash_on_hand -= bet_amount
            slot_effects = get_game_effects(session, "slots")
            final_wheels = spin_slots(
                session.consecutive_losses,
                get_game_luck(session, "slots"),
                symbol_multipliers=slot_effects.get("slots_symbol_multipliers", {}),
            )

            for _ in range(5):
                session.slots_wheels = [[_rnd.choice(["cherry", "lemon", "watermelon", "bell", "heart", "horseShoe", "bar", "diamond", "seven"]) for _ in range(3)] for _ in range(3)]
                refresh_slots(window, session)
                window.read(timeout=60)

            session.slots_wheels = final_wheels
            session.slots_winning_lines = check_win(session.slots_wheels)
            payout_multiplier = calculate_slot_multiplier(session.slots_winning_lines)
            payout = int(round(bet_amount * payout_multiplier))
            session.cash_on_hand += payout
            if payout > 0:
                session.consecutive_losses = 0
                symbols = ", ".join([line[1] for line in session.slots_winning_lines])
                session.slot_message = f"Won {len(session.slots_winning_lines)} line(s) [{symbols}]! Payout: ${payout}."
            else:
                session.consecutive_losses += 1
                session.slot_message = f"No win. You lost ${bet_amount}."

            refresh_slots(window, session)
            update_main_metrics(window, session)

        elif event == "-BJ_DEAL-" and session.bj_state == "betting":
            try:
                bet = int(values.get("-BJ_BET-", 0) or 0)
            except Exception:
                session.bj_message = "Invalid bet amount."
                set_status_message(window, session.bj_message, is_error=True)
                window["-BJ_MSG_LINE-"].update(session.bj_message)
                continue
            if bet <= 0:
                session.bj_message = "Enter a bet above $0."
            elif bet > session.cash_on_hand:
                session.bj_message = "You do not have enough cash on hand."
            else:
                session.saved_bj_bet = bet
                session.cash_on_hand -= bet
                session.bj_bets = [bet]
                bj_luck = get_game_luck(session, "blackjack")
                bj_effects = get_game_effects(session, "blackjack")
                preferred_ranks = bj_effects.get("preferred_ranks", [])
                session.bj_player_hands = [[
                    bj_deal_biased_card(session.bj_deck, bj_luck, favor_high=True, preferred_ranks=preferred_ranks),
                    bj_deal_biased_card(session.bj_deck, bj_luck, favor_high=True, preferred_ranks=preferred_ranks),
                ]]
                session.bj_dealer_hand = [bj_deal_card(session.bj_deck), bj_deal_card(session.bj_deck)]
                if is_blackjack(session.bj_player_hands[0]):
                    session.bj_state = "game_over"
                    payout = int(round(bet * 2.5))
                    session.cash_on_hand += payout
                    session.bj_message = f"BLACKJACK! You won ${payout}!"
                else:
                    session.bj_state = "playing"
                    session.bj_message = "Your move."
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)
            update_main_metrics(window, session)

        elif event == "-BJ_HIT-" and session.bj_state == "playing":
            active_hand = session.bj_player_hands[session.bj_active_hand]
            bj_effects = get_game_effects(session, "blackjack")
            active_hand.append(
                bj_deal_biased_card(
                    session.bj_deck,
                    get_game_luck(session, "blackjack"),
                    favor_high=True,
                    preferred_ranks=bj_effects.get("preferred_ranks", []),
                )
            )
            if bj_calculate_hand_value(active_hand) >= 21:
                session.bj_state = "dealer_turn"
            session.bj_message = "Hit."
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)

        elif event == "-BJ_STAND-" and session.bj_state == "playing":
            session.bj_state = "dealer_turn"
            session.bj_message = "Stand."
            window["-BJ_MSG_LINE-"].update(session.bj_message)

        elif event == "-BJ_DOUBLE-" and session.bj_state == "playing":
            active_hand = session.bj_player_hands[session.bj_active_hand]
            current_bet = session.bj_bets[session.bj_active_hand]
            if session.cash_on_hand >= current_bet and len(active_hand) == 2:
                session.cash_on_hand -= current_bet
                session.bj_bets[session.bj_active_hand] += current_bet
                bj_effects = get_game_effects(session, "blackjack")
                active_hand.append(
                    bj_deal_biased_card(
                        session.bj_deck,
                        get_game_luck(session, "blackjack"),
                        favor_high=True,
                        preferred_ranks=bj_effects.get("preferred_ranks", []),
                    )
                )
                session.bj_state = "dealer_turn"
                session.bj_message = "Double down."
                update_main_metrics(window, session)
            else:
                session.bj_message = "Cannot double down."
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)

        elif event == "-BJ_SPLIT-" and session.bj_state == "playing":
            active_hand = session.bj_player_hands[session.bj_active_hand]
            current_bet = session.bj_bets[session.bj_active_hand]
            if can_split(active_hand) and session.cash_on_hand >= current_bet:
                session.cash_on_hand -= current_bet
                card1, card2 = active_hand
                bj_luck = get_game_luck(session, "blackjack")
                bj_effects = get_game_effects(session, "blackjack")
                preferred_ranks = bj_effects.get("preferred_ranks", [])
                session.bj_player_hands[session.bj_active_hand] = [
                    card1,
                    bj_deal_biased_card(session.bj_deck, bj_luck, favor_high=True, preferred_ranks=preferred_ranks),
                ]
                session.bj_player_hands.insert(
                    session.bj_active_hand + 1,
                    [card2, bj_deal_biased_card(session.bj_deck, bj_luck, favor_high=True, preferred_ranks=preferred_ranks)],
                )
                session.bj_bets.insert(session.bj_active_hand + 1, current_bet)
                session.bj_message = "Split hand."
                update_main_metrics(window, session)
            else:
                session.bj_message = "Cannot split."
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)

        elif event == "-BJ_RESET-":
            reset_blackjack(session)
            update_main_metrics(window, session)
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)

        elif event == "-POKER_ACTION-":
            if session.he_state == "ante":
                try:
                    ante = int(values.get("-POKER_BET-", 0) or 0)
                except Exception:
                    set_status_message(window, "Invalid poker ante amount.", is_error=True)
                    window["-POKER_MSG_LINE-"].update("Invalid ante amount.")
                    continue
                if ante <= 0:
                    set_status_message(window, "Poker ante must be above $0.", is_error=True)
                    window["-POKER_MSG_LINE-"].update("Enter an ante above $0.")
                    continue
                if ante > session.cash_on_hand:
                    set_status_message(window, "Not enough cash on hand for ante.", is_error=True)
                    window["-POKER_MSG_LINE-"].update("Not enough cash on hand.")
                    continue
                session.saved_he_ante = ante
                session.cash_on_hand -= ante
                session.he_pot = ante * 2
                poker_luck = get_game_luck(session, "poker")
                poker_effects = get_game_effects(session, "poker")
                session.he_player_hole = poker_deal_biased_cards(
                    session.he_deck,
                    2,
                    poker_luck,
                    favor_high=True,
                    preferred_ranks=poker_effects.get("preferred_ranks", []),
                )
                session.he_dealer_hole = poker_deal_cards(session.he_deck, 2)
                session.he_state = "pre_flop"
            elif session.he_state in ["pre_flop", "flop", "turn"]:
                try:
                    bet = int(values.get("-POKER_BET-", 0) or 0)
                except Exception:
                    set_status_message(window, "Invalid poker bet amount.", is_error=True)
                    window["-POKER_MSG_LINE-"].update("Invalid bet amount.")
                    continue
                if bet > session.cash_on_hand:
                    set_status_message(window, "Not enough cash on hand for poker bet.", is_error=True)
                    window["-POKER_MSG_LINE-"].update("Not enough cash on hand.")
                    continue
                session.cash_on_hand -= bet
                session.he_pot += bet * 2
                if session.he_state == "pre_flop":
                    session.he_community.extend(poker_deal_cards(session.he_deck, 3))
                    session.he_state = "flop"
                elif session.he_state == "flop":
                    session.he_community.extend(poker_deal_cards(session.he_deck, 1))
                    session.he_state = "turn"
                elif session.he_state == "turn":
                    session.he_community.extend(poker_deal_cards(session.he_deck, 1))
                    session.he_state = "river"
            elif session.he_state == "river":
                score_p, hand_p = get_best_hand(session.he_player_hole, session.he_community)
                score_d, hand_d = get_best_hand(session.he_dealer_hole, session.he_community)
                winner = determine_winner(score_p, score_d)
                if winner == "player":
                    session.cash_on_hand += session.he_pot
                elif winner == "tie":
                    session.cash_on_hand += session.he_pot // 2
                session.he_result = {"winner": winner, "player": (score_p, hand_p), "dealer": (score_d, hand_d)}
                session.he_state = "game_over"
                update_main_metrics(window, session)
            refresh_poker_cards(window, session)
            window["-POKER_MSG_LINE-"].update(format_poker_status(session))

        elif event == "-POKER_FOLD-" and session.he_state in ["pre_flop", "flop", "turn", "river"]:
            session.he_result = {"winner": "dealer", "reason": "You folded."}
            session.he_state = "game_over"
            window["-POKER_MSG_LINE-"].update("You folded.")

        elif event == "-POKER_RESET-":
            reset_poker(session)
            update_main_metrics(window, session)
            refresh_poker_cards(window, session)
            window["-POKER_MSG_LINE-"].update("Start a hand to play.")

        if session.bj_state == "dealer_turn":
            settle_blackjack_dealer(session)
            refresh_blackjack_cards(window, session)
            window["-BJ_MSG_LINE-"].update(session.bj_message)
            update_main_metrics(window, session)

    window.close()


if __name__ == "__main__":
    main()
