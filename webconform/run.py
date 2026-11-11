"""Run one setting of WebConform on a test suite bundle with one model, one decision per test case.

    python -m webconform.run --bundle probes.zip --base-url http://127.0.0.1:8000/v1 --model qwen3-vl-8b --setting s0 --out s0.jsonl
    python -m webconform.run ... --setting cvx --proposals s0.jsonl --out cvx.jsonl        (second-stage settings need the s0 decisions)

The output is one JSON line per decision. A run can be resumed, test cases already in the output file are skipped."""
import argparse, concurrent.futures as cf, json, os, sys, threading
from . import bundle, client, prompts
from .parse import parse, parse_rg

def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--bundle", required=True); a.add_argument("--base-url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--setting", default="s0", choices=prompts.SETTINGS); a.add_argument("--out", required=True)
    a.add_argument("--proposals", help="decisions of the s0 setting of the same model, required by cvx, cv, sc and rg")
    a.add_argument("--ids", help="file with one test case id per line (for example the main set), default all")
    a.add_argument("--api-key-env", default="OPENAI_API_KEY", help="name of the environment variable that holds the API key")
    a.add_argument("--extra-body", help='JSON merged into every request, for example {"reasoning": {"effort": "low"}}')
    a.add_argument("--concurrency", type=int, default=8); a.add_argument("--limit", type=int); a.add_argument("--max-tokens", type=int, default=4096)
    o = a.parse_args(argv)
    ids = [l.strip() for l in open(o.ids, encoding="utf-8") if l.strip()] if o.ids else None
    man, cases = bundle.load(o.bundle, ids)
    prop = {}
    if o.setting in prompts.TWO_STAGE:
        if not o.proposals: sys.exit("--proposals is required for the setting " + o.setting)
        for line in open(o.proposals, encoding="utf-8"):
            r = json.loads(line); prop[r["test_case"]] = r.get("answer")
    done = set()
    if os.path.exists(o.out):
        for line in open(o.out, encoding="utf-8"):
            try: done.add(json.loads(line)["test_case"])
            except (ValueError, KeyError): pass
    todo = [q for q in cases if q["sid"] not in done and (o.setting not in prompts.TWO_STAGE or prop.get(q["sid"]))]
    if o.limit: todo = todo[:o.limit]
    key = os.environ.get(o.api_key_env); extra = json.loads(o.extra_body) if o.extra_body else None; lock = threading.Lock()
    print(f"{man.get('name')} built {man.get('built')}: {len(cases)} test cases, {len(done)} already done, {len(todo)} to run", file=sys.stderr)
    def one(q):
        p = prop.get(q["sid"]); text = prompts.user_text(q, o.setting, p)
        raw, usage, lat, att = client.chat(o.base_url, o.model, prompts.system_text(o.setting), text, q["image_bytes"], api_key=key, max_tokens=o.max_tokens, extra=extra)
        ans = parse_rg(raw, q["letters"], p, q["none"]) if o.setting == "rg" else parse(raw, q["letters"])
        return {"test_case": q["sid"], "relation": q["relation"], "setting": o.setting, "model": o.model, "answer": ans, "raw": raw, "usage": usage, "latency": round(lat, 3), "attempts": att}
    n = 0
    with open(o.out, "a", encoding="utf-8") as f, cf.ThreadPoolExecutor(max_workers=max(1, o.concurrency)) as ex:
        for fut in cf.as_completed([ex.submit(one, q) for q in todo]):
            try: r = fut.result()
            except RuntimeError as e: print("failed:", e, file=sys.stderr); continue
            with lock: f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush(); n += 1
            if n % 50 == 0: print(f"{n} of {len(todo)}", file=sys.stderr)
    print(f"done: {n} new decisions in {o.out}", file=sys.stderr)

if __name__ == "__main__": main()
