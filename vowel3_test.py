#!/usr/bin/env python3
# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made with AI agents working in MV2's name.
"""whale-vowel-test, test 3 (VOWEL3-PREREG.md): is sperm whale coda 'coarticulation' carryover,
or the symmetric pattern that label noise and slowly changing states also produce?

Begus et al. (2026) report that when the vowel changes between two codas, the first click of the
new coda more often mismatches its own coda's vowel label (it looks like the previous coda).
Carryover predicts that only the FIRST click of the new coda is affected. If the labels are noisy
or the state changes mid-coda, the LAST click of the previous coda should mismatch its own label
just as often at a change. This script measures both, on the same coda pairs, and their
difference.

Usage: python vowel3_test.py --data-dir /data/coart --out-dir /out
Outputs: vowel3_results.json and RESULTS-COART.md in --out-dir.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
import urllib.request

import numpy as np

DATA_SHA = "be751b8761c87813754dba10ad7068a9e71367c0"
DATA_NAME = "focal-coarticulation-metadata.csv"
DATA_URL = ("https://raw.githubusercontent.com/Project-CETI/coda-vowel-phonology/"
            + DATA_SHA + "/" + DATA_NAME)
WHALES = ("PINCHY", "FORK", "ATWOOD", "TBB")
SEED = 20261121
B_MAIN = 9999
R_CAL = 200
B_CAL = 999
MIN_CHANGE = 10
PRIORS = {"P1": 0.75, "P2": 0.55, "P3": 0.65, "P4": 0.90, "P5": 0.55, "P6": 0.40}
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com)"
STATS = ("first", "last", "asym")


# ---------------------------------------------------------------- parsing
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
    """The authors' 'match' variable (1 = mismatch): a with 1 peak or i with 2 peaks -> 0,
    a with 2 peaks or i with 1 peak -> 1, anything else -> None (NA)."""
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
    """The authors' 'type': aa, ii -> no change (N); ia, ai -> change (C); else None."""
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
              "no_type": 0, "coart_conflicts": 0}
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
        coart = (r.get("coart") or "").strip()
        t = change_type(coart)
        if t is None:
            issues["no_type"] += 1
            continue
        pv = (r.get("prevhandvcat") or "").strip()
        v = (r.get("handvcat") or "").strip()
        if pv + v != coart:
            issues["coart_conflicts"] += 1
        rows.append({"whale": whale, "dep": whale + "|" + (r.get("tagondt") or "").strip(),
                     "type": t, "coart": coart, "deltasec": ds,
                     "mf": mismatch(v, to_int(r.get("numpks", ""))),
                     "ml": mismatch(pv, to_int(r.get("prevnumpks", "")))})
    return rows, issues


def paired(rows):
    """Rows where both the first click (mf) and the previous coda's last click (ml) are scored."""
    P = [r for r in rows if r["mf"] is not None and r["ml"] is not None]
    deps = sorted(set(r["dep"] for r in P))
    di = {d: i for i, d in enumerate(deps)}
    s = np.array([di[r["dep"]] for r in P], dtype=int)
    c = np.array([r["type"] == "C" for r in P], dtype=bool)
    mf = np.array([r["mf"] for r in P], dtype=float)
    ml = np.array([r["ml"] for r in P], dtype=float)
    gap = np.array([r["deltasec"] for r in P], dtype=float)
    return P, s, c, mf, ml, gap, deps


# ---------------------------------------------------------------- statistics
def delta(y, c):
    """Mean of y over change rows minus mean over no-change rows."""
    y = np.asarray(y, dtype=float)
    c = np.asarray(c, dtype=bool)
    nC = int(c.sum())
    nN = len(c) - nC
    if nC == 0 or nN == 0:
        return float("nan")
    return float(y[c].mean() - y[~c].mean())


def perm_null(ys, s, c, rng, B):
    """Null deltas (shape len(ys) x B) when the change/no-change labels are permuted within
    each stratum (tag deployment). Every vector in ys uses the same permutations."""
    c = np.asarray(c, dtype=bool)
    s = np.asarray(s)
    Y = np.vstack([np.asarray(y, dtype=float) for y in ys])
    n = len(c)
    nC = int(c.sum())
    nN = n - nC
    tot = Y.sum(axis=1)
    sumC = np.zeros((Y.shape[0], B))
    for st in np.unique(s):
        idx = np.flatnonzero(s == st)
        m = len(idx)
        cs = int(c[idx].sum())
        if cs == 0:
            continue
        sub = Y[:, idx]
        if cs == m:
            sumC += sub.sum(axis=1)[:, None]
            continue
        pick = np.argsort(rng.random((B, m)), axis=1)[:, :cs]
        sumC += sub[:, pick].sum(axis=2)
    return sumC / nC - (tot[:, None] - sumC) / nN


