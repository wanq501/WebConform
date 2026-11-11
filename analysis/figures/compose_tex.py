# -*- coding: utf-8 -*-
"""Compose every figure of the paper into ONE vector file figs/FigN.pdf from its printed-size panels and legend strip, so the
paper package holds one file per figure. Layout: legend strip, then rows of four panels at 0.245 of the text width. Every composed
figure is then trimmed left and right and scaled so that its drawn content spans exactly the text width (fit_width)."""
import os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); ROOT = os.path.dirname(HERE); DST = os.path.join(ROOT, "figs"); TMP = os.path.join(ROOT, "build_figs")
# figures in the order of the manuscript (M0 is the motivating figure and M1 to M5 are the method figures, written by design/wc_methods.py)
MAP = {"Fig1": ("single", "M0"),
       "Fig2": ("single", "M1"),
       "Fig3": ("single", "M2"),
       "Fig4": ("single", "M3"),
       "Fig5": ("single", "M4"),
       "Fig6": ("single", "M5"),
       "Fig7": ("grid", "Ex", ["L", "abcd", "efgh"]),
       "Fig8": ("grid", "A", ["L", "abcd", "efgh"]),
       "Fig9": ("grid", "Fig10", ["L", "abcd"]),
       "Fig10": ("grid", "Fig9", ["L", "abcd", "efgh"]),
       "Fig11": ("grid", "B", ["W:hero"]),
       "Fig12": ("grid", "B", ["L", "abcd"]),
       "Fig13": ("grid", "Fig12", ["L", "abcd"]),
       "Fig14": ("grid", "H", ["W:hero"]),
       "Fig15": ("grid", "C", ["W:hero"]),
       "Fig16": ("grid", "C", ["L", "abcd"]),
       "Fig17": ("grid", "CaseA", ["L", "abcd", "efgh", "ijkl"]),
       "Fig18": ("grid", "CaseB", ["L", "abcd", "efgh", "ijkl"]),
       "Fig19": ("grid", "CaseC", ["L", "abcd", "efgh", "ijkl"]),
       "Fig20": ("grid", "G", ["L", "abcd"]),
       "Fig21": ("grid", "D", ["L", "abcd", "efgh"]),
       "Fig22": ("grid", "E", ["L", "abcd"]),
       "Fig23": ("grid", "F", ["L", "abcd", "efgh"]),
       "Fig24": ("grid", "Fig11", ["L", "abcd"])}
TEXTW = 390.0                                              # text width of the manuscript, pt
def fit_width(name):
    """Trim the blank margins left and right of a composed figure and scale it to the text width, so that the drawn content of
    EVERY figure spans the same width, the text width, whatever margins its panels carry."""
    import numpy as np
    from PIL import Image
    pdf = os.path.join(DST, name + ".pdf"); png = os.path.join(TMP, name + "_w")
    subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", pdf, png], check=True)
    a = np.asarray(Image.open(png + ".png").convert("L")); cols = np.where((a < 250).any(0))[0]; W = a.shape[1]
    pw = float(re.search(r"Page size:\s+([\d.]+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))     # page width, bp
    left = max(0.0, cols[0] / W * pw - 0.25); right = max(0.0, (W - 1 - cols[-1]) / W * pw - 0.25)
    shutil.copy(pdf, os.path.join(TMP, name + "_raw.pdf"))
    tex = ("\\documentclass[border=0pt]{standalone}\\usepackage{graphicx}\\begin{document}\\includegraphics[trim=%.2fbp 0bp %.2fbp 0bp,clip,width=%.1fpt]{%s}\\end{document}\n" % (left, right, TEXTW, name + "_raw.pdf"))
    open(os.path.join(TMP, name + "_fit.tex"), "w").write(tex)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", name + "_fit.tex"], cwd=TMP, stdout=subprocess.DEVNULL, check=True); shutil.copy(os.path.join(TMP, name + "_fit.pdf"), pdf)
def build(name, spec):
    compose(name, spec); fit_width(name)
def compose(name, spec):
    if spec[0] == "single": shutil.copy(os.path.join(OUT, spec[1] + ".pdf"), os.path.join(DST, name + ".pdf")); return
    src, rows = spec[1], spec[2]; g = lambda f: os.path.join(OUT, f + ".pdf").replace("\\", "/"); parts = []
    for r in rows:
        if r == "L": parts.append("\\includegraphics[width=\\linewidth]{" + g(src + "_legend") + "}")
        elif r.startswith("W:"): parts.append("\\includegraphics[width=\\linewidth]{" + g(src + "_" + r[2:]) + "}")
        else: parts.append("\\hfill".join("\\includegraphics[width=0.245\\linewidth]{" + g(src + c) + "}" for c in r))
    tex = "\\documentclass[border=0pt]{standalone}\\usepackage{graphicx}\\begin{document}\\parbox{390pt}{\\centering\n" + "\\\\[2pt]\n".join(parts) + "}\\end{document}\n"
    open(os.path.join(TMP, name + ".tex"), "w").write(tex)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", name + ".tex"], cwd=TMP, stdout=subprocess.DEVNULL, check=True); shutil.copy(os.path.join(TMP, name + ".pdf"), os.path.join(DST, name + ".pdf"))
if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True); os.makedirs(TMP, exist_ok=True)
    only = sys.argv[1:]
    for k, v in MAP.items():
        if not only or k in only: build(k, v)
    print("composed", sorted(os.listdir(DST)))
