"""Item-level data for the richer figures: per (model, website) rates, per-decision reasoning tokens and latency, per-task paired
rates under each mitigation setting, per-pair commit shares, and the panel's harmful votes per decision."""
import json, collections, csv, random, math
from analysis import scr, L, pred, viol_letters, MODELS, main, tags, NAV, d, EXP
random.seed(5)
API = ["sonnet55", "gemini38", "haiku55", "gpt54mini", "qwen35"]; LOCAL = ["qwen35_9b", "qwen3vl8b", "internvl35"]
COMMIT_REL = ("R2", "R3", "CFE")
G = {}
# 1. per (model, website): element accuracy on the main set, commit-relation violation and chance, R1 violation and chance
site = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0.0, 0, 0, 0.0, 0, 0]))
for m in MODELS:
    for s in main:
        q = scr[s]; p = pred(m, s, 's0')
        if not p: continue
        w = q['website']; a = site[m][w]
        a[6] += 1; a[7] += p in L(q['gold_letters'])
        ch = len(viol_letters(q)) / (int(q['n_options']) + 1); v = p in viol_letters(q)
        if q['relation'] in COMMIT_REL: a[0] += 1; a[1] += v; a[2] += ch
        if q['relation'] == 'R1': a[3] += 1; a[4] += v; a[5] += ch
G['site'] = {m: {w: {'n_c': a[0], 'v_c': a[1], 'ch_c': a[2], 'n_r1': a[3], 'v_r1': a[4], 'ch_r1': a[5], 'n': a[6], 'acc': a[7] / a[6] if a[6] else None,
                     'split': next(scr[s]['split'] for s in main if scr[s]['website'] == w), 'domain': next(scr[s]['domain'] for s in main if scr[s]['website'] == w)} for w, a in site[m].items()} for m in MODELS}
# 2. per decision: reasoning tokens and latency, by outcome (violation / demonstrated control / other), commit-relation and RC probes
rec = {(r['tag'], r['sid'], r['cond']): r for r in d['records'] if r.get('ok')}
G['tok'] = {}
for m in ("gemini38", "haiku55", "gpt54mini", "qwen35"):
    out = {'v': [], 'g': [], 'o': []}
    for s in main:
        q = scr[s]
        if q['relation'] not in COMMIT_REL + ('RC', 'CFF'): continue
        r = rec.get((m, s, 's0')); p = pred(m, s, 's0')
        if not r or not p: continue
        u = r.get('usage') or {}; rt = ((u.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0) or u.get('completion_tokens', 0)
        k = 'v' if p in viol_letters(q) else ('g' if p in L(q['gold_letters']) else 'o')
        out[k].append([rt, r.get('latency') or 0])
    G['tok'][m] = out
# 3. per task: S0 and each mitigation setting, violation rate on commit relations and right-commit rate on RC/CFF, pooled over the four models
MM = ['haiku55', 'qwen35_9b', 'qwen3vl8b', 'internvl35']
G['task'] = {}
for c in ('cvx', 'cv', 's2', 'rg', 'sc', 's1'):
    rows = []
    tasks = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, None])
    for m in MM:
        for s in main:
            q = scr[s]; a, b = pred(m, s, 's0'), pred(m, s, c)
            if not a or not b: continue
            t = tasks[q['annotation_id']]; t[6] = q['relation'] if t[6] is None else t[6]
            if q['relation'] in COMMIT_REL: t[0] += 1; t[1] += a in viol_letters(q); t[2] += b in viol_letters(q)
            if q['relation'] in ('RC', 'CFF'): t[3] += 1; t[4] += a in L(q['gold_letters']); t[5] += b in L(q['gold_letters'])
    G['task'][c] = [{'n_v': t[0], 'v0': t[1], 'v1': t[2], 'n_c': t[3], 'c0': t[4], 'c1': t[5]} for t in tasks.values()]
# 3b. per (model, task): the same two rates, one entry per model and task (the unit of Fig. 13 and of the task table)
G['mtask'] = {}
for c in ('cvx', 'cv', 's2', 'rg', 'sc', 's1'):
    T = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    for m in MM:
        for s in main:
            q = scr[s]; a, b = pred(m, s, 's0'), pred(m, s, c)
            if not a or not b: continue
            t = T[(m, q['annotation_id'])]
            if q['relation'] in COMMIT_REL: t[0] += 1; t[1] += a in viol_letters(q); t[2] += b in viol_letters(q)
            if q['relation'] in ('RC', 'CFF'): t[3] += 1; t[4] += a in L(q['gold_letters']); t[5] += b in L(q['gold_letters'])
    G['mtask'][c] = [{'n_v': t[0], 'v0': t[1], 'v1': t[2], 'n_c': t[3], 'c0': t[4], 'c1': t[5]} for t in T.values()]
# 4. per counterfactual pair: share of models committing in each state, per group and under S1 / CVX
G['pairs'] = {}
for s, q in scr.items():
    if q['relation'] != 'CFF' or s not in main: continue        # the pairs kept for the test
    e = 'CFE_' + s[4:]
    def com(m, sid, cond='s0'):
        p = pred(m, sid, cond); qq = scr[sid]
        return None if not p else p in [l for l in L(qq['repeat_letters']) if tags[sid].get(l) not in NAV]
    row = {}
    for grp, ms in (('all', MODELS), ('api', API), ('local', LOCAL), ('mit', MM)):
        f = [com(m, s) for m in ms]; g = [com(m, e) for m in ms]; f = [x for x in f if x is not None]; g = [x for x in g if x is not None]
        row[grp] = (sum(f) / len(f) if f else None, sum(g) / len(g) if g else None)
    for cond in ('s1', 'cvx'):
        g = [com(m, e, cond) for m in MM]; g = [x for x in g if x is not None]; row['e_' + cond] = sum(g) / len(g) if g else None
    G['pairs'][s[4:]] = row
