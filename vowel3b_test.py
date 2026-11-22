#!/usr/bin/env python3
# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made with AI agents working in MV2's name.
"""whale-vowel-test, test 3, amendment 1 (VOWEL3-AMENDMENT-1.md).

Test 3 (VOWEL3-PREREG.md, job vowel3-coart-v1) asked whether the published sperm whale coda
'coarticulation' (the first click of a new coda mismatches its own vowel label at a vowel change)
is carryover, or matched by the previous coda's last click. Its asymmetry test, a permutation of
the change labels within tag deployments, failed its own calibration: in worlds where every pair
is symmetric by construction it fired 20.5% of the time at a nominal 5%. A label permutation
treats the per-pair difference d = mf - ml as exchangeable between change and no-change rows, but
d is non-zero far more often in change rows, so the permutation null is too narrow.

This amendment replaces that test with the exact test for the symmetric world itself: under
symmetry the two clicks of a pair are exchangeable, so every discordant pair's sign is a fair coin.
The null distribution of A = mean_C(d) - mean_N(d) is then the convolution of two binomials and is
computed exactly (no random numbers). Calibration reuses the registered worlds (W0, W1_full,
W1_half) with R = 1000 each. Standard library only.

Usage: python vowel3b_test.py --data-dir /data/coart --out-dir /out
Outputs: vowel3b_results.json and RESULTS-COART-A1.md in --out-dir.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
import urllib.request

DATA_SHA = "be751b8761c87813754dba10ad7068a9e71367c0"
DATA_NAME = "focal-coarticulation-metadata.csv"
DATA_URL = ("https://raw.githubusercontent.com/Project-CETI/coda-vowel-phonology/"
            + DATA_SHA + "/" + DATA_NAME)
WHALES = ("PINCHY", "FORK", "ATWOOD", "TBB")
SEED = 20261122
R_CAL = 1000
ALPHA = 0.05
SIZE_MAX = 0.10
POWER_MIN = 0.80
MIN_CHANGE = 10
# counts published by job vowel3-coart-v1 (results/coart/vowel3_results.json); the amendment
# must see the same pairs or it stops with REPRO_FAILED.
V1 = {"nC": 44, "nN": 716, "mfC": 11, "mfN": 66, "mlC": 9, "mlN": 72}
PRIORS = {"Q1": 0.70, "Q2": 0.50, "Q3": 0.60, "Q4": 0.95}
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com)"
WORLDS = ("W0", "W1_full", "W1_half")


# ---------------------------------------------------------------- parsing (as vowel3_test.py)
def to_int(s):
    try:
        f = float(str(s).strip())
    except ValueError:
        return None
    if not math.isfinite(f) or f != int(f):
        return None
    return int(f)


def to_float(s):
    try:
        f = float(str(s).strip())
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def mismatch(vowel, npk):
    """The authors' 'match' variable (1 = mismatch): a+1 peak or i+2 peaks -> 0,
    a+2 peaks or i+1 peak -> 1, anything else -> None."""
    if vowel == "a" and npk == 1:
        return 0
    if vowel == "i" and npk == 2:
        return 0
    if vowel == "a" and npk == 2:
        return 1
    if vowel == "i" and npk == 1:
        return 1
    return None


def change_type(coart):
    if coart in ("aa", "ii"):
        return "N"
    if coart in ("ia", "ai"):
        return "C"
    return None


def load_rows(path):
    """Rows after the authors' filters (0 < deltasec < 10, four whales) with a defined type."""
    with open(path, newline="", encoding="utf-8") as fh:
        raw = list(csv.DictReader(fh))
    issues = {"rows": len(raw), "bad_deltasec": 0, "out_of_window": 0, "other_whale": 0,
              "no_type": 0}
    rows = []
    for r in raw:
        ds = to_float(r.get("deltasec", ""))
        if ds is None:
            issues["bad_deltasec"] += 1
            continue
        if not (0.0 < ds < 10.0):
            issues["out_of_window"] += 1
            continue
        whale = (r.get("whale") or "").strip()
        if whale not in WHALES:
            issues["other_whale"] += 1
            continue
        t = change_type((r.get("coart") or "").strip())
        if t is None:
            issues["no_type"] += 1
            continue
        pv = (r.get("prevhandvcat") or "").strip()
        v = (r.get("handvcat") or "").strip()
        rows.append({"whale": whale, "type": t,
                     "mf": mismatch(v, to_int(r.get("numpks", ""))),
                     "ml": mismatch(pv, to_int(r.get("prevnumpks", "")))})
    return rows, issues


