import math

import pygame
import pygame.gfxdraw

from colors import *


class VerticalGauge:
    """Vertical bar gauge with value, label, and optional warning zones."""

    def __init__(self, x, y, w, h, min_val, max_val, label, unit="",
                 warn_low=None, warn_high=None, fmt="{:.0f}",
                 show_scale=True, scale_count=5, font_scale=1.0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.unit = unit
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.fmt = fmt
        self.show_scale = show_scale
        self.scale_count = scale_count

        self.value_font = pygame.font.SysFont("helvetica", max(7, int(w // 4 * font_scale)), bold=True)
        self.label_font = pygame.font.SysFont("helvetica", max(7, int(w // 6 * font_scale)))
        self.scale_font = pygame.font.SysFont("helvetica", max(7, int(w // 5 * font_scale)))

        self.pad_top = 16
        self.pad_bot = 28
        self.bar_w = max(6, w // 3)

        if show_scale:
            self.bar_x = x + w - self.bar_w - 2
        else:
            self.bar_x = x + (w - self.bar_w) // 2

        self.bar_y = y + self.pad_top
        self.bar_h = h - self.pad_top - self.pad_bot

        self._build_static()

    def _build_static(self):
        self._static = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        lt = self.label_font.render(self.label, True, WHITE)
        lr = lt.get_rect(midtop=(self.bar_x - self.x + self.bar_w // 2, 1))
        self._static.blit(lt, lr)

        if self.unit:
            ut = self.label_font.render(self.unit, True, TEXT_DIM)
            ur = ut.get_rect(midbottom=(self.w // 2, self.h - 1))
            self._static.blit(ut, ur)

        bx = self.bar_x - self.x
        by = self.bar_y - self.y
        pygame.draw.rect(self._static, ARC_BG, (bx, by, self.bar_w, self.bar_h))

        if self.show_scale and self.scale_count > 1:
            for i in range(self.scale_count):
                frac = i / (self.scale_count - 1)
                tick_val = self.min_val + frac * (self.max_val - self.min_val)
                tick_y = by + self.bar_h - int(frac * self.bar_h)

                pygame.draw.line(self._static, BORDER,
                                 (bx - 3, tick_y), (bx, tick_y))

                ts = self.scale_font.render(str(int(tick_val)), True, TEXT_DIM)
                tr = ts.get_rect(midright=(bx - 5, tick_y))
                self._static.blit(ts, tr)

        if self.warn_high is not None:
            wf = (self.warn_high - self.min_val) / max(1, self.max_val - self.min_val)
            wy = by + self.bar_h - int(wf * self.bar_h)
            pygame.draw.line(self._static, (ARC_RED[0], ARC_RED[1], ARC_RED[2], 100),
                             (bx, wy), (bx + self.bar_w, wy))

        if self.warn_low is not None:
            wf = (self.warn_low - self.min_val) / max(1, self.max_val - self.min_val)
            wy = by + self.bar_h - int(wf * self.bar_h)
            pygame.draw.line(self._static, (ARC_RED[0], ARC_RED[1], ARC_RED[2], 100),
                             (bx, wy), (bx + self.bar_w, wy))

    def draw(self, surface, value):
        surface.blit(self._static, (self.x, self.y))

        frac = max(0, min(1, (value - self.min_val) / max(1, self.max_val - self.min_val)))
        fill_h = int(frac * self.bar_h)

        in_warning = False
        color = ARC_GREEN
        if self.warn_high is not None and value >= self.warn_high:
            color = ARC_RED
            in_warning = True
        elif self.warn_low is not None and value <= self.warn_low:
            color = ARC_RED
            in_warning = True
        elif self.warn_high is not None and value >= self.warn_high * 0.82:
            color = ARC_ORANGE

        if fill_h > 0:
            fy = self.bar_y + self.bar_h - fill_h
            pygame.draw.rect(surface, color,
                             (self.bar_x, fy, self.bar_w, fill_h))

        val_color = RED if in_warning else TEXT_PRIMARY
        vt = self.value_font.render(self.fmt.format(value), True, val_color)

        vr = vt.get_rect(center=(self.bar_x + self.bar_w // 2,
                                 self.bar_y + self.bar_h + 10))

        surface.blit(vt, vr)


class RPMBar:
    """Wide horizontal RPM bar across the top."""

    def __init__(self, x, y, w, h, max_rpm=7000, warn_rpm=6000):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.max_rpm = max_rpm
        self.warn_rpm = warn_rpm
        self.warn_frac = warn_rpm / max_rpm

        self.value_font = pygame.font.SysFont("helvetica", max(14, h // 2), bold=True)
        self.label_font = pygame.font.SysFont("helvetica", max(9, h // 4))
        self.tick_font = pygame.font.SysFont("helvetica", max(8, h // 5))

        self.bar_h = max(8, h // 3)
        self.bar_y = y + h - self.bar_h

        self._build_static()

    def _build_static(self):
        self._static = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        by = self.h - self.bar_h
        pygame.draw.rect(self._static, ARC_BG, (0, by, self.w, self.bar_h))

        tick_step = 1000
        for rpm in range(0, self.max_rpm + 1, tick_step):
            frac = rpm / self.max_rpm
            tx = int(frac * self.w)
            pygame.draw.line(self._static, BORDER, (tx, by - 3), (tx, by))
            ts = self.tick_font.render(str(rpm // 1000), True, TEXT_DIM)
            tr = ts.get_rect(midbottom=(tx, by - 4))
            self._static.blit(ts, tr)

        lt = self.label_font.render("RPM", True, TEXT_LABEL)
        self._static.blit(lt, (2, 2))

    def draw(self, surface, rpm):
        surface.blit(self._static, (self.x, self.y))

        frac = max(0, min(1, rpm / self.max_rpm))
        fill_w = int(frac * self.w)

        if fill_w > 0:
            warn_x = int(self.warn_frac * self.w)
            green_w = min(fill_w, warn_x)
            if green_w > 0:
                pygame.draw.rect(surface, ARC_GREEN,
                                 (self.x, self.bar_y, green_w, self.bar_h))

            if fill_w > warn_x:
                orange_end = min(fill_w, int(self.warn_frac * 1.08 * self.w))
                if orange_end > warn_x:
                    pygame.draw.rect(surface, ARC_ORANGE,
                                     (self.x + warn_x, self.bar_y,
                                      orange_end - warn_x, self.bar_h))
                if fill_w > orange_end:
                    pygame.draw.rect(surface, ARC_RED,
                                     (self.x + orange_end, self.bar_y,
                                      fill_w - orange_end, self.bar_h))

        in_warn = rpm >= self.warn_rpm
        val_color = RED if in_warn else TEXT_PRIMARY
        vt = self.value_font.render(f"{rpm:.0f}", True, val_color)
        vr = vt.get_rect(midright=(self.x + self.w - 4, self.y + (self.h - self.bar_h) // 2))
        surface.blit(vt, vr)


class GearIndicator:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.font = pygame.font.SysFont("helvetica", min(w, h) - 10, bold=True)
        self.label_font = pygame.font.SysFont("helvetica", max(8, min(w, h) // 5))
        self._label = self.label_font.render("GEAR", True, TEXT_DIM)

    def draw(self, surface, gear):
        gear_str = "N" if gear == 0 else str(int(gear))

        cx, cy = self.x + self.w // 2, self.y + self.h // 2

        pygame.draw.rect(surface, PANEL_BG, (self.x, self.y, self.w, self.h))
        pygame.draw.rect(surface, BORDER, (self.x, self.y, self.w, self.h), 1)

        text = self.font.render(gear_str, True, CYAN)
        rect = text.get_rect(center=(cx, cy - 4))
        surface.blit(text, rect)

        lr = self._label.get_rect(center=(cx, cy + self.h // 2 - 10))
        surface.blit(self._label, lr)


class WarningBar:
    def __init__(self, x, y, w):
        self.x = x
        self.y = y
        self.w = w
        self.font = pygame.font.SysFont("helvetica", 10, bold=True)

    def draw(self, surface, data):
        items = []
        clt = data.get("clt", 0)
        if clt > 100:
            items.append(("OVERHEAT", RED))
        oil = data.get("oilpressure", 50)
        rpm = data.get("rpm", 0)
        if oil < 25 and rpm > 500:
            items.append(("LOW OIL", RED))
        batt = data.get("batteryv", 14)
        if batt < 12.0:
            items.append(("BATT", ORANGE))
        afr = data.get("afr", 14.7)
        if afr > 16.0:
            items.append(("LEAN", RED))
        elif afr < 11.0:
            items.append(("RICH", YELLOW))

        if not items:
            return

        offset = self.x
        for msg, color in items:
            pygame.gfxdraw.filled_circle(surface, offset + 4, self.y + 5, 3, color)
            pygame.gfxdraw.aacircle(surface, offset + 4, self.y + 5, 3, color)
            t = self.font.render(msg, True, color)
            surface.blit(t, (offset + 10, self.y))
            offset += t.get_width() + 20