# 5. panel votes per decision (validation round): harmful votes and every oracle's flag
votes = list(csv.DictReader(open(f'{EXP}/tables/08_panel_votes_r2.csv', encoding='utf-8-sig'))); judges = [c[:-5] for c in votes[0] if c.endswith('_vote')]
G['votes'] = [{'h': sum(1 for j in judges if r[j + '_vote'] == 'H'), 'n': sum(1 for j in judges if r[j + '_vote'] in 'HN'), 'wc': r['oracle_violation'] == '1', 'ea': r['element_wrong'] == '1', 'rl': r['risk_label'] == '1',
               'rl2': r['risk_label'] == '1' and r['chosen_tag'] not in ('a', 'label'), 'rel': r['relation']} for r in votes]
# 6. concentration: how many of the eight models violate each probe, against models that err independently at their own rates.
#    The expectation is the Poisson-binomial distribution of the eight rates; the test shuffles each model's violations over the probes.
import numpy as np
def concentration(rels, n_perm=5000, seed=3):
    ids = [s for s in main if scr[s]['relation'] in rels and all(pred(m, s, 's0') for m in MODELS)]
    V = np.array([[1 if pred(m, s, 's0') in viol_letters(scr[s]) else 0 for m in MODELS] for s in ids]); k = V.sum(1); pm = V.mean(0); pb_ = np.ones(1)
    for p in pm: pb_ = np.convolve(pb_, [1 - p, p])
    rng = np.random.default_rng(seed); hi_o, z_o = int((k >= 4).sum()), int((k == 0).sum()); gh = gz = 0
    for _ in range(n_perm):
        kk = np.column_stack([rng.permutation(V[:, j]) for j in range(V.shape[1])]).sum(1); gh += (kk >= 4).sum() >= hi_o; gz += (kk == 0).sum() >= z_o
    def kappa(a, b):
        po = (a == b).mean(); pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()); return float((po - pe) / (1 - pe)) if pe < 1 else float('nan')
    K = [[kappa(V[:, i], V[:, j]) for j in range(len(MODELS))] for i in range(len(MODELS))]
    return {'n': len(ids), 'obs': np.bincount(k, minlength=9).tolist(), 'exp': (len(ids) * pb_).tolist(), 'hi_obs': hi_o, 'hi_exp': float(len(ids) * pb_[4:].sum()), 'p_hi': (gh + 1) / (n_perm + 1),
            'none_obs': z_o, 'none_exp': float(len(ids) * pb_[0]), 'p_none': (gz + 1) / (n_perm + 1), 'var_obs': float(k.var()), 'var_exp': float((pm * (1 - pm)).sum()), 'kappa': K}
G['conc'] = {key: concentration(rels) for key, rels in (('R1', ('R1',)), ('R2', ('R2',)), ('R3', ('R3',)), ('CFE', ('CFE',)), ('C', ('R2', 'R3', 'CFE')))}
Kc = np.array(G['conc']['C']['kappa']); G['kappa_mean'] = {'api': float(np.mean([Kc[i, j] for i in range(5) for j in range(i + 1, 5)])), 'local': float(np.mean([Kc[i, j] for i in range(5, 8) for j in range(i + 1, 8)])), 'across': float(np.mean([Kc[i, j] for i in range(5) for j in range(5, 8)]))}
# 7. the two groups of models: task-clustered bootstrap of the pooled violation rate of the API models and of the local models per relation
def group_rates(R, n=2000, seed=31):
    per = collections.defaultdict(lambda: [0, 0, 0, 0])
    for s in main:
        q = scr[s]
        if q['relation'] != R: continue
        t = per[q['annotation_id']]
        for m in MODELS:
            p = pred(m, s, 's0')
            if not p: continue
            k = 0 if m in API else 2; t[k] += p in viol_letters(q); t[k + 1] += 1
    T = np.array(list(per.values()), float); rng = np.random.default_rng(seed); Sx = T[rng.integers(0, len(T), size=(n, len(T)))].sum(1)
    d = 100 * Sx[:, 2] / Sx[:, 3] - 100 * Sx[:, 0] / Sx[:, 1]; tot = T.sum(0)
    return {'api': 100 * tot[0] / tot[1], 'local': 100 * tot[2] / tot[3], 'diff': 100 * tot[2] / tot[3] - 100 * tot[0] / tot[1], 'ci': [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], 'p': float(max(1.0 / n, min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))))}
G['group'] = {R: group_rates(R) for R in ('R1', 'R2', 'R3', 'CFE')}
json.dump(G, open('figdata2.json', 'w', encoding='utf-8'), default=float)
for key, c in G['conc'].items(): print(key, 'n', c['n'], 'four or more:', c['hi_obs'], 'expected %.1f' % c['hi_exp'], 'p %.4f' % c['p_hi'], '| none:', c['none_obs'], 'expected %.1f' % c['none_exp'], 'p %.4f' % c['p_none'])
print('kappa', {k: round(v, 2) for k, v in G['kappa_mean'].items()}); print('group', {R: (round(v['diff'], 1), round(v['p'], 4)) for R, v in G['group'].items()})
# quick look
for m, o in G['tok'].items():
    md = lambda xs: sorted(x[0] for x in xs)[len(xs) // 2] if xs else None
    print(m, 'reasoning tokens median: violation', md(o['v']), len(o['v']), '| gold', md(o['g']), len(o['g']), '| other', md(o['o']), len(o['o']))
print('sites per model', {m: len(v) for m, v in G['site'].items()}, '| tasks', {c: len(v) for c, v in G['task'].items()}, '| pairs', len(G['pairs']), '| votes', len(G['votes']))
