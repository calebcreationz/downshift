# Downshift

A cost audit for agent decisions on SERV Reasoning. Built for SERV Hackathon 02, Open track.

Results page: https://calebcreationz.github.io/downshift/

## What it does

Given a decision task whose correct answers can be computed by code, Downshift sends the same cases to several models through SERV Reasoning, scores every answer against the code-computed truth, and reports accuracy and cost per decision. The goal is to find the cheapest model that still decides correctly. It then checks its own cost estimate against the console bill.

All decisions go through `https://inference-api.openserv.ai/v1/chat/completions` at low reasoning effort, using `gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-6-luna` and `gemini-3.8-flash`.

## First results

The task is an invented expense-claim policy: claims with line items, EUR conversion, per-person meal caps, duplicates, planted "ignore the rules" notes and exact-boundary totals. Answers come from a reference implementation in the harness, so nothing was labelled by hand.

Policy A, 60 claims, 9 rules:

- GPT-5.4 Mini: 60/60, about $0.068
- Gemini 3.8 Flash: 60/60, about $0.038
- GPT-5.4 Nano: 54/60, about $0.021
- GPT-6-Luna: 60/60, about $0.0067

Policy B, 40 claims, 9 rules including "personal card and over $300", with the format fix below:

- Gemini 3.8 Flash: 40/40, about $0.025
- GPT-5.4 Mini: 37/40, about $0.049
- GPT-5.4 Nano: 35/40, about $0.015
- GPT-6-Luna: 34/40, about $0.0055 (the same 34 in two runs)

A 17-rule policy on 40 other claims gave 40/40 for all four models; Luna cost about $0.0064 and Mini about $0.058.

On Policy A, Luna matched Mini at roughly a tenth of the cost. On Policy B the best buy was Gemini 3.8 Flash: more accurate than Mini at about half the cost. The cheapest model that is good enough depends on the policy.

## Findings

**Short policies broke the answer format, and one line fixed it.** In the first sweep, models often decided correctly but not in the one word asked for ("APPROVED", "DECISION...", JSON). Strict parsing gave Nano 4/40 and Luna 20/40 at 9 rules. Adding one line ("Reply with only the verdict word... no JSON") took bad-format replies to zero in all seven runs with the line, across four models. Nano went from 4/40 to 35/40 at 9 rules and from 21/40 to 40/40 at 5 rules. A retry for bad format was built in and never triggered.

**What was left was half a rule.** Luna's six misses on Policy B were real. Five were claims paid by company card with a total over $300; the policy escalates only if the card is personal and the total is over $300, and Luna escalated anyway. The sixth was a total of exactly $1,000.00 against "over $1,000". Mini over-escalated three times on the same set; Gemini never did. Each of Luna's six was checked against the rule by hand and the reference was right.

**The raw switch does not switch.** The docs describe the header `x-openserv-disable-braid: true` as turning SERV off. On chat completions with `gpt-5.4-nano` it changed nothing: four variants (no header and three spellings) all reported 197 input tokens for the same one-line request. In the Playground, raw mode used 172 input tokens against 385 with SERV on the same prompt. So these results compare models with each other, not raw against SERV. This was reported to the OpenServ team.

**The cost estimate was wrong once, and the bill caught it.** Estimates come from reported token counts and listed prices. For Gemini 3.8 Flash the harness first used another Gemini model's price, so it estimated about $0.07 where the console billed $0.44. For Mini, Nano and Luna the estimates were 5 to 30 percent under the billed totals ($0.28, $0.16, $0.06, which include playground tests and retries). The scripts now use Gemini's listed price. The bill is the source of truth.

## Limits

- Two invented policies, 40 to 100 claims per run. Luna's Policy B score repeated exactly, but Mini's and Gemini's are single runs, so small gaps are hints, not proof.
- The policies are simpler than real company rules.
- No raw baseline, so nothing here shows what SERV adds over a direct model call.
- The 17-rule set had only 4 APPROVE cases out of 40, so over-escalation would barely show there. Mini was not run on the 5- and 13-rule sets, and Gemini's cost at 17 rules is not shown.

## Run it yourself

You need a SERV API key and a few tenths of a dollar of credit. Open a new Google Colab notebook, paste a script into a cell, run it, and paste your key when asked. Do not put the key in a script.

- `harness_60cases.py`: Policy A, 60 claims, seed 7 (SERV rows only; the original run also tried Google's free tier directly, which failed on quota)
- `harness_sweep.py`: policy-size sweep at 5, 9, 13 and 17 rules, 40 claims, seed 11
- `harness_format_fix.py`: the format fix, the Policy B comparison and Luna's wrong answers (loads `harness_sweep.py` from this repo; about $0.15)

Cost per decision comes from the `usage` token counts times the listed price. Compare the total with the console Usage page before trusting it.

## Files

- `index.html`: results page with a monthly-cost calculator
- `README.md`: this file
- `harness_60cases.py`, `harness_sweep.py`, `harness_format_fix.py`: the test harness
