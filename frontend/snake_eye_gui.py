import os
import sys
import PySimpleGUI as sg

# Package-relative imports when running as a package or standalone script.
try:
    from ..backend.casinoBackEnd import (
        initialize_account,
        get_total_value,
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
        calculate_hand_value as bj_calculate_hand_value,
        is_blackjack,
        can_split,
        format_hand as bj_format_hand,
        format_card as bj_format_card,
    )
    from ..backend.pokerBackEnd import (
        create_deck as poker_create_deck,
        deal_cards as poker_deal_cards,
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
        calculate_hand_value as bj_calculate_hand_value,
        is_blackjack,
        can_split,
        format_hand as bj_format_hand,
        format_card as bj_format_card,
    )
    from backend.pokerBackEnd import (
        create_deck as poker_create_deck,
        deal_cards as poker_deal_cards,
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


def draw_casino_banner(graph):
    import random
    graph.erase()
    # Background
    graph.draw_rectangle((0, 0), (640, 120), fill_color="#101820", line_color="#FDD835", line_width=4)

    # Title and subtitle — centered, top half
    graph.draw_text("Snake Eye Casino", (320, 100), font=("Helvetica", 22, "bold"), color="#FFD54F")
    graph.draw_text("Live casino action — slots, blackjack, poker", (320, 73), font=("Helvetica", 11), color="#E0E0E0")

    # Chips — left side, bottom half (y=38, radius 16)
    for x in (30, 68, 106):
        graph.draw_circle((x, 38), 16, fill_color="#B71C1C", line_color="#FFFFFF", line_width=2)
        graph.draw_circle((x, 38), 10, fill_color="#FDD835", line_color="#FFFFFF", line_width=1)
        graph.draw_text("$", (x, 38), font=("Helvetica", 11, "bold"), color="#641E16")

    # 4 suit cards — right area, bottom half (y=38, card half-w=17 half-h=22)
    suit_data = [(430, "♠", "#1E88E5"), (465, "♥", "#E53935"), (500, "♦", "#FBC02D"), (535, "♣", "#27AE60")]
    for x, suit, color in suit_data:
        graph.draw_rectangle((x - 17, 16), (x + 17, 60), fill_color="#FFFFFF", line_color="#B0BEC5", line_width=1)
        graph.draw_text(suit, (x, 38), font=("Helvetica", 18, "bold"), color=color)

    # 2 dice — far right, bottom half (y=38, half-size=13, spaced so left edge > 552)
    for dx in (578, 616):
        graph.draw_rectangle((dx - 13, 25), (dx + 13, 51), fill_color="#FFFFFF", line_color="#333333", line_width=1)
        dot_coords = {
            1: [(dx, 38)],
            2: [(dx - 5, 44), (dx + 5, 32)],
            3: [(dx - 5, 44), (dx, 38), (dx + 5, 32)],
            4: [(dx - 5, 44), (dx + 5, 44), (dx - 5, 32), (dx + 5, 32)],
            5: [(dx - 5, 44), (dx + 5, 44), (dx, 38), (dx - 5, 32), (dx + 5, 32)],
            6: [(dx - 5, 46), (dx - 5, 38), (dx - 5, 30), (dx + 5, 46), (dx + 5, 38), (dx + 5, 30)],
        }
        for dot_x, dot_y in dot_coords[random.randint(1, 6)]:
            graph.draw_circle((dot_x, dot_y), 2, fill_color="#000000", line_color="#000000")


def format_wheels(wheels):
    return "\n".join([" | ".join(row) for row in wheels])


def format_blackjack_status(session):
    lines = [f"Blackjack - {session.bj_state.replace('_', ' ').title()}", f"Message: {session.bj_message}"]
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
            prefix = "👉 " if idx == session.bj_active_hand and session.bj_state == "playing" else "   "
            lines.append(f"{prefix}Hand {idx + 1} [Bet ${bet}]: {bj_format_hand(hand)} ({score})")
    return "\n".join(lines)


def format_poker_status(session):
    lines = [f"Texas Hold'em - {session.he_state.replace('_', ' ').title()}", f"Pot: ${session.he_pot}"]
    lines.append(f"Community: {poker_format_hand(session.he_community)}")
    lines.append(f"Your Hole: {poker_format_hand(session.he_player_hole)}")
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


def update_main_metrics(window, session):
    window["-DIGITAL-"].update(format_money(session.digital_balance))
    window["-CASH-"].update(format_money(session.cash_on_hand))
    window["-TOTAL-"].update(format_money(get_total_value(session)))


def main():
    session = SessionState()
    initialize_account(session)
    sg.theme("DarkAmber")

    layout = [
        [
            sg.Graph(
                canvas_size=(640, 120),
                graph_bottom_left=(0, 0),
                graph_top_right=(640, 120),
                key="-BANNER-",
                enable_events=False,
                background_color="#101820",
            )
        ],
        [
            sg.Text("Digital balance:", text_color="#FFD54F"),
            sg.Text(format_money(session.digital_balance), key="-DIGITAL-", text_color="#FFFFFF"),
            sg.Text("   "),
            sg.Text("Cash on hand:", text_color="#FFD54F"),
            sg.Text(format_money(session.cash_on_hand), key="-CASH-", text_color="#FFFFFF"),
            sg.Text("   "),
            sg.Text("Total value:", text_color="#FFD54F"),
            sg.Text(format_money(get_total_value(session)), key="-TOTAL-", text_color="#FFFFFF"),
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Transfer amount:", text_color="#FFFFFF"), sg.Input(key="-TRANSFER-", size=(10, 1)), sg.Button("Transfer")],
        [sg.Text("Withdraw amount:", text_color="#FFFFFF"), sg.Input(key="-WITHDRAW-", size=(10, 1)), sg.Button("Withdraw")],
        [sg.Text("Message:", text_color="#FFFFFF"), sg.Text("", key="-MSG-", size=(60, 1), text_color="#FFFFFF")],
        [sg.HorizontalSeparator()],
        [
            sg.Button("Shop", button_color=("#101820", "#FDD835")),
            sg.Button("Inventory", button_color=("#101820", "#FDD835")),
            sg.Button("Slots", button_color=("#101820", "#FDD835")),
            sg.Button("Blackjack", button_color=("#101820", "#FDD835")),
            sg.Button("Poker", button_color=("#101820", "#FDD835")),
            sg.Button("Quit", button_color=("#FFFFFF", "#D32F2F")),
        ],
    ]

    _icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'icon.ico')
    app_icon = _icon_path if os.path.exists(_icon_path) else None
    window = sg.Window("Snake Eye Casino", layout, finalize=True, icon=app_icon)
    draw_casino_banner(window["-BANNER-"])

    def show_message(text=""):
        window["-MSG-"].update(text)

    def open_inventory_window():
        inventory = get_inventory(session)
        inv_layout = [[sg.Text("Inventory", font=(None, 16))]]
        if inventory:
            for item in inventory:
                inv_layout.append([sg.Text(f"- {item['name']}")])
        else:
            inv_layout.append([sg.Text("(empty)")])
        inv_layout.append([sg.Button("Close")])
        inv_win = sg.Window("Inventory", inv_layout, modal=True, icon=app_icon)
        inv_win.read()
        inv_win.close()

    def open_shop_window():
        if "shop_message" not in session:
            session.shop_message = ""
        items = get_shop_items()
        shop_layout = [[sg.Text("Shop", font=(None, 16))]]
        for item in items:
            shop_layout.append(
                [
                    sg.Text(f"{item['name']} - ${item['price']}: {item['description']}", size=(50, 1)),
                    sg.Button("Buy", key=("BUY", item["id"])),
                ]
            )
        shop_layout.append([sg.Text("Message:"), sg.Text(session.shop_message, key="-SHOP_MSG-", size=(40, 1))])
        shop_layout.append([sg.Button("Close")])
        shop_win = sg.Window("Shop", shop_layout, modal=True, finalize=True, icon=app_icon)
        while True:
            event, _ = shop_win.read()
            if event in (sg.WIN_CLOSED, "Close"):
                break
            if isinstance(event, tuple) and event[0] == "BUY":
                _, item_id = event
                success, msg = buy_item(session, item_id)
                session.shop_message = msg
                shop_win["-SHOP_MSG-"].update(msg)
                update_main_metrics(window, session)
        shop_win.close()

    def open_slot_window():
        import random as _rnd
        if "consecutive_losses" not in session:
            session.consecutive_losses = 0
        if "slots_wheels" not in session:
            session.slots_wheels = spin_slots(session.consecutive_losses)
            session.slots_winning_lines = []
            session.slot_message = "Place a bet and spin to win!"

        SLOT_SYMS = ["cherry","lemon","watermelon","bell","heart","horseShoe","bar","diamond","seven"]
        SLOT_W, SLOT_H = 500, 320
        REEL_W, REEL_GAP, SYM_H = 130, 12, 86
        start_x = (SLOT_W - (3 * REEL_W + 2 * REEL_GAP)) // 2
        reel_xs = [start_x, start_x + REEL_W + REEL_GAP, start_x + 2 * (REEL_W + REEL_GAP)]
        start_y = (SLOT_H - 3 * SYM_H) // 2
        row_ys = [
            start_y + 2 * SYM_H + SYM_H // 2,
            start_y + SYM_H + SYM_H // 2,
            start_y + SYM_H // 2,
        ]

        ROW_NAMES = ["Top row", "Middle row", "Bottom row"]
        COL_NAMES = ["Left wheel", "Center wheel", "Right wheel"]
        DIAG_TLBR = "Diagonal top-left to bottom-right"
        DIAG_BLTR = "Diagonal bottom-left to top-right"
        DIAG_CELLS_TLBR = {(0, 0), (1, 1), (2, 2)}
        DIAG_CELLS_BLTR = {(0, 2), (1, 1), (2, 0)}

        SYM_BG = {
            "cherry": "#FADBD8", "lemon": "#FEF9E7", "watermelon": "#D5F5E3",
            "bell": "#FDEBD0", "heart": "#FCE4EC", "horseShoe": "#EAECEE",
            "bar": "#D6EAF8", "diamond": "#E8DAEF", "seven": "#FADBD8",
        }

        def draw_symbol(graph, sym, cx, cy):
            """Draw each slot symbol using primitives so each looks distinct."""
            s = 20
            if sym == "cherry":
                # Upright cherries: stem at top, fruit below
                graph.draw_line((cx, cy + s), (cx, cy + s // 3), color="#27AE60", width=3)
                graph.draw_line((cx, cy + s // 3), (cx - 8, cy + 2), color="#27AE60", width=3)
                graph.draw_line((cx, cy + s // 3), (cx + 8, cy + 2), color="#27AE60", width=3)
                r = s // 3
                graph.draw_circle((cx - 8, cy - 8), r, fill_color="#C0392B", line_color="#922B21", line_width=1)
                graph.draw_circle((cx + 8, cy - 8), r, fill_color="#C0392B", line_color="#922B21", line_width=1)
            elif sym == "lemon":
                # Horizontal lemon body with pointed tips
                graph.draw_circle((cx - 9, cy), 11, fill_color="#F4D03F", line_color="#D4AC0D", line_width=2)
                graph.draw_circle((cx + 9, cy), 11, fill_color="#F4D03F", line_color="#D4AC0D", line_width=2)
                graph.draw_rectangle((cx - 9, cy - 11), (cx + 9, cy + 11), fill_color="#F4D03F", line_color="#F4D03F", line_width=1)
                graph.draw_circle((cx - 22, cy), 3, fill_color="#F4D03F", line_color="#D4AC0D", line_width=1)
                graph.draw_circle((cx + 22, cy), 3, fill_color="#F4D03F", line_color="#D4AC0D", line_width=1)
            elif sym == "watermelon":
                # Green circle with red interior and seeds
                graph.draw_circle((cx, cy), s, fill_color="#27AE60", line_color="#1E8449", line_width=2)
                graph.draw_circle((cx, cy), s - 5, fill_color="#E74C3C", line_color="#E74C3C", line_width=1)
                for ox, oy in [(-s//2+3, s//4), (0, s//2-2), (s//2-3, s//4), (-s//3+2, -s//4), (s//3-2, -s//4)]:
                    graph.draw_circle((cx + ox, cy + oy), 3, fill_color="#1C2833", line_color="#1C2833", line_width=1)
            elif sym == "bell":
                # Bell shape: wide body + narrower dome + clapper (not a bullseye)
                graph.draw_rectangle((cx - s, cy - s // 3), (cx + s, cy + s // 3), fill_color="#E67E22", line_color="#CA6F1E", line_width=1)
                graph.draw_rectangle((cx - s // 2, cy + s // 3), (cx + s // 2, cy + s * 4 // 5), fill_color="#E67E22", line_color="#CA6F1E", line_width=1)
                graph.draw_circle((cx, cy + s * 4 // 5 + s // 7), s // 6, fill_color="#E67E22", line_color="#CA6F1E", line_width=1)
                graph.draw_rectangle((cx - s - 2, cy - s // 3 - 3), (cx + s + 2, cy - s // 3 + 3), fill_color="#CA6F1E", line_color="#CA6F1E", line_width=1)
                graph.draw_circle((cx, cy - s // 3 - s // 4), s // 6, fill_color="#CA6F1E", line_color="#A04000", line_width=1)
            elif sym == "heart":
                graph.draw_text("♥", (cx, cy), font=("Helvetica", 32, "bold"), color="#E91E63")
            elif sym == "horseShoe":
                graph.draw_text("∩", (cx, cy + 5), font=("Helvetica", 38, "bold"), color="#717D7E")
            elif sym == "bar":
                graph.draw_rectangle((cx - s, cy - s // 2 + 2), (cx + s, cy + s // 2 - 2), fill_color="#1A5276", line_color="#FDD835", line_width=2)
                graph.draw_text("BAR", (cx, cy), font=("Helvetica", 14, "bold"), color="#FDD835")
            elif sym == "diamond":
                # Classic engagement-ring diamond silhouette
                top = [(cx - 12, cy + 8), (cx + 12, cy + 8), (cx + 7, cy + 2), (cx - 7, cy + 2)]
                bottom = [(cx - 7, cy + 2), (cx + 7, cy + 2), (cx, cy - 16)]
                graph.draw_polygon(top, fill_color="#D6EAF8", line_color="#5DADE2", line_width=2)
                graph.draw_polygon(bottom, fill_color="#A9CCE3", line_color="#5DADE2", line_width=2)
                graph.draw_line((cx, cy + 8), (cx, cy - 16), color="#FFFFFF", width=1)
                graph.draw_line((cx - 7, cy + 2), (cx, cy - 16), color="#EBF5FB", width=1)
                graph.draw_line((cx + 7, cy + 2), (cx, cy - 16), color="#EBF5FB", width=1)
                # Ring band beneath the diamond
                graph.draw_line((cx - 13, cy - 18), (cx + 13, cy - 18), color="#F1C40F", width=3)
            elif sym == "seven":
                graph.draw_text("7", (cx, cy + 2), font=("Helvetica", 34, "bold"), color="#C0392B")
            else:
                graph.draw_text(sym[:3].upper(), (cx, cy), font=("Helvetica", 14, "bold"), color="#333333")

        def draw_slots_graph(graph, wheels, winning_lines):
            graph.erase()
            win_set = {name for name, _ in winning_lines}
            graph.draw_rectangle((0, 0), (SLOT_W, SLOT_H), fill_color="#1B4332")
            fx1 = start_x - 10
            fy1 = start_y - 10
            fx2 = start_x + 3 * REEL_W + 2 * REEL_GAP + 10
            fy2 = start_y + 3 * SYM_H + 10
            graph.draw_rectangle((fx1 - 2, fy1 - 2), (fx2 + 2, fy2 + 2), fill_color="#B7950B", line_color="#B7950B")
            graph.draw_rectangle((fx1, fy1), (fx2, fy2), fill_color="#1C2833", line_color="#FDD835", line_width=3)
            mid_y = row_ys[1]
            for ax in (fx1 - 14, fx2 + 6):
                graph.draw_rectangle((ax, mid_y - 8), (ax + 10, mid_y + 8), fill_color="#FDD835")
            for col, rx in enumerate(reel_xs):
                for row in range(3):
                    cy = row_ys[row]
                    symbol = wheels[col][row]
                    bg = SYM_BG.get(symbol, "#FFFFFF")
                    is_win = (
                        ROW_NAMES[row] in win_set
                        or COL_NAMES[col] in win_set
                        or (DIAG_TLBR in win_set and (col, row) in DIAG_CELLS_TLBR)
                        or (DIAG_BLTR in win_set and (col, row) in DIAG_CELLS_BLTR)
                    )
                    cell_bg = "#FFFDE7" if is_win else bg
                    cell_border = "#FFD700" if is_win else "#CFD8DC"
                    cell_bw = 3 if is_win else 1
                    graph.draw_rectangle(
                        (rx + 2, cy - SYM_H // 2 + 2),
                        (rx + REEL_W - 2, cy + SYM_H // 2 - 2),
                        fill_color=cell_bg, line_color=cell_border, line_width=cell_bw,
                    )
                    draw_symbol(graph, symbol, rx + REEL_W // 2, cy)
                if col < 2:
                    sep_x = rx + REEL_W + REEL_GAP // 2
                    graph.draw_line((sep_x, fy1 + 4), (sep_x, fy2 - 4), color="#37474F", width=2)

        slot_layout = [
            [sg.Text("🎰  Slot Machine", font=(None, 15, "bold"))],
            [sg.Graph(
                canvas_size=(SLOT_W, SLOT_H),
                graph_bottom_left=(0, 0),
                graph_top_right=(SLOT_W, SLOT_H),
                key="-SLOT_GRAPH-",
                background_color="#1B4332",
            )],
            [
                sg.Text("Bet:"),
                sg.Input(default_text=str(session.get("slot_bet_amount", 1)), key="-SLOT_BET-", size=(8, 1)),
                sg.Button("Spin"),
                sg.Button("Close"),
            ],
            [sg.Text(session.slot_message, key="-SLOT_MSG-", size=(60, 2))],
        ]
        slot_win = sg.Window("Slots", slot_layout, modal=True, finalize=True, icon=app_icon)
        draw_slots_graph(slot_win["-SLOT_GRAPH-"], session.slots_wheels, session.slots_winning_lines)
        while True:
            event, values = slot_win.read()
            if event in (sg.WIN_CLOSED, "Close"):
                break
            if event == "Spin":
                try:
                    bet_amount = int(values.get("-SLOT_BET-", 0) or 0)
                except Exception:
                    slot_win["-SLOT_MSG-"].update("Invalid bet amount.")
                    continue
                if bet_amount <= 0:
                    slot_win["-SLOT_MSG-"].update("Enter a bet above $0.")
                    continue
                if bet_amount > session.cash_on_hand:
                    slot_win["-SLOT_MSG-"].update("Not enough cash on hand.")
                    continue
                session.cash_on_hand -= bet_amount
                session.slots_wheels = spin_slots(session.consecutive_losses)
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
                # Spin animation — show random symbols cycling before the real result
                for frame in range(18):
                    fake = [[_rnd.choice(SLOT_SYMS) for _ in range(3)] for _ in range(3)]
                    draw_slots_graph(slot_win["-SLOT_GRAPH-"], fake, [])
                    slot_win["-SLOT_MSG-"].update("Spinning" + "." * ((frame % 3) + 1))
                    slot_win.read(timeout=70)
                draw_slots_graph(slot_win["-SLOT_GRAPH-"], session.slots_wheels, session.slots_winning_lines)
                slot_win["-SLOT_MSG-"].update(session.slot_message)
                update_main_metrics(window, session)
        slot_win.close()

    def open_blackjack_window():
        if "bj_state" not in session:
            reset_blackjack(session)

        bj_layout = [
            [sg.Text("Blackjack", font=(None, 16))],
            [sg.Multiline(format_blackjack_status(session), size=(70, 20), key="-BJ_INFO-", disabled=True)],
            [sg.Text("Bet amount:"), sg.Input(default_text=str(session.saved_bj_bet), key="-BJ_BET-", size=(10, 1)), sg.Button("Deal")],
            [sg.Button("Hit"), sg.Button("Stand"), sg.Button("Double Down"), sg.Button("Split"), sg.Button("Play Again"), sg.Button("Close")],
        ]
        bj_win = sg.Window("Blackjack", bj_layout, modal=True, finalize=True, icon=app_icon)
        while True:
            event, values = bj_win.read()
            if event in (sg.WIN_CLOSED, "Close"):
                break
            if event == "Deal" and session.bj_state == "betting":
                try:
                    bet = int(values.get("-BJ_BET-", 0) or 0)
                except Exception:
                    session.bj_message = "Invalid bet amount."
                    bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
                    continue
                if bet <= 0:
                    session.bj_message = "Enter a bet above $0."
                elif bet > session.cash_on_hand:
                    session.bj_message = "You do not have enough cash on hand."
                else:
                    session.saved_bj_bet = bet
                    session.cash_on_hand -= bet
                    session.bj_bets = [bet]
                    session.bj_player_hands = [[bj_deal_card(session.bj_deck), bj_deal_card(session.bj_deck)]]
                    session.bj_dealer_hand = [bj_deal_card(session.bj_deck), bj_deal_card(session.bj_deck)]
                    if is_blackjack(session.bj_player_hands[0]):
                        session.bj_state = "game_over"
                        payout = int(round(bet * 2.5))
                        session.cash_on_hand += payout
                        session.bj_message = f"BLACKJACK! You won ${payout}!"
                    else:
                        session.bj_state = "playing"
                        session.bj_message = "Your move."
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
                update_main_metrics(window, session)
            elif event == "Hit" and session.bj_state == "playing":
                active_hand = session.bj_player_hands[session.bj_active_hand]
                active_hand.append(bj_deal_card(session.bj_deck))
                if bj_calculate_hand_value(active_hand) >= 21:
                    session.bj_state = "dealer_turn"
                session.bj_message = "Hit."
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
            elif event == "Stand" and session.bj_state == "playing":
                session.bj_state = "dealer_turn"
                session.bj_message = "Stand."
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
            elif event == "Double Down" and session.bj_state == "playing":
                active_hand = session.bj_player_hands[session.bj_active_hand]
                current_bet = session.bj_bets[session.bj_active_hand]
                if session.cash_on_hand >= current_bet and len(active_hand) == 2:
                    session.cash_on_hand -= current_bet
                    session.bj_bets[session.bj_active_hand] += current_bet
                    active_hand.append(bj_deal_card(session.bj_deck))
                    session.bj_state = "dealer_turn"
                    session.bj_message = "Double down."
                    update_main_metrics(window, session)
                else:
                    session.bj_message = "Cannot double down."
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
            elif event == "Split" and session.bj_state == "playing":
                active_hand = session.bj_player_hands[session.bj_active_hand]
                current_bet = session.bj_bets[session.bj_active_hand]
                if can_split(active_hand) and session.cash_on_hand >= current_bet:
                    session.cash_on_hand -= current_bet
                    card1, card2 = active_hand
                    session.bj_player_hands[session.bj_active_hand] = [card1, bj_deal_card(session.bj_deck)]
                    session.bj_player_hands.insert(session.bj_active_hand + 1, [card2, bj_deal_card(session.bj_deck)])
                    session.bj_bets.insert(session.bj_active_hand + 1, current_bet)
                    session.bj_message = "Split hand."
                    update_main_metrics(window, session)
                else:
                    session.bj_message = "Cannot split."
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
            elif event == "Play Again":
                reset_blackjack(session)
                update_main_metrics(window, session)
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
            if session.bj_state == "dealer_turn":
                dealer_score = bj_calculate_hand_value(session.bj_dealer_hand)
                while dealer_score < 17:
                    session.bj_dealer_hand.append(bj_deal_card(session.bj_deck))
                    dealer_score = bj_calculate_hand_value(session.bj_dealer_hand)
                session.bj_state = "game_over"
                total_net = 0
                results = []
                for idx, hand in enumerate(session.bj_player_hands):
                    player_score = bj_calculate_hand_value(hand)
                    bet = session.bj_bets[idx]
                    if player_score > 21:
                        results.append(f"Hand {idx + 1}: Bust (${bet} lost)")
                        total_net -= bet
                    elif dealer_score > 21 or player_score > dealer_score:
                        payout = bet * 2
                        session.cash_on_hand += payout
                        results.append(f"Hand {idx + 1}: Win! Payout ${payout}")
                        total_net += bet
                    elif player_score == dealer_score:
                        session.cash_on_hand += bet
                        results.append(f"Hand {idx + 1}: Push. Bet returned.")
                    else:
                        results.append(f"Hand {idx + 1}: Lose (${bet} lost)")
                        total_net -= bet
                session.bj_message = " | ".join(results)
                bj_win["-BJ_INFO-"].update(format_blackjack_status(session))
                update_main_metrics(window, session)
        bj_win.close()

    def open_poker_window():
        if "he_state" not in session:
            reset_poker(session)
        poker_layout = [
            [sg.Text("Texas Hold'em", font=(None, 16))],
            [sg.Multiline(format_poker_status(session), size=(70, 20), key="-POKER_INFO-", disabled=True)],
            [sg.Text("Bet amount (0 to check/call):"), sg.Input(default_text=str(session.saved_he_ante), key="-POKER_BET-", size=(10, 1)), sg.Button("Action")],
            [sg.Button("Fold"), sg.Button("Next Hand"), sg.Button("Close")],
        ]
        poker_win = sg.Window("Poker", poker_layout, modal=True, finalize=True, icon=app_icon)
        while True:
            event, values = poker_win.read()
            if event in (sg.WIN_CLOSED, "Close"):
                break
            if event == "Action":
                if session.he_state == "ante":
                    try:
                        ante = int(values.get("-POKER_BET-", 0) or 0)
                    except Exception:
                        poker_win["-POKER_INFO-"].update("Invalid ante amount.")
                        continue
                    if ante <= 0:
                        poker_win["-POKER_INFO-"].update("Enter an ante above $0.")
                        continue
                    if ante > session.cash_on_hand:
                        poker_win["-POKER_INFO-"].update("Not enough cash on hand.")
                        continue
                    session.saved_he_ante = ante
                    session.cash_on_hand -= ante
                    session.he_pot = ante * 2
                    session.he_player_hole = poker_deal_cards(session.he_deck, 2)
                    session.he_dealer_hole = poker_deal_cards(session.he_deck, 2)
                    session.he_state = "pre_flop"
                elif session.he_state in ["pre_flop", "flop", "turn"]:
                    try:
                        bet = int(values.get("-POKER_BET-", 0) or 0)
                    except Exception:
                        poker_win["-POKER_INFO-"].update("Invalid bet amount.")
                        continue
                    if bet > session.cash_on_hand:
                        poker_win["-POKER_INFO-"].update("Not enough cash on hand.")
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
            elif event == "Fold" and session.he_state in ["pre_flop", "flop", "turn", "river"]:
                session.he_result = {"winner": "dealer", "reason": "You folded."}
                session.he_state = "game_over"
            elif event == "Next Hand":
                reset_poker(session)
                update_main_metrics(window, session)
            poker_win["-POKER_INFO-"].update(format_poker_status(session))
        poker_win.close()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Quit"):
            break
        if event == "Transfer":
            try:
                amount = float(values.get("-TRANSFER-", 0) or 0)
            except Exception:
                show_message("Invalid transfer amount.")
                continue
            session.transfer_amount = amount
            transfer_to_digital(session)
            update_main_metrics(window, session)
            show_message(session.wallet_message)
        elif event == "Withdraw":
            try:
                amount = float(values.get("-WITHDRAW-", 0) or 0)
            except Exception:
                show_message("Invalid withdraw amount.")
                continue
            session.withdraw_amount = amount
            withdraw_to_cash(session)
            update_main_metrics(window, session)
            show_message(session.wallet_message)
        elif event == "Shop":
            open_shop_window()
        elif event == "Inventory":
            open_inventory_window()
        elif event == "Slots":
            open_slot_window()
        elif event == "Blackjack":
            open_blackjack_window()
        elif event == "Poker":
            open_poker_window()

    window.close()


if __name__ == "__main__":
    main()
