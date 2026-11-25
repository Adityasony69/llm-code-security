# Do security prompts make code from small local LLMs safer? A small study with scanners and manual review

**Technical report v3, 2026-11-25.** Author: Aditya Soni. This version corrects mistakes in v2, listed at the end under "Corrections". Numbers come from `data/results_qwen2.5-coder_3b.csv`, `data/results_qwythos-9b.csv`, `data/samples/qwythos-9b/meta.jsonl` and `report/manual-review.md`. The exception is Semgrep on qwythos: that column in the CSV is wrong for the second run, so those numbers come from `data/semgrep_rescan.csv`, a rescan of the same files on 2026-11-25 (Section 3). Quotes from 2407.07064, 2605.24298, 2602.05868 and 2607.23088 were checked word for word against the arXiv html text (2026-10-29); the 2510.26103 Table 8 figure was checked by me against the paper (2026-11-16). Other papers' details come from abstracts and tool summaries and are paraphrased, not quoted.

*Does asking a small AI model for "secure code" actually make its code safer?*

## Summary

**The question.** A lot of students and small teams now run small AI models on their own laptop to write code. A common habit is to add "write secure code" to the prompt and then run a security scanner to check the result. I wanted to know if that habit works.

**What I did.**
- I used 10 everyday backend tasks (login, file upload, password reset, fetching a URL, and so on) and asked two small local models to write Flask or FastAPI code for each one.
- Each task was asked three ways: a normal prompt, the same prompt plus "write secure code", and a "you are a security engineer" prompt. Five runs each, so 300 code files in total.
- I scanned every file with two free security scanners (Bandit and Semgrep), and 30 files were reviewed line by line. An AI assistant did the first pass of that review and I checked the labels and lowered two of them.

**What I found.**
1. The total number of scanner warnings did not change in any clear way with the prompt, for either model. The kind of warning did change for the bigger model: with the secure prompt it set the server to listen on all addresses more often (17 of 27 files, against 6 of 37 for the same tasks with the normal prompt).
2. When 30 files were read by hand, 12 had a serious bug and the scanners missed 7 of them. The 5 they caught were four keys typed directly into the code and one SSRF. They missed things like one user being able to read another user's profile, or a password reset token being handed to whoever asks for it.
3. The "secure" prompt did fix some of those serious bugs (three in the files I read), but it left others in place and added two new hardcoded keys. For the qwen files that is 6 of 10 with a serious bug going to 5 of 10, which is too small to call an improvement.
4. The "secure" prompt made the bigger model write about twice as much code, so 22 of its 50 answers were cut off before the code was finished.

**Why it matters.** A clean scanner report does not mean the code is safe, and a "no change" result from scanners does not mean a prompt did nothing. If you use local models for backend code, you still have to read the login, ownership and token logic yourself.

## Key terms

- **Local model:** an AI model that runs on your own computer (here through Ollama), not on a company's server.
- **Prompt / condition:** the instruction given to the model. Each of the three prompt styles is called a condition.
- **Seed:** a number that controls the model's randomness. Different seeds give different answers to the same prompt.
- **Token limit:** the maximum length of the model's answer. A token is roughly a short word or part of a word. Here the limit was 1,500 tokens.
- **Static scanner:** a tool that reads code without running it and flags patterns that are often unsafe.
- **Bandit / Semgrep:** two free static scanners for Python.
- **Hardcoded secret:** a password or key written directly in the code, so anyone who sees the code has it.
- **IDOR (insecure direct object reference):** the app lets you open `/profile/5` without checking that profile 5 is yours.
- **SSRF (server-side request forgery):** the app fetches any URL a user gives it, so an attacker can make the server call internal addresses.
- **Path traversal:** a file name like `../../config.py` lets a user read or write files outside the intended folder.
- **Authentication bypass:** a login check that can be skipped or fooled.
- **p-value:** a number that says how likely a difference this size is to show up by pure chance. Small (below about 0.05) suggests a real effect; large means "can't tell apart from chance".

## Abstract

