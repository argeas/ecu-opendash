import pygame

from colors import *
from gauges import VerticalGauge, RPMBar, GearIndicator, WarningBar

# Needed for BigValueDisplay
from colors import NEON_GREEN, PANEL_BG, BORDER, WHITE, TEXT_DIM, RED, ORANGE


class Page:
    """Base class for a dashboard page."""

    def __init__(self, screen, name):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.name = name
        self.gauges = []
        self.horiz_bars = []
        self.extras = []
        self._sep_y = []

    def render(self, data):
        pass


class MainPage(Page):
    """Page 1: Primary driving gauges."""

    def __init__(self, screen):
        super().__init__(screen, "MAIN")

        self.rpm = RPMBar(x=0, y=0, w=self.w, h=42, max_rpm=8000, warn_rpm=6000)

        gauge_y = 46
        gauge_h = 195
        col_w = self.w // 8

        self.boost = VerticalGauge(
            col_w * 0, gauge_y, col_w, gauge_h,
            0, 200, "BOOST", "kPa",
            warn_high=150, show_scale=True, scale_count=5,
        )
        self.map_g = VerticalGauge(
            col_w * 1, gauge_y, col_w, gauge_h,
            0, 255, "MAP", "kPa",
            warn_high=200, show_scale=True, scale_count=4,
        )
        self.afr = VerticalGauge(
            col_w * 2, gauge_y, col_w, gauge_h,
            10, 20, "AFR", "",
            warn_high=16, warn_low=13, fmt="{:.1f}",
            show_scale=True, scale_count=5,
        )
        self.clt = VerticalGauge(
            col_w * 3, gauge_y, col_w, gauge_h,
            -40, 130, "CLT", "°C",
            warn_high=93, show_scale=True, scale_count=4,
        )
        self.oil = VerticalGauge(
            col_w * 4, gauge_y, col_w, gauge_h,
            0, 100, "OIL", "psi",
            warn_low=25, show_scale=True, scale_count=4,
        )
        self.batt = VerticalGauge(
            col_w * 5, gauge_y, col_w, gauge_h,
            8, 16, "BATT", "V",
            warn_low=12, fmt="{:.1f}",
            show_scale=True, scale_count=4,
        )
        self.tps = VerticalGauge(
            col_w * 6, gauge_y, col_w, gauge_h,
            0, 100, "TPS", "%",
            warn_high=90, show_scale=True, scale_count=3,
        )

        gear_w = col_w
        self.gear = GearIndicator(
            x=col_w * 7, y=gauge_y, w=gear_w, h=gauge_h // 2 - 2,
        )
        self.ve = VerticalGauge(
            col_w * 7, gauge_y + gauge_h // 2 + 2, gear_w, gauge_h // 2 - 2,
            0, 100, "VE", "%",
            show_scale=False,
        )

        bot_y = 246
        bot_h = 30
        third = self.w // 3
        self.adv_bar = HorizBar(0, bot_y, third, bot_h, 0, 45, "ADV", "°")
        self.iat_bar = HorizBar(third, bot_y, third, bot_h, -20, 60, "IAT", "°C", warn_high=50)
        self.pw_bar = HorizBar(third * 2, bot_y, third, bot_h, 0, 20, "PW", "ms", fmt="{:.1f}")

        self.warnings = WarningBar(x=2, y=280, w=self.w)
        self._sep_y = [44, 244, 278]

    def render(self, data):
        rpm = data.get("rpm", 0)
        boost = data.get("boost", max(0, data.get("map", 0) - data.get("baro", 101)))
        map_val = data.get("map", 0)
        afr = data.get("afr", 14.7)
        clt = data.get("clt", 0)
        oil = data.get("oilpressure", 0)
        batt = data.get("batteryv", 0)
        tps = data.get("tps", 0)
        gear = data.get("gear", 0)
        ve = data.get("ve", 0)
        advance = data.get("advance", 0)
        iat = data.get("iat", 0)
        pw = data.get("pw1", 0)

        for sy in self._sep_y:
            pygame.draw.line(self.screen, BORDER, (0, sy), (self.w, sy))

        self.rpm.draw(self.screen, rpm)
        self.boost.draw(self.screen, boost)
        self.map_g.draw(self.screen, map_val)
        self.afr.draw(self.screen, afr)
        self.clt.draw(self.screen, clt)
        self.oil.draw(self.screen, oil)
        self.batt.draw(self.screen, batt)
        self.tps.draw(self.screen, tps)
        self.gear.draw(self.screen, gear)
        self.ve.draw(self.screen, ve)
        self.adv_bar.draw(self.screen, advance)
        self.iat_bar.draw(self.screen, iat)
        self.pw_bar.draw(self.screen, pw)
        self.warnings.draw(self.screen, data)


