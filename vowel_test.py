# SPDX-License-Identifier: Apache-2.0
# vowel_test.py: the pre-registered test of VOWEL-PREREG.md. Are sperm whale "coda vowels"
# (Begus et al. 2025 Open Mind; 2026 Proc R Soc B) a property of each coda, or do they persist
# through bouts and tag deployments like a state of the moment? Neighbouring codas of one whale
# in one bout are compared with the vowel mix of their (whale, deployment, coda type) strata;
# labels are permuted within those strata; power and size are measured in synthetic "bout" and
# "coda" worlds laid on the real timeline. Only aggregate counts are written (the DSWP timing
# tables have no licence file and are never redistributed).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import os
import sys
import time
from collections import Counter

import numpy as np

from describe_vowels import SOURCES, deployment_of, fetch, file_of, getter, join, read_table

VERSION = "whale-vowel-test-1"
MD5 = {"codamd.csv": "be50098e0e806d6df7cd2144b80d900d",
       "DominicaCodas.csv": "46c2ff249bc6fa327d5bbe596f06be63",
       "sperm-whale-dialogues.csv": "eeeeb20cda64d88320b6ccee1185379a"}
GAP = 60.0
B_PRIMARY = 9999
B_DEP = 9999
R_CAL = 200
B_CAL = 999
EPS_POWER = (0.05, 0.10, 0.20, 0.30)
EPS_MATCH = tuple(round(0.05 * k, 2) for k in range(11))
R_MATCH = 20
ALPHA = 0.05
Q_STRONG = 0.5
SIZE_MAX = 0.10
POWER_MIN = 0.80
POWER_EPS = 0.20
MIN_WB_PAIRS = 200
MIN_DEP_UNITS = 10
GAP_BINS = (("0-10", 0.0, 10.0), ("10-60", 10.0, 60.0), ("60-300", 60.0, 300.0),
            ("300+", 300.0, float("inf")))
SEEDS = {"primary": 20261201, "dep": 20261202, "coda_world": 20261203,
         "bout_world": 20261204, "match": 20261205}
ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PRIORS = {"Q1": 0.70, "Q2": 0.40, "Q3": 0.55, "Q4": 0.85, "Q5": 0.97, "Q6": 0.65, "Q7": 0.05}
CHUNK = 1000


def finite(x):
    return (isinstance(x, (int, float)) and not isinstance(x, bool) and x == x
            and abs(x) != float("inf"))


# ----------------------------------------------------------------------- units and pairs
def build_units(md_h, md_rows, codas):
    """Labelled (a/i), named, uniquely timed codas with a deployment, sorted by whale,
    deployment, file, time, coda number and row."""
    g = getter(md_h)
    units = []
    for i, (row, c) in enumerate(zip(md_rows, codas)):
        lab = g(row, "handv")
        if lab not in ("a", "i") or not c.get("whale") or c.get("join") != "dialogue":
            continue
        if c.get("t") is None:
            continue
        dep = deployment_of(c.get("rec"))
        if dep is None:
            continue
        units.append({"i": i, "whale": c["whale"], "dep": dep,
                      "file": file_of(c.get("rec")) or "", "type": c.get("codatype") or "",
                      "t": float(c["t"]), "y": 1 if lab == "a" else 0,
                      "num": c["codanum"] if c.get("codanum") is not None else -1})
    units.sort(key=lambda u: (u["whale"], u["dep"], u["file"], u["t"], u["num"], u["i"]))
    return units


def same_run(a, b):
    return a["whale"] == b["whale"] and a["dep"] == b["dep"] and a["file"] == b["file"]


def pairs_of(units):
    """Consecutive codas of one whale in one deployment and file: (k - 1, k, gap)."""
    return [(k - 1, k, units[k]["t"] - units[k - 1]["t"]) for k in range(1, len(units))
            if same_run(units[k - 1], units[k])]


def bout_ids(units, gap=GAP):
    """Bout index of every unit: a new bout at a new whale, deployment or file, or after a
    silence longer than gap."""
    ids, cur = [], -1
    for k, u in enumerate(units):
        if k == 0 or not same_run(units[k - 1], u) or u["t"] - units[k - 1]["t"] > gap:
            cur += 1
        ids.append(cur)
    return np.array(ids, dtype=np.int64)


def strata_ids(units, keys):
    index, ids = {}, []
    for u in units:
        k = tuple(u[x] for x in keys)
        if k not in index:
            index[k] = len(index)
        ids.append(index[k])
    return np.array(ids, dtype=np.int64)


