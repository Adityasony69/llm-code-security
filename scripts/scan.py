"""Scan generated samples with Bandit. Usage: scan.py MODEL_DIRNAME  -> data/results_<dir>.csv"""
import csv, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANDIT = ROOT / ".venv" / "Scripts" / "bandit.exe"


def main():
    d = ROOT / "data" / "samples" / sys.argv[1]
    rows = []
    for f in sorted(d.glob("*.py")):
        task, cond, seed = f.stem.split("__")
        if f.stat().st_size == 0:
            rows.append([f.stem, task, cond, seed, "empty", "", "", 0, 0, 0, ""])
            continue
        out = ROOT / "data" / "_bandit_tmp.json"
        subprocess.run([str(BANDIT), "-q", "-f", "json", "-o", str(out), str(f)], cwd=ROOT, capture_output=True)
        data = json.loads(out.read_text(encoding="utf-8"))
        res = data["results"]
        sev = lambda s: sum(r["issue_severity"] == s for r in res)
        parse_err = bool(data.get("errors"))
        rows.append([f.stem, task, cond, seed, "parse_error" if parse_err else "ok", len(res), "",
                     sev("HIGH"), sev("MEDIUM"), sev("LOW"), ";".join(sorted({r["test_id"] for r in res}))])
    sg_out = ROOT / "data" / "_semgrep_tmp.json"
    subprocess.run([sys.executable, "-m", "semgrep", "--config", "p/python", "--json", "-o", str(sg_out),
                    "--metrics=off", str(d)], cwd=ROOT, capture_output=True)
    sg = {}
    for r in json.loads(sg_out.read_text(encoding="utf-8"))["results"]:
        sg.setdefault(Path(r["path"]).stem, set()).add(r["check_id"].split(".")[-1])
    for row in rows:
        row[6] = len(sg.get(row[0], ()))
    dest = ROOT / "data" / f"results_{sys.argv[1]}.csv"
    with dest.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sample", "task", "cond", "seed", "status", "findings", "semgrep", "high", "medium", "low", "test_ids"])
        w.writerows(rows)
    print("wrote", dest, len(rows), "rows")


if __name__ == "__main__":
    main()
