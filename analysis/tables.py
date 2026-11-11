"""Every table of the paper as a complete float, in the house table style of RuleSight: footnotesize, full text width (tabular*),
numeric columns aligned on the decimal point with siunitx S columns and centred headers, bold for the emphasised values,
short captions and one-line notes. Data: numbers.json, numbers2.json (oracle v2)."""
import json, os
os.makedirs('tables', exist_ok=True)
N = json.load(open('numbers.json', encoding='utf-8')); X = json.load(open('numbers2.json', encoding='utf-8'))
M = N['models']; NAME = N['name']; S0 = N['s0']
BS = chr(92); NL = BS + BS
def p1(x): return f'{100 * x:.1f}'
def r2(x): return f'{x:.2f}' if x == x else '{--}'
def pf(p): return '{$<$0.001}' if p < 0.001 else f'{p:.3f}'
def bold(s, on): return (BS + 'bfseries ' + s) if on else s
def head(cols): return ' & '.join(cols) + ' ' + NL
def mc(t): return BS + 'multicolumn{1}{c}{' + t + '}'
def table(label, caption, spec, header, rows, note=None, sep='3pt', extra_head=None):
    out = [BS + 'begin{table}[!htbp]', BS + 'centering', BS + 'footnotesize', BS + 'setlength{' + BS + 'tabcolsep}{' + sep + '}', BS + 'caption{' + caption + '}', BS + 'label{' + label + '}',
           BS + 'begin{tabular*}{' + BS + 'textwidth}{@{' + BS + 'extracolsep{' + BS + 'fill}}' + spec + '@{}}', BS + 'toprule']
    if extra_head: out += extra_head
    out += [header, BS + 'midrule'] + rows + [BS + 'bottomrule', BS + 'end{tabular*}']
    if note: out.append(BS + 'tabnote{' + note + '}')
    out.append(BS + 'end{table}')
    open(f'tables/{label.split(":")[1]}.tex', 'w', encoding='utf-8').write('\n'.join(out) + '\n')

# ---- T1 probe bank
rows = [f'R1 safety & 4,116 & Step of a read-only task that shows a state-changing control {NL}',
        f'R2 precondition & 113 & One to three steps before the commit of a state-changing task {NL}',
        f'R3 idempotency & 48 & Step after the commit, with the commit control still shown {NL}',
        f'RC commit step & 236 & Commit step, at which activating the commit is correct {NL}',
        f'CF pairs & 20 & 10 commit steps, each as recorded and with one typed input erased {NL}',
        BS + 'midrule', f'Total & 4,533 & 840 tasks on 124 websites, 1,617 test cases in the main set {NL}']
table('tab:data', 'Test suite built from the three Multimodal-Mind2Web test splits.', 'lrp{0.68' + BS + 'textwidth}', head(['Kind', mc('Test cases'), 'Definition']), rows, 'RC denotes the reference commit, and CF the counterfactual pairs.')

# ---- T2 models, tokens, latency, cost
acc = {'sonnet55': ('API', 'low'), 'gemini38': ('API', 'low'), 'haiku55': ('API', 'low'), 'gpt54mini': ('API', 'low'), 'qwen35': ('API', 'off'), 'qwen35_9b': ('local', 'off'), 'qwen3vl8b': ('local', 'off'), 'internvl35': ('local', 'off')}
rows = []
for m in M:
    c = X['cost'][m]; tot = N['cost'].get(m, {}).get('usd', 0)
    rows.append(f"{NAME[m]} & {acc[m][0]} & {acc[m][1]} & {c['prompt']:.0f} & {c['completion']:.0f} & {c['reasoning']:.0f} & {c['lat_med']:.1f} & " + (f"{c['usd_per_1k']:.2f}" if tot else '{--}') + ' ' + NL)
table('tab:models', 'Multimodal large language models (MLLMs) under test, with tokens, latency and cost per decision in the vanilla setting (S0).', 'llcS[table-format=4.0,group-separator={,},group-minimum-digits=4]S[table-format=3.0]S[table-format=3.0]S[table-format=1.1]S[table-format=1.2]',
      head(['Model', 'Access', 'Reasoning', mc('Input'), mc('Output'), mc('Reasoning'), mc('Latency (s)'), mc('Cost (USD)')]), rows,
      'Tokens are means and Latency is the median per decision. Cost in US dollars (USD) per 1,000 decisions. API, application programming interface.', sep='2pt',
      extra_head=[' & & & ' + BS + 'multicolumn{3}{c}{Tokens} & & ' + NL, BS + 'cmidrule(lr){4-6}'])

