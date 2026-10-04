import pygame

from poker import PokerGame
from ui_mouse import get_position
from ui_scaling import (
    blit_at,
    blit_center,
    draw_ellipse,
    draw_line,
    draw_rect,
    make_font,
)


class PokerScreen:
    def __init__(self, game: PokerGame):
        self.game = game

        self.deal_button = pygame.Rect(375, 525, 150, 50)
        self.fold_button = pygame.Rect(165, 525, 160, 50)
        self.call_button = pygame.Rect(370, 525, 160, 50)
        self.raise_button = pygame.Rect(575, 525, 160, 50)
        self.raise_amount_box = pygame.Rect(575, 480, 160, 36)
        self.raise_amount_text = ""
        self.raise_amount_active = False
        self.action_feedback = ""

        self.card_font = make_font("Segoe UI Symbol", 28)
        self.card_rank_font = make_font(None, 19)
        self.card_suit_font = make_font("Segoe UI Symbol", 28)
        self.small_card_suit_font = make_font("Segoe UI Symbol", 18)
        self.text_font = make_font(None, 24)
        self.action_message_font = make_font(None, 18)
        self.seat_name_font = make_font(None, 16)
        self.seat_stack_font = make_font("Consolas", 14)
        self.button_font = make_font(None, 32)
        self.powerup_font = make_font(None, 16)
        self.use_lucky_cards = False
        self.lucky_cards_button = pygame.Rect(30, 105, 220, 30)
        self.seat_positions = [
            (360, 410),  # You
            (70, 340),
            (70, 150),
            (360, 110),
            (650, 150),
            (650, 340),
        ]
        self.animation_interval = 170
        self.animation_started_at = None
        self.animation_events = []
        self.visible_hole_cards = [set() for _ in self.seat_positions]
        self.visible_board_count = 0
        self.scheduled_board_count = 0
        self.showdown_scheduled = False

    def is_player_turn(self):
        return self.game.is_player_turn

    @property
    def seats(self):
        return self.game.seats

    @property
    def round(self):
        return self.game.round

    def handle_event(self, event):
        if self.is_animating:
            return
        if event.type == pygame.KEYDOWN and self.raise_amount_active:
            if event.key == pygame.K_BACKSPACE:
                self.raise_amount_text = self.raise_amount_text[:-1]
                self.action_feedback = ""
            elif event.key == pygame.K_RETURN:
                self._raise()
            elif event.unicode.isdigit() and len(self.raise_amount_text) < 7:
                self.raise_amount_text += event.unicode
                self.action_feedback = ""
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.lucky_cards_button.collidepoint(event.pos):
            if (
                (self.round is None or self.round.finished)
                and self.game.player["temp_powerups"].count("Lucky Cards")
            ):
                self.use_lucky_cards = not self.use_lucky_cards
            return

        if self.raise_amount_box.collidepoint(event.pos):
            if self.is_player_turn() and self.round.can_raise:
                self.raise_amount_active = True
                self.raise_amount_text = ""
                self.action_feedback = ""
            return

        if (
            self.deal_button.collidepoint(event.pos)
            and (self.round is None or self.round.finished)
        ):
            try:
                self.game.start_hand(
                    use_lucky_cards=self.use_lucky_cards,
                )
                self._begin_hand_animation()
                if self.use_lucky_cards:
                    self.use_lucky_cards = False
            except RuntimeError as error:
                if self.round is not None:
                    self.round.message = str(error)
            return

        if not self.is_player_turn():
            return

        if self.fold_button.collidepoint(event.pos):
            self.raise_amount_active = False
            self._perform_action("fold")
        elif self.call_button.collidepoint(event.pos):
            self.raise_amount_active = False
            action = "check" if self.round.amount_to_call == 0 else "call"
            self._perform_action(action)
        elif self.raise_button.collidepoint(event.pos):
            self._raise()
        self._animate_new_board_cards()

    def _perform_action(self, action, raise_to=None):
        try:
            self.game.act(action, raise_to=raise_to)
        except (RuntimeError, ValueError) as error:
            self.action_feedback = str(error)
            return False

        self.action_feedback = ""
        return True

    def _raise(self):
        if not self.is_player_turn() or not self.round.can_raise:
            self.raise_amount_active = False
            return
        try:
            raise_to = int(self.raise_amount_text)
        except ValueError:
            self.action_feedback = "Enter a raise-to amount before raising."
            return

        if not self._perform_action("raise", raise_to=raise_to):
            return

        self.raise_amount_active = False
        self.raise_amount_text = ""

    def leave(self):
        self.game.leave()

    @property
    def is_animating(self):
        return self.animation_started_at is not None

    def _begin_hand_animation(self):
        self.visible_hole_cards = [set() for _ in self.seats]
        self.visible_board_count = 0
        self.scheduled_board_count = 0
        self.showdown_scheduled = False
        self.animation_events = []
        event_number = 0
        max_cards = max(
            (len(seat["hole_cards"]) for seat in self.seats),
            default=0,
        )
        for card_index in range(max_cards):
            for seat_index, seat in enumerate(self.seats):
                if card_index < len(seat["hole_cards"]):
                    self.animation_events.append((
                        event_number * self.animation_interval,
                        "hole",
                        seat_index,
                        card_index,
                    ))
                    event_number += 1
        self.animation_started_at = pygame.time.get_ticks()
        self._animate_new_board_cards()
        self.update()

    def _animate_new_board_cards(self):
        board = self.round.board if self.round is not None else []
        has_new_board_cards = len(board) > self.scheduled_board_count
        showdown_needs_reveal = (
            self.round is not None
            and self.round.finished
            and len(board) == 5
            and not self.showdown_scheduled
        )
        if not has_new_board_cards and not showdown_needs_reveal:
            return

        if self.animation_started_at is None:
            self.animation_started_at = pygame.time.get_ticks()
            self.animation_events = []
            due_at = 0
        else:
            due_at = (
                self.animation_events[-1][0] + self.animation_interval
                if self.animation_events
                else pygame.time.get_ticks() - self.animation_started_at
            )

        for board_index in range(self.scheduled_board_count, len(board)):
            self.animation_events.append((
                due_at,
                "board",
                board_index,
                0,
            ))
            due_at += self.animation_interval
        self.scheduled_board_count = len(board)

        if showdown_needs_reveal:
            for seat_index, seat in enumerate(self.seats):
                if seat["folded"]:
                    continue
                for card_index in range(len(seat["hole_cards"])):
                    if card_index not in self.visible_hole_cards[seat_index]:
                        self.animation_events.append((
                            due_at,
                            "showdown",
                            seat_index,
                            card_index,
                        ))
                        due_at += self.animation_interval
            self.showdown_scheduled = True

    def update(self):
        if not self.is_animating:
            self._animate_new_board_cards()
            return

        elapsed = pygame.time.get_ticks() - self.animation_started_at
        while self.animation_events and self.animation_events[0][0] <= elapsed:
            _, event_type, index, card_index = self.animation_events.pop(0)
            if event_type == "hole":
                self.visible_hole_cards[index].add(card_index)
            elif event_type == "board":
                self.visible_board_count = max(
                    self.visible_board_count,
                    index + 1,
                )
            else:
                self.visible_hole_cards[index].add(card_index)

        if not self.animation_events:
            self.animation_started_at = None

    def _action_status(self):
        if self.round is None:
            return "Click Deal to start a hand."
        if self.action_feedback:
            return self.action_feedback
        if self.is_animating:
            return (
                "Dealing cards..."
                if self.visible_board_count == 0
                else "Revealing cards..."
            )
        if self.round.finished:
            return self.round.message

        actor_index = self.round.actor_index
        if actor_index is None:
            return self.round.message
        if self.seats[actor_index]["is_bot"]:
            return f"{self.seats[actor_index]['name']} is acting."

        amount_to_call = self.round.amount_to_call
        if amount_to_call:
            action = f"Your turn: call {amount_to_call}"
        else:
            action = "Your turn: check"

        if self.round.can_raise:
            return f"{action} or raise."
        return f"{action}. Raising is unavailable."

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
        draw_centered_text("Texas Hold'em", title_font, 55)
        lucky_cards_count = self.game.player["temp_powerups"].count(
            "Lucky Cards"
        )
        if lucky_cards_count:
            enabled = self.round is None or self.round.finished
            color = (
                (45, 115, 80)
                if self.use_lucky_cards and enabled
                else (35, 65, 58)
                if enabled
                else (90, 90, 90)
            )
            draw_rect(
                screen,
                color,
                self.lucky_cards_button,
                border_radius=7,
            )
            draw_rect(
                screen,
                (205, 160, 65),
                self.lucky_cards_button,
                1,
                border_radius=7,
            )
            label_text = (
                f"Lucky Cards x{lucky_cards_count}: "
                f"{'ON' if self.use_lucky_cards else 'OFF'}"
                if enabled
                else f"Lucky Cards x{lucky_cards_count}: NEXT HAND"
            )
            label = self.powerup_font.render(
                label_text,
                True,
                (255, 255, 255),
            )
            blit_center(screen, label, self.lucky_cards_button.center)

        table = pygame.Rect(220, 205, 460, 150)
        draw_ellipse(screen, (10, 100, 65), table)
        draw_ellipse(screen, (205, 160, 65), table, width=4)

        if self.round is None:
            board = []
            pot = 0
        else:
            board = self.round.board
            pot = self.round.pot

        message = self._action_status()
        draw_centered_text(message, self.action_message_font, 372)
        if self.round is not None:
            draw_centered_text(
                f"Previous action: {self.round.last_action}",
                self.seat_name_font,
                396,
            )
        draw_centered_text(f"Pot: {pot}", text_font, 245)

        card_width = 46
        card_height = 66
        gap = 9
        board_slots = max(5, len(board))
        start_x = 450 - (board_slots * card_width + (board_slots - 1) * gap) // 2
        for card_index, card in enumerate(board):
            card_rect = pygame.Rect(
                start_x + card_index * (card_width + gap),
                270,
                card_width,
                card_height,
            )
            if card_index < self.visible_board_count:
                self.draw_card_face(screen, card_rect, card)
            else:
                self.draw_card_back(screen, card_rect)

        if not board:
            draw_centered_text_for_poker(
                screen,
                "Community cards",
                self.card_font,
                450,
                285,
            )

        self.draw_chip_stack(screen, (540, 245), pot)

        reveal_bots = (
            self.round is not None
            and self.round.finished
            and len(board) == 5
            and self.visible_board_count == 5
            and not self.is_animating
        )

        for index, (x, y) in enumerate(self.seat_positions):
            seat = self.seats[index]
            is_player = not seat["is_bot"]
            panel = pygame.Rect(x, y, 180, 100)
            panel_color = (30, 45, 38) if is_player else (25, 35, 32)

            draw_rect(screen, panel_color, panel, border_radius=10)
            draw_rect(
                screen,
                (205, 160, 65),
                panel,
                2,
                border_radius=10,
            )

            name_label = self.seat_name_font.render(
                seat["name"],
                True,
                (255, 255, 255),
            )
            blit_at(screen, name_label, (x + 8, y + 8))
            stack_label = self.seat_stack_font.render(
                f"{seat['stack']} chips",
                True,
                (220, 220, 210),
            )
            blit_at(screen, stack_label, (x + 8, y + 29))
            blind = (
                "SB"
                if index == getattr(self.round, "small_blind_index", None)
                else "BB"
                if index == getattr(self.round, "big_blind_index", None)
                else None
            )
            if blind is not None:
                badge = pygame.Rect(x + 145, y + 6, 27, 20)
                draw_rect(
                    screen,
                    (205, 160, 65) if blind == "SB" else (195, 55, 55),
                    badge,
                    border_radius=5,
                )
                badge_label = self.seat_stack_font.render(
                    blind,
                    True,
                    (255, 255, 255),
                )
                blit_center(screen, badge_label, badge.center)
            self.draw_chip_stack(
                screen,
                (x + 20, y + 91),
                seat["stack"],
                compact=True,
            )

            cards = seat["hole_cards"]
            if cards and not seat["folded"]:
                card_width = 30
                card_height = 46
                card_gap = 5
                start_x = x + 90 - (2 * card_width + card_gap) // 2
                for card_index, card in enumerate(cards):
                    card_rect = pygame.Rect(
                        start_x + card_index * (card_width + card_gap),
                        y + 48,
                        card_width,
                        card_height,
                    )
                    visible = card_index in self.visible_hole_cards[index]
                    show_cards = visible and (is_player or reveal_bots)
                    if show_cards:
                        self.draw_card_face(screen, card_rect, card, small=True)
                    else:
                        self.draw_card_back(screen, card_rect, small=True)

            if seat["folded"]:
                draw_centered_text_for_poker(
                    screen,
                    "Folded",
                    self.text_font,
                    x + 90,
                    y + 84,
                )

        player_turn = self.is_player_turn()

        if self.round is None or self.round.finished:
            draw_button(
                "Dealing..." if self.is_animating else "Deal",
                self.deal_button,
            )
        else:
            can_call = (
                player_turn
                and (
                    self.round.amount_to_call == 0
                    or self.seats[0]["stack"] > 0
                )
            )
            call_label = "Check" if self.round.amount_to_call == 0 else "Call"
            can_raise = player_turn and self.round.can_raise
            input_color = (
                (255, 230, 150)
                if self.raise_amount_active
                else (245, 235, 205)
                if can_raise
                else (115, 115, 115)
            )
            draw_rect(
                screen,
                input_color,
                self.raise_amount_box,
                border_radius=7,
            )
            shown_amount = self.raise_amount_text or "Enter amount to raise"
            amount_color = (30, 25, 18) if can_raise else (190, 190, 190)
            amount_label = self.action_message_font.render(
                shown_amount,
                True,
                amount_color,
            )
            blit_center(screen, amount_label, self.raise_amount_box.center)
            if self.raise_amount_active and (
                pygame.time.get_ticks() // 500
            ) % 2 == 0:
                cursor_x = (
                    self.raise_amount_box.centerx
                    + self.action_message_font.rendered_width(
                        self.raise_amount_text
                    ) // 2
                    + 3
                )
                draw_line(
                    screen,
                    (30, 25, 18),
                    (cursor_x, self.raise_amount_box.y + 7),
                    (cursor_x, self.raise_amount_box.bottom - 7),
                    2,
                )

            self.draw_action_button(
                screen, "Fold", self.fold_button, player_turn
            )
            self.draw_action_button(
                screen, call_label, self.call_button, can_call
            )
            self.draw_action_button(
                screen,
                "Raise",
                self.raise_button,
                can_raise,
            )

    def draw_action_button(self, screen, text, rect, enabled):
        mouse_position = get_position()

        if not enabled:
            color = (115, 115, 115)
            text_color = (190, 190, 190)
        elif rect.collidepoint(mouse_position):
            color = (235, 195, 95)
            text_color = (30, 25, 18)
        else:
            color = (205, 160, 65)
            text_color = (30, 25, 18)

        draw_rect(screen, color, rect, border_radius=8)
        label = self.button_font.render(text, True, text_color)
        blit_center(screen, label, rect.center)

    def draw_card_face(self, screen, rect, card, small=False):
        rank, suit = card
        color = (170, 35, 45) if suit in ("♥", "♦") else (30, 35, 40)
        draw_rect(screen, (248, 245, 232), rect, border_radius=5)
        draw_rect(screen, (45, 45, 45), rect, 1, border_radius=5)

        rank_label = self.card_rank_font.render(rank, True, color)
        blit_at(screen, rank_label, (rect.x + 3, rect.y + 2))
        suit_font = (
            self.small_card_suit_font if small else self.card_suit_font
        )
        suit_label = suit_font.render(suit, True, color)
        center_y = (
            rect.y + rect.height * 2 // 3
            if small
            else rect.centery + 5
        )
        blit_center(screen, suit_label, (rect.centerx, center_y))

    def draw_card_back(self, screen, rect, small=False):
        draw_rect(screen, (45, 65, 115), rect, border_radius=4)
        inset = 8 if small else 10
        draw_rect(
            screen,
            (230, 230, 240),
            rect.inflate(-inset, -inset),
            1,
            border_radius=3,
        )

    def draw_chip_stack(self, screen, center, amount, compact=False):
        if amount <= 0:
            return

        chip_count = min(5, max(1, amount.bit_length() // 4))
        chip_width = 24 if compact else 32
        chip_height = 8 if compact else 11
        chip_gap = 5 if compact else 7
        colors = (
            (205, 160, 65),
            (195, 55, 55),
            (55, 105, 185),
            (45, 145, 95),
            (230, 225, 205),
        )
        left = center[0] - chip_width // 2
        bottom = center[1]
        for chip_index in range(chip_count):
            chip = pygame.Rect(
                left + (chip_index % 3) * 4,
                bottom - chip_index * chip_gap,
                chip_width,
                chip_height,
            )
            color = colors[chip_index % len(colors)]
            draw_ellipse(screen, (20, 22, 20), chip.move(0, 2))
            draw_ellipse(screen, color, chip)
            draw_ellipse(screen, (255, 235, 170), chip, width=1)


def draw_centered_text_for_poker(screen, text, font, center_x, center_y):
    label = font.render(text, True, (255, 255, 255))
    blit_center(screen, label, (center_x, center_y))