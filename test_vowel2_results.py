# SPDX-License-Identifier: Apache-2.0
# test_vowel2_results.py: grader and renderer for the pre-registered test VOWEL2-PREREG.md
# (sperm whale "long and short vowels" within bouts), published together with the registration
# and BEFORE job vowel2-test-v1 has produced any result. With its own code (stdlib only; it does
# not import vowel2_test.py) it re-derives from the raw output results/vowel2/vowel2_results.json
# the level tested, the reproduction flag, the size, power and false-alarm rates from the stored
# calibration p values, the verdict (VOWEL2-PREREG.md section 6, in order), predictions P1-P8
# and the Brier score; it checks that every p value lies on its permutation lattice and that the
# settings equal the registration; and it writes RESULTS-DUR.md:
#   python test_vowel2_results.py --render <vowel2_results.json> <RESULTS-DUR.md>
# Until the result exists the result tests are skipped; the toy tests always run.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "vowel2", "vowel2_results.json")
MD = os.path.join(HERE, "RESULTS-DUR.md")
HAVE = os.path.exists(RES)

VERSION = "whale-vowel2-test-1"
MD5 = {"codamd.csv": "be50098e0e806d6df7cd2144b80d900d",
       "DominicaCodas.csv": "46c2ff249bc6fa327d5bbe596f06be63",
       "sperm-whale-dialogues.csv": "eeeeb20cda64d88320b6ccee1185379a"}
FOUR = ("ATWOOD", "FORK", "PINCHY", "TBB")
SETTINGS = {"four": list(FOUR), "coda_type": "1+1+3", "b_main": 9999, "b_rot": 9999,
            "r_cal": 200, "b_cal": 999, "eps_sim": 0.05, "alpha": 0.05, "size_max": 0.1,
            "power_min": 0.8, "min_groups": 5, "min_minority": 15, "shrink": 0.5,
            "q_strong": 0.5,
            "seeds": {"naive_pub": 20261211, "naive_timed": 20261212, "dep": 20261213,
                      "bout": 20261214, "rot": 20261215, "size": 20261216, "power": 20261217,
                      "false_alarm": 20261218, "mode": 20261219, "mode_dep": 20261220}}
B_MAIN, B_ROT, R_CAL, B_CAL = 9999, 9999, 200, 999
ALPHA, SIZE_MAX, POWER_MIN = 0.05, 0.10, 0.80
MIN_GROUPS, MIN_MINORITY, SHRINK, Q_STRONG = 5, 15, 0.5, 0.5
TESTS = (("naive_pub", "published-style: within whale, all codas of the published subset"),
         ("naive_timed", "within whale, timed codas only"),
         ("within_dep", "within tag deployment"),
         ("within_bout", "within bout"))
LEVEL_KEY = {"bout": "within_bout", "deployment": "within_dep"}
LEVEL_NAME = {"bout": "BOUTS", "deployment": "DEPLOYMENTS"}
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
PRIORS = {"P1": 0.80, "P2": 0.35, "P3": 0.50, "P4": 0.90, "P5": 0.75, "P6": 0.60, "P7": 0.55,
          "P8": 0.60}
PRED_TEXT = {
    "P1": "published-style contrast reproduced: a longer than i, p_high <= 0.05",
    "P2": "a longer than i within the level tested, p_high <= 0.05",
    "P3": "power at the published-style effect size >= 0.80",
    "P4": "rotation-world size <= 0.10",
    "P5": "published-style false-alarm rate in bout-clustered worlds > 0.10",
    "P6": "within-level contrast below half the within-whale contrast on the same codas",
    "P7": "i-vowel short/long modes persist within bouts (p_low <= 0.05 and Q <= 0.5)",
    "P8": "i-vowel short/long mix differs between deployments of a whale, p <= 0.05"}
DM, INS, INC = "DATA_MISMATCH", "INSUFFICIENT_DATA", "INCOMPLETE"


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def finite(x):
    return is_num(x) and x == x and abs(x) != float("inf")


