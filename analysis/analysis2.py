"""Deeper analyses for the WebConform paper (oracle v2), on top of analysis.py: splits, domains, factors of R2, completion cue of R3,
oracle validity per relation and judge agreement, mitigation per relation, no-action rates, ranking agreement, cost and latency."""
import json, math, collections, itertools, re, statistics
from analysis import scr, d, L, tags, NAV, viol_letters, pred, pb, exact_p, holm, MODELS, NAME, SHORT, main, EXP
import csv
N = json.load(open('numbers.json', encoding='utf-8'))
X = {}
def rate(ids, tag, cond='s0'):
    ids = [s for s in ids if pred(tag, s, cond)]
    if not ids: return None
    v = sum(1 for s in ids if pred(tag, s, cond) in viol_letters(scr[s])); ch = sum(len(viol_letters(scr[s])) / (int(scr[s]['n_options']) + 1) for s in ids)
    return {'n': len(ids), 'v': v, 'ch': ch}
import random as _rb
_rb.seed(23)
def pool(ids, models=MODELS, cond='s0'):
    """pooled violation rate against chance over several models. The exact test treats the decisions as independent; the interval of the
    ratio comes from a bootstrap that resamples tasks, so that the decisions of all models on the probes of one task stay together."""
    a = [rate(ids, m, cond) for m in models]; a = [x for x in a if x]
    n = sum(x['n'] for x in a); v = sum(x['v'] for x in a); ch = sum(x['ch'] for x in a)
    ps = [len(viol_letters(scr[s])) / (int(scr[s]['n_options']) + 1) for m in models for s in ids if pred(m, s, cond)]
    per = collections.defaultdict(lambda: [0, 0.0])
    for m in models:
        for s in ids:
            p = pred(m, s, cond)
            if p: t_ = per[scr[s]['annotation_id']]; t_[0] += p in viol_letters(scr[s]); t_[1] += len(viol_letters(scr[s])) / (int(scr[s]['n_options']) + 1)
    keys = list(per); bs = []
    for _ in range(1000 if keys else 0):
        smp = [per[_rb.choice(keys)] for _ in keys]; c_ = sum(x[1] for x in smp)
        if c_ > 0: bs.append(sum(x[0] for x in smp) / c_)
    bs.sort(); lo, hi = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if bs else (float('nan'), float('nan'))
    return {'n': n, 'viol': v / n if n else float('nan'), 'chance': ch / n if n else float('nan'), 'ratio': v / ch if ch else float('nan'), 'p': exact_p(v, ps) if ps else float('nan'), 'v': v, 'lo': lo, 'hi': hi, 'tasks': len(keys)}
REL = ('R1', 'R2', 'R3', 'CFE')
# ---------- 1. splits (pooled over the eight models)
SPL = ('test_task', 'test_website', 'test_domain')
X['split'] = {sp: {R: pool([s for s in main if scr[s]['split'] == sp and scr[s]['relation'] == R]) for R in REL} for sp in SPL}
X['split_n'] = {sp: {'probes': sum(1 for s in main if scr[s]['split'] == sp), 'tasks': len({scr[s]['annotation_id'] for s in main if scr[s]['split'] == sp}), 'sites': len({scr[s]['website'] for s in main if scr[s]['split'] == sp})} for sp in SPL}
# ---------- 2. domains
DOM = sorted({scr[s]['domain'] for s in main})
X['domain'] = {dm: {'R1': pool([s for s in main if scr[s]['domain'] == dm and scr[s]['relation'] == 'R1']), 'C': pool([s for s in main if scr[s]['domain'] == dm and scr[s]['relation'] in ('R2', 'R3', 'CFE')]),
                    'tasks': len({scr[s]['annotation_id'] for s in main if scr[s]['domain'] == dm}), 'sites': len({scr[s]['website'] for s in main if scr[s]['domain'] == dm})} for dm in DOM}
# ---------- 3. R2 factors
r2 = [s for s in main if scr[s]['relation'] == 'R2']
X['r2_dist'] = {k: {'pooled': pool([s for s in r2 if scr[s]['steps_before_commit'] == str(k)]), **{m: rate([s for s in r2 if scr[s]['steps_before_commit'] == str(k)], m) for m in MODELS}} for k in (1, 2, 3)}
def ctype(t):
    t = (t or '').lower()
    if re.search(r'add (to )?(cart|bag|basket)|add to my', t): return 'Add to cart / bag'
    if re.search(r'follow|like|subscribe|vote|upvote', t): return 'Follow, like, subscribe'
    if re.search(r'\bsave\b|wish ?list|favou?rite|watch ?list|add to (list|calendar)', t): return 'Save to a list'
    if re.search(r'post|publish|reply|comment|send', t): return 'Post or send'
    if re.search(r'pay|buy|purchase|order|donate|confirm', t): return 'Pay, buy, order'
    return 'Other'
