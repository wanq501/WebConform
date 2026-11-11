# -*- coding: utf-8 -*-
"""Supplementary material of WebConform, part 1: every number of the supplement, computed from the console export with the
definitions of analysis.py (the same main set, oracle, chance level and counterfactual pairs as the paper).
    WC_EXPORT=DIR WC_CURATED=DIR python supp_compute.py      -> supp_data.json and data/*.csv"""
import collections, contextlib, csv, io, json, math, os, random, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
with contextlib.redirect_stdout(io.StringIO()):
    import analysis as A
EXP, CUR = A.EXP, os.environ.get('WC_CURATED', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'curated'))
L, scr, tags, MODELS, NAV = A.L, A.scr, A.tags, A.MODELS, A.NAV
MAIN = list(A.main); OUT = {}
os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
def gold(s): return set(L(scr[s]['gold_letters']))
def viol(s): return set(A.viol_letters(scr[s]))
def none(s): return scr[s]['none_letter']
REL = ('R1', 'R2', 'R3', 'RC', 'CFF', 'CFE')
# ------------------------------------------------------------------ S2 the test suite
valid = [s for s, q in scr.items() if q['valid'] == '1' and (q['relation'] not in ('CFF', 'CFE') or s[4:] in A.CF_VALID)]
SPL = ('test_task', 'test_website', 'test_domain')
OUT['suite'] = {r: {'all': {sp: sum(1 for s in valid if scr[s]['relation'] == r and scr[s]['split'] == sp) for sp in SPL}, 'main': sum(1 for s in MAIN if scr[s]['relation'] == r),
                    'bank': sum(1 for q in scr.values() if q['relation'] == r)} for r in REL}
OUT['suite_tasks'] = {sp: len({q['annotation_id'] for q in scr.values() if q['split'] == sp}) for sp in SPL}
OUT['suite_sites'] = {sp: len({q['website'] for q in scr.values() if q['split'] == sp}) for sp in SPL}
OUT['options'] = {}
for r in REL:
    ss = [s for s in MAIN if scr[s]['relation'] == r]; n = [int(scr[s]['n_options']) for s in ss]; f = [len(viol(s)) for s in ss]; p = [A.pi_(s) for s in ss]
    OUT['options'][r] = {'n': len(ss), 'mean': st.mean(n), 'median': st.median(n), 'min': min(n), 'max': max(n), 'forb': st.mean(f), 'pi': 100 * st.mean(p), 'full24': 100 * sum(1 for x in n if x >= 24) / len(n)}
ct = collections.Counter()
for s in valid:
    if scr[s]['relation'] == 'R2':
        a = scr[s]['commit_action']; txt = a.split('->')[0].split(']', 1)[-1].strip().lower() if a else ''
        ct[' '.join(txt.split())[:28]] += 1
