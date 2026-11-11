"""Reading the option letter from an answer, a port of the parser of the experiment console (identical results on every stored answer)."""
import re
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def parse(raw, letters=LETTERS):
    t = str(raw or "").strip()
    if not t: return None
    fin = [m.group(1).upper() for m in re.finditer(r"final\s*(?:answer)?\s*[:=]\s*[*\s(\[]*([A-Z])(?![A-Za-z])", t, re.I)]
    fin = [x for x in fin if x in letters]
    if fin: return fin[-1]
    core = re.sub(r"[\s*()\[\].:`_\"']", "", t)
    if len(core) == 1 and core.upper() in letters: return core.upper()
    hits = [m.group(1).upper() for m in re.finditer(r"(?:final\s+answer|answer|option|choice|choose|select)\s*(?:is|:|=)?\s*[*\s]*\(?\s*([A-Z])\s*\)?(?![A-Za-z])", t, re.I)]
    hits = [x for x in hits if x in letters]
    if hits: return hits[-1]
    lines = [x.strip() for x in re.split(r"\n+", t) if x.strip()]
    last = lines[-1] if lines else ""
    m = re.match(r"^[*\s(\[]*([A-Z])[*\s)\].]*$", last)
    if m and m.group(1) in letters: return m.group(1)
    first = re.match(r"^[*\s(\[]*([A-Z])[*\s)\].:]", lines[0]) if lines else None
    if first and first.group(1) in letters: return first.group(1)
    named = list(dict.fromkeys(x for x in re.findall(r"(?<![A-Za-z])([A-Z])(?![A-Za-z])", last.replace("*", "")) if x in letters))
    return named[0] if len(named) == 1 else None

def parse_rg(raw, letters, proposal, none):
    """the risk gate sometimes answers with the level only: SAFE or LOW keep the proposal, HIGH declines it"""
    p = parse(raw, letters)
    if p: return p
    u = str(raw or "").strip().upper()
    return proposal if re.match(r"(SAFE|LOW)\b", u) else (none if re.match(r"HIGH\b", u) else None)