def p_low(null, obs):
    null = np.asarray(null, dtype=float)
    tol = 1e-9 * max(1.0, abs(float(obs)))
    return (1 + int((null <= obs + tol).sum())) / (len(null) + 1)


def p_high(null, obs):
    null = np.asarray(null, dtype=float)
    tol = 1e-9 * max(1.0, abs(float(obs)))
    return (1 + int((null >= obs - tol).sum())) / (len(null) + 1)


def summarise(null, obs):
    null = np.asarray(null, dtype=float)
    return {"obs": float(obs), "null_mean": float(null.mean()),
            "null_sd": float(null.std(ddof=1)) if len(null) > 1 else 0.0,
            "p_low": p_low(null, obs), "p_high": p_high(null, obs), "B": int(len(null))}


def tests(mf, ml, s, c, rng, B):
    """first: delta of first-click mismatch; last: delta of last-click mismatch;
    asym: delta of (first - last) = first - last."""
    mf = np.asarray(mf, dtype=float)
    ml = np.asarray(ml, dtype=float)
    d = mf - ml
    obs = (delta(mf, c), delta(ml, c), delta(d, c))
    null = perm_null([mf, ml, d], s, c, rng, B)
    return {name: summarise(null[j], obs[j]) for j, name in enumerate(STATS)}


# ---------------------------------------------------------------- calibration worlds
def world_swap(mf, ml, rng):
    """Symmetric world: in each pair, swap the first-click and last-click scores with prob. 1/2."""
    mf = np.asarray(mf, dtype=float)
    ml = np.asarray(ml, dtype=float)
    sw = rng.random(len(mf)) < 0.5
    return np.where(sw, ml, mf), np.where(sw, mf, ml)


def plant(mf, c, delta_target, rng):
    """Carryover world: among change rows whose first click matches, make it mismatch with
    probability k = delta_target / (share of change rows with a matching first click)."""
    out = np.asarray(mf, dtype=float).copy()
    c = np.asarray(c, dtype=bool)
    zero = np.flatnonzero(c & (out == 0))
    nC = int(c.sum())
    if not (delta_target > 0) or len(zero) == 0 or nC == 0:
        return out
    k = min(1.0, delta_target * nC / len(zero))
    hit = rng.random(len(zero)) < k
    out[zero[hit]] = 1.0
    return out


def calibrate(mf, ml, s, c, rng, R, B, d_full, log=print):
    cal = {"R": R, "B": B, "delta_full": d_full}
    for name, dtarget in (("W0", 0.0), ("W1_full", d_full), ("W1_half", d_full / 2.0)):
        t0 = time.time()
        ra = rr = rf = 0
        for _ in range(R):
            a, b = world_swap(mf, ml, rng)
            a = plant(a, c, dtarget, rng)
            res = tests(a, b, s, c, rng, B)
            ra += int(res["asym"]["p_high"] <= 0.05)
            rr += int(res["asym"]["p_low"] <= 0.05)
            rf += int(res["first"]["p_high"] <= 0.05)
        nan = float("nan")
        cal[name] = {"delta": dtarget,
                     "asym_reject": ra / R if R else nan,
                     "asym_reverse_reject": rr / R if R else nan,
                     "first_reject": rf / R if R else nan}
        log("calibration %s: asym %.3f reverse %.3f first %.3f (%.0fs)" % (
            name, cal[name]["asym_reject"], cal[name]["asym_reverse_reject"],
            cal[name]["first_reject"], time.time() - t0))
    return cal


# ---------------------------------------------------------------- verdicts
def verdict(n_change, first_p_high, first_obs, asym_p_high, asym_p_low, size, power_full):
    if n_change < MIN_CHANGE:
        return "INSUFFICIENT_DATA"
    if not (first_obs > 0) or first_p_high > 0.05:
        return "NOT_REPRODUCED"
    if not (size <= 0.10):
        return "CALIBRATION_FAILED"
    if asym_p_high <= 0.05:
        return "CARRYOVER_SPECIFIC"
    if asym_p_low <= 0.05:
        return "REVERSED_ASYMMETRY"
    if power_full >= 0.8:
        return "SYMMETRIC_WITH_POWER"
    return "UNDERPOWERED"


