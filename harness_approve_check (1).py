# Downshift: would a second check on Luna's APPROVE answers be worth the extra cost? (Policy B, 9 rules)
# Luna decides all 40 claims. Gemini 3.8 Flash then re-decides (without seeing Luna's answer) the claims where
# Luna said APPROVE, ESCALATE, or both, and accuracy and total cost are compared. It loads harness_sweep.py
# from this repo (defines the helpers and asks for your OpenServ key, without running the sweep).
# Run it in a Google Colab cell. Cost: about $0.03.
import requests, time
SRC = requests.get("https://raw.githubusercontent.com/calebcreationz/downshift/main/harness_sweep.py", timeout=60).text
assert "def main()" in SRC, "could not load the harness from GitHub"
exec(SRC.rsplit("\nmain()", 1)[0])   # defines the harness and asks for the key, without running the sweep

FIX = "\nReply with only the verdict word: APPROVE, ESCALATE or REJECT. No other text, no punctuation, no JSON."
system9 = policy(9) + FIX
cases = make_cases(N_CASES)
texts = [render(i + 1, c) for i, c in enumerate(cases)]
want = [truth(c, 9) for c in cases]

def run_all(model, ts):
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return list(ex.map(lambda t: call(model, system9, t), ts))
def cost_of(outs, price):
    return sum((o["pin"] * price[0] + o["pout"] * price[1]) / 1e6 for o in outs)

luna, gem = MODELS[1], MODELS[2]
lo = run_all(luna[1], texts)
lw = [first_word(o["text"]) for o in lo]
lcost = cost_of(lo, luna[2])
ap = [i for i, w in enumerate(lw) if w == "APPROVE"]
es = [i for i, w in enumerate(lw) if w == "ESCALATE"]
print(f"luna said APPROVE {len(ap)}, ESCALATE {len(es)}, other {len(lw) - len(ap) - len(es)}")
idx = ap + es
go = run_all(gem[1], [texts[i] for i in idx])
gw = {i: first_word(o["text"]) for i, o in zip(idx, go)}
gc = {i: cost_of([o], gem[2]) for i, o in zip(idx, go)}

def report(label, route):
    f = list(lw)
    for i in route: f[i] = gw[i]
    right = sum(w == e for w, e in zip(f, want))
    cost = lcost + sum(gc[i] for i in route)
    print(f"{label}: {right}/40 | ${cost:.4f} | {len(route)} of 40 re-checked")
report("luna alone", [])
report("gemini checks ESCALATE only", es)
report("gemini checks APPROVE only", ap)
report("gemini checks APPROVE + ESCALATE", ap + es)
print("gemini disagreed with luna on", sum(gw[i] != lw[i] for i in ap), "of", len(ap), "APPROVEs")
print("for reference, from earlier runs: gem alone 40/40 $0.0252")
