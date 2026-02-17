import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import timedelta
from matplotlib.patches import Patch
from matplotlib.widgets import Button


BROWSERS = ["chrome", "firefox", "edge", "brave", "opera"]
BROWSER_SUFFIXES = [
    "- Google Chrome", "- Mozilla Firefox",
    "- Microsoft Edge", "- Brave", "- Opera"
]


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
    return window_name[:30] + "..." if len(window_name) > 30 else window_name


# draw functions

def draw_bar(df, ax):
    totals = df.groupby("app")["duration_seconds"].sum().sort_values(ascending=False) / 60
    colors = [f"C{i}" for i in range(len(totals))]
    totals.plot(kind="bar", ax=ax, color=colors)
    ax.set_xlabel("App")
    ax.set_ylabel("Minutes")

def draw_hourly(df, ax):
    df = df.copy()
    df["hour"] = df["start"].dt.hour
    hourly = df.groupby("hour")["duration_seconds"].sum() / 60
    hourly.plot(kind="bar", ax=ax)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Minutes")


def draw_timeline(df, ax, fig, state):
    df = df.copy()
    min_time = df["start"].min()
    df["display"] = df.apply(lambda r: clean_window_name(r["app"], r["window"]), axis=1)

    # color maps
    app_colors = {app: f"C{i}" for i, app in enumerate(df["app"].unique())}
    unique_windows = df.groupby(["app", "display"]).size().reset_index()[["app", "display"]]
    window_colors = {(r["app"], r["display"]): f"C{i}" for i, r in unique_windows.iterrows()}

    y_positions = {app: i for i, app in enumerate(df["app"].unique())}

    # draw bars
    bars = []
    for _, row in df.iterrows():
        start_min = (row["start"] - min_time).total_seconds() / 60
        duration_min = (row["end"] - row["start"]).total_seconds() / 60
        bar = ax.barh(y_positions[row["app"]], duration_min, left=start_min,
                      color=app_colors[row["app"]], edgecolor="white", linewidth=0.5)
        bars.append((bar[0], row["app"], row["display"]))

    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, _: (min_time + timedelta(minutes=x)).strftime("%H:%M")
    ))
    ax.set_xlabel("Time")

    # legends
    simple_legend = [Patch(facecolor=app_colors[app], label=app) for app in app_colors]
    detailed_legend = [Patch(facecolor=window_colors[(a, w)], label=f"{a}: {w}") for a, w in window_colors]
    legend_container = [ax.legend(handles=simple_legend, loc="upper center",
                                  bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)]

    # toggle button
    ax_toggle = fig.add_axes([0.88, 0.41, 0.08, 0.04])
    btn_toggle = Button(ax_toggle, "Details")
    state["toggle_ax"] = ax_toggle
    state["toggle_btn"] = btn_toggle

    detailed = [False]

    def toggle(event):
        detailed[0] = not detailed[0]
        colors = window_colors if detailed[0] else app_colors
        legend = detailed_legend if detailed[0] else simple_legend
        ncol = 2 if detailed[0] else 3
        fontsize = 7 if detailed[0] else 8

        for bar, app, display in bars:
            bar.set_color(window_colors[(app, display)] if detailed[0] else app_colors[app])

        legend_container[0].remove()
        legend_container[0] = ax.legend(handles=legend, loc="upper center",
                                        bbox_to_anchor=(0.5, -0.15), ncol=ncol, fontsize=fontsize)
        btn_toggle.label.set_text("Simple" if detailed[0] else "Details")
        fig.canvas.draw()

    btn_toggle.on_clicked(toggle)


# --- main plot controller ---

PLOTS = ["bar", "timeline", "hourly"]
TITLES = {"bar": "Time per App", "timeline": "App Timeline", "hourly": "Activity per Hour"}


def plot_all(df):
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.subplots_adjust(right=0.85, bottom=0.2)

    current = [0]
    state = {}

    def draw(index):
        try:
            fig.canvas.release_mouse(ax)
        except Exception:
            pass

        ax.cla()

        if "toggle_ax" in state:
            try:
                state["toggle_ax"].remove()
            except Exception:
                pass
            state.clear()

        plot_name = PLOTS[index]
        if plot_name == "bar":
            draw_bar(df, ax)
        elif plot_name == "timeline":
            draw_timeline(df, ax, fig, state)
        elif plot_name == "hourly":
            draw_hourly(df, ax)

        ax.set_title(f"{TITLES[plot_name]}  ({index + 1}/{len(PLOTS)})")
        fig.canvas.draw()

    def next_plot(event):
        current[0] = (current[0] + 1) % len(PLOTS)
        draw(current[0])

    def prev_plot(event):
        current[0] = (current[0] - 1) % len(PLOTS)
        draw(current[0])

    ax_prev = fig.add_axes([0.88, 0.55, 0.08, 0.04])
    ax_next = fig.add_axes([0.88, 0.48, 0.08, 0.04])
    btn_prev = Button(ax_prev, "<< Prev")
    btn_next = Button(ax_next, "Next >>")
    btn_prev.on_clicked(prev_plot)
    btn_next.on_clicked(next_plot)

    draw(0)
    plt.show()


def visualize(csv_path, plot_type=None):
    plot_all(load_csv(csv_path))
