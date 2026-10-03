import sys
import pygame
from slots_screen import SlotsScreen
from slots import SlotsGame
from blackjack import BlackjackGame
from blackjack_screen import BlackjackScreen
from poker import PokerGame
from poker_screen import PokerScreen
from roulette import RouletteGame
from roulette_screen import RouletteScreen
from shop import ShopGame
from shop_screen import ShopScreen
from casino_data import load_single_player, save_single_player


pygame.init()

WIDTH = 900
HEIGHT = 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Eye Casino")

CLOCK = pygame.time.Clock()
TITLE_FONT = pygame.font.SysFont("segoeui", 68, bold=True)
BUTTON_FONT = pygame.font.Font(None, 40)
TEXT_FONT = pygame.font.Font(None, 32)

BACKGROUND = (18, 65, 52)
BUTTON_COLOR = (205, 160, 65)
BUTTON_HOVER_COLOR = (235, 195, 95)
TEXT_COLOR = (255, 255, 255)
DARK_TEXT_COLOR = (30, 25, 18)

state = "title"

START_BUTTON = pygame.Rect(325, 370, 250, 65)
QUIT_BUTTON = pygame.Rect(325, 455, 250, 65)
BACK_BUTTON = pygame.Rect(30, 30, 130, 50)

MENU_BUTTONS = {
    "Slots": pygame.Rect(325, 170, 250, 55),
    "Blackjack": pygame.Rect(325, 240, 250, 55),
    "Poker": pygame.Rect(325, 310, 250, 55),
    "Roulette": pygame.Rect(325, 380, 250, 55),
    "Shop": pygame.Rect(740, 30, 130, 50),
}


def draw_button(text, rect):
    mouse_position = pygame.mouse.get_pos()
    color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_position) else BUTTON_COLOR

    pygame.draw.rect(SCREEN, color, rect, border_radius=10)

    label = BUTTON_FONT.render(text, True, DARK_TEXT_COLOR)
    label_rect = label.get_rect(center=rect.center)
    SCREEN.blit(label, label_rect)


def draw_centered_text(text, font, y):
    label = font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=(WIDTH // 2, y))
    SCREEN.blit(label, label_rect)


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


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "title":
                if START_BUTTON.collidepoint(event.pos):
                    state = "lobby"
                elif QUIT_BUTTON.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            elif BACK_BUTTON.collidepoint(event.pos):
                if state == "lobby":
                    state = "title"
                else:
                    if state == "poker":
                        poker_screen.leave()
                        save_single_player(player)
                    elif state == "blackjack":
                        blackjack_game.leave()
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

    SCREEN.fill(BACKGROUND)

    if state == "title":
        draw_centered_text("Snake Eye Casino", TITLE_FONT, 220)
        draw_button("Start", START_BUTTON)
        draw_button("Quit", QUIT_BUTTON)

    elif state == "lobby":
        draw_button("Back", BACK_BUTTON)
        draw_centered_text("Choose a game", TITLE_FONT, 100)
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
            TEXT_FONT,
        )

    elif state == "shop":
        shop_screen.draw(SCREEN, BACK_BUTTON, draw_button)

    else:
        draw_button("Back", BACK_BUTTON)
        draw_centered_text(state.title(), TITLE_FONT, 220)
        draw_centered_text("We'll build this screen next.", TEXT_FONT, 300)

    pygame.display.flip()
    CLOCK.tick(60)