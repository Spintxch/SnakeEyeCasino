import math

import pygame


LAYOUT_WIDTH = 900
LAYOUT_HEIGHT = 600
_scale_x = 1.0
_scale_y = 1.0
_font_scale = 1.0


def configure(surface):
    global _scale_x, _scale_y, _font_scale
    width, height = surface.get_size()
    _scale_x = width / LAYOUT_WIDTH
    _scale_y = height / LAYOUT_HEIGHT
    _font_scale = math.sqrt(_scale_x * _scale_y)


def to_layout(position):
    return (
        round(position[0] / _scale_x),
        round(position[1] / _scale_y),
    )


def map_point(position):
    return (
        round(position[0] * _scale_x),
        round(position[1] * _scale_y),
    )


def circle_point(center, offset):
    radius_scale = min(_scale_x, _scale_y)
    return (
        center[0] + offset[0] * radius_scale / _scale_x,
        center[1] + offset[1] * radius_scale / _scale_y,
    )


def map_rect(rect):
    x, y = map_point(rect.topleft)
    width = round(rect.width * _scale_x)
    height = round(rect.height * _scale_y)
    return pygame.Rect(x, y, width, height)


def draw_rect(surface, color, rect, width=0, border_radius=0):
    return pygame.draw.rect(
        surface,
        color,
        map_rect(rect),
        round(width * _font_scale),
        border_radius=round(border_radius * _font_scale),
    )


def draw_ellipse(surface, color, rect, width=0):
    return pygame.draw.ellipse(
        surface,
        color,
        map_rect(rect),
        round(width * _font_scale),
    )


def draw_circle(surface, color, center, radius, width=0):
    radius_scale = min(_scale_x, _scale_y)
    return pygame.draw.circle(
        surface,
        color,
        map_point(center),
        round(radius * radius_scale),
        round(width * radius_scale),
    )


def draw_line(surface, color, start, end, width=1):
    return pygame.draw.line(
        surface,
        color,
        map_point(start),
        map_point(end),
        max(1, round(width * _font_scale)),
    )


def draw_polygon(surface, color, points, width=0):
    return pygame.draw.polygon(
        surface,
        color,
        [map_point(point) for point in points],
        round(width * _font_scale),
    )


def blit_at(surface, image, position):
    return surface.blit(image, map_point(position))


def blit_center(surface, image, center):
    return surface.blit(image, image.get_rect(center=map_point(center)))


def blit_midleft(surface, image, position):
    return surface.blit(image, image.get_rect(midleft=map_point(position)))


def set_clip(surface, rect):
    surface.set_clip(map_rect(rect))


class ScaledFont:
    def __init__(self, family, size, bold=False):
        self.family = family
        self.base_size = size
        self.bold = bold
        self._base_font = self._make_font(size)
        self._scaled_size = None
        self._scaled_font = None

    def _make_font(self, size):
        if self.family is None:
            font = pygame.font.Font(None, size)
        else:
            font = pygame.font.SysFont(self.family, size, bold=self.bold)
        return font

    def _font_at_window_size(self):
        size = max(1, round(self.base_size * _font_scale))
        if size != self._scaled_size:
            self._scaled_font = self._make_font(size)
            self._scaled_size = size
        return self._scaled_font

    def render(self, text, antialias, color, background=None):
        return self._font_at_window_size().render(
            text,
            antialias,
            color,
            background,
        )

    def size(self, text):
        return self._base_font.size(text)

    def rendered_width(self, text):
        return round(self._font_at_window_size().size(text)[0] / _scale_x)

    def get_linesize(self):
        return self._base_font.get_linesize()


def make_font(family, size, bold=False):
    return ScaledFont(family, size, bold)