def rate_table(rows, key):
    out = {}
    for t in ("C", "N"):
        v = [r[key] for r in rows if r["type"] == t and r[key] is not None]
        out[t] = {"n": len(v), "mismatches": int(sum(v)),
                  "rate": (sum(v) / len(v)) if v else None}
    return out


def run(rows, B=B_MAIN, R=R_CAL, Bc=B_CAL, seed=SEED, log=print):
    rng = np.random.default_rng(seed)
    P, s, c, mf, ml, gap, deps = paired(rows)
    nC = int(c.sum())
    res = {"n_rows": len(rows), "n_paired": len(P), "n_change": nC, "n_nochange": len(P) - nC,
           "n_deployments": len(deps), "n_whales": len(set(r["whale"] for r in P)),
           "t0": {"first_all_rows": rate_table(rows, "mf"), "last_all_rows": rate_table(rows, "ml"),
                  "first_paired": rate_table(P, "mf"), "last_paired": rate_table(P, "ml")},
           "change_by_whale": {}, "deployments": {}}
    for r in P:
        w = res["change_by_whale"].setdefault(r["whale"], {"C": 0, "N": 0})
        w[r["type"]] += 1
        d = res["deployments"].setdefault(r["dep"], {"C": 0, "N": 0})
        d[r["type"]] += 1
    if nC == 0 or nC == len(P):
        res["main"] = None
        res["calibration"] = None
        res["verdict"] = "INSUFFICIENT_DATA"
        res["flags"] = {}
        res["predictions"] = {}
        res["brier"] = None
        res["settings"] = {"seed": seed, "B": B, "R": R, "B_cal": Bc}
        return res
    t_start = time.time()
    main_t = tests(mf, ml, s, c, rng, B)
    res["main"] = main_t
    log("main: first %.4f (p_high %.4f) last %.4f (p_high %.4f) asym %.4f (p_high %.4f, p_low %.4f) (%.0fs)" % (
        main_t["first"]["obs"], main_t["first"]["p_high"], main_t["last"]["obs"],
        main_t["last"]["p_high"], main_t["asym"]["obs"], main_t["asym"]["p_high"],
        main_t["asym"]["p_low"], time.time() - t_start))
    med = float(np.median(gap))
    halves = {}
    for name, sel in (("gap_le_median", gap <= med), ("gap_gt_median", gap > med)):
        halves[name] = {"n": int(sel.sum()), "n_change": int((c & sel).sum()),
                        "first": delta(mf[sel], c[sel]), "last": delta(ml[sel], c[sel])}
    res["gap_halves"] = {"median_deltasec": med, "halves": halves}
    d_full = max(main_t["first"]["obs"], 0.0)
    cal = calibrate(mf, ml, s, c, rng, R, Bc, d_full, log=log)
    res["calibration"] = cal
    size = cal["W0"]["asym_reject"]
    power_full = cal["W1_full"]["asym_reject"]
    v = verdict(nC, main_t["first"]["p_high"], main_t["first"]["obs"], main_t["asym"]["p_high"],
                main_t["asym"]["p_low"], size, power_full)
    res["verdict"] = v
    res["flags"] = {"LAST_CLICK_ALSO_MISMATCHES": bool(main_t["last"]["obs"] > 0
                                                       and main_t["last"]["p_high"] <= 0.05)}
    outcomes = {"P1": bool(main_t["first"]["obs"] > 0 and main_t["first"]["p_high"] <= 0.05),
                "P2": bool(main_t["last"]["obs"] > 0 and main_t["last"]["p_high"] <= 0.05),
                "P3": v != "CARRYOVER_SPECIFIC",
                "P4": bool(size <= 0.10),
                "P5": bool(cal["W0"]["first_reject"] >= 0.5),
                "P6": bool(power_full >= 0.8)}
    res["predictions"] = {q: {"prior": PRIORS[q], "outcome": outcomes[q]} for q in PRIORS}
    res["brier"] = float(np.mean([(PRIORS[q] - float(outcomes[q])) ** 2 for q in PRIORS]))
    res["settings"] = {"seed": seed, "B": B, "R": R, "B_cal": Bc}
    return res


