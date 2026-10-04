import pygame

from blackjack import BlackjackGame, calc_hand_value, card_rank
from ui_mouse import get_position
from ui_scaling import (
    blit_at,
    blit_center,
    draw_line,
    draw_rect,
    make_font,
)


class BlackjackScreen:
    def __init__(self, game: BlackjackGame):
        self.game = game
        self.bet_text = "10"
        self.bet_input_active = False

        self.bet_input_box = pygame.Rect(330, 425, 240, 48)
        self.deal_button = pygame.Rect(25, 535, 150, 50)
        self.hit_button = pygame.Rect(200, 535, 150, 50)
        self.stand_button = pygame.Rect(375, 535, 150, 50)
        self.double_button = pygame.Rect(550, 535, 150, 50)
        self.split_button = pygame.Rect(725, 535, 150, 50)

        self.card_font = make_font("Segoe UI Symbol", 30)
        self.card_rank_font = make_font(None, 20)
        self.card_suit_font = make_font("Segoe UI Symbol", 32)
        self.small_card_suit_font = make_font("Segoe UI Symbol", 20)
        self.button_font = make_font(None, 32)
        self.chips_font = make_font("Consolas", 24)
        self.powerup_font = make_font(None, 16)
        self.use_marked_deck = False
        self.marked_deck_button = pygame.Rect(680, 142, 200, 32)
        self.dealer_reveal_started_at = None
        self.dealer_reveal_order = []
        self.dealer_reveal_interval = 350
        self.dealer_reveal_skipped = False

    def handle_event(self, event):
        if self.is_revealing_dealer:
            return

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

        if self.marked_deck_button.collidepoint(event.pos):
            if (
                not self.game.round_active
                and self.game.player["temp_powerups"].count("Marked Deck")
            ):
                self.use_marked_deck = not self.use_marked_deck
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
        if self.is_revealing_dealer:
            return

        self.dealer_reveal_skipped = False
        try:
            bet = int(self.bet_text)
        except ValueError as error:
            self.game.message = "Enter a whole-number bet."
            return

        try:
            self.game.start_round(
                bet,
                use_marked_deck=self.use_marked_deck,
            )
        except RuntimeError as error:
            self.game.message = str(error)
            return
        except ValueError as error:
            self.game.message = str(error)
            return
        self.bet_input_active = False
        if self.use_marked_deck:
            self.use_marked_deck = False
        if not self.game.round_active:
            self._begin_dealer_reveal()

    def _run_action(self, action):
        was_active = self.game.round_active
        try:
            action()
        except (ValueError, RuntimeError) as error:
            self.game.message = str(error)
            return
        if was_active and not self.game.round_active:
            self._begin_dealer_reveal()

    def _begin_dealer_reveal(self):
        if not self.game.dealer_hand:
            return
        self.dealer_reveal_started_at = None
        self.dealer_reveal_order = []
        self.dealer_reveal_skipped = not any(
            calc_hand_value(hand.cards) <= 21
            for hand in self.game.hands
        )
        if self.dealer_reveal_skipped:
            return

        self.dealer_reveal_order = [
            1,
            *range(2, len(self.game.dealer_hand)),
        ]
        self.dealer_reveal_started_at = pygame.time.get_ticks()

    @property
    def is_revealing_dealer(self):
        if self.dealer_reveal_started_at is None:
            return False

        duration = (
            len(self.dealer_reveal_order) * self.dealer_reveal_interval
        )
        if pygame.time.get_ticks() - self.dealer_reveal_started_at >= duration:
            self.dealer_reveal_started_at = None
            self.dealer_reveal_order = []
            return False
        return True

    def _visible_dealer_card_indexes(self):
        card_count = len(self.game.dealer_hand)
        if self.dealer_reveal_started_at is None:
            if self.dealer_reveal_skipped:
                return {0} if card_count > 0 else set()
            if self.game.round_active:
                return {0} if card_count > 0 else set()
            return set(range(card_count))

        elapsed = pygame.time.get_ticks() - self.dealer_reveal_started_at
        revealed_count = min(
            len(self.dealer_reveal_order),
            elapsed // self.dealer_reveal_interval,
        )
        return {0, *self.dealer_reveal_order[:revealed_count]}

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
        draw_centered_text(f"Chips: {self.game.chips}", self.chips_font, 125)
        draw_centered_text("Dealer", text_font, 165)
        marked_deck_count = self.game.player["temp_powerups"].count(
            "Marked Deck"
        )
        if marked_deck_count:
            enabled = not self.game.round_active
            color = (
                (45, 115, 80)
                if self.use_marked_deck and enabled
                else (35, 65, 58)
                if enabled
                else (90, 90, 90)
            )
            draw_rect(
                screen,
                color,
                self.marked_deck_button,
                border_radius=7,
            )
            draw_rect(
                screen,
                (205, 160, 65),
                self.marked_deck_button,
                1,
                border_radius=7,
            )
            label_text = (
                f"Marked Deck x{marked_deck_count}: "
                f"{'ON' if self.use_marked_deck else 'OFF'}"
                if enabled
                else f"Marked Deck x{marked_deck_count}: NEXT DEAL"
            )
            label = self.powerup_font.render(
                label_text,
                True,
                (255, 255, 255),
            )
            blit_center(screen, label, self.marked_deck_button.center)

        self.draw_hand(
            screen,
            self.game.dealer_hand,
            center_x=450,
            y=185,
            visible_indices=self._visible_dealer_card_indexes(),
        )

        if self.game.marked_card is not None:
            preview_panel = pygame.Rect(728, 190, 147, 125)
            draw_rect(
                screen,
                (24, 62, 56),
                preview_panel,
                border_radius=8,
            )
            draw_rect(
                screen,
                (225, 182, 89),
                preview_panel,
                2,
                border_radius=8,
            )
            draw_centered_text_for_screen(
                screen,
                "Next card",
                self.card_rank_font,
                207,
                preview_panel.centerx,
            )
            preview_card = pygame.Rect(772, 220, 59, 86)
            draw_rect(
                screen,
                (245, 235, 205),
                preview_card,
                border_radius=6,
            )
            self.draw_card_face(screen, preview_card, self.game.marked_card)

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
        draw_rect(screen, input_color, self.bet_input_box, border_radius=8)
        bet_label = self.card_font.render(self.bet_text, True, (30, 25, 18))
        blit_center(screen, bet_label, self.bet_input_box.center)

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            draw_line(
                screen,
                (30, 25, 18),
                (
                    self.bet_input_box.centerx
                    + self.card_font.size(self.bet_text)[0] // 2
                    + 3,
                    self.bet_input_box.y + 12,
                ),
                (
                    self.bet_input_box.centerx
                    + self.card_font.size(self.bet_text)[0] // 2
                    + 3,
                    self.bet_input_box.bottom - 12,
                ),
                2,
            )

        message = (
            "Dealer reveals cards..."
            if self.is_revealing_dealer
            else self.game.message
        )
        draw_centered_text(message, text_font, 495)
        self.draw_action_button(
            screen,
            "Deal",
            self.deal_button,
            not self.game.round_active and not self.is_revealing_dealer,
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
                draw_rect(
                    screen, (245, 235, 205), card_rect, border_radius=6
                )
                self.draw_card_face(screen, card_rect, card)

    def draw_hand(
        self,
        screen,
        hand,
        center_x,
        y,
        visible_indices=None,
    ):
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
            is_visible = visible_indices is None or index in visible_indices
            if is_visible:
                draw_rect(
                    screen,
                    (245, 235, 205),
                    card_rect,
                    border_radius=8,
                )
                self.draw_card_face(screen, card_rect, card)
            else:
                draw_rect(
                    screen,
                    (45, 65, 115),
                    card_rect,
                    border_radius=8,
                )
                draw_rect(
                    screen,
                    (230, 230, 240),
                    card_rect.inflate(-10, -10),
                    2,
                    border_radius=5,
                )

    def draw_card_face(self, screen, rect, card):
        rank = card_rank(card)
        suit = card[1] if isinstance(card, tuple) else ""
        color = (170, 35, 45) if suit in ("♥", "♦") else (30, 35, 40)

        rank_label = self.card_rank_font.render(rank, True, color)
        blit_at(screen, rank_label, (rect.x + 4, rect.y + 3))
        if suit:
            suit_font = (
                self.small_card_suit_font
                if rect.width < 40
                else self.card_suit_font
            )
            suit_label = suit_font.render(suit, True, color)
            blit_center(screen, suit_label, rect.center)

    def draw_action_button(self, screen, text, rect, enabled):
        mouse_position = get_position()
        if not enabled:
            color, text_color = (115, 115, 115), (190, 190, 190)
        elif rect.collidepoint(mouse_position):
            color, text_color = (235, 195, 95), (30, 25, 18)
        else:
            color, text_color = (205, 160, 65), (30, 25, 18)

        draw_rect(screen, color, rect, border_radius=8)
        label = self.button_font.render(text, True, text_color)
        blit_center(screen, label, rect.center)


def draw_centered_text_for_screen(screen, text, font, y, center_x):
    label = font.render(text, True, (255, 255, 255))
    blit_center(screen, label, (center_x, y))
