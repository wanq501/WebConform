# -*- coding: utf-8 -*-
"""WebConform result figures, version 6. Same geometry and type as version 5 (one axes rectangle for every small panel, 6 pt text),
with the palette of the reference charts (pastel fills, saturated outlines) and one full-width hero panel per figure.

  A  oracle validation   hero: every validation decision under five oracle configurations (decision matrix)
                         row : precision-recall plane with iso-F1 curves, F1 and accuracy bars with intervals and test brackets, votes
  B  websites            hero: website by model heat map of the violation rate with marginal means
                         row : violins with boxes and a test bracket, two scatter panels with fits, joint density
  C  counterfactual      hero: pair by model tile matrix of the outcome in the filled and in the erased state
                         row : dumbbells filled to erased, outcomes on the erased state, history dumbbells, pair scatter
  D  reasoning           row 1 densities with medians and barcodes, row 2 joint densities per split (version 5 panels, new palette)
  E  stability           alluvial flows of the outcome over three identical runs, one panel per model
  F  guards              row 1 paired scatter per model and task, row 2 mirrored bars of fixed and introduced decisions with stars
  G  diagnostics         wrong decisions against a random wrong choice (R2, R3), bump chart of the two rankings, accuracy against conformance
  H  forest              hero: pooled ratio to chance with task-clustered 95% intervals for every group of probes"""
import sys, os, math, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import *
import figs_v5 as V5
from figs_v5 import P, done, rows_y, note, strip, pearson, pfmt, fitband, AXL, AXR, AXB, AXT, AW, AH, FS_F, O, API, LOC, MM, G2, H_ref
from matplotlib.patches import Rectangle, FancyBboxPatch, PathPatch, Polygon
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from scipy import stats

# ---------------------------------------------------------------- palette of the reference charts
B_F, B_M, B_E = "#C4D9F1", "#90B7E2", "#4A6FC4"          # blue: fill, mid, outline. The reference side, and every conforming outcome
R_F, R_M, R_E = "#E3E1F8", "#BBB9ED", "#7A6FC9"          # purple: the side of interest and every violation (names are historical)
P_F, P_M, P_E = "#E1E6EF", "#B7C2D3", "#73829C"          # slate: a third series
G_F, G_M, G_E = "#C4D9F1", "#90B7E2", "#3F63B8"          # deep blue: the right commit
N_F, N_M, N_E = "#EEF1F5", "#C9CED6", "#8E97A6"          # neutral
R_D = "#4F4699"                                          # emphasis in text
V5.OUTC = {"commit_ok": G_E, "commit": R_E, "fill": B_M, "other": N_F, "none": N_E}
OSR = json.load(open(os.path.join(ROOT, "oracle_stats.json"), encoding="utf-8"))["r2"]
CFG = [("wc", "WebConform", R_E, R_F), ("wc_nolink", "OSR only", P_E, P_F), ("rl2", "Risk+SCC", B_E, B_F), ("rl", "Risk label", B_E, B_F), ("ea", "Elem. acc.", N_E, N_F)]
SHORTCFG = {"wc": "Ours"}

def stars(p): return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
def hero(h, left=0.62, right=0.62, bottom=0.30, top=0.20):
    fig = plt.figure(figsize=(TEXTW, h)); ax = fig.add_axes([left / TEXTW, bottom / h, (TEXTW - left - right) / TEXTW, (h - bottom - top) / h]); return fig, ax
def hero_done(fig, name, l, title=None):
    if title: fig.text(0.5, 1 - 0.035 / fig.get_figheight(), title, ha="center", va="top", fontsize=FS_T, fontweight="bold", color=INK)
    if l: fig.text(0.5, 0.004, f"({l})", ha="center", va="bottom", fontsize=FS_L, color=INK)
    save(fig, name)
def hbox(fc, ec, label): return Patch(fc=fc, ec=ec, lw=0.7, label=label)
def hdot(fc, ec, label, ms=3.6): return Line2D([], [], ls="none", marker="o", ms=ms, mfc=fc, mec=ec, mew=0.7, label=label)
def lbox(ax, text, loc, ec, color=None):
    x, y, ha, va = {"ul": (0.04, 0.96, "left", "top"), "ur": (0.96, 0.96, "right", "top"), "lr": (0.96, 0.05, "right", "bottom"), "ll": (0.04, 0.05, "left", "bottom")}[loc]
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=FS_F - 0.2, color=color or ec, fontweight="bold", zorder=12, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=ec, lw=0.6, alpha=0.95))
def bracket(ax, x, y0, y1, text, dx=None, color=INK):
    """vertical test bracket at data x between rows y0 and y1 of a horizontal bar chart"""
    dx = dx if dx is not None else 0.012 * (ax.get_xlim()[1] - ax.get_xlim()[0])
    ax.plot([x - dx, x, x, x - dx], [y0, y0, y1, y1], color=color, lw=0.6, clip_on=False, zorder=8); ax.text(x + dx * 0.5, (y0 + y1) / 2, text, ha="left", va="center", fontsize=FS - 0.8, color=color, rotation=270, clip_on=False)