def p_ok(p, b):
    if not finite(p):
        return False
    k = p * (b + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= b


def le(p):
    return finite(p) and p <= ALPHA


def rate(ps):
    return sum(1 for p in ps if le(p)) / len(ps) if ps else float("nan")


def fmt(x, spec):
    return format(x, spec) if finite(x) else "n/a"


# --------------------------------------------------------------------------- regrade
def level_of(t):
    for lv in ("bout", "deployment"):
        x = t[LEVEL_KEY[lv]]
        if x["groups"] >= MIN_GROUPS and x["minority"] >= MIN_MINORITY:
            return lv
    return None


def verdict_of(level, reproduced, size, p_high, p_lo, power1):
    if level is None:
        return INS
    if not reproduced:
        return "NOT_REPRODUCED"
    sfx = "_WITHIN_" + LEVEL_NAME[level]
    if not finite(size) or size > SIZE_MAX:
        return "CALIBRATION_FAILED" + sfx
    if le(p_high):
        return "DURATION_DIFFERENCE" + sfx
    if le(p_lo):
        return "REVERSED" + sfx
    if finite(power1) and power1 >= POWER_MIN:
        return "NO_DIFFERENCE_WITH_POWER" + sfx
    return "UNDERPOWERED" + sfx


def files_gate(r):
    f = r.get("files")
    if not isinstance(f, dict) or sorted(f) != sorted(MD5):
        return INC
    if not all(isinstance(f[k], dict) and f[k].get("md5_ok") is True for k in f):
        return DM
    return None


def regrade(r):
    out = {"verdict": files_gate(r), "level": None, "reproduced": None, "size": None,
           "power": {}, "f_naive": None, "f_naive_two": None, "f_bout": None,
           "predictions": None, "brier": None, "n_true": None}
    if out["verdict"]:
        return out
    t = r.get("tests")
    if not (isinstance(t, dict) and all(isinstance(t.get(k), dict) for k, _ in TESTS)
            and isinstance(r.get("modes"), dict)):
        out["verdict"] = INC
        return out
    lv = level_of(t)
    tl = t[LEVEL_KEY[lv]] if lv else None
    cal = r.get("calibration") or {}
    size = rate(cal["size"]["p"]) if cal.get("size") else float("nan")
    power = {k: rate(v["p"]) for k, v in (cal.get("power") or {}).items()}
    fa = cal.get("false_alarm")
    f_naive = rate(fa["naive_p_high"]) if fa else float("nan")
    f_two = (sum(1 for a, b in zip(fa["naive_p_high"], fa["naive_p_low"])
                 if min(a, b) <= ALPHA / 2) / len(fa["naive_p_high"])) if fa else float("nan")
    f_bout = rate(fa["bout_p_high"]) if fa else float("nan")
    np_ = t["naive_pub"]
    rep = finite(np_.get("d")) and np_["d"] > 0 and le(np_["p_high"])
    dnt = t["naive_timed"].get("d")
    per, dep = r["modes"]["persistence"], r["modes"]["deployment"]
    pred = {"P1": rep,
            "P2": tl is not None and le(tl["p_high"]),
            "P3": finite(power.get("1.0")) and power["1.0"] >= POWER_MIN,
            "P4": finite(size) and size <= SIZE_MAX,
            "P5": finite(f_naive) and f_naive > SIZE_MAX,
            "P6": (tl is not None and finite(tl.get("d")) and finite(dnt) and dnt > 0
                   and tl["d"] < SHRINK * dnt),
            "P7": le(per.get("p_low")) and finite(per.get("q")) and per["q"] <= Q_STRONG,
            "P8": le(dep.get("p"))}
    pred = {k: bool(pred[k]) for k in ORDER}
    brier = sum((PRIORS[k] - (1.0 if pred[k] else 0.0)) ** 2 for k in ORDER) / len(ORDER)
    v = verdict_of(lv, rep, size, tl["p_high"] if tl else 1.0, tl["p_low"] if tl else 1.0,
                   power.get("1.0", float("nan")))
    out.update(verdict=v, level=lv, reproduced=rep, size=size, power=power, f_naive=f_naive,
               f_naive_two=f_two, f_bout=f_bout, predictions=pred, brier=brier,
               n_true=sum(1 for k in ORDER if pred[k]))
    return out


# --------------------------------------------------------------------------- consistency
def check_test(name, x):
    bad = []
    if x.get("B") != B_MAIN:
        bad.append(name + ": B")
    if x.get("d") is None:
        if not (x.get("groups") == 0 and x.get("p_high") == 1.0 and x.get("p_low") == 1.0):
            bad.append(name + ": empty test")
        return bad
    if not (p_ok(x.get("p_high"), B_MAIN) and p_ok(x.get("p_low"), B_MAIN)):
        bad.append(name + ": p lattice")
    elif x["p_high"] + x["p_low"] < 1.0 + 1.0 / (B_MAIN + 1) - 1e-9:
        bad.append(name + ": p_high + p_low")
    if not (isinstance(x.get("groups"), int) and x["groups"] >= 1
            and isinstance(x.get("minority"), int) and x["minority"] >= x["groups"]
            and isinstance(x.get("units"), int) and x["units"] >= 2 * x["groups"]):
        bad.append(name + ": counts")
    return bad


def check_result(r):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    if r.get("settings") != SETTINGS:
        bad.append("settings")
    g = files_gate(r)
    if g == INC:
        return bad + ["files"]
    for k, v in r["files"].items():
        if v.get("md5_ok") is not (v.get("md5") == MD5[k]):
            bad.append("md5 flag " + k)
    if g == DM:
        if r.get("verdict") != DM or "tests" in r:
            bad.append("results despite a data mismatch")
        return bad
    rg = regrade(r)
    if rg["verdict"] == INC:
        return bad + ["incomplete"]
    for k, _ in TESTS:
        bad += check_test(k, r["tests"][k])
    if r.get("level") != rg["level"]:
        bad.append("level")
    n = {k: r.get(k) for k in ("n_pub", "n_pub_a", "n_dur", "n_dur_a", "n_timed")}
    if not all(isinstance(v, int) and v >= 0 for v in n.values()):
        bad.append("counts missing")
    elif not (n["n_pub_a"] <= n["n_pub"] and n["n_dur_a"] <= n["n_dur"] <= n["n_pub"]
              and n["n_dur"] <= n["n_timed"]):
        bad.append("counts out of order")
    cal = r.get("calibration")
    if rg["level"] is None:
        if cal is not None:
            bad.append("calibration without a level")
        return bad
    if not p_ok(r.get("rotation_p_high"), B_ROT):
        bad.append("rotation p lattice")
    lists = [("size", cal["size"]["p"])]
    lists += [("power " + k, v["p"]) for k, v in sorted(cal["power"].items())]
    fa = cal["false_alarm"]
    lists += [("false alarm " + k, fa[k]) for k in ("naive_p_high", "naive_p_low", "bout_p_high")]
    for name, ps in lists:
        if len(ps) != R_CAL or not all(p_ok(p, B_CAL) for p in ps):
            bad.append(name + ": R or lattice")
    dn = r["tests"]["naive_pub"].get("d")
    want = ["0.5", "1.0"] if finite(dn) and dn > 0 else []
    if sorted(cal["power"]) != want:
        bad.append("power keys")
    for k in want:
        if abs(cal["power"][k]["delta"] - float(k) * dn) > 1e-9 * max(1.0, abs(dn)):
            bad.append("power delta " + k)
    return bad


def compare_job(r, rg):
    bad = []
    if r.get("verdict") != rg["verdict"]:
        bad.append("verdict")
    if r.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    a, b = r.get("brier"), rg["brier"]
    if not ((a is None and b is None) or (finite(a) and finite(b) and abs(a - b) < 1e-9)):
        bad.append("brier")
    return bad


# --------------------------------------------------------------------------- rendering
def yes_no(v):
    return "not run" if v is None else ("yes" if v else "no")


def md5_line(r):
    f = r.get("files") or {}
    return "Code version `{}`; data files md5 match: {}".format(
        r.get("version"), ", ".join("%s %s" % (k, yes_no((f.get(k) or {}).get("md5_ok")))
                                    for k in MD5))


def ceti_line(r):
    c = r.get("ceti_copy") or {}
    if "same_as_osf" in c:
        return "codamd.csv in Project-CETI/coda-vowel-phonology (commit be751b8) is " + (
            "identical to the OSF copy" if c["same_as_osf"] else "NOT identical to the OSF copy")
    return "codamd.csv in Project-CETI/coda-vowel-phonology: not compared ({})".format(
        c.get("error", "missing"))


def units_line(r):
    return ("Published subset (1+1+3 codas of ATWOOD, FORK, PINCHY and TBB with a vowel and a "
            "duration): **{:,}** codas ({:,} a, {:,} i); timed: **{:,}** of them in {} bouts and "
            "{} whale-deployments").format(r["n_pub"], r["n_pub_a"], r["n_pub"] - r["n_pub_a"],
                                           r["n_dur"], r["n_bouts_dur"], r["n_deployments_dur"])


def whale_row(w, x):
    """| whale | a codas | i codas | mean a (s) | mean i (s) | a - i (s) |"""
    diff = x["mean_a"] - x["mean_i"] if finite(x["mean_a"]) and finite(x["mean_i"]) else None
    return "| {} | {:,} | {:,} | {} | {} | {} |".format(
        w, x["n_a"], x["n_i"], fmt(x["mean_a"], ".4f"), fmt(x["mean_i"], ".4f"),
        fmt(diff, "+.4f"))


def contrast_row(k, text, x):
    """| comparison | D = a - i (s) | groups with both vowels | minority-vowel codas | p_high |
    p_low |"""
    return "| {} | {} | {:,} | {:,} | {} | {} |".format(
        text, fmt(x.get("d"), "+.4f"), x["groups"], x["minority"], fmt(x["p_high"], ".4f"),
        fmt(x["p_low"], ".4f"))


def level_line(rg):
    return ("Level tested: **{}** (the first of bout, deployment with at least 5 groups holding "
            "both vowels and 15 minority-vowel codas)").format(rg["level"] or "none")


def rotation_line(r):
    return ("Rotation p_high at that level (labels turned within groups, runs kept, B = 9,999): "
            "{}").format(fmt(r.get("rotation_p_high"), ".4f"))


def size_line(rg):
    return ("Size in rotation worlds (effect removed, R = 200, B = 999): **{}** (calibration "
            "fails above 0.10)").format(fmt(rg["size"], ".3f"))


def power_row(k, r, rg):
    """| effect added to a-codas | delta (s) | power |"""
    return "| {} x published-style D | {} | {} |".format(
        k, fmt(r["calibration"]["power"][k]["delta"], ".4f"), fmt(rg["power"][k], ".3f"))


def fa_line(rg):
    return ("Bout-clustered worlds with no vowel effect (one vowel per bout, 5% flipped, real "
            "durations, R = 200): published-style test says 'a longer' in **{}**, either "
            "direction (p <= 0.025 each side) in {}; within-bout test says 'a longer' in "
            "{}").format(fmt(rg["f_naive"], ".3f"), fmt(rg["f_naive_two"], ".3f"),
                         fmt(rg["f_bout"], ".3f"))


def mode_row(w, x):
    """| whale | i codas | split (s) | long | mean short (s) | mean long (s) | dip | dip p |"""
    return "| {} | {:,} | {} | {:,} | {} | {} | {} | {} |".format(
        w, x["n_i"], fmt(x.get("threshold"), ".4f"), x["n_long"], fmt(x.get("mean_short"), ".4f"),
        fmt(x.get("mean_long"), ".4f"), fmt(x.get("dip"), ".4f"), fmt(x.get("dip_p"), ".4f"))


def persist_line(r):
    p = r["modes"]["persistence"]
    if "skipped" in p:
        return "Short/long persistence within bouts: skipped ({})".format(p["skipped"])
    return ("Short/long persistence within bouts: {:,} switches in {:,} neighbouring i-coda "
            "pairs, expected {:.2f}, Q = **{:.4f}**, p_low = {:.4f} (B = 9,999, shuffled within "
            "whale x deployment)").format(p["switches"], p["pairs"], p["expected"], p["q"],
                                          p["p_low"])


def mode_dep_line(r):
    d = r["modes"]["deployment"]
    if "skipped" in d:
        return "Short/long mix by deployment: skipped ({})".format(d["skipped"])
    return ("Short/long mix by deployment (whales {}; {} deployments, {:,} i-codas): G = {:.3f} "
            "(null mean {:.3f}), p = **{:.4f}**").format(
        ", ".join(d["whales"]), len(d["deployments"]), d["n_units"], d["g_obs"], d["null_mean"],
        d["p"])


def dep_row(x):
    """| whale | deployment | first date | bouts | a | i | mean a (s) | mean i (s) | long i |"""
    return "| {} | {} | {} | {} | {:,} | {:,} | {} | {} | {:,} |".format(
        x["whale"], x["dep"], x["first_date"] or "n/a", x["bouts"], x["n_a"], x["n_i"],
        fmt(x["mean_a"], ".4f"), fmt(x["mean_i"], ".4f"), x["n_i_long"])


def verdict_line(rg):
    return "Verdict: **`%s`**" % rg["verdict"]


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def pred_row(k, rg):
    return "| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, (rg["predictions"] or {}).get(k)))


def score_lines(rg):
    if rg["predictions"] is None:
        return ["0 of 0 graded predictions true"]
    return ["%d of %d graded predictions true" % (rg["n_true"], len(ORDER)),
            "Brier score **%.3f**" % rg["brier"]]


def required_strings(r, rg):
    out = [verdict_line(rg)] + score_lines(rg) + [md5_line(r)]
    if rg["predictions"] is None:
        return out
    out += [ceti_line(r), units_line(r)]
    out += [whale_row(w, r["per_whale"][w]) for w in FOUR]
    out += [contrast_row(k, s, r["tests"][k]) for k, s in TESTS]
    out += [level_line(rg)]
    if rg["level"] is not None:
        out += [rotation_line(r), size_line(rg)]
        out += [power_row(k, r, rg) for k in sorted(r["calibration"]["power"], reverse=True)]
        out += [fa_line(rg)]
    out += [mode_row(w, r["modes"]["per_whale"][w]) for w in FOUR]
    out += [persist_line(r), mode_dep_line(r)]
    out += [dep_row(x) for x in r["per_deployment"]]
    return out


def check_md(md, r, rg):
    missing = [s for s in required_strings(r, rg) if s not in md]
    lines = md.splitlines()
    pr = rg["predictions"] or {}
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, pr.get(k))):
            missing.append("prediction row " + k)
    return missing