# ----------------------------------------------------------------------- statistics
def permute_within(y, strata, n_perm, rng):
    """n_perm label vectors, each a uniformly random permutation of y within strata."""
    n = len(y)
    base = np.argsort(strata, kind="stable")
    keys = strata[None, :] + rng.random((n_perm, n))
    order = np.argsort(keys, axis=1, kind="stable")
    out = np.empty((n_perm, n), dtype=y.dtype)
    out[:, base] = y[order]
    return out


def switches(Y, i1, i2):
    """Number of pairs with differing labels (one vector, or one count per row)."""
    return (Y[..., i1] != Y[..., i2]).sum(axis=-1)


def expected_pairs(y, strata, i1, i2):
    """Exact probability that each pair differs when labels are shuffled within strata."""
    ns = np.bincount(strata).astype(float)
    ks = np.bincount(strata, weights=np.asarray(y, dtype=float), minlength=len(ns))
    sa, sb = strata[i1], strata[i2]
    pa, pb = ks[sa] / ns[sa], ks[sb] / ns[sb]
    across = pa * (1 - pb) + (1 - pa) * pb
    n, k = ns[sa], ks[sa]
    within = 2 * k * (n - k) / (n * np.maximum(n - 1, 1))
    return np.where(sa == sb, within, across)


def expected_switches(y, strata, i1, i2):
    if len(i1) == 0:
        return 0.0
    return float(expected_pairs(y, strata, i1, i2).sum())


def null_switches(y, strata, i1, i2, n_perm, rng):
    out, done = [], 0
    while done < n_perm:
        m = min(CHUNK, n_perm - done)
        out.append(switches(permute_within(y, strata, m, rng), i1, i2))
        done += m
    return np.concatenate(out)


def p_low(obs, null):
    return (1 + int((null <= obs).sum())) / (len(null) + 1)


def p_high(obs, null):
    return (1 + int((null >= obs).sum())) / (len(null) + 1)


def g_setup(units):
    s = strata_ids(units, ("whale", "type"))
    c = strata_ids(units, ("whale", "type", "dep"))
    nc = np.bincount(c).astype(float)
    cell_s = np.zeros(len(nc), dtype=np.int64)
    cell_s[c] = s
    return s, c, nc, cell_s


def _term(O, E):
    safe_o = np.where(O > 0, O, 1.0)
    safe_e = np.where(E > 0, E, 1.0)
    return np.where(O > 0, O * np.log(safe_o / safe_e), 0.0)


def g_values(Y, c, nc, cell_s):
    """Likelihood-ratio G of label by deployment, summed over (whale, coda type) strata,
    for each row of Y."""
    Y2 = np.atleast_2d(np.asarray(Y, dtype=float))
    n = Y2.shape[1]
    M = np.zeros((n, len(nc)))
    M[np.arange(n), c] = 1.0
    S = np.zeros((len(nc), int(cell_s.max()) + 1))
    S[np.arange(len(nc)), cell_s] = 1.0
    Oa = Y2 @ M
    As = (Oa @ S) @ S.T
    Ns = (nc @ S) @ S.T
    Ea = nc[None, :] * As / Ns[None, :]
    Ei = nc[None, :] - Ea
    Oi = nc[None, :] - Oa
    return 2.0 * (_term(Oa, Ea) + _term(Oi, Ei)).sum(axis=1)


def dep_units(units):
    """Units of whales with at least 2 deployments of MIN_DEP_UNITS or more units each."""
    cnt = Counter((u["whale"], u["dep"]) for u in units)
    ok = {k for k, v in cnt.items() if v >= MIN_DEP_UNITS}
    per_whale = Counter(w for w, _ in ok)
    return [u for u in units if (u["whale"], u["dep"]) in ok and per_whale[u["whale"]] >= 2]


# ----------------------------------------------------------------------- synthetic worlds
def sim_coda_world(y, strata, rng):
    ns = np.bincount(strata).astype(float)
    ks = np.bincount(strata, weights=np.asarray(y, dtype=float), minlength=len(ns))
    return (rng.random(len(y)) < (ks / ns)[strata]).astype(np.int8)


def sim_bout_world(y, wd, bouts, eps, rng):
    nw = np.bincount(wd).astype(float)
    kw = np.bincount(wd, weights=np.asarray(y, dtype=float), minlength=len(nw))
    bout_wd = np.zeros(int(bouts.max()) + 1, dtype=np.int64)
    bout_wd[bouts] = wd
    base = (rng.random(len(bout_wd)) < (kw / nw)[bout_wd]).astype(np.int8)
    flip = (rng.random(len(y)) < eps).astype(np.int8)
    return base[bouts] ^ flip


