# ecu-opendash

Bare-metal car dashboard for Raspberry Pi with Elegoo 3.5" SPI display.

Built for Land Rover Discovery 1 with T16 Turbo running Dropbear v2 (Speeduino) ECU on Teensy 4.1.

## Hardware

- Raspberry Pi 3B / Zero 2W
- Elegoo 3.5" SPI display (ILI9486)
- Dropbear v2 ECU (Teensy 4.1) via USB serial

## Quick Start

```bash
# Run demo on Mac (no hardware needed)
make demo

# Sync to Pi and setup
make sync
make setup

# View logs
make logs
```

## Gauges

- RPM tachometer
- Gear indicator
- Boost/MAP
- AFR
- Coolant temperature
- Oil pressure
- Battery voltage
- TPS, VE, Ignition advance, IAT (bar gauges)
- Warning panel (overheat, low oil, low battery, lean/rich)