OUT['r2_commits'] = ct.most_common(12); OUT['r2_valid'] = sum(ct.values())
OUT['r2_steps'] = dict(collections.Counter(scr[s]['steps_before_commit'] for s in valid if scr[s]['relation'] == 'R2'))
# ------------------------------------------------------------------ S4 counterfactual pairs, the filter cascade
D = {c['sid']: c for c in json.load(open(os.path.join(CUR, 'cases.json'), encoding='utf-8'))['cases']}
def opts(sid): return [(o['letter'], o['tag'], (o.get('text') or '').strip()) for o in D[sid]['options']] if sid in D else None
pairs = []
for pid in A.CF_ALL:
    e = scr['CFE_' + pid]; f = scr.get('CFF_' + pid); t = tags['CFE_' + pid]
    field = [t.get(l) for l in L(e['gold_letters'])]; commit = [l for l in L(e['repeat_letters']) if t.get(l) not in NAV]
    c1 = e['task_intent'] == 'write'; c2 = c1 and bool(field) and all(x in ('input', 'textarea') for x in field); c3 = c2 and bool(commit); c4 = c3 and pid[:8] not in A.CF_INSPECTION_DROP
    fo, eo = opts('CFF_' + pid), opts('CFE_' + pid)                                                  # controls of the recorded list missing from the erased list
    ndiff = sum((collections.Counter((t, x) for _, t, x in fo) - collections.Counter((t, x) for _, t, x in eo)).values()) if fo and eo else None
    fl = [(o.get('text') or '') for o in D.get('CFE_' + pid, {'options': []})['options'] if o['letter'] in L(e['gold_letters'])]
    cm = [(o.get('text') or '') for o in D.get('CFE_' + pid, {'options': []})['options'] if o['letter'] in L(e['repeat_letters'])]
    row = {'pid': pid, 'website': e['website'], 'task': e['task'], 'field': fl[0] if fl else '', 'field_tag': field[0] if field else '', 'commit': cm[0] if cm else '', 'write': c1, 'typed': c2, 'state': c3, 'kept': c4, 'ndiff': ndiff}
    if c4:
        row['filled'] = sum(1 for m in MODELS if A.pred(m, 'CFF_' + pid, 's0') in gold('CFF_' + pid)); row['erased'] = sum(1 for m in MODELS if A.pred(m, 'CFE_' + pid, 's0') in viol('CFE_' + pid))
        row['fill_input'] = sum(1 for m in MODELS if A.pred(m, 'CFE_' + pid, 's0') in gold('CFE_' + pid))
    pairs.append(row)
OUT['pairs'] = pairs; OUT['cascade'] = [len(pairs), sum(p['write'] for p in pairs), sum(p['typed'] for p in pairs), sum(p['state'] for p in pairs), sum(p['kept'] for p in pairs)]
# ------------------------------------------------------------------ S5 decision anatomy in the vanilla setting
def kind(s, p):
    if p is None: return 'unparsed'
    if p == none(s): return 'none'
    if p in gold(s): return 'correct'
    if p in viol(s): return 'forbidden'
    tg = tags[s].get(p)
    if tg in NAV: return 'nav'
    if p in set(L(scr[s]['write_letters'])) | set(L(scr[s]['strict_letters'])): return 'otherwrite'
    if tg in ('input', 'textarea', 'select'): return 'field'
    return 'other'
KINDS = ('correct', 'forbidden', 'otherwrite', 'nav', 'field', 'other', 'none', 'unparsed')
anat = {}
for r in REL:
    for m in MODELS + ['all']:
        ms = MODELS if m == 'all' else [m]; c = collections.Counter(kind(s, A.pred(mm, s, 's0')) for s in MAIN if scr[s]['relation'] == r for mm in ms); n = sum(c.values())
        anat[f'{r}|{m}'] = {k: 100 * c[k] / n for k in KINDS} | {'n': n}
OUT['anatomy'] = anat
# ------------------------------------------------------------------ S5 position of the forbidden control and number of options
def rate(rows):
    v = sum(x[0] for x in rows); p = sum(x[1] for x in rows); n = len(rows); return {'n': n, 'vr': 100 * v / n, 'pi': 100 * p / n, 'ratio': v / p if p else float('nan')}
pos = collections.defaultdict(list); nopt = collections.defaultdict(list)
for s in MAIN:
    q = scr[s]
    if q['relation'] not in ('R2', 'R3', 'CFE'): continue
    g = sorted(gold(s)); fb = sorted(viol(s)); order = q['option_tags'] and [x.split(':')[0] for x in L(q['option_tags'])]
    where = 'after' if g and fb and order.index(fb[0]) > order.index(g[0]) else 'before'
    n = int(q['n_options']); nb = '24' if n >= 24 else ('13 to 23' if n >= 13 else '12 or fewer')
    for m in MODELS:
        x = (A.pred(m, s, 's0') in viol(s), A.pi_(s)); pos[(q['relation'], where)].append(x); pos[('all', where)].append(x); nopt[nb].append(x)
