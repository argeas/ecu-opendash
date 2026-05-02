"""CSV data logger for ECU channels."""
import csv
import os
import threading
import time
from datetime import datetime


class DataLogger:
    def __init__(self, log_dir="/opt/opendash/logs", interval=0.1, max_files=50):
        self.log_dir = log_dir
        self.interval = interval
        self.max_files = max_files
        self._running = False
        self._thread = None
        self._reader = None
        self._file = None
        self._writer = None
        self._columns = [
            "timestamp", "rpm", "map", "boost", "afr", "lambda", "clt", "iat",
            "tps", "advance", "pw1", "ve", "batteryv", "oilpressure", "gear",
            "baro", "accelenrich", "gammae", "rpmdot", "boosttarget", "boostduty",
        ]
        os.makedirs(log_dir, exist_ok=True)

    def start(self, reader):
        self._reader = reader
        self._running = True
        self._open_new_file()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"DataLogger started: {self._current_path}")

    def _open_new_file(self):
        if self._file:
            self._file.close()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_path = os.path.join(self.log_dir, f"log_{ts}.csv")
        self._file = open(self._current_path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self._columns, extrasaction="ignore")
        self._writer.writeheader()
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        files = sorted(
            [f for f in os.listdir(self.log_dir) if f.endswith(".csv")],
            key=lambda f: os.path.getmtime(os.path.join(self.log_dir, f)),
        )
        while len(files) > self.max_files:
            old = files.pop(0)
            os.remove(os.path.join(self.log_dir, old))

    def _loop(self):
        while self._running:
            if self._reader:
                data = self._reader.get_data()
                if data and data.get("rpm") is not None:
                    row = {"timestamp": datetime.now().isoformat()}
                    row.update(data)
                    self._writer.writerow(row)
                    self._file.flush()
            time.sleep(self.interval)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._file:
            self._file.close()

    @property
    def current_file(self):
        return self._current_path if hasattr(self, "_current_path") else None

    def list_logs(self):
        if not os.path.exists(self.log_dir):
            return []
        files = [f for f in os.listdir(self.log_dir) if f.endswith(".csv")]
        files.sort(reverse=True)
        return [
            {"name": f, "size": os.path.getsize(os.path.join(self.log_dir, f))}
            for f in files
        ]