def calibrate(simulate, strata, i1, i2, r, b, rng):
    ps = []
    for _ in range(r):
        ys = simulate(rng)
        ps.append(p_low(int(switches(ys, i1, i2)), null_switches(ys, strata, i1, i2, b, rng)))
    return ps


def reject_rate(ps):
    return sum(1 for p in ps if p <= ALPHA) / len(ps) if ps else float("nan")


# ----------------------------------------------------------------------- decision
def verdict_of(n_wb, e_null, size, pl, q, power20):
    if n_wb < MIN_WB_PAIRS or not (finite(e_null) and e_null > 0):
        return "INSUFFICIENT_DATA"
    if not finite(size) or size > SIZE_MAX:
        return "CALIBRATION_FAILED"
    if finite(pl) and pl <= ALPHA:
        return "VOWELS_CLUSTER_STRONGLY" if q <= Q_STRONG else "VOWELS_CLUSTER_WEAKLY"
    if finite(power20) and power20 >= POWER_MIN:
        return "NO_CLUSTERING_WITH_POWER"
    return "UNDERPOWERED"


def grade(r):
    w, d, c = r["within"], r["deployment_test"], r["calibration"]
    share_w = w["switches"] / r["n_within_bout_pairs"]
    nb = r["n_between_bout_pairs"]
    share_b = r["between"]["switches"] / nb if nb else float("nan")
    pdep = d.get("p")
    pred = {"Q1": w["p_low"] <= ALPHA, "Q2": finite(w["q"]) and w["q"] <= Q_STRONG,
            "Q3": finite(pdep) and pdep <= ALPHA,
            "Q4": c["bout_world"]["%.2f" % POWER_EPS]["power"] >= POWER_MIN,
            "Q5": c["coda_world"]["size"] <= SIZE_MAX,
            "Q6": finite(share_b) and share_b > share_w, "Q7": w["p_high"] <= ALPHA}
    pred = {k: bool(pred[k]) for k in ORDER}
    brier = sum((PRIORS[k] - (1.0 if pred[k] else 0.0)) ** 2 for k in ORDER) / len(ORDER)
    return pred, brier


