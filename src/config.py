SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 30

SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.1

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

# Gauge warning thresholds
WARN_CLT_HIGH = 100
WARN_OIL_LOW = 25
WARN_BATTERY_LOW = 12.0
WARN_AFR_LEAN = 16.0
WARN_AFR_RICH = 11.0
