# -*- coding: utf-8 -*-
"""3D figures of WebConform as rows of four printed-size panels, like the accepted RuleSight 3D rows. EVERY 3D panel uses the same
viewing angle VIEW, the same box aspect ASPECT, the same canvas size and the same axes rectangle; within a row the panels share
one coordinate system.
  Fig9   per model: violation rate and random-choice level per relation as gradient bars with values (reference 5 colour scale)
  Fig10  per relation: waterfall of the bootstrap densities of the ratio to chance, one density per model (density reference)
  Fig11  per mitigation model: every setting as a bubble in (violation, right commits, no action) with stem and floor shadow"""
import sys, os, math, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from matplotlib import colors as mcolors, cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from house import *

VIEW = dict(elev=24, azim=-58)                 # the one viewing angle
ASPECT = (1.2, 1.4, 0.85)                      # the one box aspect
W3, H3 = PW, 1.30                              # the one canvas: one quarter of the text width
RECT = [0.05, 0.05, 0.86, 1.02]
# 3D figures use one cool colour scale, from light blue to deep purple, to match the blue and purple scheme of the 2D figures;
# models run from blue (API) to purple (local)
REF5 = mcolors.LinearSegmentedColormap.from_list("cool", ["#DCEBFA", "#B4D2F2", "#86B2E6", "#5B8ED8", "#5F74CC", "#7663C2", "#6A4FA8", "#4A3382"])
MCOL = {m: mcolors.to_hex(REF5(v)) for m, v in zip(["sonnet55", "gemini38", "haiku55", "gpt54mini", "qwen35", "qwen35_9b", "qwen3vl8b", "internvl35"], (0.18, 0.28, 0.38, 0.48, 0.58, 0.74, 0.86, 0.98))}
SETC = {"s0": "#3A3A3A", "cvx": "#6A4FA8", "cv": "#A99BDC", "s2": "#3F63B8", "sc": "#86B2E6", "rg": "#8E97A6", "s1": "#C9CED6"}
def ax3(fig, rect=None):
    ax = fig.add_axes(rect or RECT, projection="3d"); ax.computed_zorder = False
    for p in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane): p.set_facecolor("white"); p.set_edgecolor("#C3C8CF"); p.set_linewidth(0.4)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a._axinfo["grid"].update(color="#D3D6DB", linestyle=(0, (3, 2)), linewidth=0.3); a._axinfo["tick"]["inward_factor"] = 0.0; a._axinfo["tick"]["outward_factor"] = 0.2; a.line.set_linewidth(0.6); a.line.set_color(INK)
    ax.view_init(**VIEW); ax.set_box_aspect(ASPECT, zoom=0.93); ax.tick_params(labelsize=FS - 0.6, pad=-3.2); return ax

def head(fig, title, l, sub=None, red=True):
    fig.text(0.5, 0.99, title, ha="center", va="top", fontsize=FS_T, fontweight="bold", color=INK)
    if sub: fig.text(0.5, 0.925, sub, ha="center", va="top", fontsize=FS - 0.4, color=OURS_D if red else "#7A7A7A")
    fig.text(0.5, 0.004, f"({l})", ha="center", va="bottom", fontsize=FS_L, color=INK)

def gbar(ax, x, y, z, color, dx, dy, order, n=20):
    hi = max(z, 0.004); zs = np.linspace(0, hi, n + 1); polys, cols = [], []
    for k in range(n):
        t = (k + 0.5) / n; c = tint(color, 0.85 * (1 - t) ** 1.3); r, g, b = mcolors.to_rgb(c)
        polys += [[(x, y, zs[k]), (x + dx, y, zs[k]), (x + dx, y, zs[k + 1]), (x, y, zs[k + 1])], [(x + dx, y, zs[k]), (x + dx, y + dy, zs[k]), (x + dx, y + dy, zs[k + 1]), (x + dx, y, zs[k + 1])]]
        cols += [c, (r * 0.86, g * 0.86, b * 0.86)]
    polys.append([(x, y, hi), (x + dx, y, hi), (x + dx, y + dy, hi), (x, y + dy, hi)]); cols.append(tint(color, 0.15))
    pc = Poly3DCollection(polys, facecolors=cols, edgecolors=cols, linewidths=0.2); pc.set_zorder(order); ax.add_collection3d(pc)

