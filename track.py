import sys
import time
import platform
import psutil
import os
import csv
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class AppTracker:
    current_app: str | None = None
    start_time: datetime | None = None
    csv_path: str = "data/activity.csv"
    system: str = field(default_factory=platform.system)

    def get_active_window(self):
        if self.system == "Windows":
            return self._get_window_windows()
        elif self.system == "Linux":
            return self._get_window_linux()
        return {"app_name": "Unknown", "window_name": "Unknown"}

    def _get_window_windows(self):
        import win32gui
        import win32process
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        return {
            "app_name": psutil.Process(pid).name(),
            "window_name": win32gui.GetWindowText(window)
        }
    

    def _get_window_linux(self):
        import subprocess
        try:
            window_id = subprocess.check_output(["xdotool", "getactivewindow"]).strip()
            window_name = subprocess.check_output(
                    ["xdotool", "getwindowname", window_id.decode()]).decode().strip()
            pid = subprocess.check_output(
                    ["xdotool", "getwindowpid", window_id.decode()]).decode().strip()
            with open(f"/proc/{pid}/comm") as f:
                app_name = f.read().strip()
            return {"app_name": app_name, "window_name": window_name}
        except Exception:
            return {"app_name": "Unknown", "window_name": "Unknown"}


    def start_tracking(self, duration: int):
        end_time = datetime.now() + timedelta(seconds=duration)
        current_window = None
        try:
            while datetime.now() < end_time:
                active = self.get_active_window()
                app, window = active["app_name"], active["window_name"]
                if (app, window) != current_window:
                    if self.start_time is not None and current_window is not None:
                        self.log_to_csv(*current_window, self.start_time, datetime.now())
                    current_window = (app, window)
                    self.start_time = datetime.now()
                remaining = (end_time - datetime.now()).seconds
                mins, secs = divmod(remaining, 60)
                print(f"\rTracking... {mins:02d}:{secs:02d} remaining", end="", flush=True)
                time.sleep(1)
        finally:
            print("\nTracking stopped.")
            if self.start_time is not None and current_window is not None:
                self.log_to_csv(*current_window, self.start_time, datetime.now())
            print("Generating plot...")
            self._plot()
            self._reset()

    def log_to_csv(self, app_name, window_name, start_time, end_time):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        file_exists = os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["app", "window", "start", "end", "duration_seconds"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "app": app_name,
                "window": window_name,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": round((end_time - start_time).total_seconds(), 2)
            })

    def _plot(self):
        from plots_maker import visualize
        visualize(self.csv_path)

    def _reset(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(self.csv_path, self.csv_path.replace(".csv", f"_{timestamp}.csv"))
        self.current_app = None
        self.start_time = None


def parse_duration(s):
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if s[-1] in units:
        return int(s[:-1]) * units[s[-1]]
    raise ValueError(f"Unknown duration format: {s}. Use s, m, h, or d (e.g. 30m, 2h)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from plots_maker import visualize
        visualize(sys.argv[1])
    else:
        duration = input("How long do you want to track? (30s, 10m, 2h, 1d, etc.): ")
        seconds = parse_duration(duration)
        tracker = AppTracker()
        print(f"Starting tracker on {tracker.system}...")
        tracker.start_tracking(duration=seconds)
