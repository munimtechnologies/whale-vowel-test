# SPDX-License-Identifier: Apache-2.0
# test_vowel3_results.py: the grader for the pre-registered sperm whale coda "coarticulation"
# mirror test (VOWEL3-PREREG.md, job vowel3-coart-v1), written and published while the job was
# still waiting in the queue, before any result existed. With its own code (stdlib only; it does
# not import vowel3_test.py for any check except the optional byte-for-byte render comparison)
# it re-derives from the raw job output (results/coart/vowel3_results.json):
#   - the filter arithmetic (rows read minus each drop = rows kept);
#   - that pairs, change / no-change counts, per-whale and per-deployment tables add up, and that
#     every deployment belongs to the whale it is filed under;
#   - every mismatch rate from its counts, and Delta_first and Delta_last from the paired rates;
#   - A = Delta_first - Delta_last;
#   - the place of every p value on the permutation lattice (1 + k) / (B + 1), and
#     p_low + p_high >= 1 + 1 / (B + 1) (ties are counted on both sides);
#   - calibration rates as whole counts out of R, the planted deltas (max(Delta_first, 0) and half);
#   - the verdict of VOWEL3-PREREG.md section 5 (in order), the LAST_CLICK flag, predictions
#     P1-P6 and the Brier score of section 6;
# and checks that the job's own verdict, flag, predictions and Brier score agree with the regrade.
# Until results/coart/vowel3_results.json exists the result tests are skipped; the toy tests,
# whose expected values are all worked out by hand, always run.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "coart", "vowel3_results.json")
MD = os.path.join(HERE, "RESULTS-COART.md")
HAVE = os.path.exists(RES)

DATA_SHA = "be751b8761c87813754dba10ad7068a9e71367c0"
DATA_NAME = "focal-coarticulation-metadata.csv"
WHALES = ("PINCHY", "FORK", "ATWOOD", "TBB")
SETTINGS = {"seed": 20261121, "B": 9999, "R": 200, "B_cal": 999}
B_MAIN = 9999
R_CAL = 200
B_CAL = 999
ALPHA = 0.05
SIZE_MAX = 0.10
POWER_MIN = 0.80
FIRST_FIRES_MIN = 0.5
MIN_CHANGE = 10
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6")
PRIORS = {"P1": 0.75, "P2": 0.55, "P3": 0.65, "P4": 0.90, "P5": 0.55, "P6": 0.40}
STATS = ("first", "last", "asym")
WORLDS = ("W0", "W1_full", "W1_half")
T0_KEYS = ("first_all_rows", "last_all_rows", "first_paired", "last_paired")
ISSUE_KEYS = ("rows", "bad_deltasec", "out_of_window", "other_whale", "no_type", "coart_conflicts")
COUNT_KEYS = ("n_rows", "n_paired", "n_change", "n_nochange", "n_deployments", "n_whales")
INS = "INSUFFICIENT_DATA"
FLAG = "LAST_CLICK_ALSO_MISMATCHES"


# --------------------------------------------------------------------------
# helpers (None stands for the job's NaN, which its clean() writes as null)
# --------------------------------------------------------------------------
def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def finite(x):
    return is_num(x) and x == x and abs(x) != float("inf")


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    if not (is_num(a) and is_num(b)):
        return False
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def gt(x, t):
    return finite(x) and x > t


def le(x, t):
    return finite(x) and x <= t


def ge(x, t):
    return finite(x) and x >= t


