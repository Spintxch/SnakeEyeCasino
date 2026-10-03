import pygame
from roulette import (
    BLACK_NUMBERS,
    RED_NUMBERS,
    RouletteGame,
)


class RouletteScreen:
    def __init__(self, game: RouletteGame):
        self.game = game
        self.selected_numbers = []
        self.bet_text = "1"
        self.bet_input_active = False
        self.selected_bet_type = None
        self.location = None

        self.number_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)
        self.button_font = pygame.font.Font(None, 23)

        self.number_buttons = {}
        for row in range(12):
            for column in range(3):
                number = str(row * 3 + column + 1)
                self.number_buttons[number] = pygame.Rect(
                    120 + column * 88,
                    145 + row * 25,
                    82,
                    23,
                )

        self.number_buttons["0"] = pygame.Rect(164, 455, 82, 28)
        self.number_buttons["00"] = pygame.Rect(252, 455, 82, 28)

        inside_options = [
            ("Straight", "Straight Up", None),
            ("Split", "Split", None),
            ("Street", "Street", None),
            ("Corner", "Corner", None),
            ("Line", "Line", None),
        ]
        outside_options = [
            ("Red", "Red", None),
            ("Black", "Black", None),
            ("Odd", "Odd", None),
            ("Even", "Even", None),
            ("Low 1-18", "Low", None),
            ("High 19-36", "High", None),
            ("Dozen 1", "Dozen", tuple(range(1, 13))),
            ("Dozen 2", "Dozen", tuple(range(13, 25))),
            ("Dozen 3", "Dozen", tuple(range(25, 37))),
            ("Column 1", "Column", tuple(range(1, 37, 3))),
            ("Column 2", "Column", tuple(range(2, 37, 3))),
            ("Column 3", "Column", tuple(range(3, 37, 3))),
        ]

        self.inside_buttons = []
        for index, (label, bet_type, location) in enumerate(inside_options):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(475 + column * 195, 150 + row * 34, 185, 28)
            self.inside_buttons.append((rect, label, bet_type, location))

        self.outside_buttons = []
        for index, (label, bet_type, location) in enumerate(outside_options):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(475 + column * 195, 300 + row * 30, 185, 26)
            self.outside_buttons.append((rect, label, bet_type, location))

        self.bet_input_box = pygame.Rect(545, 490, 220, 42)
        self.spin_button = pygame.Rect(575, 540, 160, 40)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.bet_input_active:
            if event.key == pygame.K_BACKSPACE:
                self.bet_text = self.bet_text[:-1]
            elif event.key == pygame.K_RETURN:
                self._spin()
            elif event.unicode.isdigit() and len(self.bet_text) < 7:
                self.bet_text += event.unicode
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        for rect, _, bet_type, location in (
            self.inside_buttons + self.outside_buttons
        ):
            if rect.collidepoint(event.pos):
                self.selected_bet_type = bet_type
                self.location = location
                self.selected_numbers.clear()
                self.game.message = (
                    "Select the number(s) for this inside bet."
                    if bet_type in (
                        "Straight Up", "Split", "Street", "Corner", "Line"
                    )
                    else "Bet selected. Enter an amount and spin."
                )
                self.bet_input_active = False
                return

        for number, rect in self.number_buttons.items():
            if not rect.collidepoint(event.pos):
                continue

            (
                self.selected_numbers,
                self.location,
                self.game.message,
            ) = self.game.select_number(
                self.selected_bet_type,
                self.selected_numbers,
                number,
            )

            self.bet_input_active = False
            return

        clicked_input = self.bet_input_box.collidepoint(event.pos)
        if clicked_input and not self.bet_input_active:
            self.bet_text = ""
        self.bet_input_active = clicked_input

        if self.spin_button.collidepoint(event.pos):
            self._spin()

    def _spin(self):
        try:
            bet = int(self.bet_text)
        except ValueError:
            self.game.message = "Enter a whole-number bet."
            return

        if self.selected_bet_type is None:
            self.game.message = "Choose a bet type first."
            return

        try:
            self.game.spin(bet, self.selected_bet_type, self.location)
        except ValueError as error:
            self.game.message = str(error)
        self.bet_input_active = False

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
        draw_centered_text("Roulette", title_font, 55)
        draw_centered_text(f"Chips: {self.game.chips}", text_font, 105)

        for label_text, y in (("Inside Bets", 132), ("Outside Bets", 282)):
            label = self.small_font.render(label_text, True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=(670, y)))

        for number, rect in self.number_buttons.items():
            if number in ("0", "00"):
                color = (20, 125, 70)
            elif number in RED_NUMBERS:
                color = (165, 35, 40)
            elif number in BLACK_NUMBERS:
                color = (35, 35, 35)
            else:
                color = (40, 95, 65)

            pygame.draw.rect(screen, color, rect, border_radius=3)
            text = self.number_font.render(number, True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=rect.center))

            selected_numbers = set(self.selected_numbers)
            if isinstance(self.location, str) and self.location.isdigit():
                selected_numbers.add(int(self.location))
            elif isinstance(self.location, (tuple, list)):
                selected_numbers.update(self.location)

            if number.isdigit() and int(number) in selected_numbers:
                pygame.draw.rect(screen, (255, 220, 80), rect, 2)

        for buttons in (self.inside_buttons, self.outside_buttons):
            for rect, label, bet_type, location in buttons:
                selected = (
                    self.selected_bet_type == bet_type
                    and self.location == location
                    and not self.selected_numbers
                )
                color = (255, 195, 75) if selected else (205, 160, 65)
                pygame.draw.rect(screen, color, rect, border_radius=6)
                text = self.button_font.render(label, True, (30, 25, 18))
                screen.blit(text, text.get_rect(center=rect.center))

        input_color = (
            (255, 230, 150)
            if self.bet_input_active
            else (245, 235, 205)
        )
        pygame.draw.rect(
            screen,
            input_color,
            self.bet_input_box,
            border_radius=7,
        )
        bet_label = self.number_font.render(
            self.bet_text or (" " if self.bet_input_active else "Bet amount"),
            True,
            (30, 25, 18),
        )
        bet_rect = bet_label.get_rect(center=self.bet_input_box.center)
        screen.blit(bet_label, bet_rect)

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            cursor_x = bet_rect.right + 3 if self.bet_text else self.bet_input_box.centerx
            pygame.draw.line(
                screen,
                (30, 25, 18),
                (cursor_x, self.bet_input_box.y + 8),
                (cursor_x, self.bet_input_box.bottom - 8),
                2,
            )

        draw_button("Spin", self.spin_button)
        draw_centered_text(self.game.message, self.small_font, 585)