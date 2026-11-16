"""Generate code samples from a local Ollama model. Usage: generate.py MODEL N [TASK_ID ...]"""
import json, re, sys, time, urllib.request
from pathlib import Path
from tasks import TASKS, CONDITIONS

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def ask(model, prompt, seed):
    payload = {"model": model, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.7, "seed": seed, "num_ctx": 4096, "num_predict": 1500}}
    if model.startswith("qwythos"):
        payload["think"] = False  # model otherwise writes its reasoning into the reply and hits num_predict before the code
    body = json.dumps(payload).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def main():
    model, n = sys.argv[1], int(sys.argv[2])
    only = set(sys.argv[3:])
    out = ROOT / "data" / "samples" / model.replace(":", "_")
    out.mkdir(parents=True, exist_ok=True)
    meta = []
    for t in TASKS:
        if only and t["id"] not in only:
            continue
        for cond, tpl in CONDITIONS.items():
            for i in range(n):
                name = f'{t["id"]}__{cond}__{i}'
                path = out / f"{name}.py"
                if path.exists():
                    continue
                t0 = time.time()
                res = ask(model, tpl.format(**t), seed=i)
                raw = res["response"]
                m = FENCE.findall(raw)
                code = max(m, key=len) if m else ""
                path.write_text(code, encoding="utf-8")
                (out / f"{name}.raw.txt").write_text(raw, encoding="utf-8")
                rec = {"name": name, "task": t["id"], "cond": cond, "seed": i, "extracted": bool(m),
                       "tokens": res.get("eval_count"), "secs": round(time.time() - t0, 1)}
                meta.append(rec)
                print(rec, flush=True)
    log = out / "meta.jsonl"
    with log.open("a", encoding="utf-8") as f:
        for r in meta:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
