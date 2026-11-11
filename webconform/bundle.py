"""Reading a test suite bundle (format webconform-bundle/1): a ZIP archive with manifest.json, probes.jsonl and the screenshots."""
import json, os, zipfile
from .oracle import make_question

def load(path, ids=None):
    """the manifest and the test cases of a bundle, each with its options lettered and its screenshot as bytes"""
    z = zipfile.ZipFile(path); names = z.namelist(); base = {os.path.basename(n): n for n in names}
    find = lambda n: n if n in names else next((k for k in names if k.endswith("/" + n)), None)
    man_n, prb_n = find("manifest.json"), find("probes.jsonl")
    if not man_n or not prb_n: raise ValueError("not a WebConform bundle: manifest.json or probes.jsonl is missing")
    man = json.loads(z.read(man_n).decode("utf-8"))
    if man.get("format") != "webconform-bundle/1": raise ValueError("unsupported bundle format: %s" % man.get("format"))
    keep = set(ids) if ids else None; cases = []
    for line in z.read(prb_n).decode("utf-8").splitlines():
        if not line.strip(): continue
        q = make_question(json.loads(line))
        if keep is not None and q["sid"] not in keep: continue
        img = q.get("image"); n = base.get(os.path.basename(img)) if img else None
        if not n: continue                                   # a test case without its screenshot is not run, as in the console
        q["image_bytes"] = z.read(n); cases.append(q)
    return man, cases