def render_markdown(r, rg):
    L = ["# RESULTS-DUR: do sperm whale 'long and short vowels' hold within bouts?", "",
         "Graded by `test_vowel2_results.py` (published with the registration, before the result "
         "existed) from `results/vowel2/vowel2_results.json`, the output of `vowel2_test.py` "
         "registered in `VOWEL2-PREREG.md`. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI "
         "agents; not yet checked by a human expert. Text CC BY 4.0.", "", "## Verdict", "",
         verdict_line(rg), ""]
    for s in score_lines(rg):
        L += [s, ""]
    L += ["## Data", "", md5_line(r), ""]
    if rg["predictions"] is not None:
        L += [ceti_line(r), "", units_line(r), "",
              "## Published-style durations by whale (all codas of the subset)", "",
              "| whale | a codas | i codas | mean a (s) | mean i (s) | a - i (s) |",
              "|---|---|---|---|---|---|"]
        L += [whale_row(w, r["per_whale"][w]) for w in FOUR]
        L += ["", "## Duration contrast at each level (D = weighted mean of a minus i)", "",
              "| comparison | D = a - i (s) | groups with both vowels | minority-vowel codas | "
              "p_high | p_low |", "|---|---|---|---|---|---|"]
        L += [contrast_row(k, s, r["tests"][k]) for k, s in TESTS]
        L += ["", level_line(rg), ""]
        if rg["level"] is not None:
            L += [rotation_line(r), "", "## Calibration", "", size_line(rg), "",
                  "| effect added to a-codas | delta (s) | power |", "|---|---|---|"]
            L += [power_row(k, r, rg) for k in sorted(r["calibration"]["power"], reverse=True)]
            L += ["", fa_line(rg), ""]
        L += ["## i-vowel durations: short and long modes (secondary)", "",
              "| whale | i codas | split (s) | long | mean short (s) | mean long (s) | dip | "
              "dip p |", "|---|---|---|---|---|---|---|---|"]
        L += [mode_row(w, r["modes"]["per_whale"][w]) for w in FOUR]
        L += ["", persist_line(r), "", mode_dep_line(r), "",
              "## By deployment (exploratory)", "",
              "| whale | deployment | first date | bouts | a | i | mean a (s) | mean i (s) | "
              "long i |", "|---|---|---|---|---|---|---|---|---|"]
        L += [dep_row(x) for x in r["per_deployment"]]
        L += [""]
    L += ["## Predictions (priors fixed in VOWEL2-PREREG.md)", "",
          "| id | prediction | prior | came true |", "|---|---|---|---|"]
    L += [pred_row(k, rg) for k in ORDER]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- result tests
