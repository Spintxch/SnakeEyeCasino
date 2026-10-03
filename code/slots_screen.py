import pygame
from slots import SlotsGame


class SlotsScreen:
    def __init__(self, game):
        self.game = game
        self.bet_text = "1"
        self.bet_input_active = False
        self.bet_input_box = pygame.Rect(330, 460, 240, 50)
        self.spin_button = pygame.Rect(370, 530, 160, 50)
        self.symbol_font = pygame.font.Font(None, 28)

    def spin(self):
        try:
            bet = int(self.bet_text)
        except ValueError:
            self.game.message = "Enter a whole-number bet."
            return

        try:
            self.game.spin(bet)
        except ValueError as error:
            self.game.message = str(error)

    def handle_event(self, event):
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
        draw_centered_text(f"Chips: {self.game.chips}", text_font, 140)

        for row_index, row in enumerate(self.game.reels):
            for column_index, symbol in enumerate(row):
                cell = pygame.Rect(
                    190 + column_index * 170,
                    190 + row_index * 70,
                    155,
                    60,
                )
                pygame.draw.rect(
                    screen,
                    (245, 235, 205),
                    cell,
                    border_radius=8,
                )

                label = self.symbol_font.render(
                    symbol,
                    True,
                    (30, 25, 18),
                )
                screen.blit(label, label.get_rect(center=cell.center))

        draw_centered_text(self.game.message, text_font, 420)
        box_color = (255, 230, 150) if self.bet_input_active else (245, 235, 205)
        pygame.draw.rect(screen, box_color, self.bet_input_box, border_radius=8)

        text_color = (30, 25, 18)

        if self.bet_text:
            bet_label = self.symbol_font.render(self.bet_text, True, text_color)
            bet_rect = bet_label.get_rect(center=self.bet_input_box.center)
            screen.blit(bet_label, bet_rect)
            cursor_x = bet_rect.right + 3
        else:
            cursor_x = self.bet_input_box.centerx

            if not self.bet_input_active:
                placeholder = self.symbol_font.render(
                    "Enter bet",
                    True,
                    text_color,
                )
                screen.blit(
                    placeholder,
                    placeholder.get_rect(center=self.bet_input_box.center),
                )

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            pygame.draw.line(
                screen,
                text_color,
                (cursor_x, self.bet_input_box.y + 10),
                (cursor_x, self.bet_input_box.bottom - 10),
                2,
            )
        draw_button("Spin", self.spin_button)