# ----------------------------------------------------------------------- the analysis
def analyse(units, b_primary=B_PRIMARY, b_dep=B_DEP, r_cal=R_CAL, b_cal=B_CAL,
            r_match=R_MATCH, seeds=None, log=None):
    seeds = dict(SEEDS if seeds is None else seeds)
    say = log or (lambda m: None)
    n = len(units)
    y = np.array([u["y"] for u in units], dtype=np.int8)
    strata = strata_ids(units, ("whale", "dep", "type"))
    prs = pairs_of(units)
    wb = [(a, b) for a, b, dt in prs if dt <= GAP]
    bb = [(a, b) for a, b, dt in prs if dt > GAP]
    i1 = np.array([a for a, _ in wb], dtype=np.int64)
    i2 = np.array([b for _, b in wb], dtype=np.int64)
    j1 = np.array([a for a, _ in bb], dtype=np.int64)
    j2 = np.array([b for _, b in bb], dtype=np.int64)
    ns = np.bincount(strata) if n else np.zeros(0, dtype=np.int64)
    ks = np.bincount(strata, weights=y.astype(float), minlength=len(ns)) if n else ns
    inf = (ks > 0) & (ks < ns)
    bouts = bout_ids(units) if n else np.zeros(0, dtype=np.int64)
    out = {"n_units": n, "n_whales": len({u["whale"] for u in units}),
           "n_deployments": len({(u["whale"], u["dep"]) for u in units}),
           "n_files": len({(u["whale"], u["dep"], u["file"]) for u in units}),
           "n_bouts": int(bouts.max()) + 1 if n else 0,
           "n_strata": int(len(ns)), "informative_strata": int(inf.sum()),
           "units_in_informative_strata": int(ns[inf].sum()),
           "share_a": float(y.mean()) if n else float("nan"),
           "n_pairs": len(prs), "n_within_bout_pairs": len(wb),
           "n_between_bout_pairs": len(bb)}
    e_null = expected_switches(y, strata, i1, i2)
    if len(wb) < MIN_WB_PAIRS or not e_null > 0:
        out.update(verdict="INSUFFICIENT_DATA", predictions=None, brier=None)
        return out
    # primary
    s_obs = int(switches(y, i1, i2))
    nul = null_switches(y, strata, i1, i2, b_primary, np.random.default_rng(seeds["primary"]))
    q = s_obs / e_null
    out["within"] = {"switches": s_obs, "expected": e_null, "q": q,
                     "p_low": p_low(s_obs, nul), "p_high": p_high(s_obs, nul),
                     "B": b_primary, "null_mean": float(nul.mean()),
                     "null_sd": float(nul.std()), "null_min": int(nul.min()),
                     "null_max": int(nul.max())}
    say("primary: S %d E %.3f Q %.4f p_low %.4f" % (s_obs, e_null, q, out["within"]["p_low"]))
    s_b = int(switches(y, j1, j2)) if len(bb) else 0
    e_b = expected_switches(y, strata, j1, j2)
    out["between"] = {"switches": s_b, "expected": e_b,
                      "q": s_b / e_b if e_b > 0 else float("nan")}
    # gap profile (exploratory)
    prof = []
    for name, lo, hi in GAP_BINS:
        sel = [(a, b) for a, b, dt in prs if (dt <= hi if lo == 0.0 else lo < dt <= hi)]
        a1 = np.array([a for a, _ in sel], dtype=np.int64)
        a2 = np.array([b for _, b in sel], dtype=np.int64)
        prof.append({"bin": name, "pairs": len(sel),
                     "switches": int(switches(y, a1, a2)) if sel else 0,
                     "expected": expected_switches(y, strata, a1, a2)})
    out["gap_profile"] = prof
    # per whale (exploratory)
    ep = expected_pairs(y, strata, i1, i2)
    dif = (y[i1] != y[i2])
    pw = {}
    for w in sorted({u["whale"] for u in units}):
        m = np.array([units[a]["whale"] == w for a in i1], dtype=bool)
        pw[w] = {"units": sum(1 for u in units if u["whale"] == w),
                 "within_pairs": int(m.sum()), "switches": int(dif[m].sum()),
                 "expected": float(ep[m].sum())}
    out["per_whale"] = pw
    # secondary: deployments of the same whale
    du = dep_units(units)
    if len({(u["whale"], u["dep"]) for u in du}) >= 2:
        yd = np.array([u["y"] for u in du], dtype=np.int8)
        s, c, nc, cell_s = g_setup(du)
        g_obs = float(g_values(yd, c, nc, cell_s)[0])
        rng = np.random.default_rng(seeds["dep"])
        gn, done = [], 0
        while done < b_dep:
            m = min(CHUNK, b_dep - done)
            gn.append(g_values(permute_within(yd, s, m, rng), c, nc, cell_s))
            done += m
        gn = np.concatenate(gn)
        tol = 1e-9 * max(1.0, abs(g_obs))
        out["deployment_test"] = {
            "whales": sorted({u["whale"] for u in du}),
            "deployments": sorted({"%s/%s" % (u["whale"], u["dep"]) for u in du}),
            "n_units": len(du), "n_cells": int(len(nc)), "g_obs": g_obs, "B": b_dep,
            "p": (1 + int((gn >= g_obs - tol).sum())) / (b_dep + 1),
            "null_mean": float(gn.mean()), "null_q95": float(np.quantile(gn, 0.95))}
    else:
        out["deployment_test"] = {"skipped": "fewer than 2 eligible deployments", "p": None}
    say("deployment test done")
    # calibration
    wd = strata_ids(units, ("whale", "dep"))
    rng = np.random.default_rng(seeds["coda_world"])
    cw = calibrate(lambda g: sim_coda_world(y, strata, g), strata, i1, i2, r_cal, b_cal, rng)
    cal = {"coda_world": {"R": r_cal, "B": b_cal, "p": cw, "size": reject_rate(cw)},
           "bout_world": {}}
    for k, eps in enumerate(EPS_POWER):
        rng = np.random.default_rng(seeds["bout_world"] + k)
        ps = calibrate(lambda g, e=eps: sim_bout_world(y, wd, bouts, e, g), strata, i1, i2,
                       r_cal, b_cal, rng)
        cal["bout_world"]["%.2f" % eps] = {"R": r_cal, "B": b_cal, "p": ps,
                                           "power": reject_rate(ps)}
        say("bout world eps %.2f power %.3f" % (eps, reject_rate(ps)))
    out["calibration"] = cal
    # matching (exploratory)
    mq = []
    for k, eps in enumerate(EPS_MATCH):
        rng = np.random.default_rng(seeds["match"] + k)
        qs = []
        for _ in range(r_match):
            ys = sim_bout_world(y, wd, bouts, eps, rng)
            e = expected_switches(ys, strata, i1, i2)
            if e > 0:
                qs.append(int(switches(ys, i1, i2)) / e)
        mq.append(float(np.mean(qs)) if qs else float("nan"))
    d = [abs(m - q) if finite(m) else float("inf") for m in mq]
    best = min(range(len(d)), key=lambda i: (d[i], i))
    out["match"] = {"eps": list(EPS_MATCH), "mean_q": mq, "R": r_match,
                    "matched_eps": EPS_MATCH[best]}
    out["verdict"] = verdict_of(len(wb), e_null, cal["coda_world"]["size"],
                                out["within"]["p_low"], q,
                                cal["bout_world"]["%.2f" % POWER_EPS]["power"])
    pred, brier = grade(out)
    out["predictions"], out["brier"] = pred, brier
    return out


