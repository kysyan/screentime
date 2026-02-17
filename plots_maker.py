import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.widgets import Button
from datetime import datetime, timedelta

BROWSERS = ["chrome", "firefox", "brave", "opera"]
BROWSER_SUFFIXES = ["- Google Chrome", "- Mozilla Firefox", "- Brave", "- Opera"]

def load_csv(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    return df

def clean_window_name(app_name, window_name):
    if not window_name or pd.isna(window_name):
        return ""
    if any(b in app_name.lower() for b in BROWSERS):
        for suffix in BROWSER_SUFFIXES:
            window_name = window_name.replace(suffix, "").strip()
        parts = [p.strip() for p in window_name.split(" - ") if len(p.strip()) > 2]
        return min(parts, key=len) if parts else window_name
    return window_name[:25] + "..." if len(window_name) > 25 else window_name

#TODO make an interactive function (timeline)

def draw_bar(df, ax):
    totals = df.groupby("app")["duration_seconds"].sum().sort_values(ascending=False) / 60
    totals.plot(kind="bar", ax=ax)
    ax.set_xlabel("App")
    ax.set_ylabel("Minutes")

def draw_hourly(df, ax):
    df = df.copy()
    df["hour"] = df["start"].dt.hour
    hourly = df.groupby("hour")["duration_seconds"].sum() / 60
    hourly.plot(kind="bar", ax=ax)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Minutes")


def draw_timeline(df):
    pass

def plot_all(df):
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.subplots_adjust(bottom=0.25)

    plots = ["bar", "timeline", "hourly"]
    titles = {"bar": "Time per App", "timeline": "App Timeline", "hourly": "Activity per Hour"}
    current = [0]
    state = {}

    def draw(index):
        ax.cla()
        # remove old toggle button if present
        if "toggle_ax" in state:
            state["toggle_ax"].remove()
            del state["toggle_ax"]
            del state["toggle_btn"]

        plot_name = plots[index]
        if plot_name == "bar":
            draw_bar(df, ax)
        elif plot_name == "timeline":
            draw_timeline(df, ax, fig, state)
        elif plot_name == "hourly":
            draw_hourly(df, ax)

        ax.set_title(f"{titles[plot_name]} ({index + 1}/{len(plots)})")
        fig.canvas.draw()

    def nextp(event):
        current[0] = (current[0] + 1) % len(plots)
        draw(current[0])

    def prevp(event):
        current[0] = (current[0] - 1) % len(plots)
        draw(current[0])

    axprev = plt.axes([0.3, 0.02, 0.15, 0.06])
    axnext = plt.axes([0.55, 0.02, 0.15, 0.06])
    bprev = Button(axprev, "← Previous")
    bnext = Button(axnext, "Next →")
    bprev.on_clicked(prevp)
    bnext.on_clicked(nextp)

    draw(0)
    plt.show()

def visualize(csv_path, plot_type=None):
    df = load_csv(csv_path)
    plot_all(df)


