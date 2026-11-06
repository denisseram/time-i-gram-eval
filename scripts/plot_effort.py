#!/usr/bin/env python3
"""Paper figures of the effort measures. Reads results/effort_per_run.csv (from scripts/effort_stats.py).

  python3 scripts/plot_effort.py      -> docs/paper-figures/evaluation/<measure>_<plot>_<pertask|overall>.{pdf,png}

Plots per measure: violin, box, raincloud (half violin + narrow box), dots (runs + mean/median bars only);
each per task (x = task, tools dodged) and overall (x = tool, 15 runs each).

Violins are drawn here, not by seaborn, so that halves, boxes, dots and markers share exact positions: Gaussian
KDE with Scott's bandwidth (seaborn's default), cut = 0 (never beyond the observed min/max), computed in log10
space on a log axis, every violin scaled to the same maximum width. With 3 runs per task × tool the per-task
violins are mostly smoothing; the dots plot is the plain alternative.

Font: Roboto from google/fonts (pinned commit, sha256-checked), instanced to static Regular/Bold with fontTools
into scripts/.fonts/ (git-ignored); the script stops if any PDF embeds a font other than Roboto.
"""
import hashlib
import re
import sys
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "results/effort_per_run.csv"
OUT = ROOT / "docs/paper-figures/evaluation"
FONT_DIR = ROOT / "scripts/.fonts"
FONT_COMMIT = "24ddc1f324cac5d9f5aedca126d298f56e3f1640"
FONT_URL = f"https://raw.githubusercontent.com/google/fonts/{FONT_COMMIT}/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf"
FONT_SHA256 = "d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134"

TOOLS = ["d3", "vega-lite", "ggtime", "time-i-gram"]
LABEL = {"d3": "D3", "vega-lite": "Vega-Lite", "ggtime": "ggtime", "time-i-gram": "time-i-gram"}
COLOR = {"d3": "#E69F00", "vega-lite": "#0072B2", "ggtime": "#009E73", "time-i-gram": "#D55E00"}  # Okabe-Ito
TASKS = ["E1", "E2", "E3", "E4", "E5"]
INK, MUTED, GRID = "#1f1f1f", "#5c5c5c", "#e3e3e3"

# measure -> axis title; log axis is decided from the data (max/min > 10), and only for chars and tokens
MEASURES = {"spec_chars": "Specification size (characters)", "output_tokens": "Output tokens",
            "wall_min": "Wall time (min)", "turns": "Turns"}
LOG_CANDIDATES = {"spec_chars", "output_tokens"}
PLOTS = ["violin", "box", "raincloud", "dots"]
WIDTH = {"pertask": 7.0, "overall": 3.5}
HEIGHT = 2.6
SEED = 20261106


# ------------------------------------------------------------------------------------------ font

def setup_font():
    regular, bold = FONT_DIR / "Roboto-Regular.ttf", FONT_DIR / "Roboto-Bold.ttf"
    if not (regular.exists() and bold.exists()):
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        vf = FONT_DIR / "Roboto-VF.ttf"
        if not vf.exists():
            print("downloading Roboto from google/fonts ...")
            urllib.request.urlretrieve(FONT_URL, vf)
        if hashlib.sha256(vf.read_bytes()).hexdigest() != FONT_SHA256:
            sys.exit(f"{vf} does not match the pinned sha256; delete it and re-run")
        from fontTools.ttLib import TTFont
        from fontTools.varLib.instancer import instantiateVariableFont
        for path, wght in [(regular, 400), (bold, 700)]:
            inst = instantiateVariableFont(TTFont(vf), {"wght": wght, "wdth": 100}, updateFontNames=True)
            inst.save(path)
    for p in (regular, bold):
        font_manager.fontManager.addfont(str(p))
    found = font_manager.findfont(font_manager.FontProperties(family="Roboto"), fallback_to_default=False)
    found_bold = font_manager.findfont(font_manager.FontProperties(family="Roboto", weight="bold"),
                                       fallback_to_default=False)
    if Path(found) != regular or Path(found_bold) != bold:
        sys.exit(f"Roboto not resolved to the instanced files: {found}, {found_bold}")
    return regular


