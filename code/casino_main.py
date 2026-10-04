import sys
import textwrap
import pygame
from slots_screen import SlotsScreen
from slots import SlotsGame
from blackjack import BlackjackGame
from blackjack_screen import BlackjackScreen
from poker import PokerGame
from poker_screen import PokerScreen
from roulette import RouletteGame
from roulette_screen import RouletteScreen
from shop import AVAILABLE_POWERUPS, ShopGame, get_luck_chance
from shop_screen import ShopScreen
from casino_data import load_single_player, save_single_player
from ui_mouse import set_position
from ui_scaling import (
    blit_at,
    blit_center,
    configure,
    draw_circle,
    draw_line,
    draw_rect,
    make_font,
    to_layout,
)


pygame.init()

WIDTH = 900
HEIGHT = 600
SCREEN = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE,
)
configure(SCREEN)
pygame.display.set_caption("Snake Eye Casino")

CLOCK = pygame.time.Clock()
TITLE_FONT = make_font("segoeui", 68, bold=True)
LOBBY_FONT = make_font("segoeui", 40, bold=True)
BUTTON_FONT = make_font(None, 40)
TEXT_FONT = make_font(None, 32)
SMALL_FONT = make_font(None, 24)
CHIPS_FONT = make_font("Consolas", 24)
CONSOLE_FONT = make_font("Consolas", 20)
LUCK_FONT = make_font(None, 18)

BACKGROUND = (9, 25, 31)
PANEL_COLOR = (15, 43, 45)
GOLD = (225, 182, 89)
BUTTON_COLOR = (30, 77, 70)
BUTTON_HOVER_COLOR = (47, 111, 93)
TEXT_COLOR = (255, 255, 255)
DARK_TEXT_COLOR = (244, 236, 214)

state = "title"

START_BUTTON = pygame.Rect(325, 370, 250, 65)
QUIT_BUTTON = pygame.Rect(325, 455, 250, 65)
BACK_BUTTON = pygame.Rect(30, 30, 130, 50)

MENU_BUTTONS = {
    "Slots": pygame.Rect(325, 185, 250, 52),
    "Blackjack": pygame.Rect(325, 252, 250, 52),
    "Poker": pygame.Rect(325, 319, 250, 52),
    "Roulette": pygame.Rect(325, 386, 250, 52),
    "Shop": pygame.Rect(740, 30, 130, 50),
}


def draw_background():
    SCREEN.fill(BACKGROUND)
    draw_circle(SCREEN, (13, 37, 39), (450, 285), 260)
    draw_circle(SCREEN, (17, 48, 47), (450, 285), 220, 2)
    draw_circle(SCREEN, (17, 48, 47), (450, 285), 184, 1)
    draw_line(SCREEN, (41, 76, 68), (0, 0), (WIDTH, 0), 3)
    draw_line(
        SCREEN,
        (41, 76, 68),
        (0, HEIGHT - 3),
        (WIDTH, HEIGHT - 3),
        3,
    )


def draw_panel(rect, fill=PANEL_COLOR):
    shadow = rect.move(0, 5)
    draw_rect(SCREEN, (4, 15, 20), shadow, border_radius=20)
    draw_rect(SCREEN, fill, rect, border_radius=20)
    draw_rect(SCREEN, (56, 99, 83), rect, 2, border_radius=20)


def draw_button(text, rect):
    mouse_position = to_layout(pygame.mouse.get_pos())
    set_position(mouse_position)
    color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_position) else BUTTON_COLOR

    draw_rect(SCREEN, (4, 15, 20), rect.move(0, 4), border_radius=12)
    draw_rect(SCREEN, color, rect, border_radius=12)
    draw_rect(SCREEN, GOLD, rect, 1, border_radius=12)

    label = BUTTON_FONT.render(text, True, DARK_TEXT_COLOR)
    blit_center(SCREEN, label, rect.center)


