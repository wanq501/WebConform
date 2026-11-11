"""Per-figure data for the redrawn figures: task-clustered bootstrap distributions, domain x relation rates, per-model R2 by
distance, confusion counts, counterfactual flows and intervals, run-by-run outcomes, and paired changes per relation."""
import json, math, random, collections
from analysis import scr, L, pred, viol_letters, MODELS, main, tags, NAV, pb
from analysis2 import pool
random.seed(11)
F = {}
REL = ('R1', 'R2', 'R3', 'CFE')
# 1. task-clustered bootstrap of the S0 violation rate per model and relation (1,000 resamples), and of the ratio to chance
F['boot'] = {}
for m in MODELS:
    for R in REL:
        ids = [s for s in main if scr[s]['relation'] == R and pred(m, s, 's0')]
        by = collections.defaultdict(list)
        for s in ids: by[scr[s]['annotation_id']].append((1 if pred(m, s, 's0') in viol_letters(scr[s]) else 0, len(viol_letters(scr[s])) / (int(scr[s]['n_options']) + 1)))
        keys = list(by); rates, ratios = [], []
        for _ in range(1000):
            smp = [by[random.choice(keys)] for _ in keys]; n = sum(len(x) for x in smp); v = sum(a for x in smp for a, _ in x); c = sum(b for x in smp for _, b in x)
            rates.append(v / n); ratios.append(v / c if c else float('nan'))
        F['boot'][f'{m}|{R}'] = {'rate': rates, 'ratio': ratios}
# 2. domain x relation, pooled over models
F['dom_rel'] = {dm: {R: pool([s for s in main if scr[s]['domain'] == dm and scr[s]['relation'] == R]) for R in REL} for dm in sorted({scr[s]['domain'] for s in main})}
# 3. counterfactual flows and intervals (button-commit pairs)
def cp_ci(k, n, a=0.05):
    from math import comb
    def cdf(x, p): return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))
    lo = 0.0 if k == 0 else _bis(lambda p: 1 - cdf(k - 1, p) - a / 2)
    hi = 1.0 if k == n else _bis(lambda p: cdf(k, p) - a / 2, inc=False)
    return lo, hi
def _bis(f, inc=True):
    a, b = 0.0, 1.0
    for _ in range(60):
        c = (a + b) / 2; v = f(c)
        if (v > 0) == inc: b = c
        else: a = c
    return (a + b) / 2
F['cf'] = {}
for m in MODELS:
    pairs = collections.defaultdict(dict)
    for s, q in scr.items():
        if q['relation'] not in ('CFF', 'CFE') or s not in main: continue        # the pairs kept for the test
        p = pred(m, s, 's0')
        if not p: continue
        commit = p in [l for l in L(q['repeat_letters']) if tags[s].get(l) not in NAV]; gold = p in L(q['gold_letters'])
        out = 'commit' if commit else ('fill' if (q['relation'] == 'CFE' and gold) else ('none' if p == q['none_letter'] else 'other'))
        pairs[s[4:]][q['relation']] = out
    full = [v for v in pairs.values() if len(v) == 2]; n = len(full)
    flow = collections.Counter((v['CFF'], v['CFE']) for v in full)
    fc = sum(1 for v in full if v['CFF'] == 'commit'); ec = sum(1 for v in full if v['CFE'] == 'commit'); fi = sum(1 for v in full if v['CFE'] == 'fill')
    # bootstrap CI of the sensitivity (filled commit rate minus erased commit rate) over pairs
    sens = []
    for _ in range(2000):
        smp = [random.choice(full) for _ in full]; sens.append((sum(1 for v in smp if v['CFF'] == 'commit') - sum(1 for v in smp if v['CFE'] == 'commit')) / n)
    sens.sort()
    F['cf'][m] = {'n': n, 'flow': {f'{a}>{b}': c for (a, b), c in flow.items()}, 'filled': fc, 'erased': ec, 'fill': fi,
                  'ci_filled': cp_ci(fc, n), 'ci_erased': cp_ci(ec, n), 'ci_fill': cp_ci(fi, n), 'sens': (fc - ec) / n, 'ci_sens': (sens[50], sens[1949])}
# 4. run-by-run outcome per probe on the stability probes
F['runs'] = {}
for m in MODELS:
    ids = sorted([s for s in main if 'jit' in L(scr[s]['subsets']) and all(pred(m, s, c) for c in ('s0', 's0r2', 's0r3'))])
    if not ids: continue
    def cat(s, c):
        p = pred(m, s, c); q = scr[s]
        return 'v' if p in viol_letters(q) else ('g' if p in L(q['gold_letters']) else ('n' if p == q['none_letter'] else 'o'))
    F['runs'][m] = [[cat(s, c) for c in ('s0', 's0r2', 's0r3')] for s in ids]
# 5. paired changes against S0, per relation and setting, pooled over the four mitigation models
MM = ['haiku55', 'qwen35_9b', 'qwen3vl8b', 'internvl35']
F['pairs'] = {}
for c in ('s1', 'cvx', 'cv', 'sc', 'rg', 's2'):
    for R in ('R2', 'R3', 'CFE', 'commit'):
        up = down = 0
        for m in MM:
            for s in main:
                q = scr[s]
                if (R == 'commit' and q['relation'] not in ('RC', 'CFF')) or (R != 'commit' and q['relation'] != R): continue
                a, b = pred(m, s, 's0'), pred(m, s, c)
                if not a or not b: continue
                if R == 'commit':
                    x0, x1 = a in L(q['gold_letters']), b in L(q['gold_letters']); up += (x1 and not x0); down += (x0 and not x1)
                else:
                    x0, x1 = a in viol_letters(q), b in viol_letters(q); up += (x0 and not x1); down += (x1 and not x0)
        F['pairs'][f'{c}|{R}'] = {'up': up, 'down': down, 'p': pb(up, down)}
json.dump(F, open('figdata.json', 'w', encoding='utf-8'), default=float)
print('figdata written', len(F['boot']), list(F['runs'])[:3], F['cf']['sonnet55']['flow'], F['pairs']['s2|commit'])
