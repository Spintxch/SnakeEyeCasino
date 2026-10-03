import pygame

from shop import (
    AVAILABLE_POWERUPS,
    ShopGame,
    total_loan_balance,
)


class ShopScreen:
    def __init__(self, game: ShopGame):
        self.game = game
        self.player = game.player
        self.amount_text = "100"
        self.amount_active = False
        self.message = "Click an item to see its details."

        self.amount_box = pygame.Rect(620, 260, 220, 46)
        self.loan_button = pygame.Rect(590, 325, 130, 45)
        self.repay_button = pygame.Rect(730, 325, 130, 45)

        self.item_viewport = pygame.Rect(35, 145, 510, 390)
        self.item_scroll = 0

        self.selected_item = None
        self.quantity_text = "1"
        self.quantity_active = False

        self.title_font = pygame.font.Font(None, 32)
        self.body_font = pygame.font.Font(None, 23)
        self.small_font = pygame.font.Font(None, 20)
        self.balance_font = pygame.font.SysFont("Consolas", 26)
        self.button_font = pygame.font.Font(None, 28)

    def get_item_layout(self):
        sections = []
        content_height = 0
        for powerup_type, title in (
            ("temp", "Temporary Power-ups"),
            ("perma", "Permanent Power-ups"),
        ):
            names = [
                name for name, details in AVAILABLE_POWERUPS.items()
                if details["type"] == powerup_type
            ]
            sections.append((title, names))
            content_height += 30
            for name in names:
                content_height += 38
                if name == self.selected_item:
                    content_height += 120

        max_scroll = max(0, content_height - self.item_viewport.height)
        self.item_scroll = min(self.item_scroll, max_scroll)
        y = self.item_viewport.y - self.item_scroll
        layout = []
        category_headers = []

        for title, names in sections:
            category_headers.append((y, title))
            y += 30
            for name in names:
                row = pygame.Rect(
                    self.item_viewport.x,
                    y,
                    self.item_viewport.width - 10,
                    34,
                )
                y += 38

                details_rect = None
                quantity_rect = None
                buy_rect = None

                if name == self.selected_item:
                    details_rect = pygame.Rect(
                        self.item_viewport.x + 4,
                        y,
                        self.item_viewport.width - 18,
                        112,
                    )
                    quantity_rect = pygame.Rect(
                        details_rect.x + 14,
                        details_rect.y + 66,
                        110,
                        36,
                    )
                    buy_rect = pygame.Rect(
                        details_rect.right - 124,
                        details_rect.y + 66,
                        110,
                        36,
                    )
                    y += 120

                layout.append((row, name, details_rect, quantity_rect, buy_rect))

        return layout, content_height, max_scroll, self.item_viewport, category_headers

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.selected_item and self.quantity_active:
                if event.key == pygame.K_BACKSPACE:
                    self.quantity_text = self.quantity_text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.buy_selected_item()
                elif event.unicode.isdigit() and len(self.quantity_text) < 5:
                    self.quantity_text += event.unicode
                return

            if self.amount_active:
                if event.key == pygame.K_BACKSPACE:
                    self.amount_text = self.amount_text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.take_loan()
                elif event.unicode.isdigit() and len(self.amount_text) < 7:
                    self.amount_text += event.unicode
                return

        if event.type == pygame.MOUSEWHEEL:
            if not self.item_viewport.collidepoint(pygame.mouse.get_pos()):
                return
            self.item_scroll -= event.y * 35
            self.get_item_layout()
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.selected_item:
            layout, _, _, _, _ = self.get_item_layout()
            selected_layout = next(
                (entry for entry in layout if entry[1] == self.selected_item),
                None,
            )
            if selected_layout:
                _, _, _, quantity_rect, buy_rect = selected_layout

                if quantity_rect.collidepoint(event.pos):
                    if not self.quantity_active:
                        self.quantity_text = ""
                    self.quantity_active = True
                    self.amount_active = False
                    return

                if buy_rect.collidepoint(event.pos):
                    self.quantity_active = False
                    self.buy_selected_item()
                    return

        if self.item_viewport.collidepoint(event.pos):
            layout, _, _, _, _ = self.get_item_layout()
            for row, name, _, _, _ in layout:
                if row.collidepoint(event.pos):
                    if self.selected_item == name:
                        self.selected_item = None
                        self.quantity_active = False
                    else:
                        self.selected_item = name
                        self.quantity_text = "1"
                        self.quantity_active = False
                    self.get_item_layout()
                    return

        if self.amount_box.collidepoint(event.pos):
            if not self.amount_active:
                self.amount_text = ""
            self.amount_active = True
            self.quantity_active = False
            return

        self.amount_active = False
        self.quantity_active = False

        if self.loan_button.collidepoint(event.pos):
            self.take_loan()
            return

        if self.repay_button.collidepoint(event.pos):
            self.repay()
            return

    def take_loan(self):
        try:
            amount = int(self.amount_text)
        except ValueError:
            self.message = "Enter a whole-number loan amount."
            return

        try:
            self.game.take_loan(amount)
        except ValueError as error:
            self.message = str(error)
            return

        self.message = f"Borrowed {amount} chips."
        self.amount_active = False

    def repay(self):
        try:
            amount = int(self.amount_text)
        except ValueError:
            self.message = "Enter a whole-number repayment."
            return

        try:
            self.game.repay(amount)
        except ValueError as error:
            self.message = str(error)
            return

        self.message = f"Repaid {amount} chips."
        self.amount_active = False

    def buy_selected_item(self):
        if self.selected_item is None:
            return

        try:
            quantity = int(self.quantity_text)
        except ValueError:
            self.message = "Enter a whole-number quantity."
            return

        try:
            self.game.buy_powerup(self.selected_item, quantity)
        except ValueError as error:
            self.message = str(error)
            return

        self.message = f"Bought {quantity} {self.selected_item}."
        self.selected_item = None
        self.quantity_active = False

    def draw(self, screen, back_button, draw_button):
        draw_button("Back", back_button)
        self.draw_text(screen, "Shop", self.title_font, (450, 65))

        balance = self.balance_font.render(
            f"Chips: {self.player['chips']}",
            True,
            (255, 255, 255),
        )
        screen.blit(balance, balance.get_rect(center=(450, 110)))

        self.draw_text(screen, "Power-ups", self.title_font, (285, 125))

        self.draw_powerups(screen)

        self.draw_text(screen, "Loans", self.title_font, (725, 155))
        self.draw_text(
            screen,
            f"Loan balance: {total_loan_balance(self.player)}",
            self.body_font,
            (725, 200),
        )
        self.draw_text(
            screen,
            f"Loans taken: {self.player['loans_taken']}",
            self.body_font,
            (725, 230),
        )

        input_color = (255, 230, 150) if self.amount_active else (245, 235, 205)
        pygame.draw.rect(screen, input_color, self.amount_box, border_radius=8)
        self.draw_input_text(
            screen,
            self.amount_box,
            self.amount_text,
            self.amount_active,
            self.body_font,
            "Amount",
        )

        draw_button("Borrow", self.loan_button)
        draw_button("Repay", self.repay_button)

        self.draw_text(
            screen,
            f"Temporary: {', '.join(self.player['temp_powerups']) or 'None'}",
            self.small_font,
            (700, 410),
        )
        self.draw_text(
            screen,
            f"Permanent: {', '.join(self.player['perma_powerups']) or 'None'}",
            self.small_font,
            (700, 445),
        )
        self.draw_text(screen, self.message, self.small_font, (450, 565))

    def draw_powerups(self, screen):
        layout, content_height, max_scroll, viewport, headers = (
            self.get_item_layout()
        )
        old_clip = screen.get_clip()
        screen.set_clip(viewport)
        mouse_position = pygame.mouse.get_pos()

        for y, title in headers:
            header_rect = pygame.Rect(viewport.x, y, viewport.width - 10, 26)
            pygame.draw.rect(
                screen,
                (30, 95, 70),
                header_rect,
                border_radius=5,
            )
            label = self.body_font.render(title, True, (255, 255, 255))
            screen.blit(label, label.get_rect(midleft=(header_rect.x + 9, y + 13)))

        for row, name, details_rect, quantity_rect, buy_rect in layout:
            if not viewport.colliderect(row):
                continue

            hovered = row.collidepoint(mouse_position)
            selected = name == self.selected_item
            row_color = (
                (255, 195, 75)
                if hovered or selected
                else (205, 160, 65)
            )
            pygame.draw.rect(screen, row_color, row, border_radius=6)

            details = AVAILABLE_POWERUPS[name]
            inventory_key = (
                "perma_powerups"
                if details["type"] == "perma"
                else "temp_powerups"
            )
            owned = self.player[inventory_key].count(name)
            label = self.small_font.render(
                f"{name} - {details['price']} | Owned: {owned}",
                True,
                (30, 25, 18),
            )
            screen.blit(label, label.get_rect(midleft=(row.x + 7, row.centery)))

            if details_rect is None:
                continue

            pygame.draw.rect(
                screen,
                (30, 75, 60),
                details_rect,
                border_radius=6,
            )
            self.draw_wrapped_text(
                screen,
                details["description"],
                self.small_font,
                pygame.Rect(
                    details_rect.x + 8,
                    details_rect.y + 5,
                    details_rect.width - 16,
                    54,
                ),
            )

            input_color = (
                (255, 230, 150)
                if self.quantity_active
                else (245, 235, 205)
            )
            pygame.draw.rect(
                screen,
                input_color,
                quantity_rect,
                border_radius=6,
            )
            self.draw_input_text(
                screen,
                quantity_rect,
                self.quantity_text,
                self.quantity_active,
                self.body_font,
                "Qty",
            )
            self.draw_local_button(screen, "Buy", buy_rect)

        screen.set_clip(old_clip)

        if max_scroll:
            track = pygame.Rect(
                viewport.right - 6,
                viewport.y,
                6,
                viewport.height,
            )
            thumb_height = max(
                35,
                int(viewport.height**2 / content_height),
            )
            thumb_y = viewport.y + int(
                (self.item_scroll / max_scroll)
                * (viewport.height - thumb_height)
            )
            pygame.draw.rect(screen, (80, 80, 80), track, border_radius=3)
            pygame.draw.rect(
                screen,
                (230, 195, 110),
                pygame.Rect(
                    track.x,
                    thumb_y,
                    track.width,
                    thumb_height,
                ),
                border_radius=3,
            )

    def draw_local_button(self, screen, text, rect):
        color = (
            (235, 195, 95)
            if rect.collidepoint(pygame.mouse.get_pos())
            else (205, 160, 65)
        )
        pygame.draw.rect(screen, color, rect, border_radius=8)
        label = self.button_font.render(text, True, (30, 25, 18))
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_input_text(self, screen, rect, value, active, font, placeholder):
        shown_text = value or ("" if active else placeholder)
        if shown_text:
            label = font.render(shown_text, True, (30, 25, 18))
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)
            cursor_x = label_rect.right + 3
        else:
            cursor_x = rect.centerx

        if active and (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(
                screen,
                (30, 25, 18),
                (cursor_x, rect.y + 9),
                (cursor_x, rect.bottom - 9),
                2,
            )

    def draw_wrapped_text(self, screen, text, font, rect):
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            candidate = f"{current_line} {word}".strip()
            if font.size(candidate)[0] > rect.width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = candidate

        if current_line:
            lines.append(current_line)

        y = rect.y
        for line in lines:
            rendered = font.render(line, True, (255, 255, 255))
            screen.blit(rendered, rendered.get_rect(centerx=rect.centerx, y=y))
            y += font.get_linesize()

    @staticmethod
    def draw_text(screen, text, font, center):
        label = font.render(text, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=center))