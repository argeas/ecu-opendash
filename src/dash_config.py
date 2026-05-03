"""Dashboard configuration - JSON-based, editable via web UI."""
import json
import os

CONFIG_PATH = os.environ.get("OPENDASH_CONFIG", "/opt/opendash/dashboard.json")

DEFAULT_CONFIG = {
    "pages": [
        {
            "name": "FOCUS",
            "layout": "grid",
            "columns": 2,
            "rows": 2,
            "padding": 3,
            "font_size": None,
            "rpm_bar": False,
            "gauges": [
                {"key": "boost", "label": "BOOST", "unit": "kPa", "min": 0, "max": 200, "warn_high": 150, "fmt": "{:.0f}"},
                {"key": "clt", "label": "COOLANT", "unit": "°C", "min": -40, "max": 130, "warn_high": 93, "fmt": "{:.0f}"},
                {"key": "oiltemp", "label": "OIL TEMP", "unit": "°C", "min": 0, "max": 150, "warn_high": 120, "fmt": "{:.0f}"},
                {"key": "iat", "label": "AIR INTAKE", "unit": "°C", "min": -20, "max": 60, "warn_high": 50, "fmt": "{:.0f}"},
            ],
            "gear": False,
            "ve_gauge": False,
            "bottom_bars": [],
        },
        {
            "name": "MAIN",
            "type": "vertical_bars",
            "rpm_bar": True,
            "gauges": [
                {"key": "boost", "label": "BST", "unit": "kPa", "min": 0, "max": 200, "warn_high": 150, "fmt": "{:.0f}"},
                {"key": "map", "label": "MAP", "unit": "kPa", "min": 0, "max": 255, "warn_high": 200, "fmt": "{:.0f}"},
                {"key": "afr", "label": "AFR", "unit": "", "min": 10, "max": 20, "warn_low": 13, "warn_high": 16, "fmt": "{:.1f}"},
                {"key": "clt", "label": "CLT", "unit": "°C", "min": -40, "max": 130, "warn_high": 93, "fmt": "{:.0f}"},
                {"key": "oilpressure", "label": "OIL", "unit": "psi", "min": 0, "max": 100, "warn_low": 25, "fmt": "{:.0f}"},
                {"key": "batteryv", "label": "BATT", "unit": "V", "min": 8, "max": 16, "warn_low": 12, "fmt": "{:.1f}"},
                {"key": "tps", "label": "TPS", "unit": "%", "min": 0, "max": 100, "warn_high": 90, "fmt": "{:.0f}"},
            ],
            "gear": True,
            "ve_gauge": True,
            "bottom_bars": [
                {"key": "advance", "label": "ADV", "unit": "°", "min": 0, "max": 45},
                {"key": "iat", "label": "IAT", "unit": "°C", "min": -20, "max": 60, "warn_high": 50},
                {"key": "pw1", "label": "PW", "unit": "ms", "min": 0, "max": 20, "fmt": "{:.1f}"},
            ],
        },
        {
            "name": "TEMPS",
            "type": "vertical_bars",
            "rpm_bar": False,
            "gauges": [
                {"key": "clt", "label": "CLT", "unit": "°C", "min": -40, "max": 130, "warn_high": 93, "fmt": "{:.0f}"},
                {"key": "oiltemp", "label": "OIL T", "unit": "°C", "min": 0, "max": 150, "warn_high": 120, "fmt": "{:.0f}"},
                {"key": "boost", "label": "BST", "unit": "kPa", "min": 0, "max": 200, "warn_high": 150, "fmt": "{:.0f}"},
                {"key": "oilpressure", "label": "OIL P", "unit": "psi", "min": 0, "max": 100, "warn_low": 25, "fmt": "{:.0f}"},
            ],
            "gear": False,
            "ve_gauge": False,
            "bottom_bars": [],
        },
    ],
    "rpm": {"max": 8000, "warn": 6000},
    "theme": "neon_green",
}

AVAILABLE_CHANNELS = [
    {"key": "rpm", "label": "RPM", "unit": "rpm"},
    {"key": "map", "label": "MAP", "unit": "kPa"},
    {"key": "boost", "label": "Boost", "unit": "kPa"},
    {"key": "afr", "label": "AFR", "unit": ""},
    {"key": "clt", "label": "Coolant Temp", "unit": "°C"},
    {"key": "iat", "label": "Intake Air Temp", "unit": "°C"},
    {"key": "tps", "label": "Throttle Position", "unit": "%"},
    {"key": "advance", "label": "Ignition Advance", "unit": "°"},
    {"key": "pw1", "label": "Pulse Width", "unit": "ms"},
    {"key": "batteryv", "label": "Battery Voltage", "unit": "V"},
    {"key": "oilpressure", "label": "Oil Pressure", "unit": "psi"},
    {"key": "oiltemp", "label": "Oil Temp", "unit": "°C"},
    {"key": "ve", "label": "Volumetric Efficiency", "unit": "%"},
    {"key": "gear", "label": "Gear", "unit": ""},
    {"key": "baro", "label": "Barometric Pressure", "unit": "kPa"},
    {"key": "accelenrich", "label": "Accel Enrichment", "unit": "%"},
    {"key": "gammae", "label": "Gamma Enrichment", "unit": "%"},
    {"key": "boosttarget", "label": "Boost Target", "unit": "kPa"},
    {"key": "boostduty", "label": "Boost Duty", "unit": "%"},
    {"key": "rpmdot", "label": "RPM Delta", "unit": "rpm/s"},
    {"key": "lambda", "label": "Lambda", "unit": "λ"},
]


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH) or ".", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
