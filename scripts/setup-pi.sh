#!/bin/bash
set -e

echo "=== OpenDash Pi Setup ==="

# Update system
sudo apt-get update
sudo apt-get install -y \
    python3-pygame \
    python3-serial \
    python3-pip \
    cmake \
    git \
    build-essential \
    fbset

# Build fbcp-ili9341 for Elegoo 3.5" (ILI9486)
echo "=== Building fbcp-ili9341 ==="
cd /tmp
if [ ! -d "fbcp-ili9341" ]; then
    git clone https://github.com/juj/fbcp-ili9341.git
fi
cd fbcp-ili9341
mkdir -p build && cd build
cmake \
    -DILI9486=ON \
    -DGPIO_TFT_DATA_CONTROL=24 \
    -DGPIO_TFT_RESET_PIN=25 \
    -DSPI_BUS_CLOCK_DIVISOR=6 \
    -DSTATISTICS=0 \
    -DDISPLAY_ROTATE_180_DEGREES=OFF \
    ..
make -j$(nproc)
sudo cp fbcp-ili9341 /usr/local/bin/

# Create fbcp systemd service
echo "=== Setting up fbcp service ==="
sudo tee /etc/systemd/system/fbcp.service > /dev/null <<'UNIT'
[Unit]
Description=Framebuffer copy for SPI display
After=local-fs.target

[Service]
Type=simple
ExecStart=/usr/local/bin/fbcp-ili9341
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl enable fbcp.service

# Setup OpenDash
echo "=== Setting up OpenDash ==="
sudo mkdir -p /opt/opendash
sudo cp -r /home/pi/ecu-opendash/src/* /opt/opendash/

sudo tee /etc/systemd/system/opendash.service > /dev/null <<'UNIT'
[Unit]
Description=OpenDash ECU Dashboard
After=fbcp.service
Wants=fbcp.service

[Service]
Type=simple
User=pi
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
ExecStart=/usr/bin/python3 /opt/opendash/main.py --fullscreen
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl enable opendash.service

# Add config.txt lines for display
echo "=== Display config ==="
if ! grep -q "hdmi_cvt=480 320" /boot/config.txt 2>/dev/null; then
    sudo tee -a /boot/config.txt > /dev/null <<'CONF'

# OpenDash - Elegoo 3.5" SPI display
dtparam=spi=on
hdmi_cvt=480 320 60 6 0 0 0
hdmi_group=2
hdmi_mode=87
hdmi_force_hotplug=1
CONF
fi

echo ""
echo "=== Setup complete ==="
echo "Reboot to start: sudo reboot"
echo "Dashboard will auto-start on boot."
echo ""
echo "To run in demo mode: python3 /opt/opendash/main.py --demo"
echo "To view logs: journalctl -u opendash -f"
