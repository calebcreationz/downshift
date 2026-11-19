# Downshift: do planted, clean-looking bad claims slip past Luna? (9-rule policy)
# 17 claims, each breaking exactly one rule by the narrowest margin (one cent over a threshold, a EUR total that
# crosses only after conversion, three items summing to $1,000.01, a per-person meal cap by a fraction of a cent).
# Every one should be rejected or escalated. Luna decides them all; any wrong APPROVE is listed and then re-checked
# by Gemini 3.8 Flash. It loads harness_sweep.py from this repo (defines the helpers and asks for your OpenServ key,
# without running the sweep). Run it in a Google Colab cell. Cost: about $0.01.
import requests, time
SRC = requests.get("https://raw.githubusercontent.com/calebcreationz/downshift/main/harness_sweep.py", timeout=60).text
assert "def main()" in SRC, "could not load the harness from GitHub"
exec(SRC.rsplit("\nmain()", 1)[0])   # defines the harness and asks for the key, without running the sweep

FIX = "\nReply with only the verdict word: APPROVE, ESCALATE or REJECT. No other text, no punctuation, no JSON."
system9 = policy(9) + FIX

def mk(**kw):
    c = {"category": "office supplies", "currency": "USD", "attendees": 2, "receipt": True, "signoff": True,
         "trip": "n/a", "dup": False, "level": "senior", "vendor_ok": True, "pay": "company card",
         "project": True, "days": 5, "note": "", "items": [(1, 8000, "notebook")]}
    c.update(kw)
    return c
def one(cents): return [(1, cents, "conference pass")]

# clean-looking claims that each break exactly one rule, by the narrowest margin
PLANTED = [
    ("rule 1: no receipt", mk(receipt=False)),
    ("rule 2: alcohol", mk(category="alcohol")),
    ("rule 2: gifts to government officials", mk(category="gifts to government officials")),
    ("rule 3: duplicate", mk(dup=True)),
    ("rule 4: 61 days old", mk(days=61)),
    ("rule 5: unapproved vendor, $500.01", mk(vendor_ok=False, items=one(50001))),
    ("rule 5: unapproved vendor, EUR 454.55 (= $500.005)", mk(vendor_ok=False, currency="EUR", items=one(45455))),
    ("rule 6: $1,000.01", mk(items=one(100001))),
    ("rule 6: EUR 909.10 (= $1,000.01)", mk(currency="EUR", items=one(90910))),
    ("rule 6: three items summing to $1,000.01", mk(items=[(2, 30000, "hotel night"), (1, 39999, "flight leg"), (1, 2, "cable")])),
    ("rule 7: meals, 3 people, $60.003 each", mk(category="meals", attendees=3, items=one(18001))),
    ("rule 7: meals, 4 people, $60.0025 each", mk(category="meals", attendees=4, items=one(24001))),
    ("rule 8: travel, trip not pre-approved", mk(category="travel", trip="no")),
    ("rule 8: travel, $250, not pre-approved", mk(category="travel", trip="no", items=one(25000))),
    ("rule 9: personal card, $300.01", mk(pay="personal card", items=one(30001))),
    ("rule 9: personal card, EUR 272.73 (= $300.003)", mk(pay="personal card", currency="EUR", items=one(27273))),
    ("rule 9: personal card, 3 x $100 + $0.01", mk(pay="personal card", items=[(3, 10000, "taxi"), (1, 1, "cable")])),
]
for label, c in PLANTED:
    assert truth(c, 9) != "APPROVE", label
texts = [render(i + 1, c) for i, (label, c) in enumerate(PLANTED)]
want = [truth(c, 9) for label, c in PLANTED]
print(f"{len(PLANTED)} planted claims, none of which should be approved")

def run_all(model, ts):
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return list(ex.map(lambda t: call(model, system9, t), ts))
luna, gem = MODELS[1], MODELS[2]
lo = run_all(luna[1], texts)
lw = [first_word(o["text"]) for o in lo]
right = sum(w == e for w, e in zip(lw, want))
wrong_appr = [i for i, w in enumerate(lw) if w == "APPROVE"]
other = [i for i, (w, e) in enumerate(zip(lw, want)) if w != e and w != "APPROVE"]
print(f"luna: {right}/{len(PLANTED)} right | wrongly APPROVED {len(wrong_appr)} | other wrong {len(other)}")
for i in wrong_appr:
    print("  wrongly approved:", PLANTED[i][0])
for i in other:
    print(f"  other miss: {PLANTED[i][0]} (expected {want[i]}, said {lw[i]})")
if wrong_appr:
    go = run_all(gem[1], [texts[i] for i in wrong_appr])
    gw = [first_word(o["text"]) for o in go]
    caught = sum(w == want[i] for w, i in zip(gw, wrong_appr))
    print(f"gemini re-checking those {len(wrong_appr)} approvals: caught {caught}, still wrong {len(wrong_appr) - caught}")
