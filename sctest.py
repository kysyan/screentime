from unittest.mock import patch, MagicMock
from datetime import datetime
from track import AppTracker

def test_log_to_csv():
    tracker = AppTracker()
    tracker.current_app = "chrome.exe"
    tracker.start_time = datetime(2024, 1, 1, 10, 0, 0)
    tracker.log_to_csv("chrome.exe", "Google Chrome", tracker.start_time, datetime(2024, 1, 1, 10, 5, 0))
    assert len(rows) == 1
    assert rows[0]["app"] == "chrome.exe"
    assert rows[0]["window"] == "Google Chrome"
    assert rows[0]["start"] == start.isoformat()
    assert rows[0]["end"] == end.isoformat()
    assert rows[0]["duration_seconds"] == "300.0"
    
    # cleanup
    os.remove("data/test_activity.csv")

def test_app_switch_logs():
    tracker = AppTracker()
    tracker.system = "Windows"
    with patch.object(tracker, "get_active_window_windows", return_value={"app_name": "chrome.exe", "window_name": "Google Chrome"}):
        window = tracker.get_active_window()
        assert window["app_name"] == "chrome.exe"