# ---- T3 S0 against chance
rows = []
for m in M:
    r = S0[m]; cells = []
    for R in ('R1', 'R2', 'R3', 'CFE'):
        sig = r[R]['p_holm'] < 0.05 and r[R]['viol'] > r[R]['chance']
        cells += [p1(r[R]['viol']), bold(r2(r[R]['ratio']), sig)]
    rows.append(f"{NAME[m]} & " + ' & '.join(cells) + f" & {p1(r['acc'])} & {p1(r['commit'])} {NL}")
ch = lambda R: p1(S0[M[0]][R]['chance'])
table('tab:s0', 'Violation rate and its ratio to the chance level in the vanilla setting.', 'l' + 'S[table-format=2.1]S[table-format=1.2]' * 3 + 'S[table-format=2.1]S[table-format=2.2]' + 'S[table-format=2.1]S[table-format=2.1]',
      head(['Model'] + [mc('Rate'), mc('Ratio')] * 4 + [mc('Accuracy'), mc('Commit')]), rows,
      'Rate, Accuracy and Commit in \\%. Bold marks ratios above 1 at Holm $p<0.05$.', sep='1.5pt',
      extra_head=[' & ' + ' & '.join(BS + 'multicolumn{2}{c}{' + t + '}' for t in ('R1', 'R2', 'R3', 'CF erased')) + ' & ' + BS + 'multicolumn{2}{c}{Correct decisions} ' + NL,
                  ' '.join(BS + 'cmidrule(lr){' + f'{a}-{a + 1}' + '}' for a in (2, 4, 6, 8, 10))])

# ---- T4 splits and domains (pooled over the eight models)
rows = []
SPN = {'test_task': 'Cross-task', 'test_website': 'Cross-website', 'test_domain': 'Cross-domain'}
for sp in ('test_task', 'test_website', 'test_domain'):
    a, c = X['split'][sp]['R1'], X['split_C'][sp]; n = X['split_n'][sp]
    rows.append(f"{SPN[sp]} & {n['tasks']} & {n['sites']} & {p1(a['viol'])} & {p1(a['chance'])} & {p1(c['viol'])} & {p1(c['chance'])} & {bold(r2(c['ratio']), c['lo'] > 1)} & {c['lo']:.2f} to {c['hi']:.2f} {NL}")
rows.append(BS + 'midrule')
for dm in sorted(X['domain']):
    a, c = X['domain'][dm]['R1'], X['domain'][dm]['C']
    rows.append(f"{dm} & {X['domain'][dm]['tasks']} & {X['domain'][dm]['sites']} & {p1(a['viol'])} & {p1(a['chance'])} & {p1(c['viol'])} & {p1(c['chance'])} & {bold(r2(c['ratio']), c['lo'] > 1)} & {c['lo']:.2f} to {c['hi']:.2f} {NL}")
table('tab:split', 'Violations by test split and domain, pooled over the eight MLLMs.', 'lS[table-format=3.0]S[table-format=2.0]S[table-format=1.1]S[table-format=1.1]S[table-format=2.1]S[table-format=2.1]S[table-format=1.2]c',
      head(['Group', mc('Tasks'), mc('Websites'), mc('Rate'), mc('Chance'), mc('Rate'), mc('Chance'), mc('Ratio'), '95\\% CI']), rows,
      'Rate and Chance in \\%. Commit relations pool the precondition (R2), idempotency (R3) and counterfactual (CF) test cases. Bold marks ratios whose 95\\% CI lies above 1.',
      extra_head=[' & & & ' + BS + 'multicolumn{2}{c}{R1 safety} & ' + BS + 'multicolumn{4}{c}{Commit relations} ' + NL, BS + 'cmidrule(lr){4-5}' + BS + 'cmidrule(lr){6-9}'])

# ---- T5 factors
rows = []
def frow(f, lv, d, first):
    return f"{f if first else ''} & {lv} & {d['probes'] if 'probes' in d else int(d['n'] / 8)} & {p1(d['viol'])} & {p1(d['chance'])} & {bold(r2(d['ratio']), d['lo'] > 1)} & {d['lo']:.2f} to {d['hi']:.2f} {NL}"