def p_ok(p, b):
    """p = (1 + k) / (1 + b) for an integer 0 <= k <= b."""
    if not finite(p):
        return False
    k = p * (b + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= b


def whole_share(x, n):
    """x = k / n for an integer 0 <= k <= n."""
    if not finite(x):
        return False
    k = x * n
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n


# --------------------------------------------------------------------------
# independent re-implementation of VOWEL3-PREREG.md sections 5 and 6
# --------------------------------------------------------------------------
def verdict_of(n_change, first_p_high, first_obs, asym_p_high, asym_p_low, size, power_full):
    if n_change < MIN_CHANGE:
        return INS
    if not gt(first_obs, 0.0) or gt(first_p_high, ALPHA):
        return "NOT_REPRODUCED"
    if not le(size, SIZE_MAX):
        return "CALIBRATION_FAILED"
    if le(asym_p_high, ALPHA):
        return "CARRYOVER_SPECIFIC"
    if le(asym_p_low, ALPHA):
        return "REVERSED_ASYMMETRY"
    if ge(power_full, POWER_MIN):
        return "SYMMETRIC_WITH_POWER"
    return "UNDERPOWERED"


def regrade(r):
    m = r.get("main")
    if m is None:
        return {"verdict": INS, "flags": {}, "predictions": {}, "brier": None}
    cal = r["calibration"]
    size = cal["W0"]["asym_reject"]
    power = cal["W1_full"]["asym_reject"]
    f, la, a = m["first"], m["last"], m["asym"]
    v = verdict_of(r["n_change"], f["p_high"], f["obs"], a["p_high"], a["p_low"], size, power)
    out = {"P1": gt(f["obs"], 0.0) and le(f["p_high"], ALPHA),
           "P2": gt(la["obs"], 0.0) and le(la["p_high"], ALPHA),
           "P3": v != "CARRYOVER_SPECIFIC",
           "P4": le(size, SIZE_MAX),
           "P5": ge(cal["W0"]["first_reject"], FIRST_FIRES_MIN),
           "P6": ge(power, POWER_MIN)}
    preds = {q: {"prior": PRIORS[q], "outcome": bool(out[q])} for q in ORDER}
    brier = sum((PRIORS[q] - (1.0 if out[q] else 0.0)) ** 2 for q in ORDER) / len(ORDER)
    return {"verdict": v, "flags": {FLAG: bool(gt(la["obs"], 0.0) and le(la["p_high"], ALPHA))},
            "predictions": preds, "brier": brier}


# --------------------------------------------------------------------------
# internal consistency of the raw output
# --------------------------------------------------------------------------
def check_tables(r):
    """Rate tables: whole counts, rate = mismatches / n (None when n = 0)."""
    bad = []
    t0 = r.get("t0") or {}
    for key in T0_KEYS:
        t = t0.get(key) or {}
        for typ in ("C", "N"):
            x = t.get(typ) or {}
            n, mm, rate = x.get("n"), x.get("mismatches"), x.get("rate")
            ok = is_int(n) and is_int(mm) and 0 <= mm <= n
            if ok:
                ok = (rate is None) if n == 0 else close(rate, mm / n)
            if not ok:
                bad.append("rate table " + key)
                break
    if bad:
        return bad
    fp, lp = t0["first_paired"], t0["last_paired"]
    fa, la = t0["first_all_rows"], t0["last_all_rows"]
    if (fp["C"]["n"] != r["n_change"] or fp["N"]["n"] != r["n_nochange"]
            or lp["C"]["n"] != r["n_change"] or lp["N"]["n"] != r["n_nochange"]):
        bad.append("paired tables vs pairs")
    if any(fa[t]["n"] < fp[t]["n"] or la[t]["n"] < lp[t]["n"] for t in ("C", "N")):
        bad.append("all-row tables smaller than paired")
    if (fa["C"]["n"] + fa["N"]["n"] > r["n_rows"]) or (la["C"]["n"] + la["N"]["n"] > r["n_rows"]):
        bad.append("all-row tables larger than rows")
    return bad


def paired_delta(t):
    c, n = t["C"]["rate"], t["N"]["rate"]
    return None if c is None or n is None else c - n


def check_main(r, tables_ok):
    bad = []
    m = r["main"]
    for s in STATS:
        x = m.get(s) or {}
        b, pl, ph = x.get("B"), x.get("p_low"), x.get("p_high")
        if not (b == B_MAIN and p_ok(pl, b) and p_ok(ph, b) and pl + ph >= 1.0 + 1.0 / (b + 1) - 1e-12
                and finite(x.get("obs")) and finite(x.get("null_mean"))
                and finite(x.get("null_sd")) and x["null_sd"] >= 0):
            bad.append("p values " + s)
    if bad:
        return bad
    if tables_ok:
        if not close(m["first"]["obs"], paired_delta(r["t0"]["first_paired"])):
            bad.append("first delta")
        if not close(m["last"]["obs"], paired_delta(r["t0"]["last_paired"])):
            bad.append("last delta")
    if not close(m["asym"]["obs"], m["first"]["obs"] - m["last"]["obs"]):
        bad.append("asym = first - last")
    g = r.get("gap_halves") or {}
    h = g.get("halves") or {}
    parts = [h.get("gap_le_median"), h.get("gap_gt_median")]
    if (not finite(g.get("median_deltasec")) or not all(isinstance(p, dict) for p in parts)
            or sum(p.get("n", 0) for p in parts) != r["n_paired"]
            or sum(p.get("n_change", 0) for p in parts) != r["n_change"]):
        bad.append("gap halves")
    cal = r.get("calibration") or {}
    ok = cal.get("R") == R_CAL and cal.get("B") == B_CAL
    d_full = max(m["first"]["obs"], 0.0)
    ok = ok and close(cal.get("delta_full"), d_full)
    targets = {"W0": 0.0, "W1_full": d_full, "W1_half": d_full / 2.0}
    for w in WORLDS:
        x = cal.get(w) or {}
        ok = ok and close(x.get("delta"), targets[w]) and all(
            whole_share(x.get(k), R_CAL)
            for k in ("asym_reject", "asym_reverse_reject", "first_reject"))
    if not ok:
        bad.append("calibration")
    return bad


def check_result(r):
    bad = []
    if r.get("settings") != SETTINGS:
        bad.append("settings")
    d = r.get("data") or {}
    url = str(d.get("url", ""))
    if DATA_SHA not in url or not url.endswith(DATA_NAME):
        bad.append("data url")
    if not all(is_int(r.get(k)) and r[k] >= 0 for k in COUNT_KEYS):
        return bad + ["counts missing"]
    iss = d.get("issues") or {}
    if not all(is_int(iss.get(k)) and iss[k] >= 0 for k in ISSUE_KEYS):
        bad.append("issues")
    elif (iss["rows"] - iss["bad_deltasec"] - iss["out_of_window"] - iss["other_whale"]
          - iss["no_type"]) != r["n_rows"]:
        bad.append("rows after filters")
    if r["n_paired"] != r["n_change"] + r["n_nochange"]:
        bad.append("pairs do not add up")
    if r["n_paired"] > r["n_rows"]:
        bad.append("more pairs than rows")
    cw = r.get("change_by_whale") or {}
    dp = r.get("deployments") or {}
    if len(cw) != r["n_whales"] or len(dp) != r["n_deployments"]:
        bad.append("whale or deployment count")
    if any(w not in WHALES for w in cw):
        bad.append("unknown whale")
    for name, tab in (("whale", cw), ("deployment", dp)):
        if (sum(v.get("C", 0) for v in tab.values()) != r["n_change"]
                or sum(v.get("N", 0) for v in tab.values()) != r["n_nochange"]):
            bad.append(name + " table sums")
    per = {}
    for k, v in dp.items():
        w = k.split("|")[0]
        per.setdefault(w, [0, 0])
        per[w][0] += v.get("C", 0)
        per[w][1] += v.get("N", 0)
    if per != {k: [v.get("C", 0), v.get("N", 0)] for k, v in cw.items()}:
        bad.append("deployments do not add up to whales")
    tb = check_tables(r)
    bad += tb
    if r.get("main") is None:
        if 0 < r["n_change"] < r["n_paired"]:
            bad.append("main missing")
        if r.get("calibration") is not None or "gap_halves" in r:
            bad.append("statistics without main")
        return bad
    return bad + check_main(r, not tb)


def compare_job(r, rg):
    """Mismatches between the job's own grading and the regrade."""
    bad = []
    if r.get("verdict") != rg["verdict"]:
        bad.append("verdict")
    if r.get("flags") != rg["flags"]:
        bad.append("flags")
    if r.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    if not close(r.get("brier"), rg["brier"]):
        bad.append("brier")
    return bad


# --------------------------------------------------------------------------
# lines RESULTS-COART.md must contain (fixed now, from the job's registered render())
# --------------------------------------------------------------------------
def required_lines(r, rg):
    out = ["**%s**" % rg["verdict"]]
    if r.get("main") is not None:
        out.append("Flag %s: %s" % (FLAG, rg["flags"][FLAG]))
    if rg["brier"] is not None:
        out.append("Brier score %.3f." % rg["brier"])
    return out


def check_md(md, r, rg):
    return [s for s in required_lines(r, rg) if s not in md]


def job_render(r):
    """vowel3_test.render(r) if the registered analysis (and numpy) can be imported, else None."""
    if not os.path.exists(os.path.join(HERE, "vowel3_test.py")):
        return None
    try:
        sys.path.insert(0, HERE)
        import vowel3_test  # noqa: E402 - optional, needs numpy
    except Exception:  # noqa: BLE001
        return None
    return vowel3_test.render(r)


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/coart/vowel3_results.json not published yet")
class TestVowel3Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_job_matches_regrade(self):
        self.assertEqual(compare_job(self.r, self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-COART.md not committed yet")
    def test_md(self):
        with open(MD, encoding="utf-8") as f:
            md = f.read().replace("\r\n", "\n")
        self.assertEqual(check_md(md, self.r, self.rg), [])
        rendered = job_render(self.r)
        if rendered is None:
            self.skipTest("vowel3_test.py or numpy not available for the render comparison")
        self.assertEqual(rendered, md)


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def rt(c_n, c_m, n_n, n_m):
    return {"C": {"n": c_n, "mismatches": c_m, "rate": (c_m / c_n) if c_n else None},
            "N": {"n": n_n, "mismatches": n_m, "rate": (n_m / n_n) if n_n else None}}


def stat(obs, p_low, p_high, null_mean=0.0, null_sd=0.08):
    return {"obs": obs, "null_mean": null_mean, "null_sd": null_sd, "p_low": p_low,
            "p_high": p_high, "B": 9999}


def toy_result():
    """130 rows read, 2 + 5 + 3 + 10 dropped -> 110 kept; 100 pairs, 20 change, 80 no change.
    First click: 8/20 = 0.4 vs 8/80 = 0.1 -> Delta_first 0.3. Last click: 6/20 = 0.3 vs 0.1 ->
    Delta_last 0.2. A = 0.1. W0 size 9/200 = 0.045, W1_full power 170/200 = 0.85, W0 first-click
    test fires 124/200 = 0.62 -> SYMMETRIC_WITH_POWER, flag true, P1-P6 all true,
    Brier (.0625 + .2025 + .1225 + .01 + .2025 + .36) / 6 = .96 / 6 = 0.16."""
    return {
        "n_rows": 110, "n_paired": 100, "n_change": 20, "n_nochange": 80,
        "n_deployments": 3, "n_whales": 2,
        "t0": {"first_all_rows": rt(22, 9, 85, 9), "last_all_rows": rt(21, 6, 84, 8),
               "first_paired": rt(20, 8, 80, 8), "last_paired": rt(20, 6, 80, 8)},
        "change_by_whale": {"ATWOOD": {"C": 12, "N": 50}, "PINCHY": {"C": 8, "N": 30}},
        "deployments": {"ATWOOD|d1": {"C": 7, "N": 30}, "ATWOOD|d2": {"C": 5, "N": 20},
                        "PINCHY|d3": {"C": 8, "N": 30}},
        "main": {"first": stat(0.3, 1.0, 0.0003, 0.01),
                 "last": stat(0.2, 0.99, 0.013),
                 "asym": stat(0.1, 0.84, 0.17, 0.0, 0.1)},
        "gap_halves": {"median_deltasec": 2.5, "halves": {
            "gap_le_median": {"n": 50, "n_change": 11, "first": 0.35, "last": 0.1},
            "gap_gt_median": {"n": 50, "n_change": 9, "first": 0.25, "last": 0.3}}},
        "calibration": {"R": 200, "B": 999, "delta_full": 0.3,
                        "W0": {"delta": 0.0, "asym_reject": 0.045, "asym_reverse_reject": 0.05,
                               "first_reject": 0.62},
                        "W1_full": {"delta": 0.3, "asym_reject": 0.85, "asym_reverse_reject": 0.0,
                                    "first_reject": 0.99},
                        "W1_half": {"delta": 0.15, "asym_reject": 0.4,
                                    "asym_reverse_reject": 0.005, "first_reject": 0.9}},
        "verdict": "SYMMETRIC_WITH_POWER",
        "flags": {FLAG: True},
        "predictions": {q: {"prior": PRIORS[q], "outcome": True} for q in ORDER},
        "brier": 0.16,
        "settings": dict(SETTINGS),
        "data": {"url": "https://raw.githubusercontent.com/Project-CETI/coda-vowel-phonology/"
                        + DATA_SHA + "/" + DATA_NAME,
                 "md5": "0" * 32, "bytes": 1000,
                 "issues": {"rows": 130, "bad_deltasec": 2, "out_of_window": 5, "other_whale": 3,
                            "no_type": 10, "coart_conflicts": 1}},
        "seconds": 12.0}


def toy_insufficient():
    """No change pair at all: the job skips every test (main and calibration null)."""
    r = toy_result()
    r.update(n_change=0, n_nochange=100, verdict=INS, flags={}, predictions={}, brier=None,
             main=None, calibration=None)
    del r["gap_halves"]
    r["t0"] = {"first_all_rows": rt(2, 1, 105, 11), "last_all_rows": rt(1, 0, 104, 10),
               "first_paired": rt(0, 0, 100, 10), "last_paired": rt(0, 0, 100, 10)}
    r["change_by_whale"] = {"ATWOOD": {"C": 0, "N": 62}, "PINCHY": {"C": 0, "N": 38}}
    r["deployments"] = {"ATWOOD|d1": {"C": 0, "N": 37}, "ATWOOD|d2": {"C": 0, "N": 25},
                        "PINCHY|d3": {"C": 0, "N": 38}}
    return r


class TestToy(unittest.TestCase):
    def test_default(self):
        r = toy_result()
        self.assertEqual(check_result(r), [])
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "SYMMETRIC_WITH_POWER")
        self.assertEqual(rg["flags"], {FLAG: True})
        self.assertTrue(all(rg["predictions"][q]["outcome"] for q in ORDER))
        self.assertAlmostEqual(rg["brier"], 0.16, places=12)
        self.assertEqual(compare_job(r, rg), [])
        r2 = json.loads(json.dumps(r))
        self.assertEqual(check_result(r2), [])
        self.assertEqual(compare_job(r2, regrade(r2)), [])

    def test_verdict_table(self):
        v = verdict_of
        self.assertEqual(v(9, 0.001, 0.3, 0.5, 0.5, 0.0, 1.0), INS)
        self.assertEqual(v(10, 0.001, 0.0, 0.5, 0.5, 0.0, 1.0), "NOT_REPRODUCED")
        self.assertEqual(v(10, 0.001, None, 0.5, 0.5, 0.0, 1.0), "NOT_REPRODUCED")
        self.assertEqual(v(10, 0.0501, 0.3, 0.5, 0.5, 0.0, 1.0), "NOT_REPRODUCED")
        self.assertEqual(v(10, 0.05, 0.3, 0.5, 0.5, 0.105, 1.0), "CALIBRATION_FAILED")
        self.assertEqual(v(10, 0.05, 0.3, 0.5, 0.5, None, 1.0), "CALIBRATION_FAILED")
        self.assertEqual(v(10, 0.05, 0.3, 0.05, 0.96, 0.10, 0.0), "CARRYOVER_SPECIFIC")
        self.assertEqual(v(10, 0.05, 0.3, 0.96, 0.05, 0.10, 1.0), "REVERSED_ASYMMETRY")
        self.assertEqual(v(10, 0.05, 0.3, 0.5, 0.5, 0.10, 0.80), "SYMMETRIC_WITH_POWER")
        self.assertEqual(v(10, 0.05, 0.3, 0.5, 0.5, 0.10, 0.795), "UNDERPOWERED")
        self.assertEqual(v(10, 0.05, 0.3, 0.5, 0.5, 0.10, None), "UNDERPOWERED")

    def test_regrade_variants(self):
        r = toy_result()
        r["main"]["asym"].update(p_low=0.98, p_high=0.03)
        self.assertEqual(check_result(r), [])
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "CARRYOVER_SPECIFIC")
        self.assertFalse(rg["predictions"]["P3"]["outcome"])
        # P3 false: (.65 - 0)^2 = .4225 replaces .1225 -> 1.26 / 6 = 0.21
        self.assertAlmostEqual(rg["brier"], 0.21, places=12)
        self.assertEqual(compare_job(r, rg), ["verdict", "predictions", "brier"])
        r = toy_result()
        r["main"]["last"].update(p_low=0.94, p_high=0.07)
        rg = regrade(r)
        self.assertEqual(rg["flags"], {FLAG: False})
        self.assertFalse(rg["predictions"]["P2"]["outcome"])
        self.assertEqual(rg["verdict"], "SYMMETRIC_WITH_POWER")
        r = toy_result()
        r["calibration"]["W1_full"]["asym_reject"] = 0.795
        r["calibration"]["W0"]["first_reject"] = 0.495
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "UNDERPOWERED")
        self.assertFalse(rg["predictions"]["P5"]["outcome"])
        self.assertFalse(rg["predictions"]["P6"]["outcome"])

    def test_insufficient(self):
        r = toy_insufficient()
        self.assertEqual(check_result(r), [])
        rg = regrade(r)
        self.assertEqual(rg, {"verdict": INS, "flags": {}, "predictions": {}, "brier": None})
        self.assertEqual(compare_job(r, rg), [])
        self.assertEqual(required_lines(r, rg), ["**INSUFFICIENT_DATA**"])
        r["gap_halves"] = {}
        self.assertEqual(check_result(r), ["statistics without main"])
        r = toy_result()
        r["main"] = None
        r["calibration"] = None
        del r["gap_halves"]
        self.assertEqual(check_result(r), ["main missing"])

    def test_consistency_catches_errors(self):
        r = toy_result()
        r["main"]["first"]["obs"] = 0.31
        self.assertEqual(sorted(check_result(r)),
                         sorted(["first delta", "asym = first - last", "calibration"]))
        r = toy_result()
        r["main"]["last"]["p_low"] = 0.99005
        self.assertEqual(check_result(r), ["p values last"])
        r = toy_result()
        r["main"]["asym"]["p_low"] = 0.80
        self.assertEqual(check_result(r), ["p values asym"])
        r = toy_result()
        r["calibration"]["W0"]["asym_reject"] = 0.0475
        self.assertEqual(check_result(r), ["calibration"])
        r = toy_result()
        r["calibration"]["W1_half"]["delta"] = 0.1
        self.assertEqual(check_result(r), ["calibration"])
        r = toy_result()
        r["n_rows"] = 111
        self.assertEqual(check_result(r), ["rows after filters"])
        r = toy_result()
        r["deployments"]["PINCHY|d3"]["C"] = 7
        self.assertEqual(check_result(r), ["deployment table sums",
                                           "deployments do not add up to whales"])
        r = toy_result()
        r["gap_halves"]["halves"]["gap_le_median"]["n_change"] = 10
        self.assertEqual(check_result(r), ["gap halves"])
        r = toy_result()
        r["settings"]["seed"] = 1
        self.assertEqual(check_result(r), ["settings"])
        r = toy_result()
        r["t0"]["first_paired"]["C"]["mismatches"] = 9
        self.assertEqual(check_result(r), ["rate table first_paired"])
        r = toy_result()
        r["data"]["url"] = r["data"]["url"].replace(DATA_SHA, "main")
        self.assertEqual(check_result(r), ["data url"])
        r = toy_result()
        r["change_by_whale"]["MYSTERY"] = r["change_by_whale"].pop("PINCHY")
        r["deployments"]["MYSTERY|d3"] = r["deployments"].pop("PINCHY|d3")
        self.assertEqual(check_result(r), ["unknown whale"])

    def test_compare_job_catches_errors(self):
        r = toy_result()
        r["verdict"] = "UNDERPOWERED"
        r["brier"] = 0.2
        r["flags"] = {FLAG: False}
        self.assertEqual(compare_job(r, regrade(r)), ["verdict", "flags", "brier"])
        r = copy.deepcopy(toy_result())
        r["predictions"]["P4"]["outcome"] = False
        self.assertEqual(compare_job(r, regrade(r)), ["predictions"])

    def test_lattice(self):
        self.assertTrue(p_ok(0.0001, 9999))
        self.assertTrue(p_ok(1.0, 9999))
        self.assertTrue(p_ok(0.0003, 9999))
        self.assertFalse(p_ok(0.0, 9999))
        self.assertFalse(p_ok(0.99005, 9999))
        self.assertFalse(p_ok(None, 9999))
        self.assertTrue(whole_share(0.045, 200))
        self.assertTrue(whole_share(0.0, 200))
        self.assertFalse(whole_share(0.0475, 200))
        self.assertFalse(whole_share(1.005, 200))

    def test_md_lines(self):
        r = toy_result()
        rg = regrade(r)
        lines = required_lines(r, rg)
        self.assertEqual(lines, ["**SYMMETRIC_WITH_POWER**",
                                 "Flag LAST_CLICK_ALSO_MISMATCHES: True",
                                 "Brier score 0.160."])
        md = "## Verdict\n\n**SYMMETRIC_WITH_POWER**\n\nFlag LAST_CLICK_ALSO_MISMATCHES: True\n\nBrier score 0.160.\n"
        self.assertEqual(check_md(md, r, rg), [])
        self.assertEqual(check_md(md.replace("0.160", "0.161"), r, rg), ["Brier score 0.160."])


if __name__ == "__main__":
    unittest.main()