def repel(fig, labs, dz, rounds=40):
    for _ in range(rounds):
        fig.canvas.draw(); r = fig.canvas.get_renderer(); bb = [t.get_window_extent(r).expanded(1.04, 1.08) for t in labs]; moved = False
        for a in range(len(labs)):
            for b in range(a + 1, len(labs)):
                if not bb[a].overlaps(bb[b]): continue
                t = labs[a] if bb[a].y0 >= bb[b].y0 else labs[b]; x, y, z = t._position3d if hasattr(t, "_position3d") else t.get_position_3d(); t.set_position_3d((x, y, z + dz)); moved = True
        if not moved: break

# ---------------------------------------------------------------- Fig. 9: per model, violation and chance per relation
REL = ["R1", "R2", "R3", "CFE"]; RS = {"R1": "R1", "R2": "R2", "R3": "R3", "CFE": "CF"}; NB = mcolors.Normalize(0, 50)
def bars_model(name, m, l):
    fig = plt.figure(figsize=(W3, H3)); ax = ax3(fig, [-0.005, 0.05, 0.93, 1.02]); S0 = N["s0"][m]
    az = np.deg2rad(VIEW["azim"]); eye = np.array([np.cos(az), np.sin(az)]); D = 0.5; YP = (0.0, 1.6)
    cells = sorted(((i, j) for i in range(4) for j in range(2)), key=lambda ij: (ij[0] + D / 2) * eye[0] + (YP[ij[1]] + D / 2) * eye[1])
    val = lambda i, j: 100 * (S0[REL[i]]["chance"] if j == 0 else S0[REL[i]]["viol"])
    for k, (i, j) in enumerate(cells):
        z = val(i, j); gbar(ax, i - D / 2, YP[j] - D / 2, z, REF5(NB(z)) if j == 1 else "#B9C0CA", D, D, k + 1)
    labs = [ax.text(i, YP[1], val(i, 1) + 1.5, f"{val(i, 1):.1f}", ha="center", va="bottom", fontsize=FS - 1.6, fontweight="bold", color=INK, zorder=1000, bbox=dict(boxstyle="square,pad=0.06", fc="white", ec="none", alpha=0.8)) for i in range(4)]
    ax.set_xticks(range(4)); ax.set_xticklabels([RS[r] for r in REL], ha="right", va="center"); ax.set_yticks(list(YP)); ax.set_yticklabels(["Chance", "S0"], ha="left", va="center")
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(-0.6, 2.2); ax.set_zlim(0, 55); ax.set_zticks([0, 25, 50])
    k = sum(1 for R in REL[1:] if S0[R]["p_holm"] < 0.05 and S0[R]["viol"] > S0[R]["chance"]); head(fig, MNAME[m], l, f"{k} of 3 commit relations above chance", red=k > 0)
    repel(fig, labs, 1.5); save(fig, name)

# ---------------------------------------------------------------- Fig. 10: waterfall of bootstrap ratio densities, per relation
XR = (-3.2, 4.2)                                # log2 of the ratio to chance: 1/8 to 16
def waterfall(name, R, l, title):
    fig = plt.figure(figsize=(W3, H3)); ax = ax3(fig, [-0.01, 0.02, 1.00, 1.08]); grid = np.linspace(XR[0], XR[1], 241)
    for i, m in enumerate(ORDER[::-1]):                                # back to front
        y = len(ORDER) - 1 - i; d = np.array([v for v in FG["boot"][f"{m}|{R}"]["ratio"] if v == v]); d = np.log2(np.clip(d, 2 ** XR[0], 2 ** XR[1]))
        sd = d.std() if d.std() > 0 else 0.05; bw = 1.06 * sd * len(d) ** (-0.2) * 1.4
        z = np.exp(-0.5 * ((grid[:, None] - d[None, :]) / bw) ** 2).sum(1); z = 0.85 * z / z.max()
        col = MCOL[m]; verts = [(grid[0], y, 0)] + [(gx, y, gz) for gx, gz in zip(grid, z)] + [(grid[-1], y, 0)]
        pc = Poly3DCollection([verts], facecolors=[tint(col, 0.25)], edgecolors=[col], linewidths=0.5, alpha=0.95); pc.set_zorder(i + 1); ax.add_collection3d(pc)
    ax.plot([0, 0], [-0.5, len(ORDER) - 0.5], [0, 0], color=CHANCE, lw=0.7, ls=(0, (2, 1.2)), zorder=100)
    ax.set_xlim(*XR); ax.set_ylim(-0.6, len(ORDER) - 0.4); ax.set_zlim(0, 1.0); ax.set_xticks([-3, 0, 2, 4]); ax.set_xticklabels(["1/8", "1\u00d7", "4", "16"])
    ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([]); ax.set_zticks([])                     # models are named by colour in the legend strip
    k = sum(1 for m in ORDER if N["s0"][m][R]["p_holm"] < 0.05 and N["s0"][m][R]["viol"] > N["s0"][m][R]["chance"])
    head(fig, title, l, f"pooled ratio {X['grp']['all'][R]['ratio']:.2f}", red=True); save(fig, name)