X['r2_ctype'] = {}
for c in ('Add to cart / bag', 'Follow, like, subscribe', 'Save to a list', 'Post or send', 'Pay, buy, order', 'Other'):
    ids = [s for s in r2 if ctype(scr[s]['commit_action']) == c]
    if ids: X['r2_ctype'][c] = dict(pool(ids), probes=len(ids), tasks=len({scr[s]['annotation_id'] for s in ids}))
def gop(a):
    m = re.search(r'->\s*(CLICK|TYPE|SELECT|HOVER|ENTER)', a or ''); return m.group(1) if m else 'OTHER'
X['r2_pending'] = {}
for op in ('TYPE', 'SELECT', 'CLICK'):
    ids = [s for s in r2 if gop(scr[s]['gold_action']) == op]
    if ids: X['r2_pending'][op] = dict(pool(ids), probes=len(ids))
# ---------- 4. R3 completion cue
r3 = [s for s in main if scr[s]['relation'] == 'R3']
X['r3_cue'] = {cue: dict(pool([s for s in r3 if (scr[s]['evidence_rule'] in ('1', 'True', 'true')) == (cue == 'visible')]), probes=sum(1 for s in r3 if (scr[s]['evidence_rule'] in ('1', 'True', 'true')) == (cue == 'visible'))) for cue in ('visible', 'not visible')}
# ---------- 5. ranking agreement between element accuracy and conformance
acc = {m: N['s0'][m]['acc'] for m in MODELS}
conf = {m: 1 - sum(N['s0'][m][R]['viol'] * N['s0'][m][R]['n'] for R in ('R2', 'R3', 'CFE')) / sum(N['s0'][m][R]['n'] for R in ('R2', 'R3', 'CFE')) for m in MODELS}
def kendall(a, b):
    ks = list(a); c = dd = 0
    for i, j in itertools.combinations(ks, 2):
        s = (a[i] - a[j]) * (b[i] - b[j]); c += s > 0; dd += s < 0
    return (c - dd) / (c + dd) if c + dd else float('nan')
X['rank'] = {'acc': acc, 'conf': conf, 'tau': kendall(acc, conf), 'acc_rank': {m: r + 1 for r, m in enumerate(sorted(MODELS, key=lambda m: -acc[m]))}, 'conf_rank': {m: r + 1 for r, m in enumerate(sorted(MODELS, key=lambda m: -conf[m]))}}
# ---------- 6. oracle validity per relation and judge agreement (Fleiss kappa)
X['panel_rel'] = {}; X['kappa'] = {}
for rn in ('r1', 'r2'):
    rows = list(csv.DictReader(open(f'{EXP}/tables/08_panel_votes_{rn}.csv', encoding='utf-8-sig')))
    judges = [c[:-5] for c in rows[0].keys() if c.endswith('_vote')]
    per = {}
    for R in ('R1', 'R2', 'R3', 'CFE', 'RC', 'CFF'):
        sub = [r for r in rows if r['relation'] == R and r['reference'] in ('H', 'N')]
        if not sub: continue
        tp = sum(1 for r in sub if r['oracle_violation'] == '1' and r['reference'] == 'H'); fp = sum(1 for r in sub if r['oracle_violation'] == '1' and r['reference'] == 'N')
        fn = sum(1 for r in sub if r['oracle_violation'] != '1' and r['reference'] == 'H'); tn = len(sub) - tp - fp - fn
        per[R] = {'n': len(sub), 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, 'harmful': tp + fn}
    X['panel_rel'][rn] = per
    full = [r for r in rows if all(r[j + '_vote'] in ('H', 'N') for j in judges)]
    n, k = len(full), len(judges)
    P = [((sum(1 for j in judges if r[j + '_vote'] == 'H')) * (sum(1 for j in judges if r[j + '_vote'] == 'H') - 1) + (sum(1 for j in judges if r[j + '_vote'] == 'N')) * (sum(1 for j in judges if r[j + '_vote'] == 'N') - 1)) / (k * (k - 1)) for r in full]
    pH = sum(sum(1 for j in judges if r[j + '_vote'] == 'H') for r in full) / (n * k); Pe = pH ** 2 + (1 - pH) ** 2; Pbar = sum(P) / n
    X['kappa'][rn] = {'n': n, 'fleiss': (Pbar - Pe) / (1 - Pe), 'pairwise': N['panel'][rn]['pairwise'], 'unanimous': sum(1 for r in full if len({r[j + '_vote'] for j in judges}) == 1) / n,
                      'per_judge_H': {j: sum(1 for r in rows if r[j + '_vote'] == 'H') / max(1, sum(1 for r in rows if r[j + '_vote'] in ('H', 'N'))) for j in judges}}
