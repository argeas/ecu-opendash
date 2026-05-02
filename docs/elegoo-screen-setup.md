# Elegoo 3.5" SPI Display Setup — Raspberry Pi OS Bookworm

## Hardware

- **Display**: Elegoo 3.5" TFT LCD (480x320, resistive touch)
- **Controller**: ILI9486
- **Touch controller**: XPT2046
- **Interface**: SPI (not HDMI)

## GPIO Pinout

| Function | GPIO Pin |
|----------|----------|
| SPI MOSI | GPIO 10 (SPI0_MOSI) |
| SPI MISO | GPIO 9 (SPI0_MISO) |
| SPI SCLK | GPIO 11 (SPI0_SCLK) |
| SPI CS | GPIO 8 (SPI_CE0) |
| DC (Data/Command) | GPIO 24 |
| RST (Reset) | GPIO 25 |
| Backlight | Always on (no GPIO control) |
| Touch CS | GPIO 7 (SPI_CE1) |
| Touch IRQ | GPIO 17 |

## Bookworm Setup (DRM mode — recommended)

On Raspberry Pi OS Bookworm, the `piscreen` overlay with `drm` flag is the correct approach. No third-party driver scripts (LCD-show, goodtft, etc.) are needed.

### config.txt

Add to `/boot/firmware/config.txt` under `[all]`:

```
dtparam=spi=on
dtoverlay=piscreen,drm,speed=18000000
hdmi_force_hotplug=1
```

That's it. Reboot and the display becomes a proper DRM output device.

### Touch calibration

If touch axes are inverted or swapped, add parameters:

```
dtoverlay=piscreen,drm,speed=18000000,invx,invy,swapxy
```

Available flags: `invx`, `invy`, `swapxy`. Adjust to match your orientation.

### SDL2 video driver

Applications using SDL2 (Pygame, etc.) should use the `kmsdrm` driver:

```
export SDL_VIDEODRIVER=kmsdrm
```

Or in a systemd service:

```ini
Environment=SDL_VIDEODRIVER=kmsdrm
```

## What does NOT work on Bookworm

### Legacy fbcp-ili9341

`fbcp-ili9341` mirrors the HDMI framebuffer to SPI. On Bookworm:
- Requires disabling `dtoverlay=vc4-kms-v3d` (KMS driver)
- Without KMS, SDL2 has no usable video backend (`fbcon`, `kmsdrm`, `directfb` all fail)
- The `fbcon` kernel module is not available in Bookworm's default kernel
- **Verdict**: dead end on Bookworm

### Legacy fbtft without drm flag

```
dtoverlay=piscreen,speed=16000000,rotate=270
```

This creates a legacy `/dev/fb1` framebuffer, but SDL2/Pygame on Bookworm can't render to it without `fbcon` support.

### goodtft/LCD-show scripts

- Designed for Bullseye and earlier
- Hardcoded paths to `/boot/config.txt` (Bookworm uses `/boot/firmware/config.txt`)
- Modifies system files in ways that break Bookworm
- **Do not use on Bookworm**

## SPI speed notes

| Speed | Result |
|-------|--------|
| 16000000 (16 MHz) | Conservative, stable |
| 18000000 (18 MHz) | Recommended for Elegoo |
| 32000000 (32 MHz) | May cause artifacts on some units |

## Driver sources

The Elegoo 3.5" is electrically identical to the Waveshare RPi LCD(A) 3.5". The `piscreen` overlay in the Pi kernel is compatible with both.

## References

- [RPi Forum: LCD 3.5 TFT on Bookworm (SOLVED)](https://forums.raspberrypi.com/viewtopic.php?t=382506)
- [Waveshare 3.5" Wiki](https://www.waveshare.com/wiki/3.5inch_RPi_LCD_(A))
- [LCD Wiki 3.5" Display](https://www.lcdwiki.com/3.5inch_RPi_Display)
- [Elegoo official tutorial](https://www.elegoo.com/blogs/arduino-projects/elegoo-3-5-inch-touch-screen-for-raspberry-pi-manual)
- [goodtft/LCD-show (legacy, not for Bookworm)](https://github.com/goodtft/LCD-show)