def draw_centered_text(text, font, y):
    label = font.render(text, True, TEXT_COLOR)
    blit_center(SCREEN, label, (WIDTH // 2, y))


player = load_single_player()

slots_game = SlotsGame(player)
slots_screen = SlotsScreen(slots_game)
blackjack_game = BlackjackGame(player)
blackjack_screen = BlackjackScreen(blackjack_game)
poker_game = PokerGame(player)
poker_screen = PokerScreen(poker_game)
roulette_game = RouletteGame(player)
roulette_screen = RouletteScreen(roulette_game)
shop_game = ShopGame(player)
shop_screen = ShopScreen(shop_game)

console_open = False
console_command = ""
console_output = "Type help for debug commands."


def execute_console_command(command):
    global console_output
    parts = command.strip().split()
    if not parts:
        return

    action = parts[0].casefold()
    if action == "help" and len(parts) == 1:
        console_output = (
            "add chips <amount> | add item <name> [quantity] | items"
        )
    elif action == "items" and len(parts) == 1:
        console_output = "Available items: " + ", ".join(
            AVAILABLE_POWERUPS
        )
    elif action in ("add", "chips") and (
        (action == "chips" and len(parts) == 2)
        or (action == "add" and len(parts) == 3 and parts[1].casefold() == "chips")
    ):
        amount_text = parts[-1]
        try:
            amount = int(amount_text)
        except ValueError:
            console_output = "Chip amount must be a positive whole number."
            return
        if amount <= 0:
            console_output = "Chip amount must be a positive whole number."
            return
        player["chips"] += amount
        if poker_game.round is not None and not poker_game.round.finished:
            poker_game.seats[0]["stack"] += amount
        console_output = f"Added {amount} chips. Balance: {player['chips']}."
        save_single_player(player)
    elif action in ("add", "item") and (
        (action == "item" and len(parts) >= 2)
        or (action == "add" and len(parts) >= 3 and parts[1].casefold() == "item")
    ):
        item_parts = parts[1:] if action == "item" else parts[2:]
        quantity = 1
        if item_parts[-1].isdigit():
            quantity = int(item_parts.pop())
        item_name = " ".join(item_parts).casefold()
        item = next(
            (
                name for name in AVAILABLE_POWERUPS
                if name.casefold() == item_name
            ),
            None,
        )
        if item is None:
            console_output = "Unknown item. Type items to list available items."
            return
        if quantity < 1:
            console_output = "Item quantity must be at least 1."
            return
        inventory_key = (
            "perma_powerups"
            if AVAILABLE_POWERUPS[item]["type"] == "perma"
            else "temp_powerups"
        )
        player.setdefault(inventory_key, []).extend([item] * quantity)
        console_output = f"Added {quantity} {item}."
        save_single_player(player)
    else:
        console_output = "Unknown command. Type help for debug commands."


def draw_console():
    panel = pygame.Rect(55, 178, 790, 220)
    draw_rect(SCREEN, (5, 12, 16), panel, border_radius=10)
    draw_rect(SCREEN, GOLD, panel, 2, border_radius=10)
    draw_centered_text("DEBUG CONSOLE", CONSOLE_FONT, 205)
    output_lines = textwrap.wrap(console_output, width=58) or [""]
    for index, line in enumerate(output_lines[:3]):
        output_label = CONSOLE_FONT.render(line, True, (225, 225, 225))
        blit_at(SCREEN, output_label, (75, 232 + index * 22))
    command_label = CONSOLE_FONT.render("> " + console_command, True, (255, 230, 150))
    blit_center(SCREEN, command_label, (450, 320))
    hint = CONSOLE_FONT.render("Enter to run | ` or Esc to close", True, (170, 185, 185))
    blit_center(SCREEN, hint, (450, 365))


def draw_luck_boost():
    luck_percent = round(get_luck_chance(player) * 100)
    if luck_percent <= 0:
        return

    badge = pygame.Rect(690, 72, 180, 30)
    draw_rect(SCREEN, (24, 62, 56), badge, border_radius=16)
    draw_rect(SCREEN, GOLD, badge, 1, border_radius=16)
    label = LUCK_FONT.render(f"Luck boost: {luck_percent}%", True, GOLD)
    blit_center(SCREEN, label, badge.center)


while True:
    set_position(to_layout(pygame.mouse.get_pos()))

    for event in pygame.event.get():
        if event.type == pygame.VIDEORESIZE:
            SCREEN = pygame.display.set_mode(
                (max(1, event.w), max(1, event.h)),
                pygame.RESIZABLE,
            )
            configure(SCREEN)
            continue

        if event.type in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
        ):
            event_data = event.dict.copy()
            event_data["pos"] = to_layout(event.pos)
            if "rel" in event_data:
                event_data["rel"] = to_layout(event.rel)
            event = pygame.event.Event(event.type, event_data)
        elif event.type == pygame.MOUSEWHEEL:
            event_data = event.dict.copy()
            event_data["pos"] = to_layout(
                getattr(event, "pos", pygame.mouse.get_pos())
            )
            event = pygame.event.Event(event.type, event_data)

        if event.type == pygame.QUIT:
            save_single_player(player)
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
            console_open = not console_open
            console_command = ""
            continue

        if console_open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    console_open = False
                    console_command = ""
                elif event.key == pygame.K_RETURN:
                    execute_console_command(console_command)
                    console_command = ""
                elif event.key == pygame.K_BACKSPACE:
                    console_command = console_command[:-1]
                elif event.unicode.isprintable() and len(console_command) < 58:
                    console_command += event.unicode
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "title":
                if START_BUTTON.collidepoint(event.pos):
                    state = "lobby"
                elif QUIT_BUTTON.collidepoint(event.pos):
                    save_single_player(player)
                    pygame.quit()
                    sys.exit()

            elif BACK_BUTTON.collidepoint(event.pos):
                if state == "lobby":
                    state = "title"
                else:
                    if state == "poker":
                        poker_screen.leave()
                    elif state == "blackjack":
                        blackjack_game.leave()
                    elif state == "slots":
                        slots_screen.finish_spin()
                    elif state == "roulette":
                        roulette_screen.finish_spin()

                    save_single_player(player)
                    state = "lobby"

            elif state == "lobby":
                for name, rect in MENU_BUTTONS.items():
                    if rect.collidepoint(event.pos):
                        state = "shop" if name == "Shop" else name.lower()
                        save_single_player(player)
                        break

        if state == "slots":
            slots_screen.handle_event(event)
            save_single_player(player)

        elif state == "blackjack":
            blackjack_screen.handle_event(event)
            save_single_player(player)

        elif state == "poker":
            poker_screen.handle_event(event)
            save_single_player(player)

        elif state == "roulette":
            roulette_screen.handle_event(event)
            save_single_player(player)

        elif state == "shop":
            shop_screen.handle_event(event)
            save_single_player(player)

    if state == "slots" and slots_screen.update():
        save_single_player(player)
    elif state == "roulette" and roulette_screen.update():
        save_single_player(player)
    elif state == "poker":
        poker_screen.update()

    draw_background()

    if state == "title":
        draw_panel(pygame.Rect(205, 115, 490, 395))
        draw_centered_text("SNAKE EYE", TITLE_FONT, 218)
        draw_centered_text("CASINO", TITLE_FONT, 282)
        draw_centered_text(
            "A little luck goes a long way",
            SMALL_FONT,
            330,
        )
        draw_button("PLAY", START_BUTTON)
        draw_button("QUIT", QUIT_BUTTON)

    elif state == "lobby":
        draw_panel(pygame.Rect(235, 52, 430, 480))
        draw_button("Back", BACK_BUTTON)
        draw_centered_text("CHOOSE A GAME", LOBBY_FONT, 98)
        balance_rect = pygame.Rect(340, 128, 220, 38)
        draw_rect(SCREEN, (24, 62, 56), balance_rect, border_radius=19)
        draw_rect(SCREEN, GOLD, balance_rect, 1, border_radius=19)
        balance = CHIPS_FONT.render(f"{player['chips']} chips", True, GOLD)
        blit_center(SCREEN, balance, balance_rect.center)
        for name, rect in MENU_BUTTONS.items():
            draw_button(name, rect)
    elif state == "slots":
        slots_screen.draw(
            SCREEN,
            BACK_BUTTON,
            draw_button,
            draw_centered_text,
            TITLE_FONT,
            TEXT_FONT,
        )

    elif state == "blackjack":
        blackjack_screen.draw(
            SCREEN,
            BACK_BUTTON,
            draw_button,
            draw_centered_text,
            TITLE_FONT,
            TEXT_FONT,
        )

    elif state == "poker":
        poker_screen.draw(
            SCREEN,
            BACK_BUTTON,
            draw_button,
            draw_centered_text,
            TITLE_FONT,
            TEXT_FONT,
        )

    elif state == "roulette":
        roulette_screen.draw(
            SCREEN,
            BACK_BUTTON,
            draw_button,
            draw_centered_text,
            TITLE_FONT,
        )

    elif state == "shop":
        shop_screen.draw(SCREEN, BACK_BUTTON, draw_button)

    else:
        draw_button("Back", BACK_BUTTON)
        draw_centered_text(state.title(), TITLE_FONT, 220)
        draw_centered_text("We'll build this screen next.", TEXT_FONT, 300)

    if state in ("slots", "blackjack", "poker", "roulette"):
        draw_luck_boost()

    if console_open:
        draw_console()

    pygame.display.flip()
    CLOCK.tick(60)