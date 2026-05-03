"""Dynamic page renderer — builds layout from JSON config."""
import pygame
from colors import *
from gauges import VerticalGauge, RPMBar, GearIndicator, WarningBar


class BigValueCell:
    """Large value display for grid cells."""

    def __init__(self, x, y, w, h, label, unit="", warn_low=None, warn_high=None,
                 fmt="{:.0f}", font_size=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.fmt = fmt

        fs = font_size or max(28, min(h // 2, w // 3))
        self.value_font = pygame.font.SysFont("helvetica", fs, bold=True)
        self.label_font = pygame.font.SysFont("helvetica", max(9, fs // 4))
        self.unit_font = pygame.font.SysFont("helvetica", max(8, fs // 5))

        self._label_surf = self.label_font.render(label, True, WHITE)
        self._unit_surf = self.unit_font.render(unit, True, TEXT_DIM) if unit else None

    def draw(self, surface, value):
        color = NEON_GREEN
        if self.warn_high is not None and value >= self.warn_high:
            color = RED
        elif self.warn_high is not None and value >= self.warn_high * 0.85:
            color = ORANGE
        elif self.warn_low is not None and value <= self.warn_low:
            color = RED

        cx = self.x + self.w // 2
        cy = self.y + self.h // 2

        pygame.draw.rect(surface, PANEL_BG, (self.x, self.y, self.w, self.h))
        pygame.draw.rect(surface, BORDER, (self.x, self.y, self.w, self.h), 1)

        lr = self._label_surf.get_rect(midtop=(cx, self.y + 5))
        surface.blit(self._label_surf, lr)

        vt = self.value_font.render(self.fmt.format(value), True, color)
        vr = vt.get_rect(center=(cx, cy + 4))
        surface.blit(vt, vr)

        if self._unit_surf:
            ur = self._unit_surf.get_rect(midbottom=(cx, self.y + self.h - 3))
            surface.blit(self._unit_surf, ur)


class HorizBar:
    """Compact horizontal bar."""

    def __init__(self, x, y, w, h, min_val, max_val, label, unit="",
                 warn_low=None, warn_high=None, fmt="{:.0f}"):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.min_val, self.max_val = min_val, max_val
        self.warn_low, self.warn_high = warn_low, warn_high
        self.fmt = fmt
        self.font = pygame.font.SysFont("helvetica", max(10, h // 3))
        self.label, self.unit = label, unit

    def draw(self, surface, value):
        frac = max(0, min(1, (value - self.min_val) / max(1, self.max_val - self.min_val)))
        color = ARC_GREEN
        in_w = False
        if self.warn_high and value >= self.warn_high:
            color, in_w = ARC_RED, True
        elif self.warn_low and value <= self.warn_low:
            color, in_w = ARC_RED, True
        elif self.warn_high and value >= self.warn_high * 0.85:
            color = ARC_ORANGE

        bar_h = max(4, self.h // 3)
        bar_y = self.y + self.h - bar_h - 1
        pygame.draw.rect(surface, ARC_BG, (self.x + 1, bar_y, self.w - 2, bar_h))
        fill_w = int((self.w - 2) * frac)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (self.x + 1, bar_y, fill_w, bar_h))

        vc = RED if in_w else TEXT_PRIMARY
        lt = self.font.render(self.label, True, TEXT_LABEL)
        surface.blit(lt, (self.x + 3, self.y + 1))
        vt = self.font.render(f"{self.fmt.format(value)}{self.unit}", True, vc)
        surface.blit(vt, (self.x + self.w - vt.get_width() - 3, self.y + 1))


def _get_value(data, key):
    if key == "boost":
        return data.get("boost", max(0, data.get("map", 0) - data.get("baro", 101)))
    if key == "oiltemp":
        return data.get("oiltemp", data.get("clt", 0) * 0.85)
    if key == "lambda":
        afr = data.get("afr", 14.7)
        return afr / 14.7
    return data.get(key, 0)


class DynamicPage:
    """Renders a page from JSON config."""

    LAYOUTS = ["grid", "vertical_bars", "horizontal_rows"]

    def __init__(self, screen, page_config):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.name = page_config.get("name", "PAGE")
        self.config = page_config

        layout = page_config.get("layout", "auto")
        if layout == "auto":
            ptype = page_config.get("type", "")
            if ptype == "big_values" or ptype == "grid":
                layout = "grid"
            else:
                layout = "vertical_bars"

        self.layout = layout
        self.gauges_config = page_config.get("gauges", [])
        self.rpm_bar_enabled = page_config.get("rpm_bar", False)
        self.gear_enabled = page_config.get("gear", False)
        self.bottom_bars_config = page_config.get("bottom_bars", [])
        self.font_size = page_config.get("font_size", None)
        self.columns = page_config.get("columns", None)
        self.rows = page_config.get("rows", None)
        self.padding = page_config.get("padding", 3)

        self._build()

    def _build(self):
        if self.layout == "grid":
            self._build_grid()
        elif self.layout == "vertical_bars":
            self._build_vertical()
        elif self.layout == "horizontal_rows":
            self._build_horizontal()

    def _build_grid(self):
        self._cells = []
        n = len(self.gauges_config)
        if n == 0:
            return

        cols = self.columns or (2 if n <= 4 else 3)
        rws = self.rows or ((n + cols - 1) // cols)
        pad = self.padding

        cell_w = (self.w - pad * (cols + 1)) // cols
        cell_h = (self.h - pad * (rws + 1)) // rws

        for i, gc in enumerate(self.gauges_config):
            col = i % cols
            row = i // cols
            if row >= rws:
                break
            x = pad + col * (cell_w + pad)
            y = pad + row * (cell_h + pad)
            cell = BigValueCell(
                x, y, cell_w, cell_h,
                gc.get("label", gc["key"]),
                gc.get("unit", ""),
                gc.get("warn_low"), gc.get("warn_high"),
                gc.get("fmt", "{:.0f}"),
                self.font_size,
            )
            self._cells.append((gc["key"], cell))

        self._rpm_bar = None
        self._gear = None
        self._bottom_bars = []
        self._warnings = None

    def _build_vertical(self):
        self._cells = []
        pad = self.padding

        y_start = 0
        rpm_h = 42
        if self.rpm_bar_enabled:
            self._rpm_bar = RPMBar(0, 0, self.w, rpm_h, max_rpm=8000, warn_rpm=6000)
            y_start = rpm_h + pad
        else:
            self._rpm_bar = None

        bot_h = 0
        if self.bottom_bars_config:
            bot_h = 30 + pad

        warn_h = 20
        gauge_h = self.h - y_start - bot_h - warn_h

        n_gauges = len(self.gauges_config)
        extra = 1 if self.gear_enabled else 0
        total_cols = n_gauges + extra
        if total_cols == 0:
            total_cols = 1
        col_w = self.w // total_cols
        fs = self.font_size

        for i, gc in enumerate(self.gauges_config):
            g = VerticalGauge(
                col_w * i, y_start, col_w, gauge_h,
                gc.get("min", 0), gc.get("max", 100),
                gc.get("label", gc["key"]), gc.get("unit", ""),
                gc.get("warn_low"), gc.get("warn_high"),
                gc.get("fmt", "{:.0f}"),
                show_scale=True, scale_count=4,
                font_scale=0.5 if n_gauges <= 4 else 1.0,
            )
            self._cells.append((gc["key"], g))

        if self.gear_enabled:
            gx = col_w * n_gauges
            self._gear = GearIndicator(gx, y_start, col_w, gauge_h // 2 - 2)
            ve_gc = {"key": "ve", "min": 0, "max": 100, "label": "VE", "unit": "%"}
            ve = VerticalGauge(
                gx, y_start + gauge_h // 2 + 2, col_w, gauge_h // 2 - 2,
                0, 100, "VE", "%", show_scale=False,
            )
            self._cells.append(("ve", ve))
        else:
            self._gear = None

        self._bottom_bars = []
        if self.bottom_bars_config:
            bar_y = self.h - warn_h - 30
            bw = self.w // max(1, len(self.bottom_bars_config))
            for i, bc in enumerate(self.bottom_bars_config):
                bar = HorizBar(
                    bw * i, bar_y, bw, 30,
                    bc.get("min", 0), bc.get("max", 100),
                    bc.get("label", bc["key"]), bc.get("unit", ""),
                    bc.get("warn_low"), bc.get("warn_high"),
                    bc.get("fmt", "{:.0f}"),
                )
                self._bottom_bars.append((bc["key"], bar))

        self._warnings = WarningBar(x=2, y=self.h - warn_h, w=self.w)
        self._sep_lines = []
        if self.rpm_bar_enabled:
            self._sep_lines.append(rpm_h + pad - 1)
        if self.bottom_bars_config:
            self._sep_lines.append(self.h - warn_h - 30 - pad)
        self._sep_lines.append(self.h - warn_h - 2)

    def _build_horizontal(self):
        self._build_grid()

    def render(self, data):
        if self.layout == "grid":
            self._render_grid(data)
        elif self.layout == "vertical_bars":
            self._render_vertical(data)
        else:
            self._render_grid(data)

    def _render_grid(self, data):
        for key, cell in self._cells:
            cell.draw(self.screen, _get_value(data, key))

    def _render_vertical(self, data):
        for sy in self._sep_lines:
            pygame.draw.line(self.screen, BORDER, (0, sy), (self.w, sy))

        if self._rpm_bar:
            self._rpm_bar.draw(self.screen, data.get("rpm", 0))

        for key, g in self._cells:
            g.draw(self.screen, _get_value(data, key))

        if self._gear:
            self._gear.draw(self.screen, data.get("gear", 0))

        for key, bar in self._bottom_bars:
            bar.draw(self.screen, _get_value(data, key))

        if self._warnings:
            self._warnings.draw(self.screen, data)
