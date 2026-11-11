"""Tests of the WebConform package against the experiment: run with  python tests/run_tests.py  from the repository root.
1  the parser reads every stored answer of the experiment exactly as the experiment console did
2  the oracle gives the forbidden set and the chance level of the paper on every test case, and the pooled ratio of the paper
3  the prompts equal those of the console module (harness/atelier/webconform.js), rendered with Node.js when it is installed
4  end to end: a small bundle, a mock OpenAI-compatible server, the run command for a first- and a second-stage setting, the score"""
import contextlib, csv, http.server, io, json, os, shutil, subprocess, sys, tempfile, threading, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "analysis"))
from webconform import prompts, oracle
from webconform.parse import parse, parse_rg, LETTERS
EXP, CUR = os.path.join(ROOT, "data", "export"), os.path.join(ROOT, "data", "curated")
SCR = {r["probe"]: r for r in csv.DictReader(open(os.path.join(EXP, "screens.csv"), encoding="utf-8-sig"))}
L = lambda s: [x for x in (s or "").split("|") if x]

def q_from_screens(r):
    """a test case rebuilt from screens.csv (tags and the flags of every option, without texts)"""
    tags = dict(x.split(":", 1) for x in L(r["option_tags"])); strict, rep, gold = set(L(r["strict_letters"])), set(L(r["repeat_letters"])), set(L(r["gold_letters"]))
    opts = [{"letter": l, "tag": t, "text": "", "strict": l in strict, "repeat": l in rep, "gold": l in gold} for l, t in tags.items()]
    return {"sid": r["probe"], "relation": r["relation"], "options": opts, "none": r["none_letter"]}

def test_parse():
    d = json.load(open(os.path.join(EXP, "results.json"), encoding="utf-8")); n = bad = 0
    s0 = {(r["tag"], r["sid"]): (r.get("parsed") or {}).get("answer") for r in d["records"] if r.get("ok") and r["cond"] == "s0"}   # proposals of the risk gate
    for r in d["records"]:
        if not r.get("ok") or r["sid"] not in SCR: continue
        letters = LETTERS[:int(SCR[r["sid"]]["n_options"]) + 1]; stored = (r.get("parsed") or {}).get("answer"); n += 1
        if r["cond"] == "rg":   # the paper applies the level-only rule of the risk gate to answers without a letter (analysis.pred), as the console does
            mine = parse_rg(r.get("raw"), letters, s0.get((r["tag"], r["sid"])), SCR[r["sid"]]["none_letter"])
            stored = stored or parse_rg(r.get("raw"), "", s0.get((r["tag"], r["sid"])), SCR[r["sid"]]["none_letter"])
        else: mine = parse(r.get("raw"), letters)
        if stored != mine: bad += 1
    assert bad == 0, f"{bad} of {n} answers parsed differently"; return f"{n:,} stored answers read identically, risk-gate levels included"

def test_oracle():
    with contextlib.redirect_stdout(io.StringIO()):
        cwd = os.getcwd(); os.chdir(os.path.join(ROOT, "analysis")); import analysis as A; os.chdir(cwd)
    for s, r in SCR.items():
        q = q_from_screens(r); assert oracle.forbidden(q) == A.viol_letters(r), s; assert abs(oracle.chance(q) - A.pi_(s)) < 1e-12, s
    from webconform.score import score
    rows = [(A.pred(m, s, "s0") in oracle.forbidden(q_from_screens(SCR[s])), oracle.chance(q_from_screens(SCR[s]))) for s in A.main if SCR[s]["relation"] == "R2" for m in A.MODELS]
    ratio = sum(v for v, _ in rows) / sum(p for _, p in rows); ref = json.load(open(os.path.join(ROOT, "analysis", "numbers2.json")))["grp"]["all"]["R2"]["ratio"]
    assert abs(ratio - ref) < 1e-12, (ratio, ref)
    import numpy as np, random
    random.seed(1)
    for _ in range(20):
        ps = [random.random() * 0.2 for _ in range(30)]; k = random.randint(0, 8); assert abs(oracle.exact_p(k, ps) - A.exact_p(k, ps)) < 1e-9
    return f"forbidden set and chance level equal on all {len(SCR):,} test cases, pooled R2 ratio {ratio:.2f} as in the paper"

def running_example():
    c = {x["sid"]: x for x in json.load(open(os.path.join(CUR, "cases.json"), encoding="utf-8"))["cases"]}["R2_721d2638-65b7-409e-8714-31d2d495e08e_8"]
    return {"task": c["task"], "options": [{"letter": o["letter"], "tag": o["tag"], "text": o.get("text")} for o in c["options"]], "none": c["none"],
            "history": ["[textbox]  Recipient's Name -> TYPE: John", "[textbox]  Recipient's Email -> TYPE: abc@test.com"], "paraphrases": None}