for k, lv in ((1, 'one step'), (2, 'two steps'), (3, 'three steps')): rows.append(frow('R2, steps to commit', lv, X['r2_dist'][str(k)]['pooled'], k == 1))
rows.append(BS + 'midrule')
for i, (c, lv) in enumerate((('Add to cart / bag', 'add to cart or bag'), ('Follow, like, subscribe', 'follow, like, subscribe'), ('Save to a list', 'save to a list'))): rows.append(frow('R2, commit type', lv, X['r2_ctype'][c], i == 0))
rows.append(BS + 'midrule')
for i, (c, lv) in enumerate((('TYPE', 'type into a field'), ('CLICK', 'click a control'))): rows.append(frow('R2, next action', lv, X['r2_pending'][c], i == 0))
rows.append(BS + 'midrule')
for i, (c, lv) in enumerate((('visible', 'visible'), ('not visible', 'not visible'))): rows.append(frow('R3, completion cue', lv, X['r3_cue'][c], i == 0))
table('tab:factors', 'Violation rate by test case property, pooled over the eight MLLMs.', 'llS[table-format=2.0]S[table-format=2.1]S[table-format=2.1]S[table-format=1.2]c',
      head(['Factor', 'Level', mc('Test cases'), mc('Rate'), mc('Chance'), mc('Ratio'), '95\\% CI']), rows, 'Rate and Chance in \\%. Bold marks ratios whose 95\\% CI lies above 1. Commit types with fewer than 10 test cases are omitted.', sep='2pt')

# ---- T6 among wrong decisions
rows = []
for m in M:
    r = S0[m]; rows.append(f"{NAME[m]} & " + ' & '.join(f"{r[R]['n_wrong']} & {p1(r[R]['wrong_viol'])} & {p1(r[R]['wrong_chance'])} & {bold(r2(r[R]['wrong_ratio']), r[R]['wrong_p'] < 0.05 and r[R]['wrong_ratio'] > 1)}" for R in ('R2', 'R3')) + ' ' + NL)
table('tab:wrong', 'Forbidden commits among wrong decisions in the vanilla setting, against a random wrong choice.', 'l' + 'S[table-format=2.0]S[table-format=2.1]S[table-format=2.1]S[table-format=1.2]' * 2,
      head(['Model'] + [mc('Wrong'), mc('Observed'), mc('Chance'), mc('Ratio')] * 2), rows, 'Observed and Chance in \\% of the wrong decisions. Bold marks ratios above 1 at Holm $p<0.05$.', sep='2pt',
      extra_head=[' & ' + ' & '.join(BS + 'multicolumn{4}{c}{' + t + '}' for t in ('R2 precondition', 'R3 idempotency')) + ' ' + NL, BS + 'cmidrule(lr){2-5}' + BS + 'cmidrule(lr){6-9}'])

# ---- T7 ranks
R_ = X['rank']; rows = []
for m in sorted(M, key=lambda m: R_['acc_rank'][m]):
    rows.append(f"{NAME[m]} & {p1(R_['acc'][m])} & {R_['acc_rank'][m]} & {p1(R_['conf'][m])} & {R_['conf_rank'][m]} & {(lambda d: f'{d:+d}' if d else '0')(R_['acc_rank'][m] - R_['conf_rank'][m])} {NL}")
table('tab:rank', 'Element accuracy and conformance rankings of the eight MLLMs.', 'lS[table-format=2.1]S[table-format=1.0]S[table-format=2.1]S[table-format=1.0]S[table-format=+1.0]',
      head(['Model', mc('Accuracy'), mc('Rank'), mc('Conformance'), mc('Rank'), mc('\\sgnslot Shift')]), rows,
      f"Accuracy and Conformance in \\%. Conformance is the share of decisions without a violation on R2, R3 and CF. Kendall $\\tau={R_['tau']:.2f}$.")

# ---- T8 panel validity, both rounds
names = [('WebConform（本文判定器）', 'WebConform oracle'), ('元素准确率（选错即有害）', 'Element accuracy'), ('风险标签（改状态即有害）', 'Action-risk label'), ('风险标签 v2（非链接控件）', 'Action-risk label, non-link')]
rows = []
for k, n in names:
    a, b = N['panel']['r1']['oracles'][k], N['panel']['r2']['oracles'][k]; best = k == names[0][0]
    rows.append(f"{n} & {p1(a['precision'])} & {p1(a['recall'])} & {p1(a['f1'])} & {bold(p1(b['precision']), best)} & {p1(b['recall'])} & {bold(p1(b['f1']), best)} {NL}")
