import pygame

from poker import PokerGame


class PokerScreen:
    def __init__(self, game: PokerGame):
        self.game = game

        self.deal_button = pygame.Rect(375, 525, 150, 50)
        self.fold_button = pygame.Rect(165, 525, 160, 50)
        self.call_button = pygame.Rect(370, 525, 160, 50)
        self.raise_button = pygame.Rect(575, 525, 160, 50)

        self.card_font = pygame.font.SysFont("Segoe UI Symbol", 28)
        self.card_rank_font = pygame.font.Font(None, 19)
        self.card_suit_font = pygame.font.SysFont("Segoe UI Symbol", 28)
        self.small_card_suit_font = pygame.font.SysFont("Segoe UI Symbol", 18)
        self.text_font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 32)

        self.seat_positions = [
            (360, 390),  # You
            (70, 340),
            (70, 150),
            (360, 110),
            (650, 150),
            (650, 340),
        ]

    def is_player_turn(self):
        return self.game.is_player_turn

    @property
    def seats(self):
        return self.game.seats

    @property
    def round(self):
        return self.game.round

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.deal_button.collidepoint(event.pos):
            if self.round is None or self.round.finished:
                try:
                    self.game.start_hand()
                except RuntimeError as error:
                    if self.round is not None:
                        self.round.message = str(error)
            return

        if not self.is_player_turn():
            return

        if self.fold_button.collidepoint(event.pos):
            self.game.act("fold")
        elif self.call_button.collidepoint(event.pos):
            action = "check" if self.round.amount_to_call == 0 else "call"
            self.game.act(action)
        elif self.raise_button.collidepoint(event.pos):
            if self.round.can_raise:
                self.game.act("raise")

    def leave(self):
        self.game.leave()

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

        table = pygame.Rect(220, 185, 460, 190)
        pygame.draw.ellipse(screen, (10, 100, 65), table)
        pygame.draw.ellipse(screen, (205, 160, 65), table, width=4)

        if self.round is None:
            message = "Click Deal to start a hand."
            board = []
            pot = 0
        else:
            message = self.round.message
            board = self.round.board
            pot = self.round.pot

        draw_centered_text(message, text_font, 105)
        draw_centered_text(f"Pot: {pot}", text_font, 245)

        if board:
            card_width = 48
            card_height = 64
            gap = 8
            start_x = 450 - (len(board) * card_width + (len(board) - 1) * gap) // 2
            for card_index, card in enumerate(board):
                card_rect = pygame.Rect(
                    start_x + card_index * (card_width + gap),
                    270,
                    card_width,
                    card_height,
                )
                self.draw_card_face(screen, card_rect, card)
        else:
            draw_centered_text_for_poker(
                screen,
                "Community cards",
                self.card_font,
                450,
                285,
            )

        reveal_bots = self.round is not None and len(board) == 5

        for index, (x, y) in enumerate(self.seat_positions):
            seat = self.seats[index]
            is_player = not seat["is_bot"]
            panel = pygame.Rect(x, y, 180, 90)
            panel_color = (30, 45, 38) if is_player else (25, 35, 32)

            pygame.draw.rect(screen, panel_color, panel, border_radius=10)
            pygame.draw.rect(
                screen,
                (205, 160, 65),
                panel,
                2,
                border_radius=10,
            )

            name = "You" if is_player else f"Bot {index}"
            draw_centered_text_for_poker(
                screen,
                f"{name}: {seat['stack']} chips",
                self.text_font,
                x + 90,
                y + 25,
            )

            cards = seat["hole_cards"]
            if cards:
                show_cards = is_player or reveal_bots or seat["folded"]
                if show_cards:
                    card_width = 42
                    card_height = 36
                    gap = 5
                    start_x = x + 90 - (2 * card_width + gap) // 2
                    for card_index, card in enumerate(cards):
                        card_rect = pygame.Rect(
                            start_x + card_index * (card_width + gap),
                            y + 46,
                            card_width,
                            card_height,
                        )
                        self.draw_card_face(screen, card_rect, card, small=True)
                else:
                    for card_index in range(2):
                        card_rect = pygame.Rect(
                            x + 44 + card_index * 48,
                            y + 46,
                            42,
                            36,
                        )
                        pygame.draw.rect(
                            screen,
                            (45, 65, 115),
                            card_rect,
                            border_radius=4,
                        )
                        pygame.draw.rect(
                            screen,
                            (230, 230, 240),
                            card_rect,
                            1,
                            border_radius=4,
                        )

            if seat["folded"]:
                draw_centered_text_for_poker(
                    screen,
                    "Folded",
                    self.text_font,
                    x + 90,
                    y + 82,
                )

        player_turn = self.is_player_turn()

        if self.round is None or self.round.finished:
            draw_button("Deal", self.deal_button)
        else:
            call_label = (
                "Check"
                if self.round.amount_to_call == 0
                else f"Call {self.round.amount_to_call}"
            )
            self.draw_action_button(
                screen, "Fold", self.fold_button, player_turn
            )
            self.draw_action_button(
                screen, call_label, self.call_button, player_turn
            )
            self.draw_action_button(
                screen,
                "Raise",
                self.raise_button,
                player_turn and self.round.can_raise,
            )

    def draw_action_button(self, screen, text, rect, enabled):
        mouse_position = pygame.mouse.get_pos()

        if not enabled:
            color = (115, 115, 115)
            text_color = (190, 190, 190)
        elif rect.collidepoint(mouse_position):
            color = (235, 195, 95)
            text_color = (30, 25, 18)
        else:
            color = (205, 160, 65)
            text_color = (30, 25, 18)

        pygame.draw.rect(screen, color, rect, border_radius=8)
        label = self.button_font.render(text, True, text_color)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_card_face(self, screen, rect, card, small=False):
        rank, suit = card
        color = (170, 35, 45) if suit in ("♥", "♦") else (30, 35, 40)
        pygame.draw.rect(screen, (248, 245, 232), rect, border_radius=5)
        pygame.draw.rect(screen, (45, 45, 45), rect, 1, border_radius=5)

        rank_label = self.card_rank_font.render(rank, True, color)
        screen.blit(rank_label, (rect.x + 3, rect.y + 2))
        suit_font = (
            self.small_card_suit_font if small else self.card_suit_font
        )
        suit_label = suit_font.render(suit, True, color)
        center_y = rect.y + (rect.height * 2 // 3 if small else rect.centery + 5)
        screen.blit(suit_label, suit_label.get_rect(center=(rect.centerx, center_y)))


def draw_centered_text_for_poker(screen, text, font, center_x, center_y):
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=(center_x, center_y)))