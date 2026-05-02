# OpenDash — Project Instructions

## Overview

OpenDash is a bare-metal car dashboard for Raspberry Pi with an Elegoo 3.5" SPI display (ILI9486).
Built for a Land Rover Discovery 1 with T16 Turbo engine running a Dropbear v2 (Speeduino) ECU on Teensy 4.1.

## Tech Stack

- **Language**: Python 3
- **UI**: Pygame-CE (framebuffer rendering, no X11/desktop)
- **ECU Protocol**: Speeduino/TunerStudio MS serial protocol at 115200 baud
- **Display**: Elegoo 3.5" ILI9486 SPI via fbcp-ili9341 (HDMI framebuffer mirror)
- **OS**: Raspberry Pi OS Lite (Bookworm, no desktop)
- **Hardware**: RPi 3B or Zero 2W, Teensy 4.1 via USB serial

## Common Commands

```bash
# Run demo on Mac (no ECU needed)
make demo

# Run with real ECU
make run

# Sync to Pi
make sync PI_HOST=pi@<ip>

# Setup Pi (first time after sync)
make setup

# View Pi dashboard logs
make logs

# Restart dashboard on Pi
make restart
```

## Architecture

```
USB Serial (115200 baud)
  Teensy 4.1 (Dropbear v2 ECU) → RPi USB port
    → speeduino.py: sends 'A' command, parses 75-byte response
    → dashboard.py: multi-page Pygame renderer
    → fbcp-ili9341: mirrors HDMI framebuffer → SPI display at 60fps
```

## ECU Protocol

- Speeduino 'A' command returns 75+ bytes of real-time data
- Temperatures (CLT, IAT) are raw byte - 40 to get °C
- Multi-byte values are little-endian
- 'Q' command returns firmware signature for identification
- Byte offsets defined in `src/config.py` RT_MAP dict

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, Pygame loop, event handling |
| `src/dashboard.py` | Multi-page layout, page definitions (MainPage, TempBoostPage) |
| `src/gauges.py` | VerticalGauge, RPMBar, GearIndicator, WarningBar, HorizBar |
| `src/speeduino.py` | SpeeduinoReader (serial), DemoReader (simulated data) |
| `src/config.py` | RT_MAP byte offsets, GAUGE_DEFS ranges/thresholds |
| `src/colors.py` | TSDash neon green color scheme |
| `scripts/setup-pi.sh` | Pi setup: fbcp-ili9341 build, systemd services, config.txt |
| `Makefile` | demo, run, sync, setup, logs, restart |

## Display

- Resolution: 480x320 (matches Elegoo 3.5")
- Elegoo uses ILI9486 controller on SPI
- fbcp-ili9341 copies HDMI framebuffer → SPI at ~60fps
- config.txt forces HDMI to 480x320 via hdmi_cvt
- Pi OS Lite has fbtft/SPI kernel modules built-in

## Gauge Data Sources

Ranges and thresholds sourced from TSDash Speeduino definitions:
- RPM: 0-8000 (warn 6000, crit 7000)
- AFR: 10-20 (warn lean 16, crit 17, warn rich 13)
- CLT: -40 to 130°C (warn 93, crit 104)
- MAP: 0-255 kPa (warn 200, crit 245)
- Oil Pressure: 0-100 psi (warn low 25)
- Battery: 8-16V (warn low 12)

## Pages

- **Page 1 (MAIN)**: RPM bar, 7 vertical gauges (Boost, MAP, AFR, CLT, Oil, Batt, TPS), gear indicator, VE, bottom bars (ADV, IAT, PW)
- **Page 2 (TEMPS)**: 4 tall vertical gauges (CLT, Oil Temp, Boost, Oil Pressure)
- Click/tap anywhere or press Space/Right arrow to cycle pages