# ---------------------------------------------------------------- Fig. 11: mitigation settings as bubbles
def none_rates():
    import analysis as A
    out = {}
    for m in N["mitigation"]:
        for c in ("s0", "cvx", "cv", "sc", "rg", "s2"):
            ids = [s for s in A.main if A.scr[s]["relation"] in ("R2", "R3", "CFE", "RC", "CFF") and A.pred(m, s, c)]
            out[f"{m}|{c}"] = 100 * sum(1 for s in ids if A.pred(m, s, c) == A.scr[s]["none_letter"]) / max(1, len(ids))
    return out
C6 = ["s0", "cvx", "cv", "sc", "rg", "s2"]
def bubbles(name, m, l, NR):
    fig = plt.figure(figsize=(W3, H3)); ax = ax3(fig, [-0.045, 0.05, 0.90, 1.02]); r = N["mitigation"][m]["rates"]; Z0 = 0
    for c in C6:
        x, y, z = 100 * r[c]["viol"], 100 * r[c]["commit"], NR[f"{m}|{c}"]
        ax.scatter(x, y, Z0, s=14, color="#C3C8CF", alpha=0.6, edgecolor="none", depthshade=False, zorder=1)
        ax.plot([x, x], [y, y], [Z0, z], color=SETC[c], lw=0.5, alpha=0.8, zorder=2)
    x0, y0, z0 = 100 * r["s0"]["viol"], 100 * r["s0"]["commit"], NR[f"{m}|s0"]
    for c in C6[1:]:
        x, y, z = 100 * r[c]["viol"], 100 * r[c]["commit"], NR[f"{m}|{c}"]; ax.plot([x0, x], [y0, y], [z0, z], color=GREY, lw=0.45, alpha=0.7, zorder=3)
    for c in C6:
        x, y, z = 100 * r[c]["viol"], 100 * r[c]["commit"], NR[f"{m}|{c}"]
        ax.scatter(x, y, z, s=22 if c == "s0" else 18, color="white" if c == "s0" else SETC[c], edgecolor="#3A3A3A" if c == "s0" else "white", linewidth=0.8 if c == "s0" else 0.4, depthshade=False, zorder=4)
    ax.set_xlim(5, 30); ax.set_ylim(40, 75); ax.set_zlim(0, 25); ax.set_xticks([10, 20, 30]); ax.set_yticks([40, 55, 70]); ax.set_zticks([0, 10, 20])
    ax.set_xlabel("Violation", fontsize=FS - 0.6, fontweight="bold", labelpad=-9); ax.set_ylabel("Correct commits", fontsize=FS - 0.6, fontweight="bold", labelpad=-9)
    fig.text(0.975, 0.62, "No action (%)", rotation=90, ha="center", va="center", fontsize=FS - 0.6, fontweight="bold")
    head(fig, MNAME[m], l, "every guardrail lowers correct commits", red=False); save(fig, name)