# ================================================================= A: oracle validation. Row 1 waffles, row 2 bars with intervals
WAF = {"tp": "#5E57A6", "fn": "#4A90D9", "fp": "#BDB9EC", "tn": "#E4E8F0"}
ACFG = [("wc", "WebConform"), ("wc_nolink", "OSR without the SCC"), ("rl", "Action-risk label"), ("ea", "Element accuracy")]
BARCFG = [("wc", "Ours", R_E, R_M), ("wc_nolink", "OSR only", R_E, R_F), ("rl2", "Risk+SCC", B_E, B_F), ("rl", "Risk label", B_E, B_M), ("ea", "Elem. acc.", N_E, N_F)]
def fig_oracle():
    for (k, nm), l in zip(ACFG, "abcd"):                       # one square per validation decision
        o = OSR[k]; fig, ax = P(nm, finding=f"precision {100 * o['precision']:.1f}%, recall {100 * o['recall']:.1f}%", red=(k == "wc"), axis=False)
        V5.waffle(ax, [c for c in ("tp", "fn", "fp", "tn") for _ in range(int(o[c]))], WAF, cols=18, rows=16); V5.under(fig, f"{int(o['tp'])} TP, {int(o['fp'])} FP"); done(fig, f"A{l}", l)
    rl, ea, wc = OSR["rl"], OSR["ea"], OSR["wc"]
    finds = {"precision": f"{wc['precision'] / rl['precision']:.2f} times the risk label", "recall": "the risk label flags all", "f1": "highest of the five", "acc": f"{100 * wc['acc']:.1f}% agreement"}
    for (met, ttl), l in zip((("precision", "Precision"), ("recall", "Recall"), ("f1", "F1 score"), ("acc", "Accuracy")), "efgh"):
        fig, ax = P(ttl, f"{ttl} (%)", grid="x", finding=finds[met], red=met != "recall")
        for i, (k, nm, ec, fc) in enumerate(BARCFG):
            o = OSR[k]; v = 100 * o[met]; lo, hi = [100 * x for x in o[met + "_ci"]]
            ax.barh(i, v, 0.66, color=fc, edgecolor=ec, linewidth=0.8, zorder=3); ax.plot([lo, hi], [i, i], color=INK, lw=0.7, zorder=5)
            for e in (lo, hi): ax.plot([e, e], [i - 0.14, i + 0.14], color=INK, lw=0.7, zorder=5)
            ax.text(max(hi, v) + 3, i, f"{v:.1f}", ha="left", va="center", fontsize=FS - 0.5, color=R_D if k == "wc" else INK, fontweight="bold" if k == "wc" else "normal", zorder=6)
        rows_y(ax, [c[1] for c in BARCFG]); ax.get_yticklabels()[0].set_fontweight("bold"); ax.get_yticklabels()[0].set_color(R_D)
        for t_ in ax.get_yticklabels(): t_.set_fontsize(FS - 0.4)
        ax.set_xlim(0, 140); ax.set_xticks([0, 50, 100]); done(fig, f"A{l}", l)
    strip("A_legend", rows=[[hbox(WAF["tp"], "none", "True positive (TP), flagged and harmful"), hbox(WAF["fn"], "none", "False negative (FN)"), hbox(WAF["fp"], "none", "False positive (FP)"), hbox(WAF["tn"], "none", "True negative (TN)")],
                            [hbox(R_M, R_E, "WebConform (ours)"), hbox(R_F, R_E, "OSR only"), hbox(B_F, B_E, "Action-risk label with SCC"), hbox(B_M, B_E, "Action-risk label"), hbox(N_F, N_E, "Element accuracy"), Line2D([], [], color=INK, lw=0.7, marker="|", ms=4, label="95% interval")]])

# ================================================================= B: websites as a tile matrix (its own wide figure), and the two groups of models as violins
TCMAP = LinearSegmentedColormap.from_list("tiles", ["#DCE8F8", "#B3CEEE", "#8FB3E6", "#7F8FD6", "#7468C2", "#5B4FA6", "#3B3477"])
BCMAP = LinearSegmentedColormap.from_list("bc", ["#FFFFFF", "#E6EEF9", B_F, B_M, B_E, "#2C4A9A"])
def site_table():
    names = sorted({w for m in O for w, v in G2["site"][m].items() if v["n_c"] >= 3}); M = np.array([[100 * G2["site"][m][w]["v_c"] / G2["site"][m][w]["n_c"] for w in names] for m in O])
    order = np.argsort(-M.mean(0)); return [names[i] for i in order], M[:, order]
