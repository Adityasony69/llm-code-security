"""Task-matched comparison: only tasks where every condition has ok samples; per-task means and Semgrep rule ids.
Usage: analyze_matched.py MODEL_DIRNAME"""
import csv, json, sys
from collections import Counter, defaultdict
from pathlib import Path
from analyze import perm_test, mean

ROOT = Path(__file__).resolve().parent.parent
model = sys.argv[1]
rows = list(csv.DictReader(open(ROOT / "data" / f"results_{model}.csv", encoding="utf-8")))
CONDS = ("baseline", "secure", "role")

print("Status by condition:")
for c in CONDS:
    print(f"  {c:8s}", dict(Counter(r["status"] for r in rows if r["cond"] == c)))

ok = [r for r in rows if r["status"] == "ok"]
tasks = sorted({r["task"] for r in ok if all(any(x["task"] == r["task"] and x["cond"] == c for x in ok) for c in CONDS)})
m = [r for r in ok if r["task"] in tasks]
print(f"\nTasks with ok samples in all conditions: {tasks}")

print("\nPer-task mean Semgrep / Bandit (n):")
for t in tasks:
    parts = []
    for c in CONDS:
        v = [r for r in m if r["task"] == t and r["cond"] == c]
        parts.append(f"{c}: sg={mean([int(r['semgrep']) for r in v]):.2f} bd={mean([int(r['findings']) for r in v]):.2f} (n={len(v)})")
    print(f"  {t:12s} " + " | ".join(parts))

print("\nMatched overall (permutation p vs baseline):")
for label, key in [("Semgrep", "semgrep"), ("Bandit", "findings")]:
    vals = {c: [float(r[key]) for r in m if r["cond"] == c] for c in CONDS}
    print(f"  {label:8s} " + "  ".join(f"{c}={mean(v):.2f} (n={len(v)})" + ("" if c == "baseline" else f" p={perm_test(vals['baseline'], v):.3f}") for c, v in vals.items()))

# Semgrep rule ids: scan.py leaves only the last scan in _semgrep_tmp.json, so use it only if it covers this model
sg = json.load(open(ROOT / "data" / "_semgrep_tmp.json", encoding="utf-8"))["results"]
per_file = defaultdict(set)
for x in sg:
    p = Path(x["path"])
    if p.parent.name == model:
        per_file[p.stem].add(x["check_id"].split(".")[-1])
if per_file:
    rules = {c: Counter(i for r in m if r["cond"] == c for i in per_file.get(r["sample"], ())) for c in CONDS}
    print("\nSemgrep rules, matched tasks (files containing: " + " / ".join(CONDS) + "):")
    for i in sorted({i for c in rules for i in rules[c]}, key=lambda i: -sum(rules[c][i] for c in CONDS)):
        print(f"  {i}: " + " / ".join(f"{rules[c][i]:3d}" for c in CONDS))
else:
    print("\n(_semgrep_tmp.json is from another model; rescan needed for rule breakdown)")
