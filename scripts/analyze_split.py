"""Split Bandit findings into deployment-style (B201 debug=True, B104 bind 0.0.0.0) vs other. Usage: analyze_split.py RESULTS_CSV_STEM"""
import csv, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = {"B201", "B104"}


def mean(xs):
    return sum(xs) / len(xs)


def perm_test(a, b, n=20000, seed=0):
    rnd = random.Random(seed)
    obs = abs(mean(a) - mean(b))
    pool, k, hits = a + b, len(a), 0
    for _ in range(n):
        rnd.shuffle(pool)
        hits += abs(mean(pool[:k]) - mean(pool[k:])) >= obs
    return (hits + 1) / (n + 1)


rows = [r for r in csv.DictReader(open(ROOT / "data" / f"{sys.argv[1]}.csv", encoding="utf-8")) if r["status"] == "ok"]
for r in rows:
    ids = [i for i in r["test_ids"].split(";") if i]
    r["deploy"] = float(sum(i in DEPLOY for i in ids))
    r["other"] = float(sum(i not in DEPLOY for i in ids))
conds = [c for c in ("baseline", "secure", "role") if any(r["cond"] == c for r in rows)]
by = {c: [r for r in rows if r["cond"] == c] for c in conds}
for label in ("deploy", "other"):
    vals = {c: [r[label] for r in by[c]] for c in conds}
    print(f"{label:7s} " + "  ".join(f"{c}={mean(v):.2f} (n={len(v)})" + ("" if c == "baseline" else f" p={perm_test(vals['baseline'], v):.3f}") for c, v in vals.items()))
