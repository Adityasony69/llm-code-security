# llm-code-security

everyone says just add "write secure code" to the prompt. i wanted to see if that actually does anything on small models, the kind you can run on your own laptop. so i tested it, 1st sem MCA.

the long version is [report/report.md](report/report.md), or the [pdf](report/report.pdf) if you don't want to read it here. the prompts are all in [prompts.md](prompts.md).

## what i did

10 backend tasks in flask / fastapi. login, file upload, password reset, ping, fetching a url, stuff like that. each task asked 3 ways:

- normal
- same thing + write secure code
- "you are a senior backend engineer who specialises in application security..."

5 runs each on 2 models, so 300 answers (261 were usable). the models are qwen2.5-coder:3b and qwythos-9b, which is a community 9b finetune. both on ollama with my rtx 4050. it only has 6 gb so the 9b was partly running on cpu.

then i ran bandit and semgrep on everything, and 30 files were checked line by line. AI did the first pass on those and i went through the labels. the tasks and prompts were also drafted with AI help.

## what came out

total warnings: pretty much the same for every prompt, both models.

the 30 files were more interesting. 12 of them had a serious bug. scanners caught 5 (four hardcoded keys and one ssrf) and missed 7. one of the missed ones is a profile page that checks you're logged in but never checks if it's *your* profile. another one sends the password reset token back to whoever asked for it.

did the secure prompt help? in the qwen files it fixed 3 bugs and added 2 new hardcoded keys. so 6 bad files out of 10 became 5 out of 10, i can't call that better.

my favourite is a file that has `SECRET_KEY = "your_secret_key_here"` and right next to it the comment says never hardcode secrets in production.

also with the secure prompt the 9b wrote around 2x more code and 22 of its 50 answers got cut off in the middle.

## where i messed up

semgrep never ran on the second batch. the command was failing, my script didn't check, and it just reused the old result file. so some numbers in the first versions of the report were wrong. i scanned again and fixed them in v3, all the corrections are written at the end of the report. the semgrep column in `data/results_qwythos-9b.csv` is still the old wrong one though, the right numbers are in `data/semgrep_rescan.csv`.

the script that pulls the code out of the answer also grabbed the wrong part in 3 files.

and it's a small test. 5 runs each, the code was read and not run, nobody else checked the review.

## running it

python 3.12 and [ollama](https://ollama.com). windows, the venv has to be called `.venv` because `scan.py` looks for bandit there.

```
pip install -r requirements.txt
ollama pull qwen2.5-coder:3b
python scripts/generate.py qwen2.5-coder:3b 5
python scripts/analyze.py qwen2.5-coder_3b
```

generate takes a while but it skips what's already done, so you can stop it. the samples and results are already in `data/`, so `analyze.py` works without generating anything. `scan.py` is the one with the semgrep problem, run semgrep yourself if you want to rescan.

Aditya Soni