table('tab:panel', 'Agreement of four oracles with the three-model panel (\\%).', 'l' + 'S[table-format=2.1]S[table-format=3.1]S[table-format=2.1]' * 2,
      head(['Oracle'] + [mc('Precision'), mc('Recall'), mc('F1')] * 2), rows, 'The calibration round fixed the SCC and the validation round holds only decisions it never judged.',
      extra_head=[' & ' + BS + 'multicolumn{3}{c}{Calibration round ($n=296$)} & ' + BS + 'multicolumn{3}{c}{Validation round ($n=298$)} ' + NL, BS + 'cmidrule(lr){2-4}' + BS + 'cmidrule(lr){5-7}'])

# ---- T9 per relation, validation round
OS_ = json.load(open('oracle_stats.json'))['r2']; rows = []
for R, n in (('R1', 'R1 safety'), ('R2', 'R2 precondition'), ('R3', 'R3 idempotency'), ('CFE', 'CF erased'), ('COMMIT', 'Commit step (RC, CF filled)')):
    g = OS_['rel'][R]; t = g['wc']; u = g['rl']; pr = lambda v: (p1(v['tp'] / (v['tp'] + v['fp'])) if v['tp'] + v['fp'] else '{--}')
    if R == 'COMMIT': rows.append(BS + 'midrule')
    rows.append(f"{n} & {g['n']} & {g['harmful']} & {t['tp']} & {t['fp']} & {t['fn']} & {pr(t)} & {u['tp']} & {u['fp']} & {pr(u)} {NL}")
table('tab:panelrel', 'WebConform and the action-risk label against the panel per relation.', 'lS[table-format=3.0]S[table-format=2.0]S[table-format=2.0]S[table-format=2.0]S[table-format=1.0]S[table-format=2.1]S[table-format=2.0]S[table-format=2.0]S[table-format=2.1]',
      head(['Relation', mc('Decided'), mc('Harmful'), mc('TP'), mc('FP'), mc('FN'), mc('Precision'), mc('TP'), mc('FP'), mc('Precision')]), rows,
      f"Precision in \\%. The three judges are unanimous on {100 * OS_['unanimous']:.0f}\\% of the decisions, with Fleiss $\\kappa={OS_['fleiss']:.2f}$.",
      extra_head=[' & & & ' + BS + 'multicolumn{4}{c}{WebConform} & ' + BS + 'multicolumn{3}{c}{Action-risk label} ' + NL, BS + 'cmidrule(lr){4-7}' + BS + 'cmidrule(lr){8-10}'])

# ---- T10 counterfactual pairs
rows = []; tf = te = tn = bb = cc = 0
for m in M:
    c = N['cf'][m]; rows.append(f"{NAME[m]} & {c['n']} & {c['filled']} & {p1(c['filled'] / c['n'])} & {c['emptied']} & {p1(c['emptied'] / c['n'])} & {pf(c['p'])} {NL}"); tf += c['filled']; te += c['emptied']; tn += c['n']; bb += c['b']; cc += c['c']
from analysis import pb as _pb
rows += [BS + 'midrule', f"All eight MLLMs & {tn} & {tf} & {p1(tf / tn)} & {te} & {p1(te / tn)} & {pf(_pb(bb, cc))} {NL}"]
table('tab:cf', 'Commits in the two states of the counterfactual pairs.', 'lS[table-format=2.0]S[table-format=2.0]S[table-format=2.1]S[table-format=2.0]S[table-format=2.1]S[table-format=1.3]',
      head(['Model', mc('Pairs'), mc('Commits'), mc('Rate'), mc('Commits'), mc('Rate'), mc('$p$')]), rows, 'Rate in \\%. Exact McNemar test on the discordant pairs.',
      extra_head=[' & & ' + BS + 'multicolumn{2}{c}{Input filled (correct)} & ' + BS + 'multicolumn{2}{c}{Input erased (premature)} & ' + NL, BS + 'cmidrule(lr){3-4}' + BS + 'cmidrule(lr){5-6}'])

# ---- T11 stability
rows = []
for m in M:
    st = N['stability'].get(m)
    if st and st['n'] >= 150: rows.append(f"{NAME[m]} & {st['n']} & {p1(st['changed'])} & {p1(st['gold_all3'])} & {st['viol1']} & {st['viol_all3']} & {p1(st['viol_all3'] / max(1, st['viol1']))} {NL}")
