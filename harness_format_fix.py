# Downshift: the format-fix test and the 9-rule comparison (Policy B).
# It loads harness_sweep.py from this repo (which defines the helpers and asks for your OpenServ
# key, without running the sweep), then runs three short checks, all with low reasoning effort:
#   1) Nano and Luna at 5 and 9 rules with one added line ("reply with only the verdict word"),
#      plus one retry if a reply is still not a verdict word.
#   2) Mini, Gemini 3.8 Flash and Luna at 9 rules with the same line, counting over-escalations.
#   3) Luna's wrong answers at 9 rules, next to the rule the reference says applied.
# Run it in a Google Colab cell. Cost: about $0.15. Compare the total with the console Usage page.
import requests, time
SRC = requests.get("https://raw.githubusercontent.com/calebcreationz/downshift/main/harness_sweep.py", timeout=60).text
assert "def main()" in SRC, "could not load the harness from GitHub"
exec(SRC.rsplit("\nmain()", 1)[0])

FIX = "\nReply with only the verdict word: APPROVE, ESCALATE or REJECT. No other text, no punctuation, no JSON."
FIX2 = "\nYour last reply was not a single verdict word. Reply again with exactly one of: APPROVE, ESCALATE, REJECT."
BEFORE = {("nano", 5): 21, ("nano", 9): 4, ("luna", 5): 40, ("luna", 9): 20}   # strict scores from harness_sweep.py
cases = make_cases(N_CASES)
total = 0.0

print("1) format fix, Nano and Luna")
for name, model, price in MODELS[:2]:
    for k in (5, 9):
        system = policy(k) + FIX
        def one(i, c):
            text = render(i + 1, c)
            r1 = call(model, system, text)
            w1 = first_word(r1["text"])
            r2 = call(model, system + FIX2, text) if w1 not in VALID else None
            w2 = first_word(r2["text"]) if r2 else w1
            cost = sum((r["pin"] * price[0] + r["pout"] * price[1]) / 1e6 for r in (r1, r2) if r)
            return w1, w2, truth(c, k), cost
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            res = list(ex.map(lambda ic: one(ic[0], ic[1]), enumerate(cases)))
        bad1 = sum(1 for w1, w2, e, cost in res if w1 not in VALID)
        bad2 = sum(1 for w1, w2, e, cost in res if w2 not in VALID)
        ok1 = sum(1 for w1, w2, e, cost in res if w1 == e)
        ok2 = sum(1 for w1, w2, e, cost in res if w2 == e)
        spent = sum(cost for w1, w2, e, cost in res)
        total += spent
        print(f"{name} k{k}: before {BEFORE[(name, k)]}/40 | stricter line {ok1}/40, bad format {bad1} | plus one retry {ok2}/40, bad format {bad2} | est ${spent:.4f}")

print("\n2) 9-rule comparison with the format line")
system9 = policy(9) + FIX
for name, model, price in [MODELS[3], MODELS[2], MODELS[1]]:   # mini, gem, then luna again
    texts = [render(i + 1, c) for i, c in enumerate(cases)]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        outs = list(ex.map(lambda t: call(model, system9, t), texts))
    right = over = other = bad = 0
    spent = 0.0
    for c, o in zip(cases, outs):
        w, e = first_word(o["text"]), truth(c, 9)
        spent += (o["pin"] * price[0] + o["pout"] * price[1]) / 1e6
        if w == e: right += 1
        elif w not in VALID: bad += 1
        elif e == "APPROVE" and w == "ESCALATE": over += 1
        else: other += 1
    total += spent
    print(f"{name} k9: {right}/40 right | over-escalated {over} | other wrong {other} | bad format {bad} | est ${spent:.4f}")

print("\n3) Luna's wrong answers at 9 rules")
shown = 0
for i, c in enumerate(cases):
    r = call(MODELS[1][1], system9, render(i + 1, c))
    w, e = first_word(r["text"]), truth(c, 9)
    if w != e:
        t = usd(c)
        fired = next((j + 1 for j, (_, fn, v) in enumerate(RULES[:9]) if fn(c, t)), 10)
        print(f"expected {e} (rule {fired}), luna said {w}")
        print(render(i + 1, c))
        print()
        shown += 1
print("wrong:", shown, "of", len(cases))
print(f"Estimated spend for parts 1 and 2: ${total:.4f}")