def settings():
    return {"gap": GAP, "b_primary": B_PRIMARY, "b_dep": B_DEP, "r_cal": R_CAL, "b_cal": B_CAL,
            "eps_power": list(EPS_POWER), "eps_match": list(EPS_MATCH), "r_match": R_MATCH,
            "alpha": ALPHA, "q_strong": Q_STRONG, "size_max": SIZE_MAX,
            "power_min": POWER_MIN, "power_eps": POWER_EPS, "min_wb_pairs": MIN_WB_PAIRS,
            "min_dep_units": MIN_DEP_UNITS, "seeds": dict(SEEDS)}


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        x = float(x)
    if isinstance(x, float) and not finite(x):
        return None
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def synthetic_units(seed=1, whales=4, deps=2, files=2, bouts_per_file=6, bout_len=8,
                    share_a=0.6, eps=None):
    """A synthetic timeline (no real data): codas 5 s apart in bouts 400 s apart. Labels are
    independent (eps None) or one label per bout flipped with probability eps."""
    rng = np.random.default_rng(seed)
    types = ("1+1+3", "5R1", "6i")
    units, i = [], 0
    for w in range(whales):
        for d in range(deps):
            for f in range(files):
                t = 0.0
                for _ in range(bouts_per_file):
                    base = int(rng.random() < share_a)
                    for _ in range(bout_len):
                        if eps is None:
                            lab = int(rng.random() < share_a)
                        else:
                            lab = base ^ int(rng.random() < eps)
                        units.append({"i": i, "whale": "W%d" % w, "dep": "sw%03da" % (100 + d),
                                      "file": "sw%03da%03d" % (100 + d, f + 1),
                                      "type": types[int(rng.integers(0, 3))], "t": t, "y": lab,
                                      "num": i})
                        i += 1
                        t += 5.0
                    t += 400.0
    return units


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--selftest", action="store_true",
                    help="run the full analysis on a synthetic timeline only (no real data)")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()

    def log(m):
        print("%s (%.0fs)" % (m, time.time() - t0), flush=True)

    if a.selftest:
        res = {}
        for name, eps in (("independent", None), ("bout_eps_0.10", 0.10)):
            u = synthetic_units(seed=7, eps=eps)
            res[name] = jsonable(analyse(u, log=log))
            log("selftest %s: verdict %s" % (name, res[name]["verdict"]))
        res["seconds"] = round(time.time() - t0, 1)
        with open(os.path.join(a.out_dir, "vowel_selftest.json"), "w") as f:
            json.dump(res, f, indent=1, sort_keys=True)
        return 0
    if not a.data_dir:
        ap.error("--data-dir is required unless --selftest")
    os.makedirs(a.data_dir, exist_ok=True)

    r = {"version": VERSION, "python": sys.version.split()[0], "numpy": np.__version__,
         "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": {},
         "settings": settings()}
    tables, ok = {}, True
    for name, url in SOURCES.items():
        b, h = fetch(name, url, a.data_dir)
        tables[name] = read_table(b.decode("utf-8-sig", errors="replace"))
        r["files"][name] = {"md5": h, "md5_ok": h == MD5[name], "rows": len(tables[name][1])}
        ok = ok and h == MD5[name]
    r["md5_ok"] = ok
    if not ok:
        r["verdict"] = "DATA_MISMATCH"
    else:
        md, dc, dl = (tables["codamd.csv"], tables["DominicaCodas.csv"],
                      tables["sperm-whale-dialogues.csv"])
        codas, counts = join(md[0], md[1], dc[0], dc[1], dl[0], dl[1])
        r["join_counts"] = counts
        units = build_units(md[0], md[1], codas)
        log("units %d" % len(units))
        r.update(analyse(units, log=log))
    r["seconds"] = round(time.time() - t0, 1)
    r["utc_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    r = jsonable(r)
    with open(os.path.join(a.out_dir, "vowel_results.json"), "w") as f:
        json.dump(r, f, indent=1, sort_keys=True)
    keys = ("verdict", "n_units", "n_within_bout_pairs", "predictions", "brier")
    print(json.dumps({k: r.get(k) for k in keys}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
