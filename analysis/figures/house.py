# -*- coding: utf-8 -*-
"""House style of every WebConform figure (the RuleSight house style). Each panel is drawn at its printed size: the text width
is 390 pt = 5.40 in and a panel placed four per row is 0.245 of it, so point sizes are printed sizes: 6 pt for all text,
6.5 pt bold for panel titles, 7 pt for panel letters. One palette with fixed meanings in every figure; one legend strip above
the panels of a figure; every row is four panels of one kind with the same axes geometry, or two 3D panels on one set of axes."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
ROOT = os.path.dirname(HERE)
N = json.load(open(os.path.join(ROOT, "numbers.json"), encoding="utf-8")); X = json.load(open(os.path.join(ROOT, "numbers2.json"), encoding="utf-8"))
TEXTW = 390.0 / 72.27                      # 5.397 in
PW = 0.245 * TEXTW                         # 1.322 in, one panel four per row
PH = 1.30
FS, FS_T, FS_L = 6.0, 6.5, 7.0

def _font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((c for c in ("Times New Roman", "Liberation Serif", "TeX Gyre Termes", "DejaVu Serif") if c in names), "serif")
plt.rcParams.update({
    "font.family": _font(), "font.size": FS, "axes.titlesize": FS_T, "axes.labelsize": FS, "xtick.labelsize": FS, "ytick.labelsize": FS,
    "legend.fontsize": FS, "axes.linewidth": 0.6, "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2.0, "ytick.major.size": 2.0,
    "xtick.major.pad": 1.5, "ytick.major.pad": 1.5, "axes.labelpad": 1.5, "lines.linewidth": 0.9, "grid.linewidth": 0.4, "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "stix", "axes.unicode_minus": False, "savefig.dpi": 600})

INK, SPINE, GRIDC = "#262626", "#5A5A5A", "#E3E3E3"
# palette of the user's Nature reference: #4F587D #C68DC0 #C2E0EE #776B97 #DBC8ED | #5271AE #70ACDE #F5CC7D #FFA660 #D85B59 | #CAE5F8 #9DCBED #FAEFF5 #F2C5DA #E286AF
OURS, OURS_D, OURS_L = "#7A6FC9", "#4F4699", "#BBB9ED"     # WebConform, and a forbidden state change (violation)
BLUE, BLUE_D, BLUE_L = "#90B7E2", "#4A6FC4", "#C4D9F1"     # element accuracy, filling the missing input
GREEN = "#3F63B8"                                          # the right commit
GREY, GREY_L = "#9AA3B0", "#DDE2E8"                        # no action, other
PURPLE, PURPLE_L = "#73829C", "#B7C2D3"                    # action-risk label
GOLD = "#F5CC7D"
CHANCE = "#3A3A3A"                                         # random-choice level
MODELS = ["sonnet55", "gemini38", "haiku55", "gpt54mini", "qwen35", "qwen35_9b", "qwen3vl8b", "internvl35"]
MSHORT = {"sonnet55": "Sonnet", "gemini38": "Gemini", "haiku55": "Haiku", "gpt54mini": "GPT mini", "qwen35": "Qwen3.5", "qwen35_9b": "Qwen-9B", "qwen3vl8b": "Qwen-VL", "internvl35": "InternVL"}
MNAME = N["name"]
MCOL = {"sonnet55": "#776B97", "gemini38": "#F5CC7D", "haiku55": "#4F587D", "gpt54mini": "#C68DC0", "qwen35": "#3BB5B5", "qwen35_9b": "#9DCBED", "qwen3vl8b": "#70ACDE", "internvl35": "#FFA660"}
LOCAL = {"qwen35_9b", "qwen3vl8b", "internvl35"}
SET = ["s0", "s1", "cvx", "cv", "sc", "rg", "s2"]
SETN = {"s0": "S0 vanilla", "s1": "S1 action history", "cvx": "CVX verification with explanation", "cv": "CV verification", "sc": "SC self-check", "rg": "RG risk gate", "s2": "S2 rule instruction"}
SETS = {"s0": "S0", "s1": "S1", "cvx": "CVX", "cv": "CV", "sc": "SC", "rg": "RG", "s2": "S2"}
SETC = {"s0": "#9AA3B0", "s1": "#DBC8ED", "cvx": "#D85B59", "cv": "#EBA9A8", "sc": "#70ACDE", "rg": "#776B97", "s2": "#F5CC7D"}

def tint(color, t):
    from matplotlib import colors as mc
    r, g, b = mc.to_rgb(color); return (r + (1 - r) * t, g + (1 - g) * t, b + (1 - b) * t)

def panel(left=0.30, bottom=0.40, right=0.05, top=0.15, w=PW, h=PH, projection=None):
    """a canvas of the printed panel size with fixed margins in inches, so every panel of a row lines up"""
    fig = plt.figure(figsize=(w, h)); rect = [left / w, bottom / h, 1 - (left + right) / w, 1 - (bottom + top) / h]
    ax = fig.add_axes(rect, projection=projection) if projection else fig.add_axes(rect)
    return fig, ax

def style(ax, title=None, xlabel=None, ylabel=None, grid="y"):
    for s in ax.spines.values(): s.set_color(SPINE); s.set_linewidth(0.6)
    ax.tick_params(colors=INK, length=2.0, width=0.5)
    if grid: ax.grid(True, axis=grid, ls="-", color=GRIDC, lw=0.45); ax.set_axisbelow(True)
    if title: ax.set_title(title, fontsize=FS_T, fontweight="bold", pad=2.5, color=INK)
    if xlabel: ax.set_xlabel(xlabel, fontweight="bold", color=INK)
    if ylabel: ax.set_ylabel(ylabel, fontweight="bold", color=INK)

def letter(fig, l, y=0.006):
    fig.text(0.5, y, f"({l})", ha="center", va="bottom", fontsize=FS_L, color=INK)

def gbar(ax, x0, x1, y0, y1, color, light=0.55, z=3):
    """a bar with a gradient from a light tint at its base to the full colour at its end"""
    if abs(x1 - x0) < 1e-12 or abs(y1 - y0) < 1e-12: return
    cm = LinearSegmentedColormap.from_list("g", [tint(color, light), color]); grad = np.linspace(0, 1, 64)
    img = grad.reshape(-1, 1) if y1 >= y0 else grad[::-1].reshape(-1, 1); ext = (min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))
    im = ax.imshow(img, extent=ext, origin="lower", cmap=cm, aspect="auto", interpolation="bicubic", zorder=z)
    rect = Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc="none", ec=color, lw=0.4, zorder=z + 0.1); ax.add_patch(rect); im.set_clip_path(rect)

def chance_tick(ax, x, y, w=0.62, z=6):
    ax.plot([x - w / 2, x + w / 2], [y, y], color=CHANCE, lw=0.9, solid_capstyle="butt", zorder=z)

def legend_strip(name, handles, h=0.17, w=TEXTW, rows=None):
    rows = rows or [handles]; fig = plt.figure(figsize=(w, h * len(rows)))
    for k, hs in enumerate(rows):
        fig.legend(handles=hs, loc="center", bbox_to_anchor=(0.5, 1 - (k + 0.5) / len(rows)), ncol=len(hs), frameon=False, fontsize=FS, handlelength=1.4, handletextpad=0.4, columnspacing=1.1, borderaxespad=0)
    save(fig, name)

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf")); fig.savefig(os.path.join(OUT, name + ".png"), dpi=600, facecolor="white"); plt.close(fig)

def box(color, label, ec="none"): return Patch(fc=color, ec=ec, lw=0.4, label=label)
def tick_handle(label): return Line2D([], [], color=CHANCE, lw=0.9, label=label)
def dot(color, label, marker="o", ms=4.0, mec="#555555"): return Line2D([], [], ls="none", marker=marker, ms=ms, mfc=color, mec=mec, mew=0.4, label=label)
def model_axis(ax, ms=MODELS):
    ax.set_xticks(range(len(ms))); ax.set_xticklabels([MSHORT[m] for m in ms], rotation=45, ha="right", rotation_mode="anchor"); ax.set_xlim(-0.6, len(ms) - 0.4)

DIV = LinearSegmentedColormap.from_list("div", ["#3E5A8F", "#70ACDE", "#CAE5F8", "#FFFFFF", "#F2C5DA", "#E286AF", "#D85B59", "#8E2F2D"])
SEQ_R = LinearSegmentedColormap.from_list("seqr", ["#FFFFFF", "#FAEFF5", "#F2C5DA", "#E286AF", "#D85B59", "#8E2F2D"])
SEQ_B = LinearSegmentedColormap.from_list("seqb", ["#FFFFFF", "#CAE5F8", "#9DCBED", "#70ACDE", "#5271AE", "#3E5A8F"])
FG = json.load(open(os.path.join(ROOT, "figdata.json"), encoding="utf-8"))

def subtitle(fig, text, color=None, y=None):
    """the coloured one-line finding under a panel title, as in RuleSight Figs. 6 and 9"""
    fig.text(0.5 + (fig.axes[0].get_position().x0 + fig.axes[0].get_position().x1 - 1) / 2, y if y is not None else fig.axes[0].get_position().y1 + 0.012, text,
             ha="center", va="bottom", fontsize=FS - 0.3, color=color or "#8A8A8A")
ORDER = ["sonnet55", "gemini38", "haiku55", "gpt54mini", "qwen35", "qwen35_9b", "qwen3vl8b", "internvl35"]
def model_rows(ax, ms=ORDER, divider=True):
    """models top to bottom on the y axis; a thin divider between the API models and the local ones"""
    ax.set_yticks(range(len(ms))); ax.set_yticklabels([MSHORT[m] for m in ms]); ax.set_ylim(len(ms) - 0.45, -0.55)
    if divider and len(ms) == 8: ax.axhline(4.5, color="#BFBFBF", lw=0.5, ls=(0, (2, 1.5)), zorder=1)