I generated Flask and FastAPI backend code for 10 common tasks with two small local models, qwen2.5-coder:3b and an uncensored Qwen-based 9B fine-tune run as Q4_K_M (qwythos-9b), under three prompt conditions: baseline, a generic security instruction, and a security-engineer persona (150 samples per model). The code was scanned with Bandit and Semgrep (p/python). For neither model did total scanner finding counts show a prompt effect (qwen all p > 0.4; qwythos, task-matched, all p > 0.2). Within qwythos the result depends on the task: in t01–t03 the security instruction gave more findings (p = .03 Bandit, p = .02 Semgrep), in the other matched tasks it gave fewer (not significant), and the two cancel out. Binding the server to 0.0.0.0 became more common under the security instruction (6/37 to 17/27 matched files). For qwythos, the security instruction roughly doubled output length (median 1,386 vs 736 tokens) and 22 of 50 secure outputs were cut off at the 1,500-token limit, against 3 of 50 baseline, so the secure condition is under-sampled exactly on the most complex tasks. A manual review of 30 files found 12 with a high-severity flaw, of which both scanners missed 7: insecure direct object reference (IDOR), one of two SSRF files, password-reset token disclosure, path traversal on upload, authentication bypass and secrets leaked by a health endpoint. The 5 caught were four hardcoded keys and one SSRF (by Semgrep). In the manual sample the security instruction removed some flaws and added others (qwen High-severity files 6/10 to 5/10: three flaws fixed, two new hardcoded keys), which is too small a change, from one seed, to call an improvement. I argue that scanner finding counts alone are a weak main outcome for security-prompting studies on web backend code, and that output-length limits should be reported because security prompts can change output length.

## 1. Introduction

Small code models such as qwen2.5-coder 3B can now run on an ordinary gaming laptop. For students and small teams that is attractive: it is free, works offline, and the code never leaves your machine. Most security studies of AI-written code look at large cloud models like GPT-4 or Claude, so much less is known about these small local ones, even though they are the ones many beginners actually use.

Two habits are common when people try to make AI-written code safer. The first is to add a line to the prompt, such as "write secure code" or "you are a security engineer". The second is to run a scanner like Bandit afterwards and treat a short warning list as a good sign. Many research papers also rely on the second habit: they count scanner warnings and compare the counts across prompts.

The problem is that many serious web bugs are about logic, not about a dangerous-looking line. Here is part of what qwen2.5-coder wrote for the "profile by id" task (`data/samples/qwen2.5-coder_3b/t04_profile__baseline__0.py`):

