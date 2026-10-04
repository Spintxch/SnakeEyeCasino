import pygame
import random
from slots import PAYLINES, SYMBOLS, SlotsGame
from ui_scaling import (
    blit_center,
    draw_circle,
    draw_ellipse,
    draw_line,
    draw_polygon,
    draw_rect,
    make_font,
)


class SlotsScreen:
    def __init__(self, game: SlotsGame):
        self.game = game
        self.bet_text = "1"
        self.bet_input_active = False
        self.bet_input_box = pygame.Rect(330, 460, 240, 50)
        self.spin_button = pygame.Rect(370, 530, 160, 50)
        self.symbol_font = make_font(None, 28)
        self.seven_font = make_font("Segoe UI", 48, bold=True)
        self.chips_font = make_font("Consolas", 24)
        self.powerup_font = make_font(None, 16)
        self.use_silver_reel = False
        self.use_fishing_rod = False
        self.powerup_buttons = {
            "Silver Reel": pygame.Rect(700, 215, 180, 36),
            "Fishing Rod": pygame.Rect(700, 265, 180, 36),
        }
        self.spin_started_at = None
        self.column_spin_durations = (700, 950, 1200)

    def draw_symbol(self, screen, symbol, center, background):
        x, y = center
        red = (195, 45, 50)
        gold = (220, 165, 45)
        green = (45, 135, 70)

        if symbol == "CHERRY":
            draw_line(screen, green, (x - 4, y - 7), (x - 12, y - 22), 3)
            draw_line(screen, green, (x - 4, y - 7), (x + 11, y - 20), 3)
            draw_polygon(
                screen,
                green,
                ((x - 10, y - 20), (x - 22, y - 24), (x - 17, y - 12)),
            )
            draw_polygon(
                screen,
                green,
                ((x + 9, y - 19), (x + 22, y - 23), (x + 16, y - 11)),
            )
            draw_circle(screen, red, (x - 9, y + 5), 12)
            draw_circle(screen, red, (x + 10, y + 5), 12)
            draw_circle(screen, (245, 125, 110), (x - 12, y + 1), 3)
            draw_circle(screen, (245, 125, 110), (x + 7, y + 1), 3)
        elif symbol == "LEMON":
            draw_ellipse(screen, (242, 202, 45), pygame.Rect(x - 21, y - 13, 42, 26))
            draw_polygon(
                screen,
                (242, 202, 45),
                ((x - 21, y), (x - 28, y - 4), (x - 28, y + 4)),
            )
            draw_polygon(
                screen,
                (242, 202, 45),
                ((x + 21, y), (x + 28, y - 4), (x + 28, y + 4)),
            )
            draw_ellipse(screen, green, pygame.Rect(x - 2, y - 18, 15, 8))
        elif symbol == "ORANGE":
            draw_circle(screen, (235, 130, 35), (x, y + 2), 20)
            draw_circle(screen, (255, 185, 75), (x - 6, y - 5), 4)
            draw_ellipse(screen, green, pygame.Rect(x + 1, y - 23, 17, 9))
            draw_line(screen, (125, 90, 35), (x, y - 12), (x + 1, y - 19), 3)
        elif symbol == "PLUM":
            draw_ellipse(screen, (120, 65, 155), pygame.Rect(x - 17, y - 21, 34, 42))
            draw_ellipse(screen, (175, 120, 195), pygame.Rect(x - 10, y - 14, 7, 15))
            draw_line(screen, (90, 115, 45), (x, y - 19), (x + 2, y - 25), 3)
        elif symbol == "BELL":
            draw_circle(screen, gold, (x, y - 19), 5)
            draw_polygon(
                screen,
                gold,
                (
                    (x - 5, y - 14),
                    (x + 5, y - 14),
                    (x + 7, y + 7),
                    (x + 15, y + 13),
                    (x + 15, y + 17),
                    (x - 15, y + 17),
                    (x - 15, y + 13),
                    (x - 7, y + 7),
                ),
            )
            draw_line(screen, (255, 225, 130), (x - 3, y - 8), (x - 5, y + 7), 2)
            draw_ellipse(screen, (145, 95, 25), pygame.Rect(x - 4, y + 15, 8, 6))
        elif symbol == "BAR":
            plaque = pygame.Rect(x - 28, y - 17, 56, 34)
            draw_rect(screen, (55, 55, 60), plaque, border_radius=5)
            draw_rect(screen, gold, plaque, 3, border_radius=5)
            label = self.symbol_font.render("BAR", True, (255, 240, 190))
            blit_center(screen, label, center)
        elif symbol == "HORSESHOE":
            outer = pygame.Rect(x - 21, y - 21, 42, 42)
            inner = pygame.Rect(x - 11, y - 12, 22, 28)
            draw_ellipse(screen, (115, 125, 145), outer)
            draw_ellipse(screen, (235, 235, 230), inner)
            draw_rect(
                screen,
                background,
                pygame.Rect(x - 12, y + 4, 24, 20),
            )
            draw_rect(screen, (115, 125, 145), pygame.Rect(x - 21, y + 4, 10, 12))
            draw_rect(screen, (115, 125, 145), pygame.Rect(x + 11, y + 4, 10, 12))
            draw_circle(screen, (235, 235, 230), (x - 16, y + 9), 2)
            draw_circle(screen, (235, 235, 230), (x + 16, y + 9), 2)
        elif symbol == "DIAMOND":
            draw_polygon(
                screen,
                (45, 175, 200),
                (
                    (x - 23, y - 9),
                    (x - 13, y - 20),
                    (x + 13, y - 20),
                    (x + 23, y - 9),
                    (x, y + 22),
                ),
            )
            draw_polygon(
                screen,
                (155, 235, 240),
                ((x - 13, y - 17), (x - 4, y - 17), (x - 1, y + 12), (x - 17, y - 8)),
            )
            draw_polygon(
                screen,
                (90, 205, 220),
                ((x + 4, y - 17), (x + 13, y - 17), (x + 17, y - 8), (x + 1, y + 12)),
            )
        elif symbol == "7":
            label = self.seven_font.render("7", True, red)
            blit_center(screen, label, center)

    def winning_positions(self):
        positions = set()
        for line_type, symbol, _ in self.game.wins:
            if line_type == "blackout":
                return {
                    (row, column)
                    for row in range(3)
                    for column in range(3)
                }
            if line_type == "fishing_rod":
                return {(0, 0), (1, 1), (2, 2)}
            for payline_type, line_positions in PAYLINES:
                if payline_type == line_type and all(
                    self.game.reels[row][column] == symbol
                    for row, column in line_positions
                ):
                    positions.update(line_positions)
        return positions

    def spin(self):
        if self.is_spinning:
            return

        try:
            bet = int(self.bet_text)
        except ValueError:
            self.game.message = "Enter a whole-number bet."
            return

        try:
            self.game.start_spin(
                bet,
                use_silver_reel=self.use_silver_reel,
                use_fishing_rod=self.use_fishing_rod,
            )
        except ValueError as error:
            self.game.message = str(error)
            return
        except RuntimeError as error:
            self.game.message = str(error)
            return

        if self.use_silver_reel:
            self.use_silver_reel = False
        if self.use_fishing_rod:
            self.use_fishing_rod = False
        self.spin_started_at = pygame.time.get_ticks()

    @property
    def is_spinning(self):
        if self.spin_started_at is None:
            return False

        duration = self.column_spin_durations[-1]
        return pygame.time.get_ticks() - self.spin_started_at < duration

    def update(self):
        if self.spin_started_at is None:
            return False
        if (
            pygame.time.get_ticks() - self.spin_started_at
            < self.column_spin_durations[-1]
        ):
            return False

        self.spin_started_at = None
        return self.game.finish_spin()

    def finish_spin(self):
        if self.spin_started_at is None:
            return False
        self.spin_started_at = None
        return self.game.finish_spin()

    def handle_event(self, event):
        if self.is_spinning:
            return

        if event.type == pygame.KEYDOWN and self.bet_input_active:
            if event.key == pygame.K_BACKSPACE:
                self.bet_text = self.bet_text[:-1]
            elif event.key == pygame.K_RETURN:
                self.spin()
            elif event.unicode.isdigit() and len(self.bet_text) < 7:
                self.bet_text += event.unicode
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        for name, rect in self.powerup_buttons.items():
            if not rect.collidepoint(event.pos):
                continue
            if self.game.player["temp_powerups"].count(name) == 0:
                return
            if name == "Silver Reel":
                self.use_silver_reel = not self.use_silver_reel
            else:
                self.use_fishing_rod = not self.use_fishing_rod
            return

        clicked_input = self.bet_input_box.collidepoint(event.pos)
        if clicked_input and not self.bet_input_active:
            self.bet_text = ""
        self.bet_input_active = clicked_input

        if self.spin_button.collidepoint(event.pos):
            self.spin()

    def draw(
        self,
        screen,
        back_button,
        draw_button,
        draw_centered_text,
        title_font,
        text_font,
    ):
        draw_button("Back", back_button)
        draw_centered_text("Slots", title_font, 90)
        draw_centered_text(f"Chips: {self.game.chips}", self.chips_font, 140)

        elapsed = (
            pygame.time.get_ticks() - self.spin_started_at
            if self.is_spinning
            else None
        )
        winning_positions = (
            self.winning_positions() if not self.is_spinning else set()
        )
        for row_index, row in enumerate(self.game.reels):
            for column_index, final_symbol in enumerate(row):
                symbol = final_symbol
                if (
                    elapsed is not None
                    and elapsed < self.column_spin_durations[column_index]
                ):
                    symbol = random.choice(SYMBOLS)
                cell = pygame.Rect(
                    190 + column_index * 170,
                    190 + row_index * 70,
                    155,
                    60,
                )
                is_winning_cell = (
                    row_index,
                    column_index,
                ) in winning_positions
                cell_color = (
                    (255, 226, 110)
                    if is_winning_cell
                    else (245, 235, 205)
                )
                draw_rect(
                    screen,
                    cell_color,
                    cell,
                    border_radius=8,
                )
                if is_winning_cell:
                    draw_rect(
                        screen,
                        (215, 155, 35),
                        cell,
                        3,
                        border_radius=8,
                    )

                self.draw_symbol(screen, symbol, cell.center, cell_color)

        for name, rect in self.powerup_buttons.items():
            count = self.game.player["temp_powerups"].count(name)
            if not count:
                continue
            selected = (
                self.use_silver_reel
                if name == "Silver Reel"
                else self.use_fishing_rod
            )
            draw_rect(
                screen,
                (45, 115, 80) if selected else (35, 65, 58),
                rect,
                border_radius=7,
            )
            draw_rect(screen, (205, 160, 65), rect, 1, border_radius=7)
            label = self.powerup_font.render(
                f"{name} x{count}: {'ON' if selected else 'OFF'}",
                True,
                (255, 255, 255),
            )
            blit_center(screen, label, rect.center)

        message = "Spinning..." if self.is_spinning else self.game.message
        draw_centered_text(message, text_font, 420)
        box_color = (255, 230, 150) if self.bet_input_active else (245, 235, 205)
        draw_rect(screen, box_color, self.bet_input_box, border_radius=8)

        text_color = (30, 25, 18)

        if self.bet_text:
            bet_label = self.symbol_font.render(self.bet_text, True, text_color)
            blit_center(screen, bet_label, self.bet_input_box.center)
            cursor_x = (
                self.bet_input_box.centerx
                + self.symbol_font.size(self.bet_text)[0] // 2
                + 3
            )
        else:
            cursor_x = self.bet_input_box.centerx

            if not self.bet_input_active:
                placeholder = self.symbol_font.render(
                    "Enter bet",
                    True,
                    text_color,
                )
                blit_center(screen, placeholder, self.bet_input_box.center)

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            draw_line(
                screen,
                text_color,
                (cursor_x, self.bet_input_box.y + 10),
                (cursor_x, self.bet_input_box.bottom - 10),
                2,
            )
        draw_button("Spin", self.spin_button)