"""Score decisions with the oracle of WebConform: per relation the violation rate, the chance level, their ratio and the exact test.

    python -m webconform.score --bundle probes.zip --decisions s0.jsonl [--ids main_set.txt]"""
import argparse, collections, json
from . import bundle
from .oracle import chance, exact_p, forbidden

def score(cases, decisions):
    by = collections.defaultdict(list)
    for q in cases:
        if q["sid"] in decisions and q["relation"] in ("R1", "R2", "R3", "CFE"): by[q["relation"]].append((decisions[q["sid"]] in forbidden(q), chance(q)))
    out = {}
    for r, rows in sorted(by.items()):
        k = sum(v for v, _ in rows); ps = [p for _, p in rows]; n = len(rows)
        out[r] = {"n": n, "violations": k, "rate": k / n, "chance": sum(ps) / n, "ratio": (k / sum(ps)) if sum(ps) else float("nan"), "p": exact_p(k, ps)}
    return out

def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--bundle", required=True); a.add_argument("--decisions", required=True); a.add_argument("--ids")
    o = a.parse_args(argv)
    ids = [l.strip() for l in open(o.ids, encoding="utf-8") if l.strip()] if o.ids else None
    _, cases = bundle.load(o.bundle, ids); d = {}
    for line in open(o.decisions, encoding="utf-8"):
        r = json.loads(line); d[r["test_case"]] = r.get("answer")
    print(f"{'relation':8s} {'n':>5s} {'viol.':>6s} {'rate':>7s} {'chance':>7s} {'ratio':>6s} {'p':>7s}")
    for r, v in score(cases, d).items(): print(f"{r:8s} {v['n']:5d} {v['violations']:6d} {100 * v['rate']:6.1f}% {100 * v['chance']:6.1f}% {v['ratio']:6.2f} {v['p']:7.3f}")

if __name__ == "__main__": main()
