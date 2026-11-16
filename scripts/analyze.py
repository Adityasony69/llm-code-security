"""By-rule breakdown and permutation test. Usage: analyze.py MODEL_DIRNAME"""
import csv, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = [r for r in csv.DictReader(open(ROOT / "data" / f"results_{sys.argv[1]}.csv", encoding="utf-8")) if r["status"] == "ok"]
for r in rows:
    ids = [i for i in r["test_ids"].split(";") if i]
    r["ids"] = ids
    r["n_other"] = sum(i != "B201" for i in ids)  # findings excluding debug=True (rule IDs are unique per file)


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


CONDS = [c for c in ("baseline", "secure", "role") if any(r["cond"] == c for r in rows)]
by = {c: [r for r in rows if r["cond"] == c] for c in CONDS}
print("Files containing each rule (" + " / ".join(CONDS) + "):")
allids = sorted({i for r in rows for i in r["ids"]})
for i in sorted(allids, key=lambda i: -sum(i in r["ids"] for r in rows)):
    print(f"  {i}: " + " / ".join(f'{sum(i in r["ids"] for r in by[c]):3d}' for c in CONDS))

print("\nMean findings per file (permutation p vs baseline):")
for label, f in [("all Bandit", lambda r: int(r["findings"])), ("excl. B201", lambda r: r["n_other"]),
                 ("Semgrep", lambda r: int(r["semgrep"])), ("B105 hardcoded secret", lambda r: "B105" in r["ids"])]:
    vals = {c: [float(f(r)) for r in by[c]] for c in CONDS}
    parts = [f"{c}={mean(v):.2f} (n={len(v)})" + ("" if c == "baseline" else f" p={perm_test(vals['baseline'], v):.3f}")
             for c, v in vals.items()]
    print(f"  {label:24s} " + "  ".join(parts))
print("\nNote: files are not independent (same task, similar seeds); p-values are indicative only.")

