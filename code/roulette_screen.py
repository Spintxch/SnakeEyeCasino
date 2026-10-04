import math

import pygame
from roulette import (
    BLACK_NUMBERS,
    RED_NUMBERS,
    RouletteGame,
)
from ui_scaling import (
    blit_center,
    circle_point,
    draw_circle,
    draw_line,
    draw_polygon,
    draw_rect,
    make_font,
)


WHEEL_ORDER = (
    "0", "28", "9", "26", "30", "11", "7", "20", "32", "17",
    "5", "22", "34", "15", "3", "24", "36", "13", "1", "00",
    "27", "10", "25", "29", "12", "8", "19", "31", "18", "6",
    "21", "33", "16", "4", "23", "35", "14", "2",
)


class RouletteScreen:
    def __init__(self, game: RouletteGame):
        self.game = game
        self.selected_numbers = []
        self.bet_text = "1"
        self.bet_input_active = False
        self.selected_bet_type = None
        self.location = None
        self.spin_started_at = None
        self.spin_duration = 4500
        self.wheel_center = (400, 300)
        self.wheel_radius = 125
        self.wheel_rotation = 0.0
        self.spin_start_rotation = 0.0
        self.spin_end_rotation = 0.0
        self.spin_result = None
        self.use_lucky_marble = False

        self.number_font = make_font(None, 26)
        self.small_font = make_font(None, 22)
        self.powerup_font = make_font(None, 14)
        self.button_font = make_font(None, 23)
        self.wheel_font = make_font(None, 11)
        self.wheel_result_font = make_font(None, 24)
        self.chips_font = make_font("Consolas", 24)

        self.number_buttons = {}
        for row in range(12):
            for column in range(3):
                number = str(row * 3 + column + 1)
                self.number_buttons[number] = pygame.Rect(
                    24 + column * 76,
                    145 + row * 24,
                    70,
                    22,
                )

        self.number_buttons["0"] = pygame.Rect(62, 440, 70, 26)
        self.number_buttons["00"] = pygame.Rect(138, 440, 70, 26)

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
            rect = pygame.Rect(560 + column * 158, 155 + row * 34, 150, 28)
            self.inside_buttons.append((rect, label, bet_type, location))

        self.outside_buttons = []
        for index, (label, bet_type, location) in enumerate(outside_options):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(560 + column * 158, 297 + row * 28, 150, 24)
            self.outside_buttons.append((rect, label, bet_type, location))

        self.lucky_marble_button = pygame.Rect(560, 462, 308, 19)
        self.bet_input_box = pygame.Rect(585, 484, 220, 40)
        self.spin_button = pygame.Rect(615, 530, 160, 40)

    @property
    def is_spinning(self):
        return self.spin_started_at is not None

    def update(self):
        if not self.is_spinning:
            return False
        if pygame.time.get_ticks() - self.spin_started_at < self.spin_duration:
            return False

        self.wheel_rotation = self.spin_end_rotation
        self.spin_started_at = None
        self.game.finish_spin()
        self.spin_result = self.game.last_spin
        return True

    def finish_spin(self):
        if not self.is_spinning:
            return False
        self.wheel_rotation = self.spin_end_rotation
        self.spin_started_at = None
        self.game.finish_spin()
        self.spin_result = self.game.last_spin
        return True

    def handle_event(self, event):
        if self.is_spinning:
            return
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

        if self.lucky_marble_button.collidepoint(event.pos):
            if self.game.player["temp_powerups"].count("Lucky Marble"):
                self.use_lucky_marble = not self.use_lucky_marble
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
        if self.is_spinning:
            return
        try:
            bet = int(self.bet_text)
        except ValueError:
            self.game.message = "Enter a whole-number bet."
            return

        if self.selected_bet_type is None:
            self.game.message = "Choose a bet type first."
            return

        try:
            lucky_marble_count = self.game.player["temp_powerups"].count(
                "Lucky Marble"
            )
            result = self.game.start_spin(
                bet,
                self.selected_bet_type,
                self.location,
                use_lucky_marble=self.use_lucky_marble,
            )
        except ValueError as error:
            self.game.message = str(error)
            return
        except RuntimeError as error:
            self.game.message = str(error)
            return

        self.spin_result = result
        if (
            lucky_marble_count
            > self.game.player["temp_powerups"].count("Lucky Marble")
        ):
            self.use_lucky_marble = False
        self.spin_started_at = pygame.time.get_ticks()
        self.spin_start_rotation = self.wheel_rotation
        result_index = WHEEL_ORDER.index(result)
        pocket_step = math.tau / len(WHEEL_ORDER)
        target_phase = -result_index * pocket_step
        minimum_rotation = self.spin_start_rotation + 6 * math.tau
        rotations = math.ceil(
            (minimum_rotation - target_phase) / math.tau
        )
        self.spin_end_rotation = target_phase + rotations * math.tau
        self.bet_input_active = False

    def _spin_progress(self):
        if not self.is_spinning:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.spin_started_at
        return min(1.0, max(0.0, elapsed / self.spin_duration))

    def _wheel_rotation_at(self, progress):
        eased = 1 - (1 - progress) ** 4
        return self.spin_start_rotation + (
            self.spin_end_rotation - self.spin_start_rotation
        ) * eased

    def draw_wheel(self, screen):
        radius = self.wheel_radius
        progress = self._spin_progress()
        rotation = (
            self._wheel_rotation_at(progress)
            if self.is_spinning
            else self.wheel_rotation
        )
        pocket_step = math.tau / len(WHEEL_ORDER)

        draw_circle(screen, (20, 22, 20), self.wheel_center, radius + 8)
        for index, number in enumerate(WHEEL_ORDER):
            angle = -math.pi / 2 + rotation + index * pocket_step
            half_step = pocket_step / 2
            inner_radius = radius * 0.54
            outer_radius = radius * 0.91
            points = []
            for sample in range(4):
                edge_angle = angle - half_step + pocket_step * sample / 3
                points.append(circle_point(
                    self.wheel_center,
                    (
                        math.cos(edge_angle) * outer_radius,
                        math.sin(edge_angle) * outer_radius,
                    ),
                ))
            for sample in range(3, -1, -1):
                edge_angle = angle - half_step + pocket_step * sample / 3
                points.append(circle_point(
                    self.wheel_center,
                    (
                        math.cos(edge_angle) * inner_radius,
                        math.sin(edge_angle) * inner_radius,
                    ),
                ))

            if number in ("0", "00"):
                color = (20, 125, 70)
            elif number in RED_NUMBERS:
                color = (165, 35, 40)
            else:
                color = (35, 35, 35)
            draw_polygon(screen, color, points)

            label_radius = radius * 0.76
            label = self.wheel_font.render(number, True, (255, 245, 220))
            label = pygame.transform.rotate(
                label,
                math.degrees(-angle - math.pi / 2),
            )
            blit_center(
                screen,
                label,
                circle_point(
                    self.wheel_center,
                    (
                        math.cos(angle) * label_radius,
                        math.sin(angle) * label_radius,
                    ),
                ),
            )

        draw_circle(screen, (205, 160, 65), self.wheel_center, radius * 0.53)
        draw_circle(screen, (10, 75, 52), self.wheel_center, radius * 0.47)
        result_label = "..." if self.is_spinning else (
            self.game.last_spin if self.game.last_spin is not None else "SPIN"
        )
        label = self.wheel_result_font.render(
            result_label,
            True,
            (255, 245, 220),
        )
        blit_center(screen, label, self.wheel_center)

        ball_progress = 1 - (1 - progress) ** 3
        ball_angle = -math.pi / 2 + math.tau * 6 * (1 - ball_progress)
        ball_radius = radius * 0.96
        ball_position = circle_point(
            self.wheel_center,
            (
                math.cos(ball_angle) * ball_radius,
                math.sin(ball_angle) * ball_radius,
            ),
        )
        draw_circle(screen, (5, 8, 7), (ball_position[0] + 2, ball_position[1] + 3), 9)
        draw_circle(screen, (250, 248, 235), ball_position, 7)
        draw_circle(screen, (210, 210, 195), ball_position, 7, 1)

    def draw(
        self,
        screen,
        back_button,
        draw_button,
        draw_centered_text,
        title_font,
    ):
        draw_button("Back", back_button)
        draw_centered_text("Roulette", title_font, 55)
        draw_centered_text(f"Chips: {self.game.chips}", self.chips_font, 105)

        self.draw_wheel(screen)

        for label_text, y in (("Inside Bets", 136), ("Outside Bets", 278)):
            label = self.small_font.render(label_text, True, (255, 255, 255))
            blit_center(screen, label, (720, y))

        for number, rect in self.number_buttons.items():
            if number in ("0", "00"):
                color = (20, 125, 70)
            elif number in RED_NUMBERS:
                color = (165, 35, 40)
            elif number in BLACK_NUMBERS:
                color = (35, 35, 35)
            else:
                color = (40, 95, 65)

            draw_rect(screen, color, rect, border_radius=3)
            text = self.number_font.render(number, True, (255, 255, 255))
            blit_center(screen, text, rect.center)

            selected_numbers = set(self.selected_numbers)
            if isinstance(self.location, str) and self.location.isdigit():
                selected_numbers.add(int(self.location))
            elif isinstance(self.location, (tuple, list)):
                selected_numbers.update(self.location)

            if number.isdigit() and int(number) in selected_numbers:
                draw_rect(screen, (255, 220, 80), rect, 2)

        for buttons in (self.inside_buttons, self.outside_buttons):
            for rect, label, bet_type, location in buttons:
                selected = (
                    self.selected_bet_type == bet_type
                    and self.location == location
                    and not self.selected_numbers
                )
                color = (255, 195, 75) if selected else (205, 160, 65)
                draw_rect(screen, color, rect, border_radius=6)
                text = self.button_font.render(label, True, (30, 25, 18))
                blit_center(screen, text, rect.center)

        lucky_marble_count = self.game.player["temp_powerups"].count(
            "Lucky Marble"
        )
        if lucky_marble_count:
            color = (
                (45, 115, 80)
                if self.use_lucky_marble
                else (35, 65, 58)
            )
            draw_rect(
                screen,
                color,
                self.lucky_marble_button,
                border_radius=5,
            )
            draw_rect(
                screen,
                (205, 160, 65),
                self.lucky_marble_button,
                1,
                border_radius=5,
            )
            label = self.powerup_font.render(
                f"Lucky Marble x{lucky_marble_count}: "
                f"{'ON' if self.use_lucky_marble else 'OFF'}",
                True,
                (255, 255, 255),
            )
            blit_center(screen, label, self.lucky_marble_button.center)

        input_color = (
            (255, 230, 150)
            if self.bet_input_active
            else (245, 235, 205)
        )
        draw_rect(
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
        blit_center(screen, bet_label, self.bet_input_box.center)

        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.bet_input_active and cursor_visible:
            cursor_x = (
                self.bet_input_box.centerx
                + self.number_font.size(self.bet_text)[0] // 2
                + 3
                if self.bet_text
                else self.bet_input_box.centerx
            )
            draw_line(
                screen,
                (30, 25, 18),
                (cursor_x, self.bet_input_box.y + 8),
                (cursor_x, self.bet_input_box.bottom - 8),
                2,
            )

        draw_button(
            "Spinning..." if self.is_spinning else "Spin",
            self.spin_button,
        )
        draw_centered_text(
            "The wheel is spinning..." if self.is_spinning else self.game.message,
            self.small_font,
            585,
        )