# ---------------------------------------------------------------- output
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return f if math.isfinite(f) else None
    return o


def fmt(x, spec="%.4f"):
    if x is None:
        return "n/a"
    return spec % x


def render(res):
    L = ["# RESULTS-COART: is sperm whale coda 'coarticulation' carryover or symmetric?", "",
         "Rendered by vowel3_test.py from vowel3_results.json (pre-registration VOWEL3-PREREG.md).",
         "Made with AI agents working in MV2's name (MV2, Munim, Inc.); not yet checked by a human expert.",
         "Data: Project CETI coda-vowel-phonology, focal-coarticulation-metadata.csv at %s." % DATA_SHA[:7],
         "", "## Verdict", "", "**%s**" % res["verdict"], ""]
    L += ["| quantity | value |", "|---|---|",
          "| rows after the authors' filters | %d |" % res["n_rows"],
          "| pairs with both clicks scored | %d |" % res["n_paired"],
          "| change pairs, no-change pairs | %d, %d |" % (res["n_change"], res["n_nochange"]),
          "| whales, tag deployments | %d, %d |" % (res["n_whales"], res["n_deployments"])]
    t0 = res["t0"]
    L += ["", "## Mismatch rates", "",
          "| click | rows | change: mismatches / n | no change: mismatches / n |", "|---|---|---|---|"]
    for label, key in (("first click of coda", "first_all_rows"), ("last click of previous coda", "last_all_rows"),
                       ("first click of coda", "first_paired"), ("last click of previous coda", "last_paired")):
        t = t0[key]
        L.append("| %s | %s | %d / %d (%s) | %d / %d (%s) |" % (
            label, "paired" if key.endswith("paired") else "all", t["C"]["mismatches"], t["C"]["n"],
            fmt(t["C"]["rate"], "%.3f"), t["N"]["mismatches"], t["N"]["n"], fmt(t["N"]["rate"], "%.3f")))
    m = res.get("main")
    if m:
        L += ["", "## Tests (change labels permuted within tag deployments, B = %d)" % m["first"]["B"], "",
              "| statistic | observed | null mean | p_high | p_low |", "|---|---|---|---|---|"]
        for label, key in (("first-click mismatch, change minus no change", "first"),
                           ("last-click mismatch, change minus no change", "last"),
                           ("asymmetry A = first minus last", "asym")):
            t = m[key]
            L.append("| %s | %.4f | %.4f | %.4f | %.4f |" % (label, t["obs"], t["null_mean"],
                                                           t["p_high"], t["p_low"]))
        L += ["", "Flag LAST_CLICK_ALSO_MISMATCHES: %s" % res["flags"]["LAST_CLICK_ALSO_MISMATCHES"]]
        g = res["gap_halves"]
        L += ["", "Descriptive, by inter-coda gap (median %.3f s):" % g["median_deltasec"], "",
              "| gap | pairs | change pairs | first delta | last delta |", "|---|---|---|---|---|"]
        for name in ("gap_le_median", "gap_gt_median"):
            h = g["halves"][name]
            L.append("| %s | %d | %d | %s | %s |" % (name.replace("_", " "), h["n"], h["n_change"],
                                                     fmt(h["first"]), fmt(h["last"])))
        cal = res["calibration"]
        L += ["", "## Calibration (R = %d worlds, B = %d; planted delta %.4f)" % (
            cal["R"], cal["B"], cal["delta_full"]), "",
            "| world | A test fires (p_high) | A reversed (p_low) | published-style first-click test fires |",
            "|---|---|---|---|"]
        for name in ("W0", "W1_full", "W1_half"):
            w = cal[name]
            L.append("| %s | %s | %s | %s |" % (name, fmt(w["asym_reject"], "%.3f"),
                                               fmt(w["asym_reverse_reject"], "%.3f"),
                                               fmt(w["first_reject"], "%.3f")))
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
    res = clean(res)
    with open(os.path.join(a.out_dir, "vowel3_results.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(res, indent=1, sort_keys=True))
    with open(os.path.join(a.out_dir, "RESULTS-COART.md"), "w", encoding="utf-8") as fh:
        fh.write(render(res))
    print(json.dumps({"verdict": res["verdict"], "flags": res["flags"], "brier": res["brier"]}),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