def pairs(rows):
    """(is_change, mf, ml) for rows where both clicks are scored."""
    return [(r["type"] == "C", r["mf"], r["ml"]) for r in rows
            if r["mf"] is not None and r["ml"] is not None]


# ---------------------------------------------------------------- statistics
def counts(P):
    """Per group: n, b (first click only mismatches), c (last click only), both, neither."""
    out = {g: {"n": 0, "b": 0, "c": 0, "both": 0, "neither": 0} for g in ("C", "N")}
    for is_c, mf, ml in P:
        g = out["C" if is_c else "N"]
        g["n"] += 1
        if mf == 1 and ml == 0:
            g["b"] += 1
        elif mf == 0 and ml == 1:
            g["c"] += 1
        elif mf == 1 and ml == 1:
            g["both"] += 1
        else:
            g["neither"] += 1
    return out


def deltas(cnt):
    """Delta_first, Delta_last and A = Delta_first - Delta_last from the counts."""
    C, N = cnt["C"], cnt["N"]
    df = (C["b"] + C["both"]) / C["n"] - (N["b"] + N["both"]) / N["n"]
    dl = (C["c"] + C["both"]) / C["n"] - (N["c"] + N["both"]) / N["n"]
    a = (C["b"] - C["c"]) / C["n"] - (N["b"] - N["c"]) / N["n"]
    return df, dl, a


def binom_half(k):
    """P(X = x) for X ~ Binomial(k, 1/2), x = 0..k."""
    den = 2.0 ** k
    return [math.comb(k, x) / den for x in range(k + 1)]


def sign_flip_null(cnt):
    """Exact null of A when each discordant pair's sign is a fair coin: list of (a, prob)."""
    nC, nN = cnt["C"]["n"], cnt["N"]["n"]
    kC = cnt["C"]["b"] + cnt["C"]["c"]
    kN = cnt["N"]["b"] + cnt["N"]["c"]
    pc, pn = binom_half(kC), binom_half(kN)
    out = []
    for x, px in enumerate(pc):
        sc = (2 * x - kC) / nC
        for y, py in enumerate(pn):
            out.append((sc - (2 * y - kN) / nN, px * py))
    return out


def critical_value(null, alpha=ALPHA, tol=1e-9):
    """The smallest null value a with P(A* >= a) <= alpha (values within tol count as one);
    None if even the largest value has a tail above alpha."""
    items = sorted(null, key=lambda t: -t[0])
    tail = 0.0
    a_crit = None
    i = 0
    while i < len(items):
        v = items[i][0]
        j = i
        grp = 0.0
        while j < len(items) and items[j][0] >= v - tol:
            grp += items[j][1]
            j += 1
        if tail + grp > alpha + 1e-12:
            break
        tail += grp
        a_crit = v
        i = j
    return a_crit


def exact_test(cnt, alpha=ALPHA, want_crit=False):
    """Observed A, exact p_high = P(A* >= A), p_low = P(A* <= A) (ties on both sides), and
    (if want_crit) a_crit = the smallest a with P(A* >= a) <= alpha."""
    obs = deltas(cnt)[2]
    tol = 1e-9
    null = sign_flip_null(cnt)
    hi = sum(p for a, p in null if a >= obs - tol)
    lo = sum(p for a, p in null if a <= obs + tol)
    out = {"obs": obs, "p_high": min(1.0, hi), "p_low": min(1.0, lo)}
    if want_crit:
        out["a_crit"] = critical_value(null, alpha, tol)
    return out


def mcnemar_change(cnt):
    """Exact one-sided sign test within change rows: P(X >= b) and P(X <= b), X ~ Bin(b + c, 1/2)."""
    b, c = cnt["C"]["b"], cnt["C"]["c"]
    pm = binom_half(b + c)
    return {"b": b, "c": c, "p_high": min(1.0, sum(pm[b:])), "p_low": min(1.0, sum(pm[:b + 1]))}