class TempBoostPage(Page):
    """Page 2: Coolant, Oil Temp, Boost, Oil Pressure."""

    def __init__(self, screen):
        super().__init__(screen, "TEMPS")

        gauge_y = 10
        gauge_h = 270
        col_w = self.w // 4

        self.clt = VerticalGauge(
            col_w * 0, gauge_y, col_w, gauge_h,
            0, 130, "CLT", "°C",
            warn_high=100, show_scale=True, scale_count=6, font_scale=0.5,
        )
        self.oil_temp = VerticalGauge(
            col_w * 1, gauge_y, col_w, gauge_h,
            0, 150, "OIL T", "°C",
            warn_high=120, show_scale=True, scale_count=6, font_scale=0.5,
        )
        self.boost = VerticalGauge(
            col_w * 2, gauge_y, col_w, gauge_h,
            0, 150, "BOOST", "kPa",
            warn_high=130, show_scale=True, scale_count=6, font_scale=0.5,
        )
        self.oil_p = VerticalGauge(
            col_w * 3, gauge_y, col_w, gauge_h,
            0, 100, "OIL P", "psi",
            warn_low=25, show_scale=True, scale_count=6, font_scale=0.5,
        )

        self.warnings = WarningBar(x=2, y=290, w=self.w)
        self._sep_y = [288]

    def render(self, data):
        clt = data.get("clt", 0)
        oil_temp = data.get("oiltemp", data.get("clt", 0) * 0.85)
        boost = data.get("boost", max(0, data.get("map", 0) - data.get("baro", 101)))
        oil_p = data.get("oilpressure", 0)

        for sy in self._sep_y:
            pygame.draw.line(self.screen, BORDER, (0, sy), (self.w, sy))

        self.clt.draw(self.screen, clt)
        self.oil_temp.draw(self.screen, oil_temp)
        self.boost.draw(self.screen, boost)
        self.oil_p.draw(self.screen, oil_p)
        self.warnings.draw(self.screen, data)


