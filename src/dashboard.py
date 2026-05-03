"""Dashboard — renders pages dynamically from JSON config."""
import pygame
from colors import *
from dash_config import load_config
from dynamic_page import DynamicPage


class Dashboard:
    """Multi-page dashboard driven by JSON config. Click/tap to cycle pages."""

    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self._fps_font = pygame.font.SysFont("helvetica", 9)
        self._clock = pygame.time.Clock()
        self.current_page = 0
        self._config = None
        self.pages = []
        self.reload_config()

    def reload_config(self):
        self._config = load_config()
        self.pages = []
        for page_cfg in self._config.get("pages", []):
            self.pages.append(DynamicPage(self.screen, page_cfg))
        if not self.pages:
            self.pages.append(DynamicPage(self.screen, {"name": "EMPTY", "gauges": []}))
        if self.current_page >= len(self.pages):
            self.current_page = 0

    def next_page(self):
        self.current_page = (self.current_page + 1) % len(self.pages)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.next_page()

    def render(self, data):
        self.screen.fill(DARK_BG)

        self.pages[self.current_page].render(data)

        dot_y = self.h - 8
        total_w = len(self.pages) * 12
        start_x = (self.w - total_w) // 2
        for i in range(len(self.pages)):
            dx = start_x + i * 12 + 4
            if i == self.current_page:
                pygame.draw.circle(self.screen, TEXT_PRIMARY, (dx, dot_y), 3)
            else:
                pygame.draw.circle(self.screen, BORDER, (dx, dot_y), 3)
                pygame.draw.circle(self.screen, TEXT_DIM, (dx, dot_y), 3, 1)

        fps = self._clock.get_fps()
        ft = self._fps_font.render(f"{fps:.0f}fps", True, TEXT_DIM)
        self.screen.blit(ft, (self.w - ft.get_width() - 3, self.h - 14))
        self._clock.tick()