def fig_site_map():
    """rounded tiles, one per model and website, in the style of the pair matrix; means per website on top and per model at the right"""
    names, M = site_table(); nS = len(names); Hh = 2.32; L_, R_, B_, T_ = 0.66, 0.50, 0.80, 0.42; GAP = 0.34
    fig = plt.figure(figsize=(TEXTW, Hh)); ax = fig.add_axes([L_ / TEXTW, B_ / Hh, (TEXTW - L_ - R_) / TEXTW, (Hh - B_ - T_) / Hh]); yy = [i + (GAP if i >= 5 else 0) for i in range(8)]
    for i in range(8):
        for j in range(nS):
            v = M[i, j]; ax.add_patch(FancyBboxPatch((j + 0.07, yy[i] + 0.07), 0.86, 0.86, boxstyle="round,pad=0,rounding_size=0.17", fc="#EEF1F6" if v <= 0 else TCMAP(v / 100), ec="none"))
    ax.set_xlim(0, nS); ax.set_ylim(8 + GAP, 0); ax.set_yticks([y + 0.5 for y in yy]); ax.set_yticklabels([MSHORT[m] for m in O], fontsize=FS + 0.3)
    ax.set_xticks([j + 0.5 for j in range(nS)]); ax.set_xticklabels([w[:16] for w in names], rotation=45, ha="right", rotation_mode="anchor", fontsize=5.6); ax.tick_params(length=0, pad=3)
    for s_ in ax.spines.values(): s_.set_visible(False)
    T = ax.get_yaxis_transform()
    for (a, b, lab, col) in ((yy[0], yy[4] + 1, "API", B_E), (yy[5], yy[7] + 1, "Local", R_E)):          # the two groups, named at the far left
        ax.plot([-0.132, -0.132], [a + 0.12, b - 0.12], color=col, lw=1.6, transform=T, clip_on=False, solid_capstyle="round"); ax.text(-0.142, (a + b) / 2, lab, rotation=90, ha="right", va="center", fontsize=FS, fontweight="bold", color=col, transform=T, clip_on=False)
    p = ax.get_position(); top = fig.add_axes([p.x0, p.y1 + 0.016, p.width, 0.34 / Hh]); mu = M.mean(0)
    top.bar(np.arange(nS) + 0.5, mu, 0.62, color=[TCMAP(v / 100) for v in mu], edgecolor="none"); top.set_xlim(0, nS); top.set_ylim(0, 60); top.set_xticks([]); top.set_yticks([0, 50]); top.tick_params(length=1.5, pad=1, labelsize=FS - 0.6)
    for s_ in ("top", "right"): top.spines[s_].set_visible(False)
    top.spines["left"].set_linewidth(0.5); top.spines["bottom"].set_linewidth(0.5); top.set_ylabel("Mean (%)", fontsize=FS - 0.4, labelpad=2)
    rt = fig.add_axes([p.x1 + 0.012, p.y0, 0.40 / TEXTW, p.height]); mm = M.mean(1)
    rt.barh([y + 0.5 for y in yy], mm, 0.62, color=[B_M] * 5 + [R_E] * 3, edgecolor="none"); rt.set_ylim(8 + GAP, 0); rt.set_xlim(0, 50); rt.set_yticks([]); rt.set_xticks([0, 40]); rt.tick_params(length=1.5, pad=1, labelsize=FS - 0.6)
    for y, v in zip(yy, mm): rt.text(v + 2, y + 0.5, f"{v:.0f}", va="center", ha="left", fontsize=FS - 0.4, color=INK)
    for s_ in ("top", "right"): rt.spines[s_].set_visible(False)
    rt.spines["left"].set_linewidth(0.5); rt.spines["bottom"].set_linewidth(0.5); rt.set_xlabel("Mean (%)", fontsize=FS - 0.4, labelpad=1)
    cax = fig.add_axes([0.5 - 0.11, 0.175 / Hh, 0.22, 0.060 / Hh]); cb = fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0, 100), cmap=TCMAP), cax=cax, orientation="horizontal"); cb.outline.set_linewidth(0.3); cb.set_ticks([0, 25, 50, 75, 100]); cb.ax.tick_params(labelsize=FS - 0.4, length=1.5, width=0.3, pad=1)
    fig.text(0.5 - 0.118, 0.205 / Hh, "Violation rate (%)", ha="right", va="center", fontsize=FS)
    fig.patches.append(FancyBboxPatch((0.5 + 0.135, 0.150 / Hh), 0.11 / TEXTW, 0.11 / Hh, boxstyle="round,pad=0,rounding_size=0.004", fc="#EEF1F6", ec="none", transform=fig.transFigure)); fig.text(0.5 + 0.135 + 0.15 / TEXTW, 0.205 / Hh, "No violation", ha="left", va="center", fontsize=FS)
    save(fig, "B_hero")