# ---------- 7. mitigation per relation (pooled over the four models), S1 history, no-action rates
MIT_M = list(N['mitigation']); CONDS = ('s0', 's1', 'cvx', 'cv', 'sc', 'rg', 's2')
X['mit_rel'] = {}
for c in CONDS:
    row = {}
    for R in ('R2', 'R3', 'CFE'):
        ids = [s for s in main if scr[s]['relation'] == R]
        a = [rate(ids, m, c) for m in MIT_M]; a = [x for x in a if x]
        row[R] = {'n': sum(x['n'] for x in a), 'viol': sum(x['v'] for x in a) / max(1, sum(x['n'] for x in a))}
    co = [s for s in main if scr[s]['relation'] in ('RC', 'CFF')]
    nn = kk = none = 0
    for m in MIT_M:
        for s in co:
            p = pred(m, s, c)
            if p: nn += 1; kk += p in L(scr[s]['gold_letters']); none += p == scr[s]['none_letter']
    row['commit'] = {'n': nn, 'rate': kk / max(1, nn), 'none': none / max(1, nn)}
    allp = [s for s in main if scr[s]['relation'] in ('R2', 'R3', 'CFE', 'RC', 'CFF')]
    tot = sum(1 for m in MIT_M for s in allp if pred(m, s, c)); nonea = sum(1 for m in MIT_M for s in allp if pred(m, s, c) == scr[s]['none_letter'])
    row['none_all'] = nonea / max(1, tot); row['n_all'] = tot
    X['mit_rel'][c] = row
# paired S1 vs S0 on R2/R3 (history)
fx = br = 0
for m in MIT_M:
    for s in main:
        if scr[s]['relation'] in ('R2', 'R3') and pred(m, s, 's0') and pred(m, s, 's1'):
            a0 = pred(m, s, 's0') in viol_letters(scr[s]); a1 = pred(m, s, 's1') in viol_letters(scr[s]); fx += a0 and not a1; br += a1 and not a0
