# OpenDash — Plan

## Target Hardware

- **Pi**: Raspberry Pi 3B (or Zero 2W)
- **Display**: Elegoo 3.5" SPI (ILI9486 controller, 480x320, resistive touch)
- **ECU**: Dropbear v2 (Speeduino firmware) on Teensy 4.1
- **Connection**: USB serial from Teensy to Pi
- **Vehicle**: Land Rover Discovery 1, T16 Turbo engine

## Operating System

**Raspberry Pi OS Lite (Bookworm, 32-bit)**
- No desktop environment — boots to console
- Kernel includes fbtft and SPI modules for Elegoo display
- Minimal footprint, fast boot (~5-8 seconds to dashboard)
- Download: https://www.raspberrypi.com/software/operating-systems/

### Why Lite?
- No X11/Wayland overhead — Pygame renders directly to framebuffer
- Smaller image, fewer services, faster boot
- Less CPU/RAM wasted on desktop we'll never see

## Display Stack

```
Pi GPU renders to HDMI framebuffer (fb0) at 480x320
  → fbcp-ili9341 reads fb0, writes to SPI display (fb1) at ~60fps
  → Elegoo 3.5" shows the dashboard
```

### Elegoo 3.5" SPI Setup

1. **config.txt** additions:
   ```
   dtparam=spi=on
   hdmi_cvt=480 320 60 6 0 0 0
   hdmi_group=2
   hdmi_mode=87
   hdmi_force_hotplug=1
   ```

2. **fbcp-ili9341** (compiled on Pi):
   ```bash
   cmake -DILI9486=ON \
         -DGPIO_TFT_DATA_CONTROL=24 \
         -DGPIO_TFT_RESET_PIN=25 \
         -DSPI_BUS_CLOCK_DIVISOR=6 \
         ..
   ```

3. **Systemd service** starts fbcp before dashboard

### Elegoo 3.5" GPIO Pinout (ILI9486)

| Function | GPIO Pin |
|----------|----------|
| SPI MOSI | GPIO 10 (SPI0_MOSI) |
| SPI MISO | GPIO 9 (SPI0_MISO) |
| SPI SCLK | GPIO 11 (SPI0_SCLK) |
| SPI CS   | GPIO 8 (SPI_CE0) |
| DC       | GPIO 24 |
| RST      | GPIO 25 |
| Backlight| Always on (no GPIO control) |
| Touch CS | GPIO 7 (SPI_CE1) |
| Touch IRQ| GPIO 17 |

---

## Features — Built

### v0.1 (Current)

- [x] Speeduino serial protocol reader ('A' command, 75-byte parse)
- [x] Demo mode with simulated ECU data
- [x] Multi-page dashboard (click/tap to cycle)
- [x] Page 1 — Main: RPM bar, Boost, MAP, AFR, CLT, Oil, Batt, TPS, Gear, VE, ADV, IAT, PW
- [x] Page 2 — Temps: CLT, Oil Temp, Boost, Oil Pressure (full-height bars)
- [x] Warning system (two-stage: yellow warn, red critical)
- [x] TSDash neon green color scheme
- [x] Accurate gauge ranges from TSDash Speeduino definitions
- [x] Pre-cached static surfaces for max FPS
- [x] Pi setup script (fbcp-ili9341 build, systemd, config.txt)

## Features — Planned

### v0.2 — Pi Deployment

- [ ] Flash Pi OS Lite to SD card
- [ ] Run setup-pi.sh, verify Elegoo display works
- [ ] Test with real Dropbear v2 ECU via USB serial
- [ ] Tune serial timing and error recovery
- [ ] Boot time optimization (disable unnecessary services)

### v0.3 — Data Logging

- [ ] Log all ECU channels to CSV on Pi SD card
- [ ] Configurable log interval (default 100ms)
- [ ] Auto-rotate logs (keep last N hours)
- [ ] Log playback mode on Mac for analysis

### v0.4 — Additional Pages

- [ ] Fuel page: PW1, PW2, Duty Cycle, VE, Fuel Correction, Gamma Enrichment
- [ ] Ignition page: Advance, Dwell, Spark output, RPM Dot
- [ ] Diagnostics page: Sync status, Loop speed, Errors, Baro, Flex Fuel %
- [ ] Peak/min hold values per session

### v0.5 — Touch Input

- [ ] Touch support via XPT2046 (Elegoo resistive touch controller)
- [ ] Page switching via swipe left/right
- [ ] Long-press for settings overlay (brightness, units °C/°F)

### v0.6 — WiFi Features

- [ ] Web dashboard mirror (Flask/WebSocket, view from phone)
- [ ] OTA config updates via WiFi
- [ ] Live data API for TunerStudio remote connection

### Future Ideas

- [ ] Shift light (screen flash at configurable RPM)
- [ ] Lap timer (GPS module add-on)
- [ ] CAN bus direct mode (MCP2515 hat, bypass USB serial)
- [ ] Night mode (dimmed colors, reduced brightness)
- [ ] Custom page editor (JSON/YAML config for gauge layouts)
- [ ] Integration with TSDash web API as data source alternative