def style():
    sns.set_theme(style="ticks", rc={
        "font.family": "Roboto", "font.size": 8, "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
        "ytick.color": MUTED, "text.color": INK, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
        "ytick.major.width": 0.6, "ytick.minor.width": 0.4, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "ytick.minor.size": 1.5, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.5,
        "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
    })


# ---------------------------------------------------------------------------------------- drawing

def kde_shape(values, log, n=200):
    """(y grid, density scaled to max 1) between min and max; None if fewer than 2 distinct values."""
    v = np.log10(values) if log else np.asarray(values, float)
    if len(np.unique(v)) < 2:
        return None
    grid = np.linspace(v.min(), v.max(), n)
    dens = gaussian_kde(v, bw_method="scott")(grid)
    return (10 ** grid if log else grid), dens / dens.max()


def violin(ax, x, values, color, half_width, log, side="both"):
    shape = kde_shape(values, log)
    if shape is None:
        return
    y, d = shape
    left = x - d * half_width if side in ("both", "left") else np.full_like(d, x)
    right = x + d * half_width if side in ("both", "right") else np.full_like(d, x)
    ax.fill_betweenx(y, left, right, color=color, alpha=0.32, lw=0, zorder=1)
    ax.plot(left, y, color=color, lw=0.8, zorder=1.1) if side != "right" else None
    ax.plot(right, y, color=color, lw=0.8, zorder=1.1) if side != "left" else None


def box(ax, x, values, color, width):
    bp = ax.boxplot([values], positions=[x], widths=width, whis=1.5, showfliers=False, patch_artist=True,
                    manage_ticks=False, zorder=2,
                    boxprops=dict(facecolor=matplotlib.colors.to_rgba(color, 0.32), edgecolor=INK, lw=0.7),
                    whiskerprops=dict(color=INK, lw=0.7), capprops=dict(color=INK, lw=0.7),
                    medianprops=dict(color="black", lw=1.4, solid_capstyle="butt"))
    return bp


def dots(ax, x, values, color, jitter, rng, size):
    xs = x + rng.uniform(-jitter, jitter, len(values))
    ax.scatter(xs, values, s=size, color=color, edgecolor="#222222", linewidth=0.5, zorder=3)


def mean_median(ax, x, values, half, median=True, mean=True):
    if median:
        ax.plot([x - half, x + half], [np.median(values)] * 2, color="black", lw=1.4, solid_capstyle="butt",
                zorder=4)
    if mean:
        ax.scatter([x], [np.mean(values)], marker="D", s=14, color="white", edgecolor="black", linewidth=0.7,
                   zorder=5)


def draw_cell(ax, plot, x, values, color, slot, log, rng, n_large):
    """One task × tool (or one tool overall) at x; slot = width available for it."""
    size = 9 if not n_large else 11
    if plot == "violin":
        violin(ax, x, values, color, slot * 0.45, log)
        dots(ax, x, values, color, slot * 0.12, rng, size)
        mean_median(ax, x, values, slot * 0.28)
    elif plot == "box":
        box(ax, x, values, color, slot * 0.6)
        dots(ax, x, values, color, slot * 0.14, rng, size)
        mean_median(ax, x, values, 0, median=False)  # the box draws the median
    elif plot == "raincloud":
        violin(ax, x - slot * 0.02, values, color, slot * 0.44, log, side="left")
        bx = x + slot * 0.13
        box(ax, bx, values, color, slot * 0.14)
        dots(ax, x + slot * 0.34, values, color, slot * 0.06, rng, size)
        mean_median(ax, bx, values, 0, median=False)  # median = the box's line, mean on the box
    elif plot == "dots":
        dots(ax, x, values, color, slot * 0.14, rng, size)
        mean_median(ax, x, values, slot * 0.3)