def fig_site():
    """the wide tile matrix, and (a to d) how many of the eight models violate each probe, against models that err independently"""
    fig_site_map()
    for (R, ttl), l in zip((("R2", "R2 precondition"), ("R3", "R3 idempotency"), ("CFE", "CF erased input"), ("C", "Three relations pooled")), "abcd"):
        c = G2["conc"][R]; n = c["n"]; obs = 100 * np.array(c["obs"]) / n; exp = 100 * np.array(c["exp"]) / n; top = float(max(obs.max(), exp.max())) * 1.22
        fig, ax = P(ttl, "MLLMs violating a test case", "Test cases (%)", grid="y", finding=f"permutation {pfmt(c['p_hi'])}", red=c["p_hi"] < 0.05)
        ax.axvspan(3.5, 8.6, color="#F4F3FC", lw=0, zorder=0)
        ax.bar(range(9), obs, 0.74, color=[TCMAP(0.10 + 0.90 * k / 8) for k in range(9)], edgecolor=[TCMAP(min(1.0, 0.30 + 0.90 * k / 8)) for k in range(9)], linewidth=0.7, zorder=3)
        ax.plot(range(9), exp, color="#4A6FC4", lw=1.0, zorder=5); ax.scatter(range(9), exp, s=9, facecolor="white", edgecolor="#4A6FC4", linewidth=0.8, zorder=6)
        ax.text(0.965, 0.955, f"4 or more\n{c['hi_obs']} test cases\n{c['hi_exp']:.1f} expected", transform=ax.transAxes, ha="right", va="top", fontsize=FS_F - 0.3, color=R_D, linespacing=1.2, zorder=8)
        ax.set_xlim(-0.6, 8.6); ax.set_xticks([0, 2, 4, 6, 8]); ax.set_ylim(0, top); ax.locator_params(axis="y", nbins=4); done(fig, f"B{l}", l)
    strip("B_legend", [hbox(TCMAP(0.55), TCMAP(0.85), "Test cases, observed"), Line2D([], [], color="#4A6FC4", lw=1.0, marker="o", ms=3.2, mfc="white", mec="#4A6FC4", label="Expected if the MLLMs failed independently"), hbox("#F4F3FC", "#CFCBEF", "Four or more of the eight MLLMs")])

# ================================================================= C: counterfactual pairs
def pair_outcomes():
    import analysis as A
    pids = sorted(A.CF_VALID); out = {}
    for pid in pids:
        f, e = A.scr["CFF_" + pid], A.scr["CFE_" + pid]; row = {}
        for m in O:
            pf_, pe = A.pred(m, "CFF_" + pid, "s0"), A.pred(m, "CFE_" + pid, "s0")
            row[m] = ("commit" if pf_ in A.L(f["gold_letters"]) else "none" if pf_ == f["none_letter"] else "other", "commit" if pe in A.viol_letters(e) else "fill" if pe in A.L(e["gold_letters"]) else "none" if pe == e["none_letter"] else "other")
        out[pid] = {"site": e["website"], "m": row}
    return out
