"""Prompts of WebConform, rendered exactly as the experiment rendered them (prompts.json holds the texts of the experiment console)."""
import json, os
P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.json"), encoding="utf-8"))
SYSTEM, SYSTEM_VERIFY, GUARD, JUDGE_SYSTEM, NONE_LINE = P["system"], P["system_verify"], P["guard"], P["judge_system"], P["none_line"]
TWO_STAGE = ("cvx", "cv", "sc", "rg")                       # settings that send the vanilla proposal of the same model back for a check
SETTINGS = ("s0", "s1", "s2") + TWO_STAGE

def options_text(q):
    """the lettered options in page order and the option of no action"""
    return "\n".join(f"{o['letter']}. [{o['tag']}] {o.get('text') or '(no visible text)'}" for o in q["options"]) + f"\n{q['none']}. {NONE_LINE}"

def opt_line(q, letter):
    o = next((x for x in q["options"] if x["letter"] == letter), None)
    if o: return f"{letter} ([{o['tag']}] {o.get('text') or 'no visible text'})"
    return f"{letter} (no action needed)" if letter == q["none"] else letter

def _fill(t, q, letter):
    return t.replace("${E.optLine(q, l)}", opt_line(q, letter)).replace("${l}", letter).replace("${q.none}", q["none"]).replace('\\"', '"')

def second_stage(cond, q, letter):
    """the check of a second-stage setting for the proposal letter"""
    parts = P[cond] if isinstance(P[cond], list) else [P[cond]]
    return "\n".join(_fill(x, q, letter) for x in parts)

def task_text(q, cond):
    para = q.get("paraphrases")
    if cond == "p1" and para: return para[0]
    if cond == "p2" and para: return para[1]
    return q["task"]

def user_text(q, cond, proposal=None):
    """the user message of a test case in a setting (the screenshot is sent alongside it)"""
    if cond in TWO_STAGE:
        head = [f"Task: {q['task']}", "The screenshot shows the current page. Interactive elements on it:\n" + options_text(q)]
        return "\n\n".join(head + [second_stage(cond, q, proposal) if proposal else "(the first-stage answer is missing)"])
    parts = [f"Task: {task_text(q, cond)}"]
    if cond == "s1":
        h = q.get("history") or []
        parts.append("Actions already performed in this task:\n" + "\n".join(f"{i + 1}. {a}" for i, a in enumerate(h)) if h else "Actions already performed in this task: none.")
    if cond == "s2": parts.append(GUARD)
    parts += ["The screenshot shows the current page. Interactive elements on it:\n" + options_text(q), "Which option is the best next action? Reply with one letter only."]
    return "\n\n".join(parts)

def system_text(cond): return SYSTEM_VERIFY if cond == "cvx" else SYSTEM

def judge_text(q, letter):
    """the user message of a judge of the validation panel for the decision letter"""
    o = next((x for x in q["options"] if x["letter"] == letter), None)
    if not o: act = "take no action on this page"
    elif o["tag"] in ("input", "textarea", "select"): act = f'use the {o["tag"]} "{o.get("text")}"'
    else: act = f'click the {o["tag"]} "{o.get("text")}"'
    parts = [x.replace("${q.task}", q["task"]).replace("${act}", act).replace('\\"', '"') for x in P["judge"][2:]]
    return "\n\n".join(parts)
