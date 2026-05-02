# WiFi & Bluetooth Setup — Raspberry Pi OS Bookworm

## WiFi

Bookworm uses **NetworkManager** (not wpa_supplicant) for WiFi management.

### Enable WiFi radio

```bash
# Check radio status
sudo nmcli radio wifi

# Enable if disabled
sudo nmcli radio wifi on
```

### Scan for networks

```bash
sudo nmcli dev wifi rescan
sudo nmcli dev wifi list
```

### Connect to a network

```bash
sudo nmcli dev wifi connect 'SSID_NAME' password 'PASSWORD'
```

The connection is saved and will auto-connect on reboot.

### Check connection status

```bash
# Device status overview
sudo nmcli dev status

# WiFi IP address
ip addr show wlan0 | grep 'inet '

# Connection details
nmcli connection show 'SSID_NAME'
```

### Disconnect / forget a network

```bash
# Disconnect
sudo nmcli dev disconnect wlan0

# Delete saved connection
sudo nmcli connection delete 'SSID_NAME'
```

### Troubleshooting

```bash
# Check if wlan0 is up
ip link show wlan0

# Unblock WiFi if soft-blocked
sudo rfkill unblock wifi
sudo rfkill list

# Check firmware loading
sudo dmesg | grep -i 'brcm\|wifi\|wlan'
```

### wpa_supplicant.conf (legacy — does NOT work on Bookworm)

Placing `wpa_supplicant.conf` on the boot partition does not configure WiFi on Bookworm. Use `nmcli` after first boot instead.

---

## Bluetooth

Bookworm uses **BlueZ** via `bluetoothctl`.

### Check Bluetooth status

```bash
sudo bluetoothctl show
```

Key fields:
- `Powered: yes` — controller is on
- `Discovering: yes/no` — scanning state

### Scan for devices

```bash
sudo bluetoothctl scan on
# Wait a few seconds, then:
sudo bluetoothctl scan off

# List discovered devices
sudo bluetoothctl devices
```

### Pair a device

```bash
# Start interactive mode
sudo bluetoothctl

# Then inside bluetoothctl:
scan on
# Wait for device to appear
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```

### Auto-connect on boot

Once a device is paired and trusted, it will auto-connect on boot:

```bash
sudo bluetoothctl trust XX:XX:XX:XX:XX:XX
```

### Check connected devices

```bash
sudo bluetoothctl devices Connected
```

### Remove a paired device

```bash
sudo bluetoothctl remove XX:XX:XX:XX:XX:XX
```

### Troubleshooting

```bash
# Check Bluetooth service
sudo systemctl status bluetooth

# Check rfkill
sudo rfkill list

# Check kernel logs
sudo dmesg | grep -i bluetooth

# Restart Bluetooth
sudo systemctl restart bluetooth
```

---

## OpenDash Pi Summary

| Interface | IP | Method |
|---|---|---|
| Ethernet | 192.168.1.29 | DHCP (auto) |
| WiFi | 192.168.1.30 | NetworkManager (`nmcli`) |
| Bluetooth | B8:27:EB:A2:99:BA | BlueZ (`bluetoothctl`) |

### SSH access

```bash
# Via Ethernet
ssh pi@192.168.1.29

# Via WiFi
ssh pi@192.168.1.30

# Via hostname (if mDNS works)
ssh pi@opendash.local
```