def fig_cf():
    PO = pair_outcomes(); pids = sorted(PO, key=lambda p: (-sum(1 for m in O if PO[p]["m"][m][1] == "commit"), PO[p]["site"])); nP = len(pids)
    fig, ax = hero(1.71, left=0.40, right=0.30, bottom=0.28, top=0.37); step = 2.35
    colF = {"commit": G_E, "other": N_M, "none": N_E}; colE = {"commit": R_E, "fill": B_M, "other": N_M, "none": N_E}
    for k, pid in enumerate(pids):
        xf = k * step; xe = xf + 1.0
        for i, m in enumerate(O):
            a, b = PO[pid]["m"][m]
            ax.add_patch(FancyBboxPatch((xf + 0.07, i + 0.09), 0.86, 0.82, boxstyle="round,pad=0,rounding_size=0.16", fc=colF[a], ec="none")); ax.add_patch(FancyBboxPatch((xe + 0.07, i + 0.09), 0.86, 0.82, boxstyle="round,pad=0,rounding_size=0.16", fc=colE[b], ec="none"))
        ax.text(xf + 1.0, -0.62, {"recreation.gov": "recreation", "finance.yahoo": "yahoo fin."}.get(PO[pid]["site"], PO[pid]["site"]), ha="center", va="bottom", fontsize=FS - 0.6, fontweight="bold", color=INK)
        ax.text(xf + 0.5, -0.12, "filled", ha="center", va="bottom", fontsize=FS - 1.4, color="#5A5A5A"); ax.text(xe + 0.5, -0.12, "erased", ha="center", va="bottom", fontsize=FS - 1.4, color="#5A5A5A")
        nprem = sum(1 for m in O if PO[pid]["m"][m][1] == "commit"); ax.text(xe + 0.5, 8.18, f"{nprem}/8", ha="center", va="top", fontsize=FS - 0.4, color=R_D if nprem else "#8E97A6", fontweight="bold" if nprem else "normal")
    ax.axhline(5, color="white", lw=2.0)
    for i, m in enumerate(O):
        k_ = sum(1 for p in pids if PO[p]["m"][m][1] == "commit"); ax.text(nP * step - 0.20, i + 0.5, f"{k_}/10", ha="left", va="center", fontsize=FS - 0.3, color=R_D, fontweight="bold")
    ax.text(nP * step - 0.20, -0.12, "premature", ha="left", va="bottom", fontsize=FS - 1.4, color="#5A5A5A")
    ax.set_xlim(-0.1, nP * step - 0.3); ax.set_ylim(8.05, -0.05); ax.set_yticks([i + 0.5 for i in range(8)]); ax.set_yticklabels([MSHORT[m] for m in O]); ax.set_xticks([]); ax.tick_params(length=0, pad=3)
    for s_ in ax.spines.values(): s_.set_visible(False)
    hs = [hbox(G_E, "none", "Correct commit on the filled state"), hbox(R_E, "none", "Premature commit on the erased state"), hbox(B_M, "none", "Fills the erased input"), hbox(N_M, "none", "Another control"), hbox(N_E, "none", "No action")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=5, frameon=False, fontsize=FS - 0.4, handlelength=1.0, handleheight=0.8, columnspacing=1.2, handletextpad=0.4)
    hero_done(fig, "C_hero", None)
    # four dumbbell panels: the commit rate between two states, per model
    import analysis as A
    prem = lambda ms, c: 100 * sum(1 for m_ in ms for p in pids if A.pred(m_, "CFE_" + p, c) in A.viol_letters(A.scr["CFE_" + p])) / (len(ms) * nP)
    fig, ax = P("Filled to erased", "Pairs committed (%)", grid="x", finding="63 to 24 of 80 commits", red=False)
    for i, m in enumerate(O):
        c = N["cf"][m]; a, b = 100 * c["filled"] / c["n"], 100 * c["emptied"] / c["n"]; xs = np.linspace(b, a, 30)
        for j in range(len(xs) - 1): ax.plot(xs[j:j + 2], [i, i], color=np.array(to_rgb(R_M)) * (1 - j / 29) + np.array(to_rgb(B_M)) * (j / 29), lw=1.8, solid_capstyle="butt", zorder=2)
        ax.scatter([a], [i], s=19, color=G_E, edgecolor="white", linewidth=0.5, zorder=4); ax.scatter([b], [i], s=19, color=R_E, edgecolor="white", linewidth=0.5, zorder=4)
    ax.axvline(4.0, color="#555555", lw=0.7, ls=(0, (3, 2)), zorder=1); rows_y(ax, [MSHORT[m] for m in O], 4.5); ax.set_xlim(-4, 104); ax.set_xticks([0, 50, 100]); done(fig, "Ca", "a")
    for (c, ttl), l in zip((("s1", "Action history (S1)"), ("cvx", "CVX, with explanation"), ("s2", "Rule instruction (S2)")), "bcd"):
        rows = [(MSHORT[m], prem([m], "s0"), prem([m], c)) for m in MM] + [("Pooled", prem(MM, "s0"), prem(MM, c))]; a0, b0 = rows[-1][1], rows[-1][2]
        fig, ax = P(ttl, "Premature commits (%)", grid="x", finding=f"{a0:.1f}% to {b0:.1f}%", red=b0 > a0 + 5)
        for i, (lab, a, b) in enumerate(rows):
            if abs(b - a) > 3: ax.annotate("", xy=(b, i), xytext=(a, i), arrowprops=dict(arrowstyle="-|>", color=R_E, lw=1.0, mutation_scale=6, shrinkA=2.6, shrinkB=2.6), zorder=3)
            ax.scatter([a], [i], s=19, facecolor="white", edgecolor=B_E, linewidth=0.9, zorder=4); ax.scatter([b], [i], s=19, color=R_E, edgecolor="white", linewidth=0.5, zorder=5)
        ax.axvline(4.0, color="#555555", lw=0.7, ls=(0, (3, 2)), zorder=1); rows_y(ax, [r[0] for r in rows], 3.5); ax.get_yticklabels()[-1].set_fontweight("bold"); ax.set_xlim(-4, 104); ax.set_xticks([0, 50, 100]); done(fig, f"C{l}", l)
    strip("C_legend", [hdot(G_E, "white", "Input filled"), hdot(R_E, "white", "Input erased"), hdot("white", B_E, "Erased, S0"), hdot(R_E, "white", "Erased, with the guardrail or the action history"), H_ref("Chance level")])

# ================================================================= E: stability as alluvial flows over three runs
def ribbon(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha=0.45):
    xm = (x0 + x1) / 2; verts = [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a), (x1, y1b), (xm, y1b), (xm, y0b), (x0, y0b), (x0, y0a)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]; ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec="none", alpha=alpha, zorder=2))