OUT['position'] = {f'{r}|{w}': rate(v) for (r, w), v in pos.items()}; OUT['nopt'] = {k: rate(v) for k, v in nopt.items()}
# ------------------------------------------------------------------ S5 leave one website out, pooled over the eight MLLMs
def pooled(rel, drop=None, models=MODELS):
    rows = [(A.pred(m, s, 's0') in viol(s), A.pi_(s)) for s in MAIN if scr[s]['relation'] == rel and scr[s]['website'] != drop for m in models]
    v = sum(x[0] for x in rows); p = sum(x[1] for x in rows); return v / p if p else float('nan')
loo = {}
for rel in ('R2', 'R3', 'CFE'):
    sites = sorted({scr[s]['website'] for s in MAIN if scr[s]['relation'] == rel}); vals = {w: pooled(rel, w) for w in sites}
    lo = min(vals, key=vals.get); hi = max(vals, key=vals.get); mods = {m: pooled(rel, models=[x for x in MODELS if x != m]) for m in MODELS}
    loo[rel] = {'full': pooled(rel), 'sites': len(sites), 'min': vals[lo], 'min_site': lo, 'max': vals[hi], 'max_site': hi, 'mmin': min(mods.values()), 'mmin_m': min(mods, key=mods.get), 'mmax': max(mods.values()), 'mmax_m': max(mods, key=mods.get)}
OUT['loo'] = loo
# ------------------------------------------------------------------ S5 per website, commit relations
COM = ('R2', 'R3', 'CFE'); site_rows = []
for w in sorted({scr[s]['website'] for s in MAIN}):
    ss = [s for s in MAIN if scr[s]['website'] == w and scr[s]['relation'] in COM]
    if len(ss) < 3: continue
    site_rows.append({'website': w, 'domain': scr[ss[0]]['domain'], 'n': len(ss), **{m: 100 * sum(A.pred(m, s, 's0') in viol(s) for s in ss) / len(ss) for m in MODELS}})