def test_prompts_js():
    q = running_example(); py = {c: prompts.user_text(q, c, "V") for c in prompts.SETTINGS}; py["judge"] = prompts.judge_text(q, "V")
    py.update({"system": prompts.SYSTEM, "system_verify": prompts.SYSTEM_VERIFY})
    if not shutil.which("node"): return "skipped, Node.js is not installed (Python renders checked against prompts.json only)"
    js = open(os.path.join(ROOT, "harness", "atelier", "webconform.js"), encoding="utf-8").read()
    a = js[js.index("E.SYSTEM = "):js.index("const urls = new Map();")]; b = js[js.index("E.JUDGE_SYSTEM ="):js.index("E.judgeSample =")]
    src = ("const E = { TWO_STAGE: { cvx: true, cv: true, sc: true, rg: true } };\n" + a + "\n" + b + "\nconst q = " + json.dumps(q) + ";\nq.byLetter = Object.fromEntries(q.options.map((o) => [o.letter, o]));\n"
           "const out = {}; for (const c of " + json.dumps(list(prompts.SETTINGS)) + ") out[c] = E.userText(q, c, 'V'); out.judge = E.judgePrompt(q, 'V'); out.system = E.SYSTEM; out.system_verify = E.SYSTEM_VERIFY;\nprocess.stdout.write(JSON.stringify(out));\n")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f: f.write(src); path = f.name
    out = json.loads(subprocess.run(["node", path], capture_output=True, text=True, check=True).stdout); os.unlink(path)
    for k in py: assert py[k] == out[k], f"{k} differs:\nPY {py[k][:300]}\nJS {out[k][:300]}"
    return f"{len(py)} prompts identical to the console module, rendered with Node.js"

def test_end_to_end():
    C = {x["sid"]: x for x in json.load(open(os.path.join(CUR, "cases.json"), encoding="utf-8"))["cases"]}; pick = {}
    for s, c in sorted(C.items()):
        if c["relation"] not in pick: pick[c["relation"]] = s
    tmp = tempfile.mkdtemp(); bz = os.path.join(tmp, "mini.zip")
    with zipfile.ZipFile(bz, "w") as z:
        z.writestr("mini/manifest.json", json.dumps({"format": "webconform-bundle/1", "name": "mini", "built": "test"}))
        lines = []
        for rel, s in pick.items():
            c = C[s]; lines.append(json.dumps({"qid": s, "relation": rel, "task": c["task"], "website": c["website"], "domain": c["domain"], "split": c["split"], "image": f"img/{s}.jpg",
                "options": [{"id": o["letter"], "tag": o["tag"], "text": o.get("text"), "box": o.get("box"), "gold": o["letter"] in c["gold"], "repeat": rel != "R1" and o["letter"] in c["forbidden"], "write": o["letter"] in c["forbidden"]} for o in c["options"]]}))
            z.write(os.path.join(CUR, "img", s + ".jpg"), f"mini/img/{s}.jpg")
        z.writestr("mini/probes.jsonl", "\n".join(lines) + "\n")
    seen = []
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"]))); seen.append(body)
            ans = "Final: A" if body["messages"][0]["content"] == prompts.SYSTEM_VERIFY else "A"
            out = json.dumps({"choices": [{"message": {"content": ans}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    env = dict(os.environ, PYTHONPATH=ROOT)
    for st, extra in (("s0", []), ("cvx", ["--proposals", os.path.join(tmp, "s0.jsonl")])):
        subprocess.run([sys.executable, "-m", "webconform.run", "--bundle", bz, "--base-url", url, "--model", "mock", "--setting", st, "--out", os.path.join(tmp, st + ".jsonl"), "--concurrency", "2"] + extra, check=True, env=env, capture_output=True)
    sc = subprocess.run([sys.executable, "-m", "webconform.score", "--bundle", bz, "--decisions", os.path.join(tmp, "s0.jsonl")], check=True, env=env, capture_output=True, text=True).stdout
    srv.shutdown(); dec = [json.loads(l) for st in ("s0", "cvx") for l in open(os.path.join(tmp, st + ".jsonl"))]
    assert len(dec) == 2 * len(pick) and all(d["answer"] == "A" for d in dec), (len(dec), len(pick), [d["answer"] for d in dec])
    from webconform import bundle
    _, cases = bundle.load(bz); q = next(x for x in cases if x["relation"] == "R2"); r = next(b for b in seen if b["messages"][1]["content"][0]["text"].startswith("Task: " + q["task"]) and b["messages"][0]["content"] == prompts.SYSTEM)
    assert r["messages"][1]["content"][0]["text"] == prompts.user_text(q, "s0") and r["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,") and r["temperature"] == 0
    shutil.rmtree(tmp); return f"{len(seen)} requests to a mock server, {len(dec)} decisions, scoring prints {len(sc.strip().splitlines()) - 1} relations"

if __name__ == "__main__":
    fails = 0
    for t in (test_parse, test_oracle, test_prompts_js, test_end_to_end):
        try: print(f"PASS  {t.__name__:18s} {t()}")
        except Exception as e: fails += 1; print(f"FAIL  {t.__name__:18s} {type(e).__name__}: {str(e)[:600]}")
    sys.exit(1 if fails else 0)