X['s1_pair'] = {'fixed': fx, 'introduced': br, 'p': pb(fx, br)}
# ---------- 8. cost, tokens and latency per model (S0 answers)
X['cost'] = {}
for m in MODELS:
    recs = [r for r in d['records'] if r['tag'] == m and r['cond'] == 's0' and r.get('ok')]
    u = [r.get('usage') or {} for r in recs]
    pt = [x.get('prompt_tokens', 0) for x in u if x]; ct = [x.get('completion_tokens', 0) for x in u if x]; rt = [((x.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0) for x in u if x]
    lat = sorted(r['latency'] for r in recs if r.get('latency')); cost = sum((x.get('cost') or 0) for x in u)
    X['cost'][m] = {'n': len(recs), 'prompt': statistics.mean(pt) if pt else float('nan'), 'completion': statistics.mean(ct) if ct else float('nan'), 'reasoning': statistics.mean(rt) if rt else 0.0,
                    'lat_med': lat[len(lat) // 2] if lat else float('nan'), 'lat_p90': lat[int(0.9 * len(lat))] if lat else float('nan'), 'usd_per_1k': 1000 * cost / len(recs) if recs and cost else 0.0}
X['split_C'] = {sp: pool([s for s in main if scr[s]['split'] == sp and scr[s]['relation'] in ('R2', 'R3', 'CFE')]) for sp in SPL}
# groups of models on the two precondition tests, and the probes and decisions that enter the analysis
GRP = {'top3': ['sonnet55', 'gemini38', 'haiku55'], 'api': ['sonnet55', 'gemini38', 'haiku55', 'gpt54mini', 'qwen35'], 'local': ['qwen35_9b', 'qwen3vl8b', 'internvl35'], 'all': MODELS}
X['grp'] = {g: {R: pool([s for s in main if scr[s]['relation'] == R], models=ms) for R in REL} for g, ms in GRP.items()}
from analysis import CF_VALID, ans
kept = [s for s, q in scr.items() if q['valid'] == '1' and (q['relation'] not in ('CFF', 'CFE') or s[4:] in CF_VALID) and 'dev' not in L(q['subsets'])]
X['kept'] = {'probes': len(kept), 'by_rel': dict(collections.Counter(scr[s]['relation'] for s in kept)), 'tasks': len({scr[s]['annotation_id'] for s in kept}), 'websites': len({scr[s]['website'] for s in kept}),
             'main': len(main), 'main_tasks': len({scr[s]['annotation_id'] for s in main}), 'main_websites': len({scr[s]['website'] for s in main}),
             'decisions_all': len(ans), 'decisions_main': sum(1 for (t_, s, c) in ans if s in main), 'decisions_main_s0': sum(1 for (t_, s, c) in ans if s in main and c == 's0')}
# ---------- forest: the pooled ratios reported in the tables, with their task-clustered intervals, as one list for the figure
def frow_(group, label, d, probes): return {'group': group, 'label': label, 'probes': probes, 'ratio': d['ratio'], 'lo': d['lo'], 'hi': d['hi'], 'p': d['p'], 'rate': d['viol'], 'chance': d['chance']}
C_ = [s for s in main if scr[s]['relation'] in ('R2', 'R3', 'CFE')]
FOR = [frow_('Relation', n_, X['grp']['all'][R], sum(1 for s in main if scr[s]['relation'] == R)) for R, n_ in (('R1', 'R1 safety'), ('R2', 'R2 precondition'), ('R3', 'R3 idempotency'), ('CFE', 'CF erased input'))]
FOR += [frow_('Test split', n_, X['split_C'][sp], sum(1 for s in C_ if scr[s]['split'] == sp)) for sp, n_ in (('test_task', 'Cross-task'), ('test_website', 'Cross-website'), ('test_domain', 'Cross-domain'))]
FOR += [frow_('Domain', dm, X['domain'][dm]['C'], sum(1 for s in C_ if scr[s]['domain'] == dm)) for dm in DOM]
FOR += [frow_('R2, steps to commit', f'{k} step' + ('s' if k > 1 else ''), X['r2_dist'][k]['pooled'], sum(1 for s in r2 if scr[s]['steps_before_commit'] == str(k))) for k in (1, 2, 3)]
FOR += [frow_('R2, commit type', n_, X['r2_ctype'][c_], sum(1 for s in r2 if ctype(scr[s]['commit_action']) == c_)) for c_, n_ in (('Add to cart / bag', 'Add to cart or bag'), ('Follow, like, subscribe', 'Follow, like, subscribe'), ('Save to a list', 'Save to a list'))]
X['forest'] = FOR
json.dump(X, open('numbers2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
# ---------- quick print
f = lambda x: f'{100 * x:.1f}'
for sp in SPL: print(sp, X['split_n'][sp], ' '.join(f"{R} {f(X['split'][sp][R]['viol'])}/{f(X['split'][sp][R]['chance'])}" for R in REL))
for dm in DOM: print(dm, X['domain'][dm]['tasks'], 'R1', f(X['domain'][dm]['R1']['viol']), '/', f(X['domain'][dm]['R1']['chance']), '| C', f(X['domain'][dm]['C']['viol']), '/', f(X['domain'][dm]['C']['chance']), X['domain'][dm]['C']['n'])
for k in (1, 2, 3): p = X['r2_dist'][k]['pooled']; print('dist', k, p['n'], f(p['viol']), f(p['chance']), round(p['ratio'], 2))
for c, p in X['r2_ctype'].items(): print('ctype', c, p['probes'], f(p['viol']), f(p['chance']), round(p['ratio'], 2))
for c, p in X['r2_pending'].items(): print('pending', c, p['probes'], f(p['viol']), f(p['chance']))
for c, p in X['r3_cue'].items(): print('r3', c, p['probes'], f(p['viol']), f(p['chance']))
print('kendall tau acc vs conformance', round(X['rank']['tau'], 3))
for rn in ('r1', 'r2'): print(rn, 'fleiss', round(X['kappa'][rn]['fleiss'], 3), 'unanimous', round(X['kappa'][rn]['unanimous'], 3), {R: (v['tp'], v['fp'], v['fn'], v['tn']) for R, v in X['panel_rel'][rn].items()})
for c in CONDS: r = X['mit_rel'][c]; print(c, ' '.join(f"{R} {f(r[R]['viol'])}" for R in ('R2', 'R3', 'CFE')), 'commit', f(r['commit']['rate']), 'none', f(r['none_all']))
print('S1 vs S0 on R2/R3', X['s1_pair'])
for m in MODELS: c = X['cost'][m]; print(m, int(c['prompt']), round(c['completion'], 1), round(c['reasoning'], 1), round(c['lat_med'], 2), round(c['usd_per_1k'], 3))