table('tab:stab', 'Reproducibility of decisions and violations over three repeated runs of the vanilla setting.', 'lS[table-format=3.0]S[table-format=2.1]S[table-format=2.1]S[table-format=2.0]S[table-format=2.0]S[table-format=3.1]',
      head(['Model', mc('Test cases'), mc('Changed'), mc('Correct in all runs'), mc('Run 1'), mc('All runs'), mc('Repeated')]), rows, 'Changed, Correct in all runs and Repeated in \\%. Changed means more than one distinct decision.',
      extra_head=[' & & ' + BS + 'multicolumn{2}{c}{Decisions} & ' + BS + 'multicolumn{3}{c}{Violations} ' + NL, BS + 'cmidrule(lr){3-4}' + BS + 'cmidrule(lr){5-7}'])

# ---- T12 mitigation per model (rows: settings; columns: the four models)
MM = list(N['mitigation']); CS = ('s0', 'cvx', 'cv', 'sc', 'rg', 's2'); SN6 = {'s0': 'S0', 'cvx': 'CVX', 'cv': 'CV', 'sc': 'SC', 'rg': 'RG', 's2': 'S2'}
SH = {'haiku55': 'Claude Haiku 5.5', 'qwen35_9b': 'Qwen3.5-9B', 'qwen3vl8b': 'Qwen3-VL-8B', 'internvl35': 'InternVL3.5-8B'}
rows = []
for c in CS:
    cells = []
    for m in MM:
        r = N['mitigation'][m]['rates']; bv = min(r[k]['viol'] for k in CS); bc = max(r[k]['commit'] for k in CS)
        cells += [bold(p1(r[c]['viol']), r[c]['viol'] == bv), bold(p1(r[c]['commit']), r[c]['commit'] == bc)]
    rows.append(f"{SN6[c]} & " + ' & '.join(cells) + ' ' + NL)
table('tab:mit', 'Violation rate and correct-commit rate per MLLM and guardrail setting.', 'l' + 'S[table-format=2.1]S[table-format=2.1]' * 4,
      head(['Setting'] + [mc('Violation'), mc('Commit')] * 4), rows, 'Values in \\%, on 171 violation and 246 benign test cases. Bold marks the best value per MLLM. CVX and CV denote commit verification with and without explanation, SC the self-check, RG the risk gate and S2 the rule instruction.', sep='2pt',
      extra_head=[' & ' + ' & '.join(BS + 'multicolumn{2}{c}{' + SH[m] + '}' for m in MM) + ' ' + NL, ' '.join(BS + 'cmidrule(lr){' + f'{a}-{a + 1}' + '}' for a in (2, 4, 6, 8))])

# ---- T13 pooled per relation, history, no action
rows = []; SN = {'s0': 'S0', 's1': 'S1 history', 'cvx': 'CVX written check', 'cv': 'CV one-letter check', 'sc': 'SC self-review', 'rg': 'RG risk gate', 's2': 'S2 rule instruction'}
for c in ('s0', 's1', 'cvx', 'cv', 'sc', 'rg', 's2'):
    r = X['mit_rel'][c]; rows.append(f"{SN[c]} & {p1(r['R2']['viol'])} & {p1(r['R3']['viol'])} & {p1(r['CFE']['viol'])} & {p1(r['commit']['rate'])} & {p1(r['none_all'])} {NL}")
table('tab:mitrel', 'Guard settings per relation, pooled over the four models (\\%).', 'lS[table-format=2.1]S[table-format=2.1]S[table-format=2.1]S[table-format=2.1]S[table-format=2.1]',
      head(['Setting', mc('R2 viol.'), mc('R3 viol.'), mc('CF viol.'), mc('Right commits'), mc('No action')]), rows, 'No action is the share of all guard probes answered with the no-action option.')

# ---- T14 pooled paired tests
PP = N['mitigation_pooled']; rows = []
for k, a, b in (('cvx_vs_s0', 'CVX', 'S0'), ('cv_vs_s0', 'CV', 'S0'), ('s2_vs_s0', 'S2', 'S0'), ('sc_vs_s0', 'SC', 'S0'), ('rg_vs_s0', 'RG', 'S0'), ('cvx_vs_s2', 'CVX', 'S2'), ('cvx_vs_cv', 'CVX', 'CV')):
    v, c = PP[k + '_v'], PP[k + '_c']; rows.append(f"{a} vs.\\ {b} & {v['x']} & {v['y']} & {pf(v['p'])} & {c['x']} & {c['y']} & {pf(c['p'])} {NL}")
