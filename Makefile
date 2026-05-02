.PHONY: demo run setup sync

# Run locally in demo mode (no ECU needed)
demo:
	cd src && python3 main.py --demo

# Run locally with real ECU
run:
	cd src && python3 main.py

# Sync to Pi
PI_HOST ?= pi@opendash.local
PI_DIR ?= /home/pi/ecu-opendash

sync:
	rsync -avz --exclude '__pycache__' --exclude '.git' \
		-e ssh \
		./ $(PI_HOST):$(PI_DIR)/

# Setup Pi (run after first sync)
setup:
	ssh $(PI_HOST) 'cd $(PI_DIR) && sudo bash scripts/setup-pi.sh'

# View Pi logs
logs:
	ssh $(PI_HOST) 'journalctl -u opendash -f'

# Restart dashboard on Pi
restart:
	ssh $(PI_HOST) 'sudo systemctl restart opendash'
