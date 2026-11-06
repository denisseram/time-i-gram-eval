#!/usr/bin/env python3
"""Dot plot of specification size per task and tool, hollow dots for runs that missed a requirement.

  python3 scripts/plot_spec_size.py [runs.csv]
      default CSV: results/effort_per_run.csv (written by scripts/effort_stats.py)
      -> docs/paper-figures/evaluation/spec-size-by-task.{pdf,png}       (3.5 in, one column)
         docs/paper-figures/evaluation/spec-size-by-task-7in.{pdf,png}   (7 in, full width)

One dot per run; a short line in the tool color marks the median of the 3 runs (no boxes or means: n = 3).
Filled = score_pct 100, hollow = not all requirements met. Dots of one group that would overlap on screen are
spread horizontally by at most +-0.04 task units; others stay on the group's center.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/effort_per_run.csv"
OUT = ROOT / "docs/paper-figures/evaluation"

TASKS = ["E1", "E2", "E3", "E4", "E5"]
TOOLS = ["d3", "vega-lite", "ggtime", "time-i-gram"]
LABEL = {"d3": "D3", "vega-lite": "Vega-Lite", "ggtime": "ggtime", "time-i-gram": "time-i-gram"}
COLOR = {"d3": "#E69F00", "vega-lite": "#0072B2", "ggtime": "#009E73", "time-i-gram": "#D55E00"}  # Okabe-Ito
DODGE = 0.2                                   # horizontal distance between tools within a task
OFFSET = dict(zip(TOOLS, (np.arange(len(TOOLS)) - (len(TOOLS) - 1) / 2) * DODGE))
JITTER = 0.04                                 # max horizontal spread for overlapping dots (task units)
YTICKS = [2000, 5000, 10000, 20000]
INK, MUTED, GRID, SEP = "#1f1f1f", "#555555", "#e2e2e2", "#ececec"
MARKER_S = 15                                 # scatter size (pt^2): ~3.9 pt diameter
EDGE_W = 0.9

RC = {
    "font.family": "Helvetica", "font.size": 8, "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 0, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42, "ps.fonttype": 42,
}


def spread(ax, x0, ys):
    """x positions for one group: dots closer than one marker diameter on screen are spread within +-JITTER."""
    diam_px = np.sqrt(MARKER_S) * ax.figure.dpi / 72 + EDGE_W
    y_px = ax.transData.transform(np.column_stack([np.full(len(ys), x0), ys]))[:, 1]
    order = np.argsort(y_px)
    xs = np.full(len(ys), float(x0))
    cluster = [order[0]]
    for prev, cur in zip(order[:-1], order[1:]):
        if y_px[cur] - y_px[prev] < diam_px:
            cluster.append(cur)
            continue
        if len(cluster) > 1:
            xs[cluster] = x0 + np.linspace(-JITTER, JITTER, len(cluster))
        cluster = [cur]
    if len(cluster) > 1:
        xs[cluster] = x0 + np.linspace(-JITTER, JITTER, len(cluster))
    return xs


def plot(df, width, height, stem):
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(width, height), layout="constrained")
        ax.set_yscale("log")
        lo, hi = df.spec_chars.min(), df.spec_chars.max()
        ax.set_ylim(min(lo / 1.15, YTICKS[0] / 1.1), max(hi * 1.15, YTICKS[-1] * 1.1))
        ax.set_xlim(-0.5, len(TASKS) - 0.5)
        ax.yaxis.set_major_locator(FixedLocator(YTICKS))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.set_xticks(range(len(TASKS)), TASKS)
        ax.grid(axis="y", which="major", color=GRID, lw=0.5)
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)
        for b in np.arange(0.5, len(TASKS) - 0.5):
            ax.axvline(b, color=SEP, lw=0.6, zorder=0)
        ax.set_xlabel("Task")
        ax.set_ylabel("Specification size\n(characters, log scale)")  # two lines: fits a 2.2 in tall axis
        fig.canvas.draw()  # final layout, so overlap is judged in real screen distances

        for i, task in enumerate(TASKS):
            for tool in TOOLS:
                g = df[(df.task == task) & (df.tool == tool)].sort_values("repeat")
                x0 = i + OFFSET[tool]
                med = g.spec_chars.median()
                ax.plot([x0 - DODGE * 0.42, x0 + DODGE * 0.42], [med, med], color=COLOR[tool], lw=1.3,
                        solid_capstyle="butt", zorder=2)
                xs = spread(ax, x0, g.spec_chars.to_numpy(float))
                full = (g.score_pct >= 100).to_numpy()
                ax.scatter(xs[full], g.spec_chars[full], s=MARKER_S, facecolor=COLOR[tool],
                           edgecolor=COLOR[tool], linewidth=EDGE_W, zorder=3)
                ax.scatter(xs[~full], g.spec_chars[~full], s=MARKER_S, facecolor="white",
                           edgecolor=COLOR[tool], linewidth=EDGE_W, zorder=3)

        ms = np.sqrt(MARKER_S)
        handles = [Line2D([], [], marker="o", ls="none", markersize=ms, markerfacecolor=COLOR[t],
                          markeredgecolor=COLOR[t], markeredgewidth=EDGE_W, label=LABEL[t]) for t in TOOLS]
        handles.append(Line2D([], [], marker="o", ls="none", markersize=ms, markerfacecolor="white",
                              markeredgecolor=MUTED, markeredgewidth=EDGE_W, label="not all requirements met"))
        fig.legend(handles=handles, loc="outside upper center", ncol=len(handles), frameon=False,
                   handlelength=0.6, handletextpad=0.2, columnspacing=0.6 if width < 5 else 1.0,
                   borderaxespad=0.1)
        fig.savefig(stem.with_suffix(".pdf"))
        fig.savefig(stem.with_suffix(".png"), dpi=300)
        plt.close(fig)


def main():
    df = pd.read_csv(CSV)
    need = {"task", "tool", "repeat", "spec_chars", "score_pct"}
    if missing := need - set(df.columns):
        sys.exit(f"{CSV} lacks columns {sorted(missing)}")
    from matplotlib import font_manager
    try:  # Helvetica is a system font (macOS); stop rather than fall back silently
        font_manager.findfont(font_manager.FontProperties(family="Helvetica"), fallback_to_default=False)
    except ValueError:
        sys.exit("Helvetica not found by matplotlib; install it or change RC['font.family']")
    OUT.mkdir(parents=True, exist_ok=True)
    plot(df, 3.5, 2.2, OUT / "spec-size-by-task")
    plot(df, 7.0, 2.2, OUT / "spec-size-by-task-7in")

    med = df.pivot_table(index="task", columns="tool", values="spec_chars", aggfunc="median")[TOOLS]
    hollow = (df[df.score_pct < 100].groupby(["task", "tool"]).size().unstack(fill_value=0)
              .reindex(index=TASKS, columns=TOOLS, fill_value=0))
    table = med.map(lambda v: f"{v:,.0f}") + hollow.map(lambda n: f"  ({n} hollow)" if n else "")
    table.columns = [LABEL[t] for t in TOOLS]
    print(f"Median spec_chars per task and tool (n = 3 each; from {CSV.name}):\n")
    print(table.to_string())
    print(f"\nWrote {OUT.relative_to(ROOT)}/spec-size-by-task{{,-7in}}.{{pdf,png}}")


if __name__ == "__main__":
    main()
