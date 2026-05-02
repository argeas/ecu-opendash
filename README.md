# ecu-opendash

Bare-metal car dashboard for Raspberry Pi with Elegoo 3.5" SPI display.

Built for Land Rover Discovery 1 with T16 Turbo running Dropbear v2 (Speeduino) ECU on Teensy 4.1.

## Hardware

- Raspberry Pi 3B / Zero 2W
- Elegoo 3.5" SPI display (ILI9486, 480x320)
- Dropbear v2 ECU (Teensy 4.1) via USB serial

## OS

**Raspberry Pi OS Lite (Bookworm, 32-bit)** — no desktop, boots straight into dashboard.

The display stack uses `fbcp-ili9341` to mirror the HDMI framebuffer to the SPI display at ~60fps. Pi OS Lite includes the necessary SPI/fbtft kernel modules out of the box.

## Quick Start

```bash
# Run demo on Mac (no hardware needed)
pip install pygame-ce pyserial
make demo

# Deploy to Pi
make sync PI_HOST=pi@<pi-ip>
make setup
# Reboot Pi — dashboard auto-starts
```

## Pages

**Page 1 — Main**: RPM bar, Boost, MAP, AFR, CLT, Oil Pressure, Battery, TPS, Gear, VE, Ignition Advance, IAT, Pulse Width

**Page 2 — Temps**: Coolant Temp, Oil Temp, Boost, Oil Pressure (full-height bars)

Click/tap anywhere or press Space to switch pages.

## Gauges

| Channel | Range | Warning | Critical |
|---------|-------|---------|----------|
| RPM | 0-8000 | 6000 | 7000 |
| AFR | 10-20 | <13 / >16 | >17 |
| CLT | -40–130°C | 93°C | 104°C |
| MAP | 0-255 kPa | 200 | 245 |
| Oil Pressure | 0-100 psi | <25 | — |
| Battery | 8-16V | <12V | — |
| TPS | 0-100% | 90% | — |

Ranges and thresholds sourced from TSDash Speeduino definitions.

## Architecture

```
Teensy 4.1 (Dropbear v2) --USB Serial 115200--> RPi
  → speeduino.py: 'A' command, parse 75-byte response
  → dashboard.py: multi-page Pygame renderer (direct framebuffer)
  → fbcp-ili9341: HDMI fb0 → SPI display at 60fps
```

## Project Structure

```
src/
  main.py          — Entry point, Pygame loop
  dashboard.py     — Multi-page layout definitions
  gauges.py        — Gauge components (VerticalGauge, RPMBar, etc.)
  speeduino.py     — Serial protocol reader + demo simulator
  config.py        — Byte offsets, ranges, thresholds
  colors.py        — TSDash neon green color scheme
scripts/
  setup-pi.sh      — Pi setup (fbcp build, systemd, display config)
```

## License

MIT
