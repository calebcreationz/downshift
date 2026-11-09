# Downshift

A cost audit for agent decisions on SERV Reasoning. Built for SERV Hackathon 02, Open track.

Results page: https://calebcreationz.github.io/downshift/

## What it does

Given a decision task whose correct answers can be computed by code, Downshift sends the same cases to several models through SERV Reasoning, scores every answer against the code-computed truth, and reports accuracy and cost per decision. The goal is to find the cheapest model that still decides correctly. It then checks its own cost estimate against the console bill.

All decisions go through `https://inference-api.openserv.ai/v1/chat/completions` at low reasoning effort, using `gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-6-luna` and `gemini-3.8-flash`.

## First results

The task is an invented expense-claim policy: claims with line items, EUR conversion, per-person meal caps, duplicates, planted "ignore the rules" notes and exact-boundary totals. Answers come from a reference implementation in the harness, so nothing was labelled by hand.

60 claims, 9-rule policy:

- GPT-5.4 Mini: 60/60, about $0.068
- Gemini 3.8 Flash: 60/60, about $0.038 (recomputed at its listed price)
- GPT-5.4 Nano: 54/60, about $0.021
- GPT-6-Luna: 60/60, about $0.0067

40 claims, 17-rule policy: all four models scored 40/40. Luna cost about $0.0064 and Mini about $0.058.

On both sets Luna matched Mini at roughly a tenth of the cost.

## Findings

**The raw switch does not switch.** The docs describe the header `x-openserv-disable-braid: true` as turning SERV off. On chat completions with `gpt-5.4-nano` it changed nothing: four variants (no header and three spellings) all reported 197 input tokens for the same one-line request. In the Playground, raw mode used 172 input tokens against 385 with SERV on the same prompt. So these results compare models with each other, not raw against SERV. This was reported to the OpenServ team.

**Short policies broke the answer format, not the reasoning.** In the sweep at 9 rules, models often answered correctly in the wrong form ("APPROVED", "DECISION...", JSON). Luna scored 20/40 on strict parsing, but 14 of the misses were "APPROVED" or "REJECTED" and only 6 were wrong decisions. Gemini 3.8 Flash scored 10/40 with 30 replies that did not start with a verdict word. At 17 rules every model answered in the right format. A stricter instruction line was not tested because credits ran out. A gate built on a model needs a format check and a retry.

**The cost estimate was wrong once, and the bill caught it.** Estimates come from reported token counts and listed prices. For Gemini 3.8 Flash the harness used another Gemini model's price, so it estimated about $0.07 where the console billed $0.44. For Mini, Nano and Luna the estimates were 5 to 30 percent under the billed totals ($0.28, $0.16, $0.06, which include playground tests and retries). The bill is the source of truth.

## Limits

- One invented task, 40 to 100 claims per run, one run per setup. Small gaps are hints, not proof.
- No raw baseline, so nothing here shows what SERV adds over a direct model call.
- The policy is simpler than real company rules.
- Gemini's cost at 17 rules is not shown because token counts were not saved.

## Run it yourself

You need a SERV API key and about $0.20 of credit. Open a new Google Colab notebook, paste a script into a cell, run it, and paste your key when asked. Do not put the key in the script.

- `harness_sweep.py`: policy-size sweep (5, 9, 13 and 17 rules, 40 claims, seed 11)
- `harness_60cases.py`: the 60-claim, 9-rule run (seed 7)

Cost per decision for each model comes from `usage` token counts times the listed price. Compare the total with the console Usage page before trusting it.

## Files

- `index.html`: results page with a monthly-cost calculator
- `README.md`: this file
- `harness_sweep.py`, `harness_60cases.py`: the test harness
