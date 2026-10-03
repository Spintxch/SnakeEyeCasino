import pygame

from blackjack import BlackjackGame, calc_hand_value, card_rank


class BlackjackScreen:
    def __init__(self, game):
        self.game = game
        self.bet_text = "10"
        self.bet_input_active = False

        self.bet_input_box = pygame.Rect(330, 425, 240, 48)
        self.deal_button = pygame.Rect(25, 535, 150, 50)
        self.hit_button = pygame.Rect(200, 535, 150, 50)
        self.stand_button = pygame.Rect(375, 535, 150, 50)
        self.double_button = pygame.Rect(550, 535, 150, 50)
        self.split_button = pygame.Rect(725, 535, 150, 50)

        self.card_font = pygame.font.SysFont("Segoe UI Symbol", 30)
        self.card_rank_font = pygame.font.Font(None, 20)
        self.card_suit_font = pygame.font.SysFont("Segoe UI Symbol", 32)
        self.small_card_suit_font = pygame.font.SysFont("Segoe UI Symbol", 20)
        self.button_font = pygame.font.Font(None, 32)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.bet_input_active:
            if event.key == pygame.K_BACKSPACE:
                self.bet_text = self.bet_text[:-1]
            elif event.key == pygame.K_RETURN:
                self._start_round()
            elif event.unicode.isdigit() and len(self.bet_text) < 7:
                self.bet_text += event.unicode
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if not self.game.round_active:
            clicked_input = self.bet_input_box.collidepoint(event.pos)
            if clicked_input and not self.bet_input_active:
                self.bet_text = ""
            self.bet_input_active = clicked_input

        if self.deal_button.collidepoint(event.pos):
            self._start_round()
        elif self.game.can_hit and self.hit_button.collidepoint(event.pos):
            self._run_action(self.game.hit)
        elif self.game.round_active and self.stand_button.collidepoint(event.pos):
            self._run_action(self.game.stand)
        elif self.game.can_double and self.double_button.collidepoint(event.pos):
            self._run_action(self.game.double_down)
        elif self.game.can_split and self.split_button.collidepoint(event.pos):
            self._run_action(self.game.split)

    def _start_round(self):
        try:
            bet = int(self.bet_text)
        except ValueError as error:
            self.game.message = "Enter a whole-number bet."
            return

        try:
            self.game.start_round(bet)
        except RuntimeError as error:
            self.game.message = str(error)
            return
        except ValueError as error:
            self.game.message = str(error)
            return
        self.bet_input_active = False

    def _run_action(self, action):
        try:
            action()
        except (ValueError, RuntimeError) as error:
            self.game.message = str(error)

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
        draw_centered_text("Blackjack", title_font, 60)
        draw_centered_text(f"Chips: {self.game.chips}", text_font, 125)
        draw_centered_text("Dealer", text_font, 165)

        self.draw_hand(
            screen,
            self.game.dealer_hand,
            center_x=450,
            y=185,
            hide_first=self.game.round_active,
        )

        if self.game.hands:
            self.draw_player_hands(screen, text_font)
        else:
            draw_centered_text("You", text_font, 300)

        input_color = (
            (255, 230, 150)
            if self.bet_input_active and not self.game.round_active
            else (180, 180, 180)
            if self.game.round_active
            else (245, 235, 205)
        )
        pygame.draw.rect(screen, input_color, self.bet_input_box, border_radius=8)
        bet_label = self.card_font.render(self.bet_text, True, (30, 25, 18))
        bet_rect = bet_label.get_rect(center=self.bet_input_box.center)
        screen.blit(bet_label, bet_rect)

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            pygame.draw.line(
                screen,
                (30, 25, 18),
                (bet_rect.right + 3, self.bet_input_box.y + 12),
                (bet_rect.right + 3, self.bet_input_box.bottom - 12),
                2,
            )

        draw_centered_text(self.game.message, text_font, 495)
        self.draw_action_button(
            screen, "Deal", self.deal_button, not self.game.round_active
        )
        self.draw_action_button(screen, "Hit", self.hit_button, self.game.can_hit)
        self.draw_action_button(
            screen, "Stand", self.stand_button, self.game.round_active
        )
        self.draw_action_button(
            screen, "Double", self.double_button, self.game.can_double
        )
        self.draw_action_button(
            screen, "Split", self.split_button, self.game.can_split
        )

    def draw_player_hands(self, screen, text_font):
        group_width = 900 / len(self.game.hands)
        max_cards = max(len(hand.cards) for hand in self.game.hands)
        card_width = min(
            54,
            max(30, int((group_width - 25 - 5 * (max_cards - 1)) / max_cards)),
        )
        card_height = 70
        gap = 5

        for hand_index, hand in enumerate(self.game.hands):
            center_x = int((hand_index + 0.5) * group_width)
            draw_centered_text_for_screen(
                screen,
                f"Hand {hand_index + 1}: {calc_hand_value(hand.cards)}",
                text_font,
                300,
                center_x,
            )

            total_width = len(hand.cards) * card_width + (len(hand.cards) - 1) * gap
            start_x = center_x - total_width // 2
            for card_index, card in enumerate(hand.cards):
                card_rect = pygame.Rect(
                    start_x + card_index * (card_width + gap),
                    325,
                    card_width,
                    card_height,
                )
                pygame.draw.rect(
                    screen, (245, 235, 205), card_rect, border_radius=6
                )
                self.draw_card_face(screen, card_rect, card)

    def draw_hand(self, screen, hand, center_x, y, hide_first=False):
        card_width = 70
        card_height = 100
        gap = 16
        total_width = len(hand) * card_width + max(0, len(hand) - 1) * gap
        start_x = center_x - total_width // 2

        for index, card in enumerate(hand):
            card_rect = pygame.Rect(
                start_x + index * (card_width + gap),
                y,
                card_width,
                card_height,
            )
            pygame.draw.rect(screen, (245, 235, 205), card_rect, border_radius=8)
            if hide_first and index == 0:
                label = self.card_font.render("?", True, (30, 25, 18))
                screen.blit(label, label.get_rect(center=card_rect.center))
            else:
                self.draw_card_face(screen, card_rect, card)

    def draw_card_face(self, screen, rect, card):
        rank = card_rank(card)
        suit = card[1] if isinstance(card, tuple) else ""
        color = (170, 35, 45) if suit in ("♥", "♦") else (30, 35, 40)

        rank_label = self.card_rank_font.render(rank, True, color)
        screen.blit(rank_label, (rect.x + 4, rect.y + 3))
        if suit:
            suit_font = (
                self.small_card_suit_font
                if rect.width < 40
                else self.card_suit_font
            )
            suit_label = suit_font.render(suit, True, color)
            screen.blit(suit_label, suit_label.get_rect(center=rect.center))

    def draw_action_button(self, screen, text, rect, enabled):
        mouse_position = pygame.mouse.get_pos()
        if not enabled:
            color, text_color = (115, 115, 115), (190, 190, 190)
        elif rect.collidepoint(mouse_position):
            color, text_color = (235, 195, 95), (30, 25, 18)
        else:
            color, text_color = (205, 160, 65), (30, 25, 18)

        pygame.draw.rect(screen, color, rect, border_radius=8)
        label = self.button_font.render(text, True, text_color)
        screen.blit(label, label.get_rect(center=rect.center))


def draw_centered_text_for_screen(screen, text, font, y, center_x):
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=(center_x, y)))