def fig_stab():
    cats = ["v", "g", "o", "n"]; col = {"v": R_E, "g": G_E, "o": N_M, "n": N_E}
    for m, l in zip(MM, "abcd"):
        runs = FG["runs"][m]; n = len(runs); ch = sum(1 for r in runs if len(set(r)) > 1); v3 = sum(1 for r in runs if set(r) == {"v"})
        fig = plt.figure(figsize=(PW, PH)); ax = fig.add_axes([0.05 / PW, AXB / PH, (PW - 0.10) / PW, AH / PH]); ax.axis("off")
        fig.text(0.5, (PH - 0.035) / PH, MNAME[m], ha="center", va="top", fontsize=FS_T, fontweight="bold", color=INK); fig.text(0.5, (PH - 0.150) / PH, f"{ch} of {n} decisions changed", ha="center", va="top", fontsize=FS_F, color=R_D if ch > 10 else "#7A7A7A")
        gap = 0.035 * n; xs = [0.0, 1.0, 2.0]; bw = 0.13; pos = []
        for k in range(3):
            y = 0; d = {}
            for c in cats:
                h = sum(1 for r in runs if r[k] == c); d[c] = (y, y + h)
                if h: ax.add_patch(Rectangle((xs[k] - bw / 2, y), bw, h, fc=col[c], ec="none", zorder=3))
                y += h + gap
            pos.append(d)
        for k in range(2):
            used0 = {c: pos[k][c][0] for c in cats}; used1 = {c: pos[k + 1][c][0] for c in cats}
            for a in cats:
                for b in cats:
                    w = sum(1 for r in runs if r[k] == a and r[k + 1] == b)
                    if not w: continue
                    ribbon(ax, xs[k] + bw / 2, xs[k + 1] - bw / 2, used0[a], used0[a] + w, used1[b], used1[b] + w, col[a], alpha=0.55 if a == b else 0.30); used0[a] += w; used1[b] += w
        tot = n + 3 * gap; ax.set_xlim(-0.10, 2.10); ax.set_ylim(tot * 1.02, -tot * 0.02)
        for k, t in enumerate(("Run 1", "Run 2", "Run 3")): ax.text(xs[k], tot * 1.035, t, ha="center", va="top", fontsize=FS - 0.3, color=INK)
        fig.text(0.5, (AXB - 0.125) / PH, f"{v3} violations in all three runs", ha="center", va="top", fontsize=FS_F, color=R_D); fig.text(0.5, 0.006, f"({l})", ha="center", va="bottom", fontsize=FS_L, color=INK); save(fig, f"E{l}")
    strip("E_legend", [hbox(R_E, "none", "Forbidden commit"), hbox(G_E, "none", "Demonstrated control"), hbox(N_M, "none", "Another control"), hbox(N_E, "none", "No action"), hbox("#D9DDE3", "none", "Flow between two runs")])