@unittest.skipUnless(HAVE, "results/vowel2/vowel2_results.json not published yet")
class TestVowel2Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_job_matches_regrade(self):
        self.assertEqual(compare_job(self.r, self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-DUR.md not written yet")
    def test_md(self):
        with open(MD, encoding="utf-8") as f:
            self.assertEqual(check_md(f.read(), self.r, self.rg), [])


# --------------------------------------------------------------------------- toy tests
def plist(n_hit, n_miss, hit=0.001, miss=0.3):
    return [hit] * n_hit + [miss] * n_miss


def ttest(d, groups, minority, ph, pl, units=None):
    return {"B": B_MAIN, "d": d, "groups": groups, "minority": minority,
            "units": units if units is not None else 3 * groups, "weight": 1.0,
            "p_high": ph, "p_low": pl, "null_mean": 0.0, "null_sd": 0.01}


def toy():
    """Default: level bout (12 groups, 20 minority); naive D 0.06 p 0.0001 (reproduced); bout D
    0.01, p_high 0.3 -> power 170/200 = 0.85 -> NO_DIFFERENCE_WITH_POWER_WITHIN_BOUTS; size
    9/200; naive false alarm 60/200; persistence Q 0.3 p 0.0001; deployment p 0.002."""
    fa = {"R": 200, "B": 999, "eps": 0.05, "naive_p_high": plist(60, 140),
          "naive_p_low": plist(50, 150), "bout_p_high": plist(11, 189)}
    return {"version": VERSION, "settings": copy.deepcopy(SETTINGS), "md5_ok": True,
            "files": {k: {"md5": v, "md5_ok": True, "rows": 1} for k, v in MD5.items()},
            "ceti_copy": {"md5": MD5["codamd.csv"], "same_as_osf": True},
            "n_pub": 600, "n_pub_a": 400, "n_dur": 500, "n_dur_a": 330, "n_timed": 1100,
            "n_bouts_dur": 60, "n_deployments_dur": 9,
            "per_whale": {w: {"n_a": 100, "n_i": 50, "mean_a": 1.2, "mean_i": 1.15}
                          for w in FOUR},
            "tests": {"naive_pub": ttest(0.06, 4, 200, 0.0001, 1.0),
                      "naive_timed": ttest(0.05, 4, 160, 0.0001, 1.0),
                      "within_dep": ttest(0.03, 7, 60, 0.01, 0.9902),
                      "within_bout": ttest(0.01, 12, 20, 0.3, 0.7002)},
            "level": "bout", "rotation_p_high": 0.25,
            "calibration": {"size": {"R": 200, "B": 999, "p": plist(9, 191)},
                            "power": {"1.0": {"delta": 0.06, "R": 200, "B": 999,
                                              "p": plist(170, 30)},
                                      "0.5": {"delta": 0.03, "R": 200, "B": 999,
                                              "p": plist(80, 120)}},
                            "false_alarm": fa},
            "modes": {"per_whale": {w: {"n_i": 50, "threshold": 1.1, "n_long": 20,
                                        "mean_short": 1.0, "mean_long": 1.3, "dip": 0.05,
                                        "dip_p": 0.01} for w in FOUR},
                      "n_timed_i": 150,
                      "persistence": {"pairs": 100, "switches": 9, "expected": 30.0, "q": 0.3,
                                      "p_low": 0.0001, "B": 9999},
                      "deployment": {"whales": ["FORK"], "deployments": ["FORK/a", "FORK/b"],
                                     "n_units": 40, "g_obs": 9.0, "B": 9999, "p": 0.002,
                                     "null_mean": 1.0}},
            "per_deployment": [{"whale": "FORK", "dep": "sw061b", "first_date": "2015-02-01",
                                "bouts": 5, "n_a": 30, "n_i": 10, "mean_a": 1.2, "mean_i": 1.1,
                                "n_i_long": 4}]}


def attach(r):
    rg = regrade(r)
    r.update(verdict=rg["verdict"], predictions=rg["predictions"], brier=rg["brier"])
    return r


class TestToy(unittest.TestCase):
    def test_default(self):
        r = toy()
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "NO_DIFFERENCE_WITH_POWER_WITHIN_BOUTS")
        self.assertEqual((rg["level"], rg["reproduced"]), ("bout", True))
        self.assertEqual(rg["size"], 0.045)
        self.assertEqual(rg["power"], {"1.0": 0.85, "0.5": 0.4})
        self.assertEqual(rg["f_naive"], 0.3)
        # either side at 0.025: hit p 0.001 in 60 high-side lists (the first 50 also low) = 60
        self.assertEqual(rg["f_naive_two"], 0.3)
        self.assertEqual(rg["f_bout"], 0.055)
        # P2 false (p 0.3); P6: 0.01 < 0.5 * 0.05
        self.assertEqual([rg["predictions"][k] for k in ORDER],
                         [True, False, True, True, True, True, True, True])
        # (.04 + .1225 + .25 + .01 + .0625 + .16 + .2025 + .16) / 8 = 1.0075 / 8
        self.assertAlmostEqual(rg["brier"], 1.0075 / 8, places=12)
        self.assertEqual(check_result(r), [])
        self.assertEqual(compare_job(r, rg), ["verdict", "predictions", "brier"])
        attach(r)
        self.assertEqual(compare_job(r, regrade(r)), [])
        md = render_markdown(r, rg)
        self.assertEqual(check_md(md, r, rg), [])
        self.assertTrue(all(ord(ch) < 128 for ch in md))

    def test_verdict_paths(self):
        r = toy()
        r["tests"]["within_bout"]["p_high"] = 0.0001
        r["tests"]["within_bout"]["p_low"] = 1.0
        self.assertEqual(regrade(r)["verdict"], "DURATION_DIFFERENCE_WITHIN_BOUTS")
        r = toy()
        r["tests"]["within_bout"].update(p_high=0.99, p_low=0.03)
        self.assertEqual(regrade(r)["verdict"], "REVERSED_WITHIN_BOUTS")
        r = toy()
        r["calibration"]["power"]["1.0"]["p"] = plist(159, 41)      # 0.795
        self.assertEqual(regrade(r)["verdict"], "UNDERPOWERED_WITHIN_BOUTS")
        r = toy()
        r["calibration"]["size"]["p"] = plist(21, 179)              # 0.105
        self.assertEqual(regrade(r)["verdict"], "CALIBRATION_FAILED_WITHIN_BOUTS")
        r = toy()
        r["tests"]["within_bout"]["minority"] = 14
        r["level"] = "deployment"
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "DURATION_DIFFERENCE_WITHIN_DEPLOYMENTS")
        self.assertFalse(rg["predictions"]["P6"])                   # 0.03 >= 0.025
        self.assertEqual(check_result(r), [])
        r = toy()
        r["tests"]["naive_pub"].update(d=-0.01, p_high=0.8, p_low=0.2002)
        r["calibration"]["power"] = {}
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "NOT_REPRODUCED")
        self.assertFalse(rg["predictions"]["P1"])
        self.assertFalse(rg["predictions"]["P3"])
        self.assertEqual(check_result(r), [])
        r = toy()
        r["tests"]["within_bout"]["groups"] = 4
        r["tests"]["within_dep"]["groups"] = 4
        r["level"] = None
        r["calibration"] = None
        r.pop("rotation_p_high")
        rg = regrade(r)
        self.assertEqual(rg["verdict"], INS)
        self.assertEqual([rg["predictions"][k] for k in ("P2", "P3", "P4", "P5", "P6")],
                         [False] * 5)
        self.assertEqual(check_result(r), [])
        self.assertEqual(check_md(render_markdown(r, rg), r, rg), [])

    def test_checks(self):
        r = toy()
        r["tests"]["within_dep"]["p_high"] = 0.01005
        r["settings"]["b_cal"] = 99
        r["calibration"]["size"]["p"][0] = 0.0105
        self.assertEqual(sorted(check_result(r)),
                         sorted(["settings", "within_dep: p lattice", "size: R or lattice"]))
        r = toy()
        r["calibration"]["power"]["0.5"]["delta"] = 0.031
        r["level"] = "deployment"
        self.assertEqual(check_result(r), ["level", "power delta 0.5"])
        r = toy()
        r["files"]["DominicaCodas.csv"] = {"md5": "0" * 32, "md5_ok": False}
        self.assertEqual(regrade(r)["verdict"], DM)
        self.assertEqual(check_result(r), ["results despite a data mismatch"])
        for k in ("tests", "modes", "calibration", "per_deployment", "per_whale"):
            r.pop(k)
        r["verdict"] = DM
        self.assertEqual(check_result(r), [])
        lines = required_strings(r, regrade(r))
        self.assertEqual(lines[0], "Verdict: **`DATA_MISMATCH`**")
        self.assertEqual(lines[2], "Code version `whale-vowel2-test-1`; data files md5 match: "
                                   "codamd.csv yes, DominicaCodas.csv no, "
                                   "sperm-whale-dialogues.csv yes")

    def test_formats(self):
        r = attach(toy())
        rg = regrade(r)
        self.assertEqual(whale_row("FORK", r["per_whale"]["FORK"]),
                         "| FORK | 100 | 50 | 1.2000 | 1.1500 | +0.0500 |")
        self.assertEqual(contrast_row("within_bout", "within bout", r["tests"]["within_bout"]),
                         "| within bout | +0.0100 | 12 | 20 | 0.3000 | 0.7002 |")
        self.assertEqual(power_row("1.0", r, rg),
                         "| 1.0 x published-style D | 0.0600 | 0.850 |")
        self.assertEqual(persist_line(r), "Short/long persistence within bouts: 9 switches in "
                                          "100 neighbouring i-coda pairs, expected 30.00, Q = "
                                          "**0.3000**, p_low = 0.0001 (B = 9,999, shuffled "
                                          "within whale x deployment)")
        self.assertEqual(dep_row(r["per_deployment"][0]),
                         "| FORK | sw061b | 2015-02-01 | 5 | 30 | 10 | 1.2000 | 1.1000 | 4 |")
        self.assertEqual(score_lines(rg), ["7 of 8 graded predictions true",
                                           "Brier score **0.126**"])
        self.assertEqual(pred_row("P2", rg), "| P2 | a longer than i within the level tested, "
                                             "p_high <= 0.05 | 0.35 | **false** |")


def render_cli(src, dst):
    with open(src, encoding="utf-8") as f:
        r = json.load(f)
    rg = regrade(r)
    md = render_markdown(r, rg)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(json.dumps({"verdict": rg["verdict"], "check_result": check_result(r),
                      "compare_job": compare_job(r, rg), "missing": check_md(md, r, rg)}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--render":
        sys.exit(render_cli(sys.argv[2], sys.argv[3]))
    unittest.main()