class BigValueDisplay:
    """Large readable value with label, for focused pages."""

    def __init__(self, x, y, w, h, label, unit="", warn_low=None, warn_high=None, fmt="{:.0f}"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.unit = unit
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.fmt = fmt
        self.value_font = pygame.font.SysFont("helvetica", max(36, h // 2), bold=True)
        self.label_font = pygame.font.SysFont("helvetica", max(12, h // 6))
        self.unit_font = pygame.font.SysFont("helvetica", max(10, h // 8))

    def draw(self, surface, value):
        in_warning = False
        color = NEON_GREEN
        if self.warn_high is not None and value >= self.warn_high:
            color = RED
            in_warning = True
        elif self.warn_low is not None and value <= self.warn_low:
            color = RED
            in_warning = True
        elif self.warn_high is not None and value >= self.warn_high * 0.85:
            color = ORANGE

        cx = self.x + self.w // 2
        cy = self.y + self.h // 2

        pygame.draw.rect(surface, PANEL_BG, (self.x, self.y, self.w, self.h))
        pygame.draw.rect(surface, BORDER, (self.x, self.y, self.w, self.h), 1)

        lt = self.label_font.render(self.label, True, WHITE)
        lr = lt.get_rect(midtop=(cx, self.y + 6))
        surface.blit(lt, lr)

        vt = self.value_font.render(self.fmt.format(value), True, color)
        vr = vt.get_rect(center=(cx, cy + 4))
        surface.blit(vt, vr)

        ut = self.unit_font.render(self.unit, True, TEXT_DIM)
        ur = ut.get_rect(midbottom=(cx, self.y + self.h - 4))
        surface.blit(ut, ur)


class BoostTempsPage(Page):
    """Page 3: Boost, Coolant Temp, IAT — large readable values."""

    def __init__(self, screen):
        super().__init__(screen, "FOCUS")

        pad = 4
        row_h = (self.h - pad * 4) // 3

        self.boost = BigValueDisplay(
            pad, pad, self.w - pad * 2, row_h,
            "BOOST", "kPa",
            warn_high=150, fmt="{:.0f}",
        )
        self.clt = BigValueDisplay(
            pad, pad * 2 + row_h, self.w - pad * 2, row_h,
            "COOLANT", "°C",
            warn_high=93, fmt="{:.0f}",
        )
        self.iat = BigValueDisplay(
            pad, pad * 3 + row_h * 2, self.w - pad * 2, row_h,
            "AIR INTAKE", "°C",
            warn_high=50, fmt="{:.0f}",
        )

    def render(self, data):
        boost = data.get("boost", max(0, data.get("map", 0) - data.get("baro", 101)))
        clt = data.get("clt", 0)
        iat = data.get("iat", 0)

        self.boost.draw(self.screen, boost)
        self.clt.draw(self.screen, clt)
        self.iat.draw(self.screen, iat)


class Dashboard:
    """Multi-page dashboard. Click/tap to cycle pages."""

    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self._fps_font = pygame.font.SysFont("helvetica", 9)
        self._page_font = pygame.font.SysFont("helvetica", 8)
        self._clock = pygame.time.Clock()

        self.pages = [
            MainPage(screen),
            TempBoostPage(screen),
            BoostTempsPage(screen),
        ]
        self.current_page = 0

    def next_page(self):
        self.current_page = (self.current_page + 1) % len(self.pages)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.next_page()

    def render(self, data):
        self.screen.fill(DARK_BG)

        self.pages[self.current_page].render(data)

        # Page indicator dots
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

        # FPS
        fps = self._clock.get_fps()
        ft = self._fps_font.render(f"{fps:.0f}fps", True, TEXT_DIM)
        self.screen.blit(ft, (self.w - ft.get_width() - 3, self.h - 14))
        self._clock.tick()


class HorizBar:
    """Compact horizontal bar for bottom row."""

    def __init__(self, x, y, w, h, min_val, max_val, label, unit="",
                 warn_low=None, warn_high=None, fmt="{:.0f}"):
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
        self.font = pygame.font.SysFont("helvetica", max(10, h // 3))

    def draw(self, surface, value):
        frac = max(0, min(1, (value - self.min_val) / max(1, self.max_val - self.min_val)))

        in_warning = False
        color = ARC_GREEN
        if self.warn_high is not None and value >= self.warn_high:
            color = ARC_RED
            in_warning = True
        elif self.warn_low is not None and value <= self.warn_low:
            color = ARC_RED
            in_warning = True
        elif self.warn_high is not None and value >= self.warn_high * 0.85:
            color = ARC_ORANGE

        bar_h = max(4, self.h // 3)
        bar_y = self.y + self.h - bar_h - 1

        pygame.draw.rect(surface, ARC_BG, (self.x + 1, bar_y, self.w - 2, bar_h))
        fill_w = int((self.w - 2) * frac)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (self.x + 1, bar_y, fill_w, bar_h))

        val_color = RED if in_warning else TEXT_PRIMARY
        lt = self.font.render(self.label, True, TEXT_LABEL)
        surface.blit(lt, (self.x + 3, self.y + 1))

        vt = self.font.render(f"{self.fmt.format(value)}{self.unit}", True, val_color)
        surface.blit(vt, (self.x + self.w - vt.get_width() - 3, self.y + 1))