s1 = X['s1_pair']; rows.append(f"S1 vs.\\ S0 (R2, R3) & {s1['fixed']} & {s1['introduced']} & {pf(s1['p'])} & {{--}} & {{--}} & {{--}} {NL}")
table('tab:mitpool', 'Paired changes against the reference setting, pooled over the four MLLMs.', 'lS[table-format=2.0]S[table-format=2.0]S[table-format=1.3]S[table-format=3.0]S[table-format=3.0]S[table-format=1.3]',
      head(['Comparison', mc('Removed'), mc('Introduced'), mc('$p$'), mc('Gained'), mc('Lost'), mc('$p$')]), rows, 'Exact McNemar test on the discordant decisions. S1 is the action-history setting.',
      extra_head=[' & ' + BS + 'multicolumn{3}{c}{Violations} & ' + BS + 'multicolumn{3}{c}{Correct commits} ' + NL, BS + 'cmidrule(lr){2-4}' + BS + 'cmidrule(lr){5-7}'])
# ---- related-work comparison
ck, xk = BS + 'cmark', BS + 'xmark'
rows = ["Offline evaluation " + BS + "citep{deng2023mind2web,zheng2024seeact} & Step & " + " & ".join([xk, xk, xk, xk]) + " " + NL,
        "Execution-based evaluation " + BS + "citep{zhou2024webarena,koh2024visualwebarena} & Episode & " + " & ".join([ck, xk, xk, xk]) + " " + NL,
        "Action-risk labels " + BS + "citep{webguard2025} & Step & " + " & ".join([xk, xk, xk, ck]) + " " + NL,
        "Policy benchmarks " + BS + "citep{levy2024stwebagentbench,ruan2024toolemu} & Episode & " + " & ".join([ck, ck, xk, xk]) + " " + NL,
        BS + 'midrule', "WebConform (Ours) & Step & " + " & ".join([xk, ck, ck, ck]) + " " + NL]
table('tab:related', 'Comparison of WebConform with existing ways of assessing web agent actions.', 'lccccc',
      head(['Approach', 'Unit', 'Execution', 'Task context', 'Controlled states', 'Validated']), rows, 'Execution marks approaches that must run the agent on a website. Validated marks verdicts checked against an independent reference.', sep='2pt')

# ---- notation
rows = [f"$T$, $\\iota(T)$ & Task and its intent, read or write {NL}", f"$s_j$, $a_j$ & Page state and demonstrated action at step $j$ {NL}", f"$C(s)$ & Interactive controls of state $s$ offered to the agent {NL}",
        f"$\\mathrm{{write}}(c)$ & Control $c$ changes server or account state when activated {NL}", f"$K$, $c_K$ & Commit step of a demonstration and its commit control {NL}", f"$d(s)$ & Decision of the agent at state $s$, a control or no action {NL}",
        f"$\\tilde{{s}}_K$ & State $s_K$ with one filled input erased {NL}", f"$\\pi(s)$ & Random-choice level of $s$, the share of forbidden options {NL}"]
table('tab:notation', 'Notation.', 'lp{0.78' + BS + 'textwidth}', head(['Symbol', 'Meaning']), rows)

# ---- RQ1 oracle effectiveness
OS = json.load(open('oracle_stats.json'))['r2']
def orow(name, k, vs=None, boldit=False):
    o = OS[k]; cells = [p1(o['precision']), p1(o['recall']), p1(o['f1']), p1(o['acc'])]
    if boldit: cells = [bold(c, True) if i != 1 else c for i, c in enumerate(cells)]
    tail = f"{OS[vs]['wc_right_other_wrong']} & {OS[vs]['other_right_wc_wrong']} & {pf(OS[vs]['p'])}" if vs else '{--} & {--} & {--}'
    return f"{name} & " + ' & '.join(cells) + ' & ' + tail + ' ' + NL
rows = [orow('Element accuracy', 'ea', 'vs_ea'), orow('Action-risk label', 'rl', 'vs_rl'), BS + 'midrule', orow('WebConform (Ours)', 'wc', None, True)]
table('tab:oracle', 'Agreement of the three oracles with the panel on the validation decisions.', 'lS[table-format=2.1]S[table-format=3.1]S[table-format=2.1]S[table-format=2.1]S[table-format=3.0]S[table-format=2.0]S[table-format=1.3]',
      head(['Oracle', mc('Precision'), mc('Recall'), mc('F1'), mc('Accuracy'), mc('Ours correct'), mc('Other correct'), mc('$p$')]), rows,
      'Precision, Recall, F1 and Accuracy in \\%. Bold marks the best value. The last columns count the decisions on which only one of the two oracles agrees with the panel.',
      extra_head=[' & ' + BS + 'multicolumn{4}{c}{Against the panel} & ' + BS + 'multicolumn{3}{c}{Paired with WebConform} ' + NL, BS + 'cmidrule(lr){2-5}' + BS + 'cmidrule(lr){6-8}'])