def axis_format(ax, col, log, values):
    if log:
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.set_minor_formatter(NullFormatter())
        lo, hi = values.min(), values.max()
        ax.set_ylim(lo / 1.15, hi * 1.15)
    else:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 1000 or v == int(v)
                                                   else f"{v:g}"))
        top = values.max()
        ax.set_ylim(0, top * 1.06)
    label = MEASURES[col]
    if log:
        label = label[:-1] + ", log scale)" if label.endswith(")") else label + " (log scale)"
    ax.set_ylabel(label)


def legend(fig, plot, overall):
    marks = [Line2D([], [], marker="D", ls="none", markersize=4, markerfacecolor="white",
                    markeredgecolor="black", markeredgewidth=0.7, label="Mean")]
    marks.append(Line2D([], [], color="black", lw=1.4, label="Median"))
    if plot in ("box", "raincloud"):
        marks[-1].set_label("Median (box: IQR, whiskers 1.5 IQR)" if not overall else "Median; box = IQR")
    runs = Line2D([], [], marker="o", ls="none", markersize=3.6, markerfacecolor="#bdbdbd",
                  markeredgecolor="#222222", markeredgewidth=0.5, label="One run")
    tools = [] if overall else [Patch(facecolor=COLOR[t], edgecolor="none", label=LABEL[t]) for t in TOOLS]
    handles = tools + [runs] + marks
    fig.legend(handles=handles, loc="outside upper center", ncol=len(handles) if not overall else 3,
               frameon=False, handlelength=1.4, handletextpad=0.5, columnspacing=1.2, borderaxespad=0.2)


def figure(df, col, plot, scope, log):
    rng = np.random.default_rng(SEED)
    fig, ax = plt.subplots(figsize=(WIDTH[scope], HEIGHT), layout="constrained")
    if scope == "pertask":
        slot, offsets = 0.2, np.array([-0.3, -0.1, 0.1, 0.3])
        for i, task in enumerate(TASKS):
            for off, tool in zip(offsets, TOOLS):
                v = df.loc[(df.task == task) & (df.tool == tool), col].to_numpy(float)
                draw_cell(ax, plot, i + off, v, COLOR[tool], slot, log, rng, False)
        ax.set_xticks(range(len(TASKS)), TASKS)
        ax.set_xlim(-0.5, len(TASKS) - 0.5)
        ax.set_xlabel("Task")
    else:
        slot = 0.8
        for i, tool in enumerate(TOOLS):
            v = df.loc[df.tool == tool, col].to_numpy(float)
            draw_cell(ax, plot, i, v, COLOR[tool], slot, log, rng, True)
        ax.set_xticks(range(len(TOOLS)), [LABEL[t] for t in TOOLS])
        ax.set_xlim(-0.55, len(TOOLS) - 0.45)
        ax.set_xlabel("Tool")
    ax.tick_params(axis="x", length=0)
    axis_format(ax, col, log, df[col])
    legend(fig, plot, scope == "overall")
    stem = OUT / f"{col.replace('spec_chars', 'characters')}_{plot}_{scope}"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    plt.close(fig)
    return stem


def pdf_fonts(path):
    return set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-_.]+)", path.read_bytes()))


def main():
    regular = setup_font()
    style()
    df = pd.read_csv(CSV)
    OUT.mkdir(parents=True, exist_ok=True)
    stems = []
    for col in MEASURES:
        span = df[col].max() / df[col].min()
        log = col in LOG_CANDIDATES and span > 10
        print(f"{col}: max/min = {span:.1f} -> {'log' if log else 'linear'} y axis")
        for plot in PLOTS:
            for scope in ("pertask", "overall"):
                stems.append(figure(df, col, plot, scope, log))
    bad = {s.name: f for s in stems if (f := pdf_fonts(s.with_suffix(".pdf"))) and
           not all(b"Roboto" in x for x in f)}
    if bad:
        sys.exit(f"non-Roboto fonts embedded: {bad}")
    print(f"{len(stems)} figures x (pdf, png) in {OUT.relative_to(ROOT)}; fonts embedded: "
          f"{sorted({x.decode() for s in stems for x in pdf_fonts(s.with_suffix('.pdf'))})} ({regular.name})")


if __name__ == "__main__":
    main()
