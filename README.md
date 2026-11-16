# Security of web code written by small local LLMs

A small study I did during my MCA (1st semester) on a simple question: if you run a small code model on your own laptop and ask it to write Flask or FastAPI code, how secure is that code, and does adding "write secure code" to the prompt help?

The full write-up is in [report/report.md](report/report.md).

## What I did

- Wrote 10 common backend tasks (login, file upload, password reset, fetch a URL, etc.). Each one is a task where a known type of bug can easily appear.
- Asked two local models to solve each task in 3 ways: a normal prompt, a prompt asking for secure code, and a "you are a security engineer" prompt. 5 runs each, so 150 files per model.
  - `qwen2.5-coder:3b`
  - `qwythos-9b` (a community 9B fine-tune, Q4_K_M)
- Scanned every file with Bandit and Semgrep.
- Read 30 of the files by hand and marked the real security problems.

Everything ran locally with Ollama on a laptop RTX 4050 (6 GB).

## What I found

1. **The prompt made no visible difference to the scanner results**, for either model.
2. **The scanners missed the serious problems.** In the 30 files I read, the only serious issues they caught were hardcoded secrets. They missed every logic flaw: users able to read other users' data (IDOR), password reset tokens handed to anyone, SSRF, and file uploads that can write anywhere on disk.
3. **Read by hand, the secure prompt did fix some of these** (3 flaws fixed in the qwen sample), but it also left SSRF and reset-token bugs in place, even though the prompt names SSRF.
4. **The secure prompt made the 9B model write about twice as much code**, so 22 of its 50 answers got cut off at the output limit. That makes its secure results less reliable, and I've reported it in the write-up rather than hidden it.

So counting scanner warnings is not a good way to judge whether a prompt makes AI code safer.

## Limits

This is a small study: 5 runs per setting, one person checking the hand review, and the code was read, not executed. The details are in section 6 of the report.

## Repo layout

```
scripts/   tasks.py (tasks + prompts), generate.py, scan.py, analyze*.py
data/      scan results (CSV) and all generated code samples
report/    report.md and manual-review.md (the 30 hand-reviewed files)
```

## Running it

Needs Python 3.12 and [Ollama](https://ollama.com) with the model pulled.

```
pip install -r requirements.txt
python scripts/generate.py qwen2.5-coder:3b 5
python scripts/scan.py qwen2.5-coder_3b
python scripts/analyze.py qwen2.5-coder_3b
```

`generate.py` skips files that already exist, so it can be stopped and started again.

## Author

Aditya Soni, MCA (AI/ML), Lovely Professional University