# ---------------------------------------------------------------- calibration worlds
def world(P, rng, delta_target):
    """W0: in every pair swap the two scores with probability 1/2. If delta_target > 0, then
    plant carryover as registered in VOWEL3-PREREG.md section 4: among change rows whose first
    click matches, set a mismatch with probability k = min(1, delta_target * nC / #matching)."""
    out = []
    for is_c, mf, ml in P:
        if rng.random() < 0.5:
            mf, ml = ml, mf
        out.append([is_c, mf, ml])
    if delta_target > 0:
        n_c = sum(1 for r in out if r[0])
        zero = [r for r in out if r[0] and r[1] == 0]
        if zero and n_c:
            k = min(1.0, delta_target * n_c / len(zero))
            for r in zero:
                if rng.random() < k:
                    r[1] = 1
    return [tuple(r) for r in out]


def calibrate(P, rng, R, d_full, log=print):
    cal = {"R": R, "delta_full": d_full}
    for name, target in (("W0", 0.0), ("W1_full", d_full), ("W1_half", d_full / 2.0)):
        t0 = time.time()
        fire = rev = mc = 0
        for _ in range(R):
            cnt = counts(world(P, rng, target))
            t = exact_test(cnt)
            fire += int(t["p_high"] <= ALPHA)
            rev += int(t["p_low"] <= ALPHA)
            mc += int(mcnemar_change(cnt)["p_high"] <= ALPHA)
        cal[name] = {"delta": target, "asym_reject": fire / R, "asym_reverse_reject": rev / R,
                     "mcnemar_reject": mc / R}
        log("calibration %s: asym %.3f reverse %.3f mcnemar %.3f (%.0fs)" % (
            name, fire / R, rev / R, mc / R, time.time() - t0))
    return cal


# ---------------------------------------------------------------- verdict
def verdict(repro_ok, n_change, n_nochange, size, p_high, p_low, power_full):
    if n_change < MIN_CHANGE or n_nochange == 0:
        return "INSUFFICIENT_DATA"
    if not repro_ok:
        return "REPRO_FAILED"
    if not (size <= SIZE_MAX):
        return "CALIBRATION_FAILED"
    if p_high <= ALPHA:
        return "CARRYOVER_SPECIFIC"
    if p_low <= ALPHA:
        return "REVERSED_ASYMMETRY"
    if power_full >= POWER_MIN:
        return "SYMMETRIC_WITH_POWER"
    return "UNDERPOWERED"


def run(rows, R=R_CAL, seed=SEED, expected=V1, log=print):
    rng = random.Random(seed)
    P = pairs(rows)
    cnt = counts(P)
    C, N = cnt["C"], cnt["N"]
    got = {"nC": C["n"], "nN": N["n"], "mfC": C["b"] + C["both"], "mfN": N["b"] + N["both"],
           "mlC": C["c"] + C["both"], "mlN": N["c"] + N["both"]}
    repro_ok = expected is None or got == expected
    res = {"n_rows": len(rows), "n_paired": len(P), "counts": cnt,
           "repro": {"expected": expected, "got": got, "ok": repro_ok},
           "settings": {"seed": seed, "R": R, "alpha": ALPHA}}
    if C["n"] < MIN_CHANGE or N["n"] == 0 or not repro_ok:
        res.update(main=None, calibration=None, predictions={}, brier=None,
                   verdict=verdict(repro_ok, C["n"], N["n"], 1.0, 1.0, 1.0, 0.0))
        return res
    df, dl, _ = deltas(cnt)
    t = exact_test(cnt, want_crit=True)
    res["main"] ={"delta_first": df, "delta_last": dl, "asym": t,
                   "k_change": C["b"] + C["c"], "k_nochange": N["b"] + N["c"],
                   "mcnemar_change": mcnemar_change(cnt)}
    log("main: A %.4f p_high %.4f p_low %.4f a_crit %s; discordant change %d, no change %d" % (
        t["obs"], t["p_high"], t["p_low"], t["a_crit"], C["b"] + C["c"], N["b"] + N["c"]))
    cal = calibrate(P, rng, R, max(df, 0.0), log=log)
    res["calibration"] = cal
    size = cal["W0"]["asym_reject"]
    power = cal["W1_full"]["asym_reject"]
    v = verdict(True, C["n"], N["n"], size, t["p_high"], t["p_low"], power)
    res["verdict"] = v
    out = {"Q1": v == "UNDERPOWERED", "Q2": power >= 0.5, "Q3": C["b"] + C["c"] >= 16,
           "Q4": size <= 0.06}
    res["predictions"] = {q: {"prior": PRIORS[q], "outcome": bool(out[q])} for q in sorted(PRIORS)}
    res["brier"] = sum((PRIORS[q] - (1.0 if out[q] else 0.0)) ** 2 for q in PRIORS) / len(PRIORS)
    return res