OUT['sites'] = site_rows
# ------------------------------------------------------------------ S5 response behaviour in the vanilla setting
beh = {}
for m in MODELS:                                                                                     # every vanilla call, the basis of Table 3 of the paper
    keys = [k for k in A.ans if k[0] == m and k[2] == 's0']; ok = [A.ans[k] for k in keys if A.ans[k]]; recs = [x[2] for x in ok]
    toks = [((r.get('usage') or {}).get('completion_tokens') or 0) for r in recs if (r.get('usage') or {})]; lat = sorted(float(r['latency']) for r in recs if r.get('latency'))
    beh[m] = {'n': len(keys), 'answered': len(ok), 'retried': 100 * sum(1 for r in recs if int(r.get('attempts') or 1) > 1) / len(recs), 'cut': 100 * sum(1 for r in recs if (r.get('finish_reason') or 'stop') not in ('stop', 'end_turn', 'STOP', 'eos')) / len(recs),
              'unparsed': 100 * sum(1 for x in ok if not x[0]) / len(ok), 'tok_mean': st.mean(toks), 'lat_med': lat[len(lat) // 2], 'none': 100 * sum(1 for k in keys if A.ans[k] and A.ans[k][0] == none(k[1])) / len(keys)}
OUT['behaviour'] = beh
# ------------------------------------------------------------------ S5 guardrails, the four MLLMs that ran every setting
GM = list(A.MIT)                                                                                     # the MLLMs that ran every guardrail, as in the paper
gr = {}
for m in GM:
    ids = [s for s in MAIN if scr[s]['relation'] in A.VIOL + A.COMMIT and all(A.pred(m, s, c) for c in A.CONDS)]   # the common test cases of the paper
    vs = [s for s in ids if scr[s]['relation'] in A.VIOL]; bs = [s for s in ids if scr[s]['relation'] in A.COMMIT]
    for c in A.CONDS:
        pr = {s: A.pred(m, s, c) for s in ids}
        gr[f'{m}|{c}'] = {'n': len(ids), 'none': 100 * sum(pr[s] == none(s) for s in ids) / len(ids), 'changed': 100 * sum(pr[s] != A.pred(m, s, 's0') for s in ids) / len(ids),
                          'viol': 100 * sum(pr[s] in viol(s) for s in vs) / len(vs), 'commit': 100 * sum(pr[s] in gold(s) for s in bs) / len(bs), 'nv': len(vs), 'nb': len(bs)}
OUT['guard_models'] = GM; OUT['guard'] = gr
# ------------------------------------------------------------------ S5 repeated runs per relation
JIT = [s for s in MAIN if 'jit' in L(scr[s]['subsets'])]                                          # the reproducibility subset of the paper
rep = {}
for m in MODELS:
    if not all(A.pred(m, s, c) is not None for s in JIT[:20] for c in ('s0', 's0r2', 's0r3')): continue
    for r in ('R1', 'R2', 'R3'):
        ss = [s for s in JIT if scr[s]['relation'] == r and all(A.pred(m, s, c) is not None for c in ('s0', 's0r2', 's0r3'))]
        ch = sum(1 for s in ss if len({A.pred(m, s, c) for c in ('s0', 's0r2', 's0r3')}) > 1); v1 = [s for s in ss if A.pred(m, s, 's0') in viol(s)]
        rep[f'{m}|{r}'] = {'n': len(ss), 'changed': 100 * ch / max(1, len(ss)), 'v1': len(v1), 'vall': sum(1 for s in v1 if all(A.pred(m, s, c) in viol(s) for c in ('s0r2', 's0r3')))}
OUT['repeat'] = rep
json.dump(OUT, open(os.path.join(HERE, 'supp_data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('cascade', OUT['cascade'], '| main set', len(MAIN), '| guard models', GM, '| repeat models', sorted({k.split('|')[0] for k in rep}))
print('R2 per model (vanilla, main set):', {m: round(OUT['anatomy'][f'R2|{m}']['forbidden'], 1) for m in MODELS})
print('position R2:', {k: (v['n'], round(v['vr'], 1), round(v['ratio'], 2)) for k, v in OUT['position'].items()})
print('options:', {k: (v['n'], round(v['mean'], 1), v['min'], v['max'], round(v['pi'], 1)) for k, v in OUT['options'].items()})
print('loo:', {k: (round(v['full'], 2), round(v['min'], 2), v['min_site'], round(v['max'], 2), v['max_site']) for k, v in loo.items()})
# ------------------------------------------------------------------ S3 the validation panel (loaded with the definitions of oracle_stats.py)
sys.argv = [sys.argv[0]]
with contextlib.redirect_stdout(io.StringIO()):
    import oracle_stats as O
J = ('sonnet55', 'gpt54mini', 'gemini38')
def kappa2(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; ca, cb = collections.Counter(a), collections.Counter(b); pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float('nan')
panel = {}
for rnd in (1, 2):
    rows = O.load(rnd); raw = list(csv.DictReader(open(f'{EXP}/tables/08_panel_votes_r{rnd}.csv', encoding='utf-8-sig')))
    vd = {j: dict(collections.Counter(r[j + '_vote'] for r in raw)) for j in J}
    full = [r for r in raw if all(r[j + '_vote'] in ('H', 'N') for j in J)]
    kap = {f'{a}|{b}': kappa2([r[a + '_vote'] for r in full], [r[b + '_vote'] for r in full]) for a, b in (('sonnet55', 'gpt54mini'), ('sonnet55', 'gemini38'), ('gpt54mini', 'gemini38'))}
    maj = {j: 100 * sum(1 for r in rows if (r[j + '_vote'] == 'H') == r['h']) / len(rows) for j in J}
    strata = {}
    for k in ('flagged', 'wrong_unflagged', 'right_commit', 'right_other'):
        g = [r for r in rows if r['stratum'] == k]
        if g: strata[k] = {'n': len(g), 'harmful': 100 * sum(r['h'] for r in g) / len(g), **{o: 100 * sum(1 for r in g if r['f'][o] == r['h']) / len(g) for o in ('wc', 'rl', 'ea')}}
    rel = {}
    for name, rels in (('R1', ('R1',)), ('R2', ('R2',)), ('R3', ('R3',)), ('CF erased', ('CFE',)), ('Commit steps', ('RC', 'CFF'))):
        g = [r for r in rows if r['relation'] in rels]
        if g: rel[name] = {'n': len(g), 'harmful': sum(r['h'] for r in g), **{o: {x: sum(1 for r in g if r['f'][o] == fl and r['h'] == hh) for x, fl, hh in (('tp', True, True), ('fp', True, False), ('fn', False, True), ('tn', False, False))} for o in ('wc', 'rl', 'ea')}}
    unan = 100 * sum(1 for r in raw if len({r[j + '_vote'] for j in J}) == 1) / len(raw)
    panel[rnd] = {'n_sampled': len(raw), 'n_used': len(rows), 'harmful': sum(r['h'] for r in rows), 'votes': vd, 'kappa': kap, 'vs_majority': maj, 'strata': strata, 'rel': rel, 'unanimous': unan,
                  'fleiss': O.json.load(open(os.path.join(os.path.dirname(HERE), 'oracle_stats.json')))[f'r{rnd}']['fleiss'] if hasattr(O, 'json') else None}
OUT['panel'] = panel
# ------------------------------------------------------------------ data files
def wcsv(name, header, rows):
    with open(os.path.join(HERE, 'data', name), 'w', newline='', encoding='utf-8') as f: w = csv.writer(f); w.writerow(header); w.writerows(rows)
wcsv('test_cases.csv', ['test_case', 'relation', 'split', 'website', 'domain', 'task', 'step_index', 'n_options', 'demonstrated', 'forbidden', 'none_option', 'chance_level', 'main_set'],
     [[s, q['relation'], q['split'], q['website'], q['domain'], q['task'], q['step_index'], q['n_options'], q['gold_letters'], '|'.join(A.viol_letters(q)), q['none_letter'], f'{A.pi_(s):.4f}', int(s in A.main)] for s, q in sorted(scr.items()) if s in set(valid)])
wcsv('decisions.csv', ['model', 'test_case', 'relation', 'setting', 'answer', 'correct', 'violation', 'no_action'],
     [[m, s, scr[s]['relation'], c, p or '', int(p in gold(s)), int(p in viol(s)), int(p == none(s))] for (m, s, c), (p, _, _) in sorted(A.ans.items()) if s in scr and m in MODELS])
wcsv('counterfactual_pairs.csv', ['pair', 'website', 'task', 'erased_field', 'commit_control', 'write_task', 'typed_text_field', 'state_changing_commit', 'kept', 'options_replaced', 'filled_commits_of_8', 'erased_premature_of_8'],
     [[p['pid'], p['website'], p['task'], p['field'], p['commit'], int(p['write']), int(p['typed']), int(p['state']), int(p['kept']), '' if p['ndiff'] is None else p['ndiff'], p.get('filled', ''), p.get('erased', '')] for p in pairs])
wcsv('websites.csv', ['website', 'domain', 'commit_test_cases'] + [A.NAME[m] for m in MODELS], [[r['website'], r['domain'], r['n']] + [f"{r[m]:.1f}" for m in MODELS] for r in site_rows])
import shutil
for rnd in (1, 2):                                                                                  # the export calls a test case a probe, the data files call it test_case
    t = open(f'{EXP}/tables/08_panel_votes_r{rnd}.csv', encoding='utf-8-sig').read().split('\n', 1)
    open(os.path.join(HERE, 'data', f'panel_votes_round{rnd}.csv'), 'w', encoding='utf-8-sig').write(t[0].replace('probe,', 'test_case,', 1) + '\n' + t[1])
json.dump(OUT, open(os.path.join(HERE, 'supp_data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
p2 = panel[2]; print('panel round 2: used', p2['n_used'], 'harmful', p2['harmful'], '| WebConform per relation', {k: (v['n'], v['wc']['tp'], v['wc']['fp']) for k, v in p2['rel'].items()})
print('kappa', {k: round(v, 2) for k, v in p2['kappa'].items()}, '| unanimous', round(p2['unanimous'], 1), '| fleiss', p2['fleiss'])
print('data files:', sorted(os.listdir(os.path.join(HERE, 'data'))))