# ---- RQ2 ablation, relations x control classification
rows = []
for name, k, osr, scc in (('Action-risk label', 'rl', xk, xk), ('+ SCC', 'rl2', xk, ck), ('+ OSR', 'wc_nolink', ck, xk), ('+ OSR + SCC (WebConform)', 'wc', ck, ck)):
    o = OS[k]; base = OS['rl']; b_ = k == 'wc'
    rows.append(f"{name} & {osr} & {scc} & {o['tp']} & {o['fp']} & {bold(p1(o['precision']), b_)} & {p1(o['recall'])} & {bold(p1(o['f1']), b_)} & {bold(p1(o['acc']), b_)} & " + (f"{100 * (o['f1'] - base['f1']):+.1f}" if k != 'rl' else '{--}') + ' ' + NL)
table('tab:ablation', 'Ablation of the operation-semantic relations (OSR) and the semantic control classification (SCC) on the validation decisions.', 'lccS[table-format=2.0]S[table-format=2.0]S[table-format=2.1]S[table-format=3.1]S[table-format=2.1]S[table-format=2.1]S[table-format=+2.1]',
      head(['Configuration', 'OSR', 'SCC', mc('TP'), mc('FP'), mc('Precision'), mc('Recall'), mc('F1'), mc('Accuracy'), mc(BS + 'sgnslot $\\Delta$F1')]), rows, 'TP and FP are the true and the false positives. Precision, Recall, F1 and Accuracy in \\%. Bold marks the best value. $\\Delta$F1 is the change against the first row in points.', sep='2pt')

# ---- RQ2 pairing against natural probes
rows = []
def cell(r, pooled=False):
    sig = (r['lo'] > 1) if pooled else (r['p_holm'] < 0.05 and r['ratio'] > 1)
    return f"{r['k'] if 'k' in r else r['v']} & {r['n']} & {p1(r['viol'])} & {bold(r2(r['ratio']), sig)}"
for m in M: rows.append(f"{NAME[m]} & {cell(S0[m]['R2'])} & {{--}} & {cell(S0[m]['CFE'])} & {{--}} {NL}")
rows.append(BS + 'midrule')
for g, nm in (('api', 'Five API models'), ('local', 'Three open-source models'), ('all', 'All eight MLLMs')):
    a_, b_ = X['grp'][g]['R2'], X['grp'][g]['CFE']
    rows.append(f"{nm} & {cell(a_, True)} & {a_['lo']:.2f} to {a_['hi']:.2f} & {cell(b_, True)} & {b_['lo']:.2f} to {b_['hi']:.2f} {NL}")
table('tab:cpp', 'Precondition violations without and with counterfactual precondition pairing (CPP).', 'lS[table-format=3.0]S[table-format=3.0]S[table-format=2.1]S[table-format=3.2]cS[table-format=2.0]S[table-format=2.0]S[table-format=2.1]S[table-format=3.2]c',
      head(['Model', mc('$k$'), mc('$n$'), mc('Rate'), mc('Ratio'), '95\\% CI', mc('$k$'), mc('$n$'), mc('Rate'), mc('Ratio'), '95\\% CI']), rows,
      'Rate in \\%. Bold marks ratios above 1, at Holm $p<0.05$ for a single MLLM and by the 95\\% confidence interval (CI) for pooled MLLMs.', sep='1pt',
      extra_head=[' & ' + BS + 'multicolumn{5}{c}{Demonstration-derived test cases (R2)} & ' + BS + 'multicolumn{5}{c}{Counterfactual pairs (CF)} ' + NL, BS + 'cmidrule(lr){2-6}' + BS + 'cmidrule(lr){7-11}'])

# ---- RQ3 per website
G2 = json.load(open('figdata2.json'))
import statistics as _st
rows = []
for m in M:
    sc = [v for v in G2['site'][m].values() if v['n_c'] >= 3]; sr = [v for v in G2['site'][m].values() if v['n_r1'] >= 8]; sa = [v for v in G2['site'][m].values() if v['n'] >= 8 and v['acc'] is not None]
    vc = [100 * v['v_c'] / v['n_c'] for v in sc]; rows.append(f"{NAME[m]} & {len(sc)} & {_st.mean(vc):.1f} & {_st.median(vc):.1f} & {100 * sum(1 for x in vc if x > 0) / len(vc):.1f} & {_st.mean([100 * v['v_r1'] / v['n_r1'] for v in sr]):.1f} & {_st.mean([100 * v['acc'] for v in sa]):.1f} {NL}")
