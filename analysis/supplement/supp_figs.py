# -*- coding: utf-8 -*-
"""Supplementary material of WebConform, part 2: the figures. Fig. S1 shows every counterfactual pair kept for the test on its two real
screenshots, Fig. S2 what the agents choose on the commit relations in the vanilla setting. Reads supp_data.json and the curated export."""
import json, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); CUR = os.environ.get('WC_CURATED', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'curated'))
D = json.load(open(os.path.join(HERE, 'supp_data.json'), encoding='utf-8')); C = {c['sid']: c for c in json.load(open(os.path.join(CUR, 'cases.json'), encoding='utf-8'))['cases']}
BLUE, PURP, PURP_M, BLUE_M, SL, INK, MUT = '#3F6BD0', '#7A5FCB', '#B9ADE8', '#8FB3E6', '#C6CCD7', '#22262E', '#5F6673'
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Liberation Serif', 'Times New Roman', 'DejaVu Serif'], 'font.size': 6.5, 'axes.linewidth': 0.6, 'pdf.fonttype': 42, 'mathtext.fontset': 'stix'})
TW = 390 / 72.27                                                                                  # text width, inches
os.makedirs(os.path.join(HERE, 'figs'), exist_ok=True)
# ------------------------------------------------------------------ Fig. S1 the counterfactual pairs
kept = [p for p in D['pairs'] if p['kept']]
def box(sid, letters):
    c = C[sid]; return [o['box'] for o in c['options'] if o['letter'] in letters and o.get('box')]
def crop(sid, bx):
    c = C[sid]; im = Image.open(os.path.join(CUR, 'img', sid + '.jpg')).convert('RGB'); s = im.width / c['crop'][2]
    x0 = min(b[0] for b in bx) - 30; y0 = min(b[1] for b in bx) - 30; x1 = max(b[0] + b[2] for b in bx) + 30; y1 = max(b[1] + b[3] for b in bx) + 30
    w, h = x1 - x0, y1 - y0; tw_ = max(w, h * 1.45); th_ = max(h, tw_ / 1.45); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - tw_ / 2, cx + tw_ / 2, cy - th_ / 2, cy + th_ / 2
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(c['crop'][2], x1), min(c['crop'][3], y1)
    return im.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))), (x0, y0, s)
nrow = (len(kept) + 1) // 2; fig = plt.figure(figsize=(TW, nrow * 1.18 + 0.05)); W_ = 0.235; GAP = 0.03
for k, p in enumerate(kept):
    r, c2 = divmod(k, 2); e, f = 'CFE_' + p['pid'], 'CFF_' + p['pid']; ce = C[e]
    fld = [o['letter'] for o in ce['options'] if o['letter'] in ce['gold']]; com = [l for l in ce['forbidden']]
    bx = box(e, set(fld) | set(com))
    for j, (sid, title) in enumerate(((f, 'filled'), (e, 'erased'))):
        im, (x0, y0, s) = crop(sid, bx); left = 0.02 + c2 * (2 * W_ + GAP + 0.01) + j * (W_ + 0.005); bottom = 1 - (r + 1) / nrow + 0.03 / nrow * 4
        ax = fig.add_axes([left, 1 - (r + 1) * (1 / nrow) + 0.16 / nrow, W_, 0.70 / nrow]); ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_color(SL); sp.set_linewidth(0.6)
        cs = C[sid]
        for o in cs['options']:
            if not o.get('box'): continue
            if j == 0 and o['letter'] in cs['gold']: col = BLUE
            elif j == 1 and o['letter'] in cs['gold']: col = BLUE
            elif j == 1 and o['letter'] in cs['forbidden']: col = PURP
            else: continue
            b = o['box']; ax.add_patch(Rectangle(((b[0] - x0) * s - 3, (b[1] - y0) * s - 3), b[2] * s + 6, b[3] * s + 6, fill=False, ec=col, lw=1.1))
        ax.set_title('%s, %s' % (p['website'], 'recorded page' if j == 0 else 'input erased'), fontsize=6.2, color=INK, pad=2)
        note = ('%d of 8 MLLMs commit' % p['filled']) if j == 0 else ('%d of 8 commit too early' % p['erased'])
        ax.text(0.5, -0.06, note, transform=ax.transAxes, ha='center', va='top', fontsize=6.2, color=PURP if (j == 1 and p['erased']) else MUT)
fig.savefig(os.path.join(HERE, 'figs', 'S1_pairs.pdf')); plt.close(fig)
# ------------------------------------------------------------------ Fig. S2 what the agents choose on the commit relations
NAME = {'sonnet55': 'Claude Sonnet 5.5', 'gemini38': 'Gemini 3.8 Flash', 'haiku55': 'Claude Haiku 5.5', 'gpt54mini': 'GPT-5.4 mini', 'qwen35': 'Qwen3.5-397B-A17B', 'qwen35_9b': 'Qwen3.5-9B', 'qwen3vl8b': 'Qwen3-VL-8B', 'internvl35': 'InternVL3.5-8B', 'all': 'All eight MLLMs'}
K = (('correct', 'demonstrated control', BLUE), ('forbidden', 'forbidden commit', PURP), ('otherwrite', 'other state-changing control', PURP_M), ('field', 'other field', BLUE_M), ('nav', 'link or label', SL), ('other', 'other control', '#E4E8EF'), ('none', 'no action', 'white'))
fig, axes = plt.subplots(1, 2, figsize=(TW, 2.1), sharey=True); order = ['sonnet55', 'gemini38', 'haiku55', 'gpt54mini', 'qwen35', 'qwen35_9b', 'qwen3vl8b', 'internvl35', 'all']
for ax, (rel, title) in zip(axes, (('R2', '(a) R2 precondition, before the commit'), ('R3', '(b) R3 idempotency, after the commit'))):
    for i, m in enumerate(order[::-1]):
        a = D['anatomy'][f'{rel}|{m}']; x = 0
        for k, lab, col in K:
            v = a[k]; ax.barh(i, v, left=x, color=col, edgecolor='#8E97A6' if col == 'white' else 'white', lw=0.4, height=0.72); x += v
        if m == 'all': ax.axhline(i + 0.5, color=SL, lw=0.6)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([NAME[m] for m in order[::-1]]); ax.set_xlim(0, 100); ax.set_xlabel('Decisions (%)'); ax.set_title(title, fontsize=6.8, pad=3)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
fig.legend(handles=[Rectangle((0, 0), 1, 1, fc=col, ec='#8E97A6' if col == 'white' else col, lw=0.4) for _, _, col in K], labels=[lab for _, lab, _ in K], loc='upper center', ncol=4, frameon=False, fontsize=6.2, handlelength=1.1, columnspacing=1.2, bbox_to_anchor=(0.56, 1.01))
fig.subplots_adjust(left=0.165, right=0.985, top=0.74, bottom=0.16, wspace=0.08)
fig.savefig(os.path.join(HERE, 'figs', 'S2_anatomy.pdf')); plt.close(fig)
print('figures written', sorted(os.listdir(os.path.join(HERE, 'figs'))))
