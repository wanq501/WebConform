"""Reproduce the paper from the released data.

    python reproduce.py               numbers and tables, checked against the reference outputs in analysis/
    python reproduce.py --figures     also the 24 figures (needs matplotlib, cairosvg and pdflatex)
    python reproduce.py --supplement  also Supplementary File 1 and the data files of Supplementary File 2 (needs pdflatex)
    python reproduce.py --all         everything

Every output is deterministic: the numbers are byte-identical to the reference outputs on any machine."""
import argparse, filecmp, os, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.abspath(__file__)); AN = os.path.join(ROOT, "analysis")

def run(script, cwd, *args):
    t0 = time.time(); print(f"> python {script} {' '.join(args)}".rstrip(), flush=True)
    r = subprocess.run([sys.executable, script, *args], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(f"failed: {script}")
    print(f"  done in {time.time() - t0:.0f} s", flush=True)

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--figures", action="store_true"); a.add_argument("--supplement", action="store_true"); a.add_argument("--all", action="store_true")
    o = a.parse_args(); refs = ("numbers.json", "numbers2.json", "figdata.json", "figdata2.json", "oracle_stats.json")
    keep = tempfile.mkdtemp()
    for f in refs: shutil.copy(os.path.join(AN, f), keep)
    for s in ("analysis.py", "analysis2.py", "figdata.py", "figdata2.py", "oracle_stats.py", "tables.py"): run(s, AN)
    same = [f for f in refs if filecmp.cmp(os.path.join(keep, f), os.path.join(AN, f), shallow=False)]
    print(f"reference outputs reproduced byte for byte: {len(same)} of {len(refs)}" + ("" if len(same) == len(refs) else f", different: {sorted(set(refs) - set(same))}"))
    print(f"tables written to analysis/tables ({len(os.listdir(os.path.join(AN, 'tables')))} files)")
    if o.figures or o.all:
        FG = os.path.join(AN, "figures")
        run(os.path.join("design", "wc_methods.py"), FG, "out")
        for s in ("figs_v6.py", "figs_3d_v3.py", "figs_cases.py", "compose_tex.py"): run(s, FG)
        print(f"figures written to analysis/figs ({len([f for f in os.listdir(os.path.join(AN, 'figs')) if f.endswith('.pdf')])} files)")
    if o.supplement or o.all:
        SP = os.path.join(AN, "supplement")
        for s in ("supp_compute.py", "supp_figs.py", "supp_tex.py"): run(s, SP)
        print("Supplementary File 1 written to analysis/supplement/supplementary.pdf, the data files of File 2 to analysis/supplement/data")
    shutil.rmtree(keep)

if __name__ == "__main__": main()