# ---------------------------------------------------------------- Fig. 12: model and website pairs as a 3D cluster with floor shadows
def clusters(name, l, title, splits):
    import json as _j
    G2 = _j.load(open(os.path.join(ROOT, "figdata2.json"), encoding="utf-8")); fig = plt.figure(figsize=(W3, H3)); ax = ax3(fig, [-0.02, 0.05, 0.88, 1.02]); Z0 = 0
    API = ["sonnet55", "gemini38", "haiku55", "gpt54mini", "qwen35"]; n = 0
    for m in ORDER:
        col = "#4A6FC4" if m in API else "#7A6FC9"
        for v in G2["site"][m].values():
            if v["n_c"] < 2 or v["acc"] is None or v["split"] not in splits or 100 * v["ch_c"] / v["n_c"] > 40: continue
            x, y, z = min(41, 100 * v["ch_c"] / v["n_c"]), min(104, 100 * v["acc"]), min(104, 100 * v["v_c"] / v["n_c"]); n += 1
            ax.scatter(x, y, Z0, s=3, color="#C3C8CF", alpha=0.5, edgecolor="none", depthshade=False, zorder=1)
            ax.scatter(x, 105, z, s=2.2, color=col, alpha=0.22, edgecolor="none", depthshade=False, zorder=1)          # projection on the back wall
            ax.scatter(0, y, z, s=2.2, color=col, alpha=0.22, edgecolor="none", depthshade=False, zorder=1)            # projection on the side wall
            ax.scatter(x, y, z, s=11, color=col, alpha=0.9, edgecolor="white", linewidth=0.35, depthshade=False, zorder=3)
    ax.set_xlim(0, 42); ax.set_ylim(0, 105); ax.set_zlim(0, 105); ax.set_xticks([0, 20, 40]); ax.set_yticks([0, 50, 100]); ax.set_zticks([0, 50, 100])
    ax.set_xlabel("Chance", fontsize=FS - 0.6, fontweight="bold", labelpad=-9); ax.set_ylabel("Accuracy", fontsize=FS - 0.6, fontweight="bold", labelpad=-9)
    fig.text(0.975, 0.62, "Violation (%)", rotation=90, ha="center", va="center", fontsize=FS - 0.6, fontweight="bold")
    head(fig, title, l, f"{n} model and website pairs", red=False); save(fig, name)

def colorbar_strip(name, cmap, norm, label, ticks, extra=None):
    fig = plt.figure(figsize=(TEXTW, 0.26)); cax = fig.add_axes([0.40, 0.46, 0.26, 0.24])
    cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal"); cb.outline.set_linewidth(0.4); cb.set_ticks(ticks); cb.ax.tick_params(labelsize=FS, length=1.5, width=0.4, pad=1)
    fig.text(0.39, 0.58, label, ha="right", va="center", fontsize=FS)
    if extra: fig.legend(handles=extra, loc="center left", bbox_to_anchor=(0.69, 0.58), frameon=False, fontsize=FS, handlelength=1.2)
    save(fig, name)

if __name__ == "__main__":
    for k, m in enumerate(ORDER): bars_model(f"Fig9{'abcdefgh'[k]}", m, "abcdefgh"[k])
    colorbar_strip("Fig9_legend", REF5, NB, "S0 violation rate (%), height and colour of the bar", [0, 10, 20, 30, 40, 50], [box("#B9C0CA", "Chance level")])
    for (R, t), l in zip((("R1", "R1 safety"), ("R2", "R2 precondition"), ("R3", "R3 idempotency"), ("CFE", "CF erased input")), "abcd"): waterfall(f"Fig10{l}", R, l, t)
    legend_strip("Fig10_legend", [Patch(fc=tint(MCOL[m], 0.25), ec=MCOL[m], lw=0.6, label=MSHORT[m]) for m in ORDER] + [Line2D([], [], color=CHANCE, lw=0.7, ls=(0, (2, 1.2)), label="Chance (1\u00d7)")])
    # front to back: Sonnet, Gemini, Haiku, GPT mini, Qwen3.5, Qwen-9B, Qwen-VL, InternVL
    NR = none_rates()
    for m, l in zip(N["mitigation"], "abcd"): bubbles(f"Fig11{l}", m, l, NR)
    legend_strip("Fig11_legend", [Line2D([], [], ls="none", marker="o", ms=4.2, mfc="white" if c == "s0" else SETC[c], mec="#3A3A3A" if c == "s0" else "white", mew=0.8 if c == "s0" else 0.4, label=SETN[c]) for c in C6] + [Line2D([], [], ls="none", marker="o", ms=4.2, mfc="#C3C8CF", mec="none", label="Shadow")])
    for (sp, ttl), l in zip(((("test_task",), "Cross-task"), (("test_website",), "Cross-website"), (("test_domain",), "Cross-domain"), (("test_task", "test_website", "test_domain"), "All splits")), "abcd"): clusters(f"Fig12{l}", l, ttl, sp)
    legend_strip("Fig12_legend", [Line2D([], [], ls="none", marker="o", ms=3.8, mfc="#4A6FC4", mec="white", label="API model on a website"), Line2D([], [], ls="none", marker="o", ms=3.8, mfc="#7A6FC9", mec="white", label="Local model on a website"), Line2D([], [], ls="none", marker="o", ms=2.6, mfc="#C3C8CF", mec="none", label="Projections on the floor and walls")])
    print("3D rows written; view", VIEW, "aspect", ASPECT)
