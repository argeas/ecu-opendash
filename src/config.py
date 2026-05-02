SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 30

SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.1

# Airbear WiFi connection (Dropbear V2)
WIFI_HOST = "speeduino.local"
WIFI_PORT = 2000
WIFI_AP_HOST = "192.168.4.1"

# Speeduino 'A' command real-time data byte offsets (firmware 202402+)
# Reference: https://wiki.speeduino.com/en/reference/Interface_Protocol
RT_MAP = {
    "secl":           {"offset": 0,  "size": 2, "signed": False, "scale": 1,    "unit": "s"},
    "status1":        {"offset": 2,  "size": 1, "signed": False, "scale": 1,    "unit": ""},
    "engine":         {"offset": 3,  "size": 1, "signed": False, "scale": 1,    "unit": ""},
    "dwell":          {"offset": 4,  "size": 1, "signed": False, "scale": 0.1,  "unit": "ms"},
    "map":            {"offset": 5,  "size": 2, "signed": False, "scale": 1,    "unit": "kPa"},
    "iat":            {"offset": 7,  "size": 1, "signed": False, "scale": 1,    "unit": "°C", "offset_val": -40},
    "clt":            {"offset": 8,  "size": 1, "signed": False, "scale": 1,    "unit": "°C", "offset_val": -40},
    "batcorrection":  {"offset": 9,  "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "batteryv":       {"offset": 10, "size": 1, "signed": False, "scale": 0.1,  "unit": "V"},
    "afr":            {"offset": 11, "size": 1, "signed": False, "scale": 0.1,  "unit": "λ"},
    "egocorrection":  {"offset": 12, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "iatcorrection":  {"offset": 13, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "wuecorrection":  {"offset": 14, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "rpm":            {"offset": 15, "size": 2, "signed": False, "scale": 1,    "unit": "rpm"},
    "accelenrich":    {"offset": 17, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "gammae":         {"offset": 18, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "ve":             {"offset": 19, "size": 1, "signed": False, "scale": 0.5,  "unit": "%"},
    "afrtarget":      {"offset": 20, "size": 1, "signed": False, "scale": 0.1,  "unit": ""},
    "pw1":            {"offset": 21, "size": 2, "signed": False, "scale": 0.001,"unit": "ms"},
    "tpsdot":         {"offset": 23, "size": 1, "signed": True,  "scale": 10,   "unit": "%/s"},
    "advance":        {"offset": 24, "size": 1, "signed": True,  "scale": 1,    "unit": "°"},
    "tps":            {"offset": 25, "size": 1, "signed": False, "scale": 0.5,  "unit": "%"},
    "loopsps":        {"offset": 26, "size": 2, "signed": False, "scale": 1,    "unit": ""},
    "boosttarget":    {"offset": 28, "size": 2, "signed": False, "scale": 1,    "unit": "kPa"},
    "boostduty":      {"offset": 30, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "spark":          {"offset": 31, "size": 1, "signed": False, "scale": 1,    "unit": ""},
    "rpmdot":         {"offset": 32, "size": 2, "signed": True,  "scale": 1,    "unit": "rpm/s"},
    "ethanolpct":     {"offset": 34, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "flexcorrection": {"offset": 35, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "flexigncorr":    {"offset": 36, "size": 1, "signed": True,  "scale": 1,    "unit": "°"},
    "idleload":       {"offset": 37, "size": 1, "signed": False, "scale": 1,    "unit": "%"},
    "status3":        {"offset": 38, "size": 1, "signed": False, "scale": 1,    "unit": ""},
    "baro":           {"offset": 39, "size": 1, "signed": False, "scale": 1,    "unit": "kPa"},
    "oilpressure":    {"offset": 40, "size": 1, "signed": False, "scale": 1,    "unit": "psi"},
    "gear":           {"offset": 41, "size": 1, "signed": False, "scale": 1,    "unit": ""},
}

# Boost is MAP minus baro (calculated)
# Lambda = AFR / stoich (calculated)

STOICH_AFR = 14.7

# Gauge ranges and warning thresholds (from TSDash Speeduino definitions)
GAUGE_DEFS = {
    "rpm":      {"min": 0, "max": 8000, "warn_high": 6000, "crit_high": 7000, "unit": "rpm"},
    "afr":      {"min": 10, "max": 20, "warn_low": 13.0, "warn_high": 16.0, "crit_high": 17.0, "unit": ""},
    "clt":      {"min": -40, "max": 130, "warn_high": 93, "crit_high": 104, "unit": "°C"},
    "iat":      {"min": -40, "max": 100, "warn_high": 50, "crit_high": 60, "unit": "°C"},
    "tps":      {"min": 0, "max": 100, "warn_high": 90, "unit": "%"},
    "map":      {"min": 0, "max": 255, "warn_high": 200, "crit_high": 245, "unit": "kPa"},
    "advance":  {"min": -10, "max": 50, "warn_high": 35, "crit_high": 45, "unit": "°"},
    "pw1":      {"min": 0, "max": 35, "warn_high": 20, "crit_high": 25, "unit": "ms"},
    "batteryv": {"min": 8, "max": 16, "warn_low": 12.0, "unit": "V"},
    "boost":    {"min": 0, "max": 200, "warn_high": 150, "crit_high": 180, "unit": "kPa"},
    "oilpressure": {"min": 0, "max": 100, "warn_low": 25, "unit": "psi"},
    "ve":       {"min": 0, "max": 150, "unit": "%"},
    "dutycycle": {"min": 0, "max": 100, "warn_high": 70, "crit_high": 80, "unit": "%"},
}

WARN_CLT_HIGH = 93
WARN_OIL_LOW = 25
WARN_BATTERY_LOW = 12.0
WARN_AFR_LEAN = 16.0
WARN_AFR_RICH = 13.0