# ================================================================= F: guards, row 2 as mirrored bars with stars
def fig_guards_bars():
    SETROW = ["s1", "s2", "sc", "rg", "cv", "cvx"]
    for R, l, ttl, up, dn, cu, cd in (("R2", "e", "R2 violations", "removed", "introduced", (R_F, R_E), (B_F, B_E)), ("R3", "f", "R3 violations", "removed", "introduced", (R_F, R_E), (B_F, B_E)),
                                         ("CFE", "g", "CF violations", "removed", "introduced", (R_F, R_E), (B_F, B_E)), ("commit", "h", "Correct commits", "gained", "lost", (B_F, B_E), (R_F, R_E))):
        mx = max(max(FG["pairs"][f"{c}|{R}"]["up"], FG["pairs"][f"{c}|{R}"]["down"]) for c in SETROW); lim = max(10, 10 * math.ceil(mx * 1.55 / 10))
        fig, ax = P(ttl, "Decisions against S0", grid="x", finding=f"left {dn}, right {up}", red=False); ax.axvline(0, color=SPINE, lw=0.6, zorder=4); labs = []
        for i, c in enumerate(SETROW):
            d = FG["pairs"][f"{c}|{R}"]; ax.barh(i, d["up"], 0.64, color=cu[0], edgecolor=cu[1], linewidth=0.8, zorder=3); ax.barh(i, -d["down"], 0.64, color=cd[0], edgecolor=cd[1], linewidth=0.8, zorder=3)
            if d["up"]: ax.text(d["up"] + 0.03 * lim, i, f"{d['up']}", ha="left", va="center", fontsize=FS - 0.9, color=INK)
            if d["down"]: ax.text(-d["down"] - 0.03 * lim, i, f"{d['down']}", ha="right", va="center", fontsize=FS - 0.9, color=INK)
            labs.append(SETS[c] + (" " + stars(d["p"]) if d["p"] < 0.05 else ""))                # the test result next to the name of the guard
        rows_y(ax, labs); ax.set_xlim(-lim, lim); t = int(lim * 0.6 // 10 * 10) or int(lim // 2); ax.set_xticks([-t, 0, t]); ax.set_xticklabels([str(t), "0", str(t)]); done(fig, f"F{l}", l)

# ================================================================= G: among wrong decisions, the forbidden commit against a random wrong choice (dumbbells)
def wrong_pooled():
    """wrong decisions over R2, R3 and the erased states together, per model: share that is the forbidden commit, the share a random wrong choice would give, Holm p"""
    import analysis as A
    out = {}
    for m in O:
        ids = [s for s in A.main if A.scr[s]["relation"] in ("R2", "R3", "CFE") and A.pred(m, s, "s0") and A.pred(m, s, "s0") not in A.L(A.scr[s]["gold_letters"])]
        wv = sum(1 for s in ids if A.pred(m, s, "s0") in A.viol_letters(A.scr[s])); ps = [A.pi_wrong(s) for s in ids]
        out[m] = {"wrong_viol": wv / len(ids), "wrong_chance": sum(ps) / len(ids), "wrong_ratio": wv / sum(ps), "p": A.exact_p(wv, ps), "n_wrong": len(ids)}
    for m, a in zip(O, A.holm([out[m]["p"] for m in O])): out[m]["wrong_p"] = a
    return out
def fig_diag():
    S0 = N["s0"]; WP = wrong_pooled()
    for (R, ttl), l in zip((("R2", "R2 precondition"), ("R3", "R3 idempotency"), ("CFE", "CF erased input"), ("ALL", "Three relations pooled")), "abcd"):
        D = WP if R == "ALL" else {m: S0[m][R] for m in O}; k = sum(1 for m in O if D[m]["wrong_p"] < 0.05 and D[m]["wrong_ratio"] > 1)
        fig, ax = P(ttl, "Wrong decisions (%)", grid="x", finding=f"{k} of 8 above chance", red=k >= 4)
        for i, m in enumerate(O):
            r = D[m]; o, c = 100 * r["wrong_viol"], 100 * r["wrong_chance"]; sig = r["wrong_p"] < 0.05 and r["wrong_ratio"] > 1; xs = np.linspace(c, o, 30)
            for j in range(len(xs) - 1): ax.plot(xs[j:j + 2], [i, i], color=np.array(to_rgb(B_M)) * (1 - j / 29) + np.array(to_rgb(R_E if sig else N_M)) * (j / 29), lw=1.8, solid_capstyle="butt", zorder=2)
            ax.scatter([c], [i], s=17, facecolor="white", edgecolor=B_E, linewidth=0.9, zorder=4); ax.scatter([o], [i], s=19, color=R_E if sig else N_E, edgecolor="white", linewidth=0.5, zorder=5)
            ax.text(118, i, f"{r['wrong_ratio']:.2f}\u00d7", ha="right", va="center", fontsize=FS - 0.5, color=R_D if sig else "#8E97A6", fontweight="bold" if sig else "normal")
        rows_y(ax, [MSHORT[m] for m in O], 4.5); ax.set_xlim(-4, 122); ax.set_xticks([0, 50, 100]); done(fig, f"G{l}", l)
    strip("G_legend", [hdot("white", B_E, "Random wrong choice"), hdot(R_E, "white", "Forbidden commits, above it at Holm $p$ < 0.05"), hdot(N_E, "white", "Not above it"), Line2D([], [], ls="none", marker="$\u00d7$", ms=4.5, color=R_D, label="Ratio of the two")])

# ================================================================= H: forest of pooled ratios
def fig_forest():
    F = X["forest"]; groups = []
    for r in F:
        if not groups or groups[-1][0] != r["group"]: groups.append((r["group"], []))
        groups[-1][1].append(r)
    nrow = len(F) + len(groups); Hh = 2.76; L_, R_, B_, T_ = 1.45, 1.95, 0.50, 0.24
    fig = plt.figure(figsize=(TEXTW, Hh)); ax = fig.add_axes([L_ / TEXTW, B_ / Hh, (TEXTW - L_ - R_) / TEXTW, (Hh - B_ - T_) / Hh]); ax.set_xscale("log", base=2); TY = ax.get_yaxis_transform()
    XL, XR = -L_ / (TEXTW - L_ - R_) + 0.02, 1 + R_ / (TEXTW - L_ - R_) - 0.02                          # the full width of the figure, in axes fractions
    lo_x, hi_x = 0.0625, 20; AWf = TEXTW - L_ - R_; CX = [1 + 0.38 / AWf, 1 + 0.86 / AWf, 1 + 1.22 / AWf, 1 + 1.30 / AWf]          # right-hand columns, in axes fractions
    ax.axvspan(lo_x, 1, color="#F0F5FC", lw=0, zorder=0); ax.axvspan(1, hi_x, color="#F5F4FC", lw=0, zorder=0); ax.axvline(1, color="#555555", lw=0.8, ls=(0, (3, 2)), zorder=2)
    y = 0
    for gi, (g, rs) in enumerate(groups):
        ax.plot([XL, XR], [y + 0.06, y + 0.06], color="#C9CED6", lw=0.6, transform=TY, clip_on=False, zorder=1)
        ax.text(XL + 0.01, y + 0.55, g, ha="left", va="center", fontsize=FS + 0.3, fontweight="bold", color=INK, transform=TY, clip_on=False); y += 1
        for k, r in enumerate(rs):
            if k % 2 == 0: ax.add_patch(Rectangle((XL, y + 0.04), XR - XL, 0.92, fc="#F7F8FB", ec="none", transform=TY, clip_on=False, zorder=0.5))
            above, below = r["lo"] > 1, r["hi"] < 1; col = "#5E57A6" if above else ("#4A6FC4" if below else "#A7AFBC"); sz = 16 + 34 * math.sqrt(r["probes"] / 1200)
            ax.plot([r["lo"], r["hi"]], [y + 0.5] * 2, color=col, lw=1.7, solid_capstyle="round", zorder=3, alpha=0.95)
            ax.scatter([r["ratio"]], [y + 0.5], s=sz, color=col if (above or below) else "white", edgecolor="white" if (above or below) else col, linewidth=0.8 if (above or below) else 1.1, zorder=4, marker="D" if r["group"] == "Relation" else "o")
            ax.text(XL + 0.07, y + 0.5, r["label"], ha="left", va="center", fontsize=FS + 0.2, color=INK, transform=TY, clip_on=False)
            ax.text(CX[0], y + 0.5, f"{100 * r['rate']:.1f}", ha="right", va="center", fontsize=FS, color="#3A3A3A", transform=TY, clip_on=False)
            ax.text(CX[1], y + 0.5, f"{100 * r['chance']:.1f}", ha="right", va="center", fontsize=FS, color="#3A3A3A", transform=TY, clip_on=False)
            ax.text(CX[2], y + 0.5, f"{r['ratio']:.2f}", ha="right", va="center", fontsize=FS + 0.2, color=col if (above or below) else INK, fontweight="bold" if (above or below) else "normal", transform=TY, clip_on=False)
            ax.text(CX[3], y + 0.5, f"{r['lo']:.2f} to {r['hi']:.2f}", ha="left", va="center", fontsize=FS - 0.2, color="#5A5A5A", transform=TY, clip_on=False); y += 1
    ax.plot([XL, XR], [y + 0.02, y + 0.02], color="#C9CED6", lw=0.6, transform=TY, clip_on=False, zorder=1)
    for x_, t_, ha_ in ((CX[0], "Rate (%)", "right"), (CX[1], "Chance (%)", "right"), (CX[2], "Ratio", "right"), (CX[3], "95% interval", "left")): ax.text(x_, -0.55, t_, ha=ha_, va="center", fontsize=FS, fontweight="bold", color=INK, transform=TY, clip_on=False)
    ax.text(0.50 * (math.log2(1) - math.log2(lo_x)) / (math.log2(hi_x) - math.log2(lo_x)), -0.55, "below chance", ha="center", va="center", fontsize=FS - 0.2, color="#4A6FC4", style="italic", transform=TY, clip_on=False)
    ax.text(1 - 0.50 * (math.log2(hi_x) - math.log2(1)) / (math.log2(hi_x) - math.log2(lo_x)), -0.55, "above chance", ha="center", va="center", fontsize=FS - 0.2, color="#5E57A6", style="italic", transform=TY, clip_on=False)
    ax.set_ylim(nrow + 0.15, -0.15); ax.set_xlim(lo_x, hi_x); ax.set_xticks([0.125, 0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_xticklabels(["1/8", "1/4", "1/2", "1", "2", "4", "8", "16"]); ax.set_yticks([])
    ax.set_xlabel("Violation rate over the chance level, log scale", fontweight="bold", labelpad=3); ax.grid(True, axis="x", ls="-", color="white", lw=0.8); ax.set_axisbelow(True); ax.tick_params(length=2, width=0.5)
    for s_ in ("top", "right", "left"): ax.spines[s_].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.6); ax.spines["bottom"].set_color(SPINE)
    hs = [Line2D([], [], color="#5E57A6", lw=1.7, marker="o", ms=4.2, mfc="#5E57A6", mec="white", label="95% interval above 1"), Line2D([], [], color="#4A6FC4", lw=1.7, marker="o", ms=4.2, mfc="#4A6FC4", mec="white", label="Below 1"),
          Line2D([], [], color="#A7AFBC", lw=1.7, marker="o", ms=4.2, mfc="white", mec="#A7AFBC", label="Includes 1"), Line2D([], [], ls="none", marker="o", ms=5.2, mfc="#C9CED6", mec="white", label="Marker size, number of test cases")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=4, frameon=False, fontsize=FS - 0.2, handlelength=1.6, columnspacing=1.6, handletextpad=0.5)
    save(fig, "H_hero")

if __name__ == "__main__":
    which = sys.argv[1:] or ["oracle", "site", "cf", "tokens", "stab", "guards", "diag", "forest"]
    for w in which:
        if w == "tokens": V5.fig_tokens()
        elif w == "guards":
            V5.fig_guards(); fig_guards_bars()
            strip("F_legend", rows=[[hbox("#F4F3FC", "#CFCBEF", "Region where the guardrail is better"), hdot(R_E, "white", "Guardrail better"), hdot(B_E, "white", "Guardrail worse"), hdot(N_M, "white", "Unchanged"), H_ref("No change")],
                                    [hbox(R_F, R_E, "Violations removed (e to g), correct commits lost (h)"), hbox(B_F, B_E, "Violations introduced (e to g), correct commits gained (h)"), Line2D([], [], ls="none", marker="$*$", ms=4.5, color=INK, label="McNemar $p$ < 0.05, 0.01, 0.001")]])
        else: globals()["fig_" + w]()
    print("v6 panels written:", which)