```python
@app.get("/users/{user_id}")
async def read_user(user_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

It checks that someone is logged in, and nothing in it looks unsafe to a scanner. But it never checks that the logged-in user is the owner of `user_id`, so the logic lets any logged-in user read any other user's profile just by changing the number in the URL. (The file would not run as written, for example its login looks up an `id` that its demo users don't have, but the missing check is real.) If scanners cannot see this kind of bug, a study that only counts scanner warnings could miss a real change caused by the prompt, or report a change that isn't really about security.

The background from earlier research, and the three questions this study asks, are below.

- Developers increasingly run small code models locally (privacy, cost, offline use). Their security behaviour on everyday web backend tasks is less studied than that of frontier models.
- The literature disagrees on whether security-aware prompting helps. One study reports no statistically significant reduction across prompting methods [2605.24298]. Others report large reductions with recursive self-critique [2407.07064], scenario-tailored guidance [2607.23088], or optimised system prompts [2605.08382].
- Most such studies measure security with static analysers. Analyser precision and recall against human ground truth are modest: in one study, Semgrep recall was 0.54 and precision 0.52, CodeQL 0.34 and 0.67 (GPT-4o Python code, human labels for each task's target CWE), and "only 65% of Semgrep's and 61% of CodeQL's reports correctly matched the ground truth" [2602.05868].
- Research questions:
  - RQ1: Do the scanners see any difference when the model is asked for secure code?
  - RQ2: What are the scanners actually catching in this code?
  - RQ3: When a person reads the code, do they reach the same conclusion as the scanners?

## 2. Related work

- **Security prompting, mixed results.**
  - 2407.07064 (GPT-3/3.5/4, LLMSecEval, Bandit): RCI "reduced the average weakness density by 77.5% compared to baseline prompting" for GPT-4. The effect of the zero-shot security variants "does not exhibit a consistent pattern across the three models that were evaluated". "Bandit flagged this weakness in the code generated by the LLMs whenever a Flask application was executed in debug mode", and with security cues "the model generated code that turned the debug mode off". qwythos-9b moves in the same direction, but not significantly (Section 4.3).
  - 2605.24298 (5 large models, 4 languages, SonarQube, chi-square tests): "no statistically significant reductions in vulnerability frequency or density across prompt methods". WA-0CoT (adds CWE hints) "generated more vulnerabilities in all languages except two instances".
  - 2607.23088 (poster; 6 frontier + Qwen3-4B + GLM-Z1-Air; CodeQL, Clang SA, expert review): baseline "vulnerability rates exceeding 56%"; with scenario-tailored guidance, "Claude-Sonnet-4 achieves the largest improvement, with a vulnerability-rate reduction of up to 45%, whereas Qwen3-4B shows the smallest improvement, with a 37% reduction". The paper does not say whether these are relative or absolute.
  - 2605.08382 (SecureForge; Semgrep + unit tests): frontier models still produce vulnerabilities "on average 23% of the time" even when explicitly asked for secure code with the relevant weaknesses in context. Optimised system prompts reduced output vulnerabilities "by up to 48%" "on frontier models" (abstract). The body also tests "the instruction-tuned variants of Qwen 2.5 Coder 7B, 14B"; per-model values appear only in figures, which I did not read.
- **Execution-based evaluation.** 2407.02395 (CodeSecEval; abstract only) argues that progress has been "hindered by benchmarks that are small, non-executable, leak mitigation details, or rely on noisy analyzers and subjective judgments", and provides 255 Python tasks (77 CWEs) with "executable functional and vulnerability-targeted security tests". This is the kind of outcome measure my results argue for.
- **Scanner validity.** 2602.05868 reports Semgrep and CodeQL precision/recall well below 1 against human labels. 2310.02059 (Copilot code in GitHub projects): "we did not follow the CWE IDs of 55 out of 235 security issues reported by Bandit". In 2510.26103 (AI-generated code in public GitHub repositories), Table 8 lists CWE-563 "Assignment to Variable without Use" as the top CodeQL finding for ChatGPT-generated Python (1,044 instances, 42.30%). That is a code-quality rule, not a security flaw.
- **Gap (modest).** After about six targeted searches I found no published study of Flask/FastAPI code from 3–9B quantized local models that compares security prompts. An unfinished student repository (github.com/Jolteer/ai-code-security) plans a similar design but reports no results. Absence from searches is not proof of novelty.

## 3. Method

- **Tasks:** 10 backend tasks (`scripts/tasks.py`), 6 Flask and 4 FastAPI: login, search, upload/download, profile by id, JWT, comments/HTML, URL fetch, ping, password reset, config/health. Each task targets a known vulnerability class. The tasks and prompts were drafted with help from an AI assistant and not validated against a benchmark. All 30 prompts are in `prompts.md`.
- **Conditions:** baseline; *secure* (baseline plus a sentence listing injection, unsafe deserialization, path traversal, weak crypto, hardcoded secrets, XSS and SSRF); *role* (security-engineer persona).
- **Models (Ollama, local, RTX 4050 Laptop 6 GB):**
  - qwen2.5-coder:3b (Ollama ID f72c60cabf62)
  - qwythos-9b: Hugging Face `llmfan46/Qwythos-9B-Claude-Mythos-5-1M-uncensored-heretic-GGUF`, Q4_K_M, thinking disabled, about 64% GPU / 36% CPU offload
- **Generation settings:** temperature 0.7, seeds 0–4, num_ctx 4096, num_predict 1500. The largest fenced Python block in each reply was kept; a reply with no closed code fence gives an empty file. The extraction script has a bug: when a reply starts with another kind of block (such as bash), it can keep the text between two blocks instead of the Python code. This caused 3 of the 4 qwen parse errors (t04 seed 3, t06 seed 2, t10 seed 4, all baseline).
- **Sample sizes:** 10 tasks × 3 conditions × 5 seeds = 150 per model. qwythos was generated in two runs (t01–t04 partial on 2026-10-29, the rest on 2026-11-16) with identical settings and a resume-safe script.
- **Scanning:** Bandit 1.9.4 (all findings in a file; per-rule numbers count files) and Semgrep 1.182.1 with p/python (unique rule ids per file). In the second run Windows Application Control blocked `semgrep.exe`, so the script used `python -m semgrep`. That command exits with an error without scanning, the script did not check for it, and it reused the result file from the first run. So the Semgrep column in `results_qwythos-9b.csv` is wrong for 40 of the 115 usable files. On 2026-11-25 all 300 files were rescanned with the same Semgrep version (`data/semgrep_rescan.csv`, with the rule ids for each file). The old column is left as it was. The rescan gives the same Semgrep count as the CSV for all 146 usable qwen files, and a Bandit rerun matches the CSV for all 261 usable files.
- **Statistics:** two-sided permutation test on per-file means, 20,000 permutations; Fisher's exact test where I compare how many files contain one rule. Files are not independent (same task, similar seeds) and there is no multiple-comparison correction, so p-values are indicative only. For qwythos, the main comparison uses only tasks with usable samples in all three conditions ("task-matched", 8 tasks).
- **Manual review:** 30 files, sampled by a rule fixed before reading: qwen seed 0, baseline + secure, all 10 tasks (20 files); qwythos seed 0, t01–t03 × 3 conditions + t04 baseline (10 files, drawn from the first run). The next seed was used where seed 0 had failed. Code was read but not executed. Severity was assigned by an LLM assistant and checked and accepted by me, and I lowered two labels from High to Medium. "High" = directly exploitable: auth bypass or account takeover, access to other users' data, arbitrary file write, SSRF, secret disclosure, or a hardcoded signing key.

## 4. Results

### 4.1 Answers that failed or got cut off

| model | condition | usable | empty (cut off) | parse error |
|---|---|---|---|---|
| qwen 3b | baseline | 46 | 0 | 4 |
| | secure | 50 | 0 | 0 |
| | role | 50 | 0 | 0 |
| qwythos 9b | baseline | 46 | 3 | 1 |
| | secure | **27** | **22** | 1 |
| | role | 42 | 7 | 1 |

- Every empty qwythos file is an output that stopped before the code block closed. For the 22 of 32 where token counts were logged, all hit the 1,500-token limit.
- Three of the four qwen parse errors come from my extraction script, not from the model (Section 3).
- **The security instruction lengthens qwythos output.** In the second run (t05–t10, plus four t04 role files, where token counts were logged), median output was 736 tokens for baseline, 1,386 for secure and 872 for role. The secure prompt asks for more protections, and the model writes more code to provide them.
- **Dropout is not random.** No secure sample survived for t04 (profile/IDOR) or t09 (password reset), and only 2 of 5 for t05 (JWT) and t06 (comments). The surviving secure files are therefore biased towards the simpler tasks.

### 4.2 Did the scanners see a difference? (RQ1)

| model, scope | metric | baseline | secure | role |
|---|---|---|---|---|
| qwen 3b, 10 tasks (n 46/50/50) | Bandit | 1.93 | 1.96 (p .93) | 1.74 (p .43) |
| | Semgrep | 0.93 | 0.94 (p 1.0) | 0.92 (p 1.0) |
| qwythos 9b, 8 matched tasks (n 37/27/36) | Bandit | 1.43 | 1.37 (p .90) | 1.78 (p .28) |
| | Semgrep (rescan) | 0.95 | 0.96 (p 1.0) | 0.89 (p .77) |

- Neither model shows a prompt effect on total scanner counts. That is a "can't tell", not proof that there is no effect.
- **The result depends on the task.** In t01–t03 (n 15/12/13) the secure condition looks worse: Bandit 1.13 vs 1.67 (p = .03), Semgrep 1.07 vs 1.50 (p = .02). In the other five matched tasks (n 22/15/23) it goes the other way: Bandit 1.64 vs 1.13 (p = .29), Semgrep 0.86 vs 0.53 (p = .36). Put together, they cancel out. The t01–t03 files are the same ones as in my earlier 56-sample run, so the full run does not test that result again, it only adds more tasks. I split the tasks this way after seeing the data, with no correction for multiple tests.
- **One rule looks significant but is confounded.** Bandit B105 (hardcoded password string) falls from 0.28 per file (baseline) to 0.04 (secure), p = .01, over all usable files. Ten of the 13 baseline B105 hits are in t04, t05 and t09, which together have only 2 usable secure files after truncation, so this drop cannot be credited to the prompt.

### 4.3 What the scanners actually catch (RQ2)

- **qwen:** Flask `debug=True` (B201) appears in 88 of 146 files and makes up about 32% of all Bandit findings.
- **qwythos:** the clearest change is in the server start line. Binding to 0.0.0.0 (B104) is in 11/46 baseline files, 17/27 secure and 19/42 role; on the matched tasks it is 6/37, 17/27 (p < .001) and 16/36 (p = .01). Semgrep `avoid_app_run_with_bad_host` (matched tasks) goes from 1/37 to 10/27 secure and 9/36 role. `debug=True` (B201) is in 27/46, 12/27 and 24/42; the drop under the secure prompt is in the direction 2407.07064 reports but is not significant (p = .33). These rule comparisons are post hoc.
- **Split metric:** separating deployment rules (B201 + B104) from all other Bandit rules, qwythos secure scores higher on deployment rules (0.83 vs 1.07 per file, p = .047) and lower on the rest (0.63 vs 0.30, p = .08); role differs from baseline on neither (p = .12, .82). For qwen no split difference was significant. The split was defined after seeing the data, so it is post hoc, and the "other" drop shares the truncation confound above.
- **Semgrep p/python** mostly overlaps with Bandit here: debug mode and bad host are 89 of its 136 hits on qwen files and 85 of 102 on qwythos files. What it adds is mainly SSRF, which Bandit did not flag: `ssrf-requests` fired on 14 of the 15 qwen t07 files and on 2 qwythos t07 files. It also flags hardcoded JWT keys (17 qwen files, 6 qwythos files).
- **False positives:** B608 (SQL built from strings) fired twice in the manual sample, both times on safe queries.

### 4.4 Reading the code by hand (RQ3)

| | qwen baseline | qwen secure | qwythos (10 files, mixed conditions) |
|---|---|---|---|
| files with a High flaw | 6/10 | 5/10 | 1/10 |
| High flaws missed by both scanners | 4 of 6 | 2 of 5 | 1 of 1 |

- **Missed High flaws:** path traversal on upload (qwen t03, baseline); IDOR (qwen t04, baseline); SSRF (qwen t07, secure, even though the secure prompt names SSRF); reset token returned to the requester (qwen t09, both conditions); config endpoint leaking secrets (qwen t10, baseline; Semgrep flagged the open CORS setting in that file, not the leak); an authentication decorator that accepts any bearer token, alongside unsalted SHA-256 passwords (qwythos t01, role).
- **Caught High flaws:** four hardcoded keys (Bandit B105; Semgrep also flagged the two JWT ones) and the SSRF in qwen t07 baseline (Semgrep `ssrf-requests`). The t07 secure file has the same SSRF but passes the URL through a helper function first, which is probably why the rule did not match.
- **What the secure prompt fixed:** the qwen t03, t04 and t10 flaws, in the one seed that was reviewed.
- **What it did not fix or introduced:** SSRF and reset-token disclosure stayed; hardcoded secrets stayed, including one file whose comment says "Never hardcode secrets"; two secure files introduced a High flaw absent from their baseline: a hardcoded SECRET_KEY in t06, and in t01 a hardcoded session key where the baseline had only a placeholder token (Medium).
- **Code that would not run:** many files have missing imports or call APIs incorrectly. Security and functionality are not separated in this design.

## 5. Discussion

- **Scanner-count nulls are weak evidence.** The scanners mostly see deployment configuration and hardcoded strings. Semgrep also sees simple SSRF, but not the access-control and design flaws these tasks are meant to elicit. A security prompt can change the code where it matters (qwen t03, t04, t10) without changing the count, and can shift the count by changing a configuration line (qwythos).
- **Prompt effects depend on the tasks.** The qwythos "secure is worse" result (p = .03 on t01–t03) is still there in the full data, but the other tasks go the other way and the total is flat. With dependent samples and no correction, single significant p-values at this scale should not be reported as findings.
- **Output-length limits interact with the prompt.** A token cap that is generous for baseline outputs truncates nearly half of secure outputs for a verbose model, and does so selectively on the hardest tasks. Studies that drop failed generations without reporting them by condition can end up comparing different task mixes.
- **This may help reconcile the literature.** Studies reporting large prompt gains used expert review [2607.23088] or tests [2605.08382], and tailored or optimised prompts. Studies reporting nulls relied on scanner counts [2605.24298] and generic cues. My design used a generic cue and scanner counts and also got a null on total counts, while manual review showed some fixes and some new flaws. I cannot separate the two explanations (how security is measured vs how specific the prompt is) with this data.
- **`debug=True` + `0.0.0.0` is not pure noise.** Together they expose the Werkzeug debugger on the network. Reporting should keep deployment configuration as its own category rather than drop it.
- **Practical note for local-model users:** a generic security sentence does not reliably fix SSRF or token-handling flaws in 3–9B models, and may make a model write code too long for its output budget.

## 6. Threats to validity

- **Sample size and dependence:** 5 seeds per cell; files from the same task are not independent; post hoc metric split; no correction for multiple tests.
- **Truncation:** 22 of 50 qwythos secure outputs were lost to the 1,500-token cap; secure results for qwythos come from a biased subset of tasks. A rerun of those 32 outputs with a larger cap was considered and not done.
- **Manual review:** one reviewer (an LLM assistant, labels checked by me); no second reviewer, so no agreement figure; code not executed; severity scale defined by me; 30 of 300 files reviewed, and the qwythos part covers only t01–t04.
- **Extraction:** at least 3 qwen baseline files were lost to a bug in my extraction script, not to the model.
- **Generation settings:** one prompt wording per condition; one decoding setting; qwythos generated in two sessions (same settings and model file).
- **Models:** qwythos-9b is an uncensored community fine-tune with undocumented training data; it does not represent mainstream 9B models.
- **Scanners:** the Semgrep failure in the second run was found only on 2026-11-25; p/python is downloaded at scan time, so its rules could differ between scans, although the qwen counts did not change. Only Bandit and Semgrep p/python; no CodeQL; no exploit or functional tests.
- **Literature:** a limited search; some details come from abstracts and tool summaries.

## 7. Conclusion

### What I found

For two small local models writing Flask/FastAPI code, the total scanner counts from Bandit and Semgrep showed no clear effect of a generic security prompt or a security persona. For qwythos the security prompt gave more warnings on the first three tasks and fewer on the rest, and it made the server listen on all addresses more often. What the scanners mostly count is one deployment line (`debug=True` and which address the server listens on) plus hardcoded strings.

Reading the code by hand showed more. 12 of the 30 files had a serious bug and both scanners missed 7 of them: IDOR, reset tokens handed out (two files), path traversal on upload, authentication bypass, leaked settings and one SSRF. They caught four hardcoded keys and the other SSRF. The security prompt fixed some bugs and added others (qwen files with a High-severity flaw went from 6 of 10 to 5 of 10, with three flaws fixed and two new hardcoded keys added), and it left SSRF in place even though the prompt names SSRF directly.

So my answer to the title question is: I can't say that it does. A "write secure code" line fixed some things and broke others in the files I checked, the sample is too small to call it an improvement, and the total number of scanner warnings doesn't tell you either way.

### What this means if you use local models

- Read the access-control logic yourself: who is logged in, whether they own the thing they are asking for, and what a reset or token endpoint gives back. That is where most of the missed bugs were.
- Treat a clean Bandit or Semgrep run as "no obvious bad lines", not as "secure".
- A security prompt can make the model write much longer answers. Raise the output limit (or check for cut-off code) when you use one.
- A general "write secure code" line is weak. Naming the exact risk for that task is more likely to help, although this study did not test that.

### For researchers

Security-prompting studies on web code should use task-specific checks (exploit tests or targeted manual review) as the main outcome, report scanner counts by rule category, and report failed or cut-off generations for each condition.

### What I would do next

- Rerun the 32 cut-off qwythos answers with a larger output limit, so the secure condition covers all tasks.
- Write small exploit tests for each task (for example, user A asks for user B's profile) and actually run the code, instead of only reading it.
- Add CodeQL as a third scanner.
- Get a second person to review the same 30 files, so the labels can be checked for agreement.
- Compare a generic security prompt with a task-specific one ("check that the user owns this record").

## Appendix: reproducing

```
python scripts/generate.py qwythos-9b 5      # skips files that already exist
python scripts/scan.py qwythos-9b
python scripts/analyze.py qwythos-9b
python scripts/analyze_matched.py qwythos-9b
python scripts/analyze_split.py results_qwythos-9b
```
The 56-sample partial results are kept in `data/results_qwythos-9b_partial56.csv`.

Two known problems with these scripts: `scan.py` calls `python -m semgrep`, which does not scan with this version (use `semgrep` directly and check that it ran), and `analyze_matched.py` prints its results and then stops with an error if `data/_semgrep_tmp.json` is missing.

## Corrections

Changed in v3 (2026-11-25), after v2 was rechecked against the raw files with help from an AI assistant:

- The qwythos Semgrep numbers were wrong because Semgrep had not run on the second batch. Rescanned and replaced.
- v2 said both scanners missed SSRF in both qwen t07 files. Semgrep had caught it in the baseline one, so qwen baseline is 4 of 6 missed, not 5 of 6.
- v2 said the early qwythos result did not replicate. It is still there in the same files and the other tasks cancel it out.
- v2 said the prompt made no difference at all for the scanners. Only the totals are flat.
- v2 said the secure prompt turned debug mode off in qwythos. The drop is not significant.
- The old title said scanners undercount the effect of security prompts, which this data is too small to show.
- Three of the qwen parse errors came from my script, the Bandit averages use all findings and not unique rule ids, and the tasks and prompts were drafted with AI help.
