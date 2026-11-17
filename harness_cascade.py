# Downshift: does a stronger checker on the cheap model's escalations change who wins? (Policy B, 9 rules)
# Luna decides all 40 claims. Only the claims where Luna said ESCALATE are sent to a second model, which
# decides them again without seeing Luna's answer. Accuracy and total cost are compared with each model alone.
# It loads harness_sweep.py from this repo (defines the helpers and asks for your OpenServ key, without
# running the sweep). Run it in a Google Colab cell. Cost: about $0.05.
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

luna = MODELS[1]
lo = run_all(luna[1], texts)
lw = [first_word(o["text"]) for o in lo]
lcost = cost_of(lo, luna[2])
print(f"luna alone: {sum(w == e for w, e in zip(lw, want))}/40 | ${lcost:.4f}")
route = [i for i, w in enumerate(lw) if w == "ESCALATE"]
print("sent to the checker:", len(route), "of", len(cases))
for name, model, price in [MODELS[2], MODELS[3]]:   # gemini, then mini
    co = run_all(model, [texts[i] for i in route])
    ccost = cost_of(co, price)
    final = list(lw)
    for i, o in zip(route, co):
        final[i] = first_word(o["text"])
    right = sum(w == e for w, e in zip(final, want))
    print(f"luna + {name} checker: {right}/40 | ${lcost + ccost:.4f} (checker ${ccost:.4f})")
print("for reference, from earlier runs: gem alone 40/40 $0.0252, mini alone 37/40 $0.0487")