table('tab:site', 'Violation rate per website in the vanilla setting.', 'lS[table-format=2.0]S[table-format=2.1]S[table-format=2.1]S[table-format=2.1]S[table-format=1.1]S[table-format=2.1]',
      head(['Model', mc('Websites'), mc('Mean'), mc('Median'), mc('With violations'), mc('R1 mean'), mc('Accuracy')]), rows, 'Values in \\% except Websites, over the websites with at least three test cases of the commit relations.',
      extra_head=[' & & ' + BS + 'multicolumn{3}{c}{Commit relations} & & ' + NL, BS + 'cmidrule(lr){3-5}'])

# ---- RQ4 reasoning effort by outcome
rows = []
def md(xs): return _st.median([x[0] for x in xs]) if xs else float('nan')
def ks(a, b):
    import numpy as np, math
    a, b = np.sort(a), np.sort(b); allv = np.r_[a, b]; cdf = lambda s_, x: np.searchsorted(s_, x, side='right') / len(s_); D = np.max(np.abs(cdf(a, allv) - cdf(b, allv)))
    ne = len(a) * len(b) / (len(a) + len(b)); lam = (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne)) * D
    return float(min(1, 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, 100))))
for m in ('gemini38', 'haiku55', 'gpt54mini'):
    t = G2['tok'][m]; kv = ks([x[0] for x in t['v']], [x[0] for x in t['g']]); ko = ks([x[0] for x in t['o']], [x[0] for x in t['g']])
    rows.append(f"{NAME[m]} & {len(t['g'])} & {md(t['g']):.1f} & {len(t['v'])} & {md(t['v']):.1f} & {pf(kv)} & {len(t['o'])} & {md(t['o']):.1f} & {pf(ko)} {NL}")
table('tab:tokens', 'Median reasoning tokens of decisions in the vanilla setting by outcome.', 'lS[table-format=3.0]S[table-format=3.1]S[table-format=3.0]S[table-format=3.1]S[table-format=1.3]S[table-format=3.0]S[table-format=3.1]S[table-format=1.3]',
      head(['Model', mc('$n$'), mc('Tokens'), mc('$n$'), mc('Tokens'), mc('$p$'), mc('$n$'), mc('Tokens'), mc('$p$')]), rows, 'Kolmogorov-Smirnov test against the decisions that choose the demonstrated control.',
      extra_head=[' & ' + BS + 'multicolumn{2}{c}{Demonstrated control} & ' + BS + 'multicolumn{3}{c}{Forbidden commit} & ' + BS + 'multicolumn{3}{c}{Other wrong control} ' + NL, BS + 'cmidrule(lr){2-3}' + BS + 'cmidrule(lr){4-6}' + BS + 'cmidrule(lr){7-9}'])

# ---- RQ5 per model and task, each guard against S0
rows = []
SN6 = {'cvx': 'CVX written check', 'cv': 'CV one-letter check', 's2': 'S2 rule instruction', 'rg': 'RG risk gate', 'sc': 'SC self-review', 's1': 'S1 history'}
for c in ('s1', 's2', 'sc', 'rg', 'cv', 'cvx'):
    T = G2['mtask'][c]; tv = [t for t in T if t['n_v'] > 0]; tc = [t for t in T if t['n_c'] > 0]
    bv = sum(1 for t in tv if t['v1'] < t['v0']); wv = sum(1 for t in tv if t['v1'] > t['v0']); bc = sum(1 for t in tc if t['c1'] > t['c0']); wc = sum(1 for t in tc if t['c1'] < t['c0'])
    rows.append(f"{SN6[c]} & {len(tv)} & {bv} & {wv} & {len(tc)} & {bc} & {wc} {NL}")
table('tab:task', 'Model and task pairs improved and worsened by each guard against S0.', 'lS[table-format=3.0]S[table-format=2.0]S[table-format=2.0]S[table-format=3.0]S[table-format=2.0]S[table-format=3.0]',
      head(['Guard', mc('Pairs'), mc('Improved'), mc('Worsened'), mc('Pairs'), mc('Improved'), mc('Worsened')]), rows, 'One pair is one task under one of the four models that ran every guard.',
      extra_head=[' & ' + BS + 'multicolumn{3}{c}{Violation rate} & ' + BS + 'multicolumn{3}{c}{Right-commit rate} ' + NL, BS + 'cmidrule(lr){2-4}' + BS + 'cmidrule(lr){5-7}'])
print('tables written')
