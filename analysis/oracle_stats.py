"""Oracle validation against the panel, recomputed from the vote tables on the decisions that lie on probes of the main set.
Five oracles on the same decisions: WebConform (OSR + SCC), OSR without the SCC, the label-based risk oracle, the risk oracle with
the SCC, and element accuracy. Paired exact tests against WebConform, bootstrap interval of the F1 difference, per relation counts."""
import csv, json, random, collections
from analysis import EXP, scr, L, tags, NAV, main, viol_letters, pb
random.seed(3)
def load(rnd):
    rows = [r for r in csv.DictReader(open(f'{EXP}/tables/08_panel_votes_r{rnd}.csv', encoding='utf-8-sig')) if r['probe'] in main and r['reference'] in ('H', 'N')]
    for r in rows:
        q = scr[r['probe']]; rel = q['relation']; ch = r['chosen']; raw = L(q['strict_letters'] if rel == 'R1' else q['repeat_letters'])
        test = rel in ('R1', 'R2', 'R3', 'CFE')
        r['f'] = {'wc': test and ch in viol_letters(q), 'wc_nolink': test and ch in raw, 'rl': r['risk_label'] == '1', 'rl2': r['risk_label'] == '1' and r['chosen_tag'] not in NAV, 'ea': r['element_wrong'] == '1'}
        r['h'] = r['reference'] == 'H'
    return rows
def prf(rows, k):
    tp = sum(r['f'][k] and r['h'] for r in rows); fp = sum(r['f'][k] and not r['h'] for r in rows); fn = sum((not r['f'][k]) and r['h'] for r in rows); tn = len(rows) - tp - fp - fn
    p = tp / max(1, tp + fp); rc = tp / max(1, tp + fn); return {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, 'precision': p, 'recall': rc, 'f1': 2 * tp / max(1, 2 * tp + fp + fn), 'acc': (tp + tn) / len(rows)}
out = {}
for rnd in (1, 2):
    rows = load(rnd); o = {'n': len(rows), 'harmful': sum(r['h'] for r in rows)}
    for k in ('wc', 'wc_nolink', 'rl', 'rl2', 'ea'): o[k] = prf(rows, k)
    boot = {k: {'f1': [], 'acc': [], 'precision': [], 'recall': []} for k in ('wc', 'wc_nolink', 'rl', 'rl2', 'ea')}       # bootstrap intervals for the bars of the figure
    for _ in range(2000):
        smp = [rows[random.randrange(len(rows))] for _ in rows]
        for k in boot:
            v = prf(smp, k); boot[k]['f1'].append(v['f1']); boot[k]['acc'].append(v['acc']); boot[k]['precision'].append(v['precision']); boot[k]['recall'].append(v['recall'])
    for k in boot:
        for met in ('f1', 'acc', 'precision', 'recall'): xs = sorted(boot[k][met]); o[k][met + '_ci'] = (xs[50], xs[1949])
    for k in ('wc_nolink', 'rl', 'rl2', 'ea'):
        b = sum((r['f']['wc'] == r['h']) and (r['f'][k] != r['h']) for r in rows); c = sum((r['f']['wc'] != r['h']) and (r['f'][k] == r['h']) for r in rows); ds = []
        for _ in range(4000):
            smp = [rows[random.randrange(len(rows))] for _ in rows]; ds.append(prf(smp, 'wc')['f1'] - prf(smp, k)['f1'])
        ds.sort(); o['vs_' + k] = {'wc_right_other_wrong': b, 'other_right_wc_wrong': c, 'p': pb(b, c), 'df1': o['wc']['f1'] - o[k]['f1'], 'ci': (ds[100], ds[3899]), 'p_boot': sum(1 for x in ds if x <= 0) / len(ds)}
    o['rel'] = {}
    for R, rels in (('R1', ('R1',)), ('R2', ('R2',)), ('R3', ('R3',)), ('CFE', ('CFE',)), ('COMMIT', ('RC', 'CFF'))):
        g = [r for r in rows if r['relation'] in rels]; o['rel'][R] = {'n': len(g), 'harmful': sum(r['h'] for r in g), **{k: prf(g, k) for k in ('wc', 'rl')}} if g else None
    votes = [[r[j + '_vote'] for j in ('gpt54mini', 'sonnet55', 'gemini38')] for r in rows]; full = [v for v in votes if all(x in 'HN' for x in v)]
    o['unanimous'] = sum(1 for v in full if len(set(v)) == 1) / len(full)
    n = len(full); pj = sum(v.count('H') for v in full) / (3 * n); P = sum((v.count('H') ** 2 + v.count('N') ** 2 - 3) / 6 for v in full) / n; Pe = pj ** 2 + (1 - pj) ** 2; o['fleiss'] = (P - Pe) / (1 - Pe)
    o['flag_share'] = {k: (sum(1 for r in rows if r['f'][k] and sum(1 for j in ('gpt54mini', 'sonnet55', 'gemini38') if r[j + '_vote'] == 'H') >= 2) / max(1, sum(1 for r in rows if r['f'][k]))) for k in ('wc', 'wc_nolink', 'rl', 'rl2', 'ea')}
    o['votes'] = [{'h': sum(1 for j in ('gpt54mini', 'sonnet55', 'gemini38') if r[j + '_vote'] == 'H'), 'n': sum(1 for j in ('gpt54mini', 'sonnet55', 'gemini38') if r[j + '_vote'] in 'HN'), **{k: bool(v) for k, v in r['f'].items()}, 'rel': r['relation']} for r in rows]
    out['r%d' % rnd] = o
json.dump(out, open('oracle_stats.json', 'w'), indent=1, default=float)
for rnd in ('r1', 'r2'):
    o = out[rnd]; print(rnd, 'n', o['n'], 'harmful', o['harmful'], 'unanimous %.3f' % o['unanimous'], 'kappa %.2f' % o['fleiss'])
    for k in ('wc', 'wc_nolink', 'rl2', 'rl', 'ea'): v = o[k]; print(f"   {k:10s} tp {v['tp']:3d} fp {v['fp']:3d} fn {v['fn']:3d} tn {v['tn']:3d}  P {100*v['precision']:5.1f} R {100*v['recall']:5.1f} F1 {100*v['f1']:5.1f} acc {100*v['acc']:5.1f}  flags harmful {100*o['flag_share'][k]:4.0f}%")
    for k in ('ea', 'rl', 'rl2', 'wc_nolink'): v = o['vs_' + k]; print(f"   WebConform vs {k:10s} {v['wc_right_other_wrong']:3d} / {v['other_right_wc_wrong']:3d}  p {v['p']:.2g}  dF1 {100*v['df1']:.1f} [{100*v['ci'][0]:.1f}, {100*v['ci'][1]:.1f}]")
    print('   per relation', {R: (v['n'], v['harmful'], v['wc']['tp'], v['wc']['fp'], v['wc']['fn'], v['rl']['tp'], v['rl']['fp']) for R, v in o['rel'].items() if v})