# ---------------------------------------------------------------- output
def fmt(x, spec="%.4f"):
    return "n/a" if x is None else spec % x


def render(res):
    L = ["# RESULTS-COART-A1: exact symmetry test for sperm whale coda 'coarticulation'", "",
         "Rendered by vowel3b_test.py (VOWEL3-AMENDMENT-1.md) from vowel3b_results.json.",
         "Made with AI agents working in MV2's name (MV2, Munim, Inc.); not yet checked by a human expert.",
         "Data: Project CETI coda-vowel-phonology, %s at %s." % (DATA_NAME, DATA_SHA[:7]),
         "", "## Verdict", "", "**%s**" % res["verdict"], "",
         "Same pairs as job vowel3-coart-v1: %s" % res["repro"]["ok"], ""]
    L += ["| group | pairs | first click only | last click only | both | neither |",
          "|---|---|---|---|---|---|"]
    for g, label in (("C", "vowel change"), ("N", "no change")):
        x = res["counts"][g]
        L.append("| %s | %d | %d | %d | %d | %d |" % (label, x["n"], x["b"], x["c"], x["both"],
                                                     x["neither"]))
    m = res.get("main")
    if m:
        a = m["asym"]
        mc = m["mcnemar_change"]
        L += ["", "## Tests (exact; each discordant pair's sign a fair coin)", "",
              "| quantity | value |", "|---|---|",
              "| Delta_first | %.4f |" % m["delta_first"],
              "| Delta_last | %.4f |" % m["delta_last"],
              "| A = Delta_first - Delta_last | %.4f |" % a["obs"],
              "| exact p_high, p_low | %.4f, %.4f |" % (a["p_high"], a["p_low"]),
              "| smallest A significant at 0.05 | %s |" % fmt(a["a_crit"]),
              "| change rows: first only vs last only | %d vs %d (p_high %.4f) |" % (
                  mc["b"], mc["c"], mc["p_high"])]
        cal = res["calibration"]
        L += ["", "## Calibration (R = %d worlds; planted delta %.4f)" % (cal["R"], cal["delta_full"]), "",
              "| world | A test fires | A reversed | change-row sign test fires |", "|---|---|---|---|"]
        for w in WORLDS:
            x = cal[w]
            L.append("| %s | %.3f | %.3f | %.3f |" % (w, x["asym_reject"], x["asym_reverse_reject"],
                                                    x["mcnemar_reject"]))
        L += ["", "## Predictions", "", "| id | prior | outcome |", "|---|---|---|"]
        for q in sorted(res["predictions"]):
            p = res["predictions"][q]
            L.append("| %s | %.2f | %s |" % (q, p["prior"], p["outcome"]))
        L += ["", "Brier score %.3f." % res["brier"]]
    L.append("")
    return "\n".join(L)


def fetch_data(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, DATA_NAME)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        req = urllib.request.Request(DATA_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            blob = r.read()
        with open(path, "wb") as fh:
            fh.write(blob)
    with open(path, "rb") as fh:
        blob = fh.read()
    return path, hashlib.md5(blob).hexdigest(), len(blob)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    path, md5, size = fetch_data(a.data_dir)
    print("data %s md5 %s bytes %d" % (DATA_NAME, md5, size), flush=True)
    rows, issues = load_rows(path)
    print("issues %s; kept %d" % (json.dumps(issues), len(rows)), flush=True)
    t0 = time.time()
    res = run(rows, log=lambda s: print(s, flush=True))
    res["data"] = {"url": DATA_URL, "md5": md5, "bytes": size, "issues": issues}
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(a.out_dir, "vowel3b_results.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(res, indent=1, sort_keys=True))
    with open(os.path.join(a.out_dir, "RESULTS-COART-A1.md"), "w", encoding="utf-8") as fh:
        fh.write(render(res))
    print(json.dumps({"verdict": res["verdict"], "brier": res["brier"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
