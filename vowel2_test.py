# SPDX-License-Identifier: Apache-2.0
# vowel2_test.py: the pre-registered test of VOWEL2-PREREG.md. Begus, Dabkowski, Sprouse, Gruber
# & Gero (2026, Proc R Soc B 293:20252994) report that sperm whale a-coda vowels are longer than
# i-coda vowels ("short and long vowels"), and that i-vowel durations are bimodal. Their models
# (PhonologyCodaVowel.R, github.com/Project-CETI/coda-vowel-phonology) treat codas as independent
# apart from a whale effect. Our earlier registered test (VOWEL-PREREG.md, RESULTS-VOWEL.md) found
# that vowels persist through bouts and differ between tag deployments of one whale. This test
# asks whether the duration difference holds between a- and i-codas of the SAME bout (or, if bouts
# are too few, the same tag deployment), how often the published-style analysis raises a false
# alarm when vowels are clustered by bout and have no effect at all, and whether the short/long
# split of i-vowels is itself clustered in time. Only aggregate numbers are written (the DSWP
# timing tables have no licence file and are never redistributed).
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import json
import os
import sys
import time

import numpy as np

from describe_vowels import SOURCES, deployment_of, fetch, file_of, fnum, getter, join, read_table
from vowel_test import (MD5, bout_ids, dep_units, expected_switches, finite, g_setup, g_values,
                        jsonable, null_switches, p_low, permute_within, sim_bout_world, strata_ids)

VERSION = "whale-vowel2-test-1"
FOUR = ("ATWOOD", "FORK", "PINCHY", "TBB")
CODA_TYPE = "1+1+3"
B_MAIN = 9999
B_ROT = 9999
R_CAL = 200
B_CAL = 999
EPS_SIM = 0.05
ALPHA = 0.05
SIZE_MAX = 0.10
POWER_MIN = 0.80
MIN_GROUPS = 5
MIN_MINORITY = 15
SHRINK = 0.5
Q_STRONG = 0.5
POWER_FRACTIONS = (("1.0", 1.0), ("0.5", 0.5))
SEEDS = {"naive_pub": 20261211, "naive_timed": 20261212, "dep": 20261213, "bout": 20261214,
         "rot": 20261215, "size": 20261216, "power": 20261217, "false_alarm": 20261218,
         "mode": 20261219, "mode_dep": 20261220}
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
PRIORS = {"P1": 0.80, "P2": 0.35, "P3": 0.50, "P4": 0.90, "P5": 0.75, "P6": 0.60, "P7": 0.55,
          "P8": 0.60}
CETI_URL = ("https://raw.githubusercontent.com/Project-CETI/coda-vowel-phonology/"
            "be751b8761c87813754dba10ad7068a9e71367c0/codamd.csv")
LEVEL_KEY = {"bout": "within_bout", "deployment": "within_dep"}
LEVEL_NAME = {"bout": "BOUTS", "deployment": "DEPLOYMENTS"}
TOL = 1e-9
CHUNK = 1000


# ----------------------------------------------------------------------- units
def vowel_of(s):
    """The R script's rule: a label starting with 'a' is a (1), with 'i' is i (0), else None."""
    s = (s or "").strip()
    if s.startswith("a"):
        return 1
    if s.startswith("i"):
        return 0
    return None


def build(md_h, md_rows, codas):
    """pub: the published duration subset (1+1+3 codas of the four whales with a vowel and a
    duration). timed: every vowel-labelled, named, uniquely timed coda with a deployment, sorted
    by whale, deployment, file, time, coda number and row, with its bout. dset: the timed codas
    of the published subset."""
    g = getter(md_h)
    pub, timed = [], []
    for i, (row, c) in enumerate(zip(md_rows, codas)):
        y = vowel_of(g(row, "handv"))
        whale = g(row, "whale")
        if y is None or not whale:
            continue
        u = {"i": i, "whale": whale, "type": g(row, "codatype"), "y": y,
             "dur": fnum(g(row, "Duration"))}
        if u["type"] == CODA_TYPE and whale in FOUR and u["dur"] is not None:
            pub.append(u)
        if c.get("join") == "dialogue" and c.get("t") is not None:
            dep = deployment_of(c.get("rec"))
            if dep is not None:
                timed.append(dict(u, dep=dep, file=file_of(c.get("rec")) or "",
                                  t=float(c["t"]), date=c.get("date") or "",
                                  num=c["codanum"] if c.get("codanum") is not None else -1))
    timed.sort(key=lambda u: (u["whale"], u["dep"], u["file"], u["t"], u["num"], u["i"]))
    if timed:
        for u, k in zip(timed, bout_ids(timed)):
            u["bout"] = int(k)
    dset = [u for u in timed if u["type"] == CODA_TYPE and u["whale"] in FOUR
            and u["dur"] is not None]
    return pub, timed, dset


# ----------------------------------------------------------------------- the contrast
def contrast_setup(y, dur, groups):
    """Constants of D = sum_g W_g (mean_a,g - mean_i,g) / sum_g W_g with W_g = n_a n_i / n, over
    groups holding both vowels. D = (sum of durations of a-codas in those groups - K) / W, which
    stays exact for any relabelling that keeps every group's count of a."""
    y = np.asarray(y, dtype=float)
    dur = np.asarray(dur, dtype=float)
    groups = np.asarray(groups, dtype=np.int64)
    ng = np.bincount(groups).astype(float)
    na = np.bincount(groups, weights=y, minlength=len(ng))
    sg = np.bincount(groups, weights=dur, minlength=len(ng))
    inf = (na > 0) & (na < ng)
    safe = np.maximum(ng, 1.0)
    w = np.where(inf, na * (ng - na) / safe, 0.0)
    k = np.where(inf, na * sg / safe, 0.0)
    return {"mask": inf[groups], "W": float(w.sum()), "K": float(k.sum()),
            "groups": int(inf.sum()), "minority": int(np.minimum(na, ng - na)[inf].sum()),
            "units": int(ng[inf].sum())}


def contrast(Y, dur, s):
    """D for one label vector, or for each row of a label matrix with the same group counts."""
    dm = np.where(s["mask"], np.asarray(dur, dtype=float), 0.0)
    return (np.asarray(Y, dtype=float) @ dm - s["K"]) / s["W"]


def p_pair(d, nul):
    tol = TOL * max(1.0, abs(d))
    b = len(nul)
    return ((1 + int((nul >= d - tol).sum())) / (b + 1),
            (1 + int((nul <= d + tol).sum())) / (b + 1))


def perm_test(y, dur, groups, b, rng):
    """D and its permutation p values (labels shuffled within groups). With no group holding
    both vowels there is no test: d None and both p = 1."""
    y = np.asarray(y, dtype=np.int8)
    groups = np.asarray(groups, dtype=np.int64)
    s = contrast_setup(y, dur, groups)
    out = {"B": b, "groups": s["groups"], "minority": s["minority"], "units": s["units"],
           "weight": s["W"]}
    if s["groups"] == 0:
        out.update(d=None, p_high=1.0, p_low=1.0, null_mean=None, null_sd=None)
        return out
    d = float(contrast(y, dur, s))
    parts, done = [], 0
    while done < b:
        m = min(CHUNK, b - done)
        parts.append(contrast(permute_within(y, groups, m, rng), dur, s))
        done += m
    nul = np.concatenate(parts)
    ph, pl = p_pair(d, nul)
    out.update(d=d, p_high=ph, p_low=pl, null_mean=float(nul.mean()), null_sd=float(nul.std()))
    return out


def group_index(groups):
    groups = np.asarray(groups, dtype=np.int64)
    return [ix for ix in (np.flatnonzero(groups == g) for g in np.unique(groups)) if len(ix) > 1]


def rotate_within(y, idx, rng):
    """Each group's label sequence (in time order) turned by a uniform random offset."""
    out = np.array(y, dtype=np.int8, copy=True)
    for ix in idx:
        out[ix] = np.roll(out[ix], int(rng.integers(0, len(ix))))
    return out


def rotation_p(y, dur, groups, b, rng):
    """p_high of the observed D against b rotations of the labels within groups (runs kept)."""
    y = np.asarray(y, dtype=np.int8)
    s = contrast_setup(y, dur, groups)
    if s["groups"] == 0:
        return 1.0
    d = float(contrast(y, dur, s))
    idx = group_index(groups)
    vals = np.array([contrast(rotate_within(y, idx, rng), dur, s) for _ in range(b)])
    return p_pair(d, vals)[0]


def rate(ps):
    return sum(1 for p in ps if p <= ALPHA) / len(ps) if ps else float("nan")


# ----------------------------------------------------------------------- i-vowel length modes
def split_point(x):
    """Threshold of the exact two-means split of the values (each part at least 2 values):
    the midpoint between the last short and the first long value. None if fewer than 4 values
    or no split between distinct values."""
    xs = np.sort(np.asarray(x, dtype=float))
    n = len(xs)
    if n < 4:
        return None
    cs, cs2 = np.cumsum(xs), np.cumsum(xs * xs)
    best, bk = None, None
    for k in range(2, n - 1):
        if not xs[k - 1] < xs[k]:
            continue
        s1, s2 = cs[k - 1], cs[-1] - cs[k - 1]
        ss = (cs2[k - 1] - s1 * s1 / k) + (cs2[-1] - cs2[k - 1] - s2 * s2 / (n - k))
        if best is None or ss < best - 1e-12:
            best, bk = ss, k
    return None if bk is None else float((xs[bk - 1] + xs[bk]) / 2.0)


def dip_of(x):
    """Hartigan's dip and its table p value (pip package diptest), or (None, None, reason)."""
    try:
        import diptest
    except ImportError as e:
        return None, None, "diptest not installed: %s" % e
    d, p = diptest.diptest(np.asarray(x, dtype=float))
    return float(d), float(p), None


def mode_analysis(pub, dset, b, seeds):
    per = {}
    th = {}
    for w in FOUR:
        x = [u["dur"] for u in pub if u["whale"] == w and u["y"] == 0]
        t = split_point(x)
        d, p, err = dip_of(x) if len(x) >= 4 else (None, None, "fewer than 4 i-codas")
        per[w] = {"n_i": len(x), "threshold": t,
                  "n_long": sum(1 for v in x if t is not None and v > t),
                  "mean_short": float(np.mean([v for v in x if v <= t])) if t is not None else None,
                  "mean_long": float(np.mean([v for v in x if v > t])) if t is not None else None,
                  "dip": d, "dip_p": p}
        if err:
            per[w]["dip_note"] = err
        th[w] = t
    iset = [dict(u, y=int(u["dur"] > th[u["whale"]])) for u in dset
            if u["y"] == 0 and th.get(u["whale"]) is not None]
    out = {"per_whale": per, "n_timed_i": len(iset)}
    prs = [(k - 1, k) for k in range(1, len(iset)) if iset[k - 1]["bout"] == iset[k]["bout"]]
    if len(iset) >= 2 and prs:
        ym = np.array([u["y"] for u in iset], dtype=np.int8)
        st = strata_ids(iset, ("whale", "dep"))
        i1 = np.array([a for a, _ in prs], dtype=np.int64)
        i2 = np.array([c for _, c in prs], dtype=np.int64)
        e = expected_switches(ym, st, i1, i2)
        s_obs = int((ym[i1] != ym[i2]).sum())
        if e > 0:
            nul = null_switches(ym, st, i1, i2, b, np.random.default_rng(seeds["mode"]))
            out["persistence"] = {"pairs": len(prs), "switches": s_obs, "expected": e,
                                  "q": s_obs / e, "p_low": p_low(s_obs, nul), "B": b}
        else:
            out["persistence"] = {"skipped": "no expected switches", "pairs": len(prs),
                                  "p_low": None}
    else:
        out["persistence"] = {"skipped": "no within-bout pairs", "pairs": 0, "p_low": None}
    du = dep_units(iset)
    if len({(u["whale"], u["dep"]) for u in du}) >= 2:
        yd = np.array([u["y"] for u in du], dtype=np.int8)
        s, c, nc, cell_s = g_setup(du)
        g_obs = float(g_values(yd, c, nc, cell_s)[0])
        rng = np.random.default_rng(seeds["mode_dep"])
        gn, done = [], 0
        while done < b:
            m = min(CHUNK, b - done)
            gn.append(g_values(permute_within(yd, s, m, rng), c, nc, cell_s))
            done += m
        gn = np.concatenate(gn)
        tol = 1e-9 * max(1.0, abs(g_obs))
        out["deployment"] = {"whales": sorted({u["whale"] for u in du}),
                             "deployments": sorted({"%s/%s" % (u["whale"], u["dep"]) for u in du}),
                             "n_units": len(du), "g_obs": g_obs, "B": b,
                             "p": (1 + int((gn >= g_obs - tol).sum())) / (b + 1),
                             "null_mean": float(gn.mean())}
    else:
        out["deployment"] = {"skipped": "fewer than 2 eligible deployments", "p": None}
    return out, th


# ----------------------------------------------------------------------- decision
def level_of(tests):
    for lv in ("bout", "deployment"):
        t = tests[LEVEL_KEY[lv]]
        if t["groups"] >= MIN_GROUPS and t["minority"] >= MIN_MINORITY:
            return lv
    return None


def verdict_of(level, reproduced, size, p_high, p_lo, power1):
    if level is None:
        return "INSUFFICIENT_DATA"
    if not reproduced:
        return "NOT_REPRODUCED"
    sfx = "_WITHIN_" + LEVEL_NAME[level]
    if not finite(size) or size > SIZE_MAX:
        return "CALIBRATION_FAILED" + sfx
    if p_high <= ALPHA:
        return "DURATION_DIFFERENCE" + sfx
    if p_lo <= ALPHA:
        return "REVERSED" + sfx
    if finite(power1) and power1 >= POWER_MIN:
        return "NO_DIFFERENCE_WITH_POWER" + sfx
    return "UNDERPOWERED" + sfx


def grade(r):
    t = r["tests"]
    lv = r["level"]
    tl = t[LEVEL_KEY[lv]] if lv else None
    cal = r.get("calibration") or {}
    size = rate(cal["size"]["p"]) if cal.get("size") else float("nan")
    pw = cal.get("power") or {}
    power1 = rate(pw["1.0"]["p"]) if "1.0" in pw else float("nan")
    fa = cal.get("false_alarm")
    f_naive = rate(fa["naive_p_high"]) if fa else float("nan")
    npub = t["naive_pub"]
    reproduced = npub["d"] is not None and npub["d"] > 0 and npub["p_high"] <= ALPHA
    dnt = t["naive_timed"]["d"]
    m = r["modes"]
    per, dep = m["persistence"], m["deployment"]
    pred = {"P1": reproduced,
            "P2": tl is not None and tl["p_high"] <= ALPHA,
            "P3": finite(power1) and power1 >= POWER_MIN,
            "P4": finite(size) and size <= SIZE_MAX,
            "P5": finite(f_naive) and f_naive > SIZE_MAX,
            "P6": (tl is not None and tl["d"] is not None and dnt is not None and dnt > 0
                   and tl["d"] < SHRINK * dnt),
            "P7": (per.get("p_low") is not None and per["p_low"] <= ALPHA
                   and per["q"] <= Q_STRONG),
            "P8": dep.get("p") is not None and dep["p"] <= ALPHA}
    pred = {k: bool(pred[k]) for k in ORDER}
    brier = sum((PRIORS[k] - (1.0 if pred[k] else 0.0)) ** 2 for k in ORDER) / len(ORDER)
    v = verdict_of(lv, reproduced, size, tl["p_high"] if tl else 1.0,
                   tl["p_low"] if tl else 1.0, power1)
    return v, pred, brier


# ----------------------------------------------------------------------- the analysis
def describe_deployments(dset, th):
    rows = {}
    for u in dset:
        k = (u["whale"], u["dep"])
        x = rows.setdefault(k, {"whale": k[0], "dep": k[1], "dates": set(), "a": [], "i": [],
                                "bouts": set()})
        x["dates"].add(u.get("date") or "")
        x["bouts"].add(u["bout"])
        x["a" if u["y"] == 1 else "i"].append(u["dur"])
    out = []
    for k in sorted(rows):
        x = rows[k]
        t = th.get(k[0])
        ds = sorted(d for d in x["dates"] if d)
        out.append({"whale": k[0], "dep": k[1], "first_date": ds[0] if ds else "",
                    "bouts": len(x["bouts"]), "n_a": len(x["a"]), "n_i": len(x["i"]),
                    "mean_a": float(np.mean(x["a"])) if x["a"] else None,
                    "mean_i": float(np.mean(x["i"])) if x["i"] else None,
                    "n_i_long": sum(1 for v in x["i"] if t is not None and v > t)})
    return out


def analyse(pub, dset, b_main=B_MAIN, b_rot=B_ROT, r_cal=R_CAL, b_cal=B_CAL, seeds=None,
            log=None):
    seeds = dict(SEEDS if seeds is None else seeds)
    say = log or (lambda m: None)
    rng_of = np.random.default_rng
    out = {"n_pub": len(pub), "n_pub_a": sum(u["y"] for u in pub), "n_dur": len(dset),
           "n_dur_a": sum(u["y"] for u in dset),
           "n_bouts_dur": len({u["bout"] for u in dset}),
           "n_deployments_dur": len({(u["whale"], u["dep"]) for u in dset})}
    pw = {}
    for w in FOUR:
        a = [u["dur"] for u in pub if u["whale"] == w and u["y"] == 1]
        i = [u["dur"] for u in pub if u["whale"] == w and u["y"] == 0]
        pw[w] = {"n_a": len(a), "n_i": len(i), "mean_a": float(np.mean(a)) if a else None,
                 "mean_i": float(np.mean(i)) if i else None}
    out["per_whale"] = pw
    yp = np.array([u["y"] for u in pub], dtype=np.int8)
    dp = np.array([u["dur"] for u in pub], dtype=float)
    y = np.array([u["y"] for u in dset], dtype=np.int8)
    d = np.array([u["dur"] for u in dset], dtype=float)
    gw = strata_ids(dset, ("whale",))
    groups = {"bout": strata_ids(dset, ("bout",)), "deployment": strata_ids(dset, ("whale", "dep"))}
    t = {"naive_pub": perm_test(yp, dp, strata_ids(pub, ("whale",)), b_main,
                                rng_of(seeds["naive_pub"])),
         "naive_timed": perm_test(y, d, gw, b_main, rng_of(seeds["naive_timed"])),
         "within_dep": perm_test(y, d, groups["deployment"], b_main, rng_of(seeds["dep"])),
         "within_bout": perm_test(y, d, groups["bout"], b_main, rng_of(seeds["bout"]))}
    out["tests"] = t
    say("naive D %s p %.4f; bout D %s p %.4f" % (t["naive_pub"]["d"], t["naive_pub"]["p_high"],
                                                  t["within_bout"]["d"],
                                                  t["within_bout"]["p_high"]))
    lv = level_of(t)
    out["level"] = lv
    cal = None
    if lv is not None:
        gl = groups[lv]
        out["rotation_p_high"] = rotation_p(y, d, gl, b_rot, rng_of(seeds["rot"]))
        # calibration worlds start from durations with the observed effect at this level
        # removed (d0 = duration - D_level for a-codas), so that only drift and runs remain
        d0 = d - t[LEVEL_KEY[lv]]["d"] * y
        idx = group_index(gl)
        rng = rng_of(seeds["size"])
        size_p = [perm_test(rotate_within(y, idx, rng), d0, gl, b_cal, rng)["p_high"]
                  for _ in range(r_cal)]
        cal = {"size": {"R": r_cal, "B": b_cal, "p": size_p}, "power": {}}
        say("size %.3f" % rate(size_p))
        dn = t["naive_pub"]["d"]
        if dn is not None and dn > 0:
            for k, f in POWER_FRACTIONS:
                rng = rng_of(seeds["power"] + int(round(f * 10)))
                ps = []
                for _ in range(r_cal):
                    ys = permute_within(y, gl, 1, rng)[0]
                    ps.append(perm_test(ys, d0 + f * dn * ys, gl, b_cal, rng)["p_high"])
                cal["power"][k] = {"delta": f * dn, "R": r_cal, "B": b_cal, "p": ps}
                say("power %s %.3f" % (k, rate(ps)))
        bouts = np.array([u["bout"] for u in dset], dtype=np.int64)
        rng = rng_of(seeds["false_alarm"])
        fa = {"R": r_cal, "B": b_cal, "eps": EPS_SIM, "naive_p_high": [], "naive_p_low": [],
              "bout_p_high": []}
        for _ in range(r_cal):
            ys = sim_bout_world(y, gw, bouts, EPS_SIM, rng)
            a = perm_test(ys, d, gw, b_cal, rng)
            fa["naive_p_high"].append(a["p_high"])
            fa["naive_p_low"].append(a["p_low"])
            fa["bout_p_high"].append(perm_test(ys, d, groups["bout"], b_cal, rng)["p_high"])
        cal["false_alarm"] = fa
        say("naive false alarm %.3f" % rate(fa["naive_p_high"]))
    out["calibration"] = cal
    modes, th = mode_analysis(pub, dset, b_main, seeds)
    out["modes"] = modes
    out["per_deployment"] = describe_deployments(dset, th)
    v, pred, brier = grade(out)
    out.update(verdict=v, predictions=pred, brier=brier)
    return out


def settings():
    return {"four": list(FOUR), "coda_type": CODA_TYPE, "b_main": B_MAIN, "b_rot": B_ROT,
            "r_cal": R_CAL, "b_cal": B_CAL, "eps_sim": EPS_SIM, "alpha": ALPHA,
            "size_max": SIZE_MAX, "power_min": POWER_MIN, "min_groups": MIN_GROUPS,
            "min_minority": MIN_MINORITY, "shrink": SHRINK, "q_strong": Q_STRONG,
            "seeds": dict(SEEDS)}


# ----------------------------------------------------------------------- synthetic data
def synthetic(seed=1, effect=0.0, eps=0.1, deps=2, bouts=4, bout_len=8, tempo_sd=0.05):
    """A synthetic dset (no real data): per whale and deployment, bouts of codas 4 s apart and
    400 s apart; one vowel per bout with a share eps of codas flipped; duration 1.2 s + a bout
    tempo + noise + effect for a-codas."""
    rng = np.random.default_rng(seed)
    out, i, b = [], 0, 0
    for w in FOUR:
        for k in range(deps):
            t = 0.0
            for _ in range(bouts):
                base = int(rng.random() < 0.6)
                tempo = rng.normal(0.0, tempo_sd)
                for _ in range(bout_len):
                    y = base ^ int(rng.random() < eps)
                    out.append({"i": i, "whale": w, "type": CODA_TYPE, "y": y,
                                "dur": 1.2 + tempo + rng.normal(0.0, 0.02) + effect * y,
                                "dep": "sw%03da" % (100 + k), "file": "sw%03da001" % (100 + k),
                                "t": t, "date": "2015-0%d-01" % (k + 1), "num": i, "bout": b})
                    i += 1
                    t += 4.0
                t += 400.0
                b += 1
    return out


# ----------------------------------------------------------------------- I/O
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()

    def log(m):
        print("%s (%.0fs)" % (m, time.time() - t0), flush=True)

    try:
        import diptest
        dv = getattr(diptest, "__version__", "unknown")
    except ImportError:
        dv = None
    r = {"version": VERSION, "python": sys.version.split()[0], "numpy": np.__version__,
         "diptest": dv, "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "files": {}, "settings": settings()}
    tables, ok = {}, True
    for name, url in SOURCES.items():
        b, h = fetch(name, url, a.data_dir)
        tables[name] = read_table(b.decode("utf-8-sig", errors="replace"))
        r["files"][name] = {"md5": h, "md5_ok": h == MD5[name], "rows": len(tables[name][1])}
        ok = ok and h == MD5[name]
    r["md5_ok"] = ok
    try:
        b, h = fetch("codamd-ceti-be751b8.csv", CETI_URL, a.data_dir)
        r["ceti_copy"] = {"md5": h, "same_as_osf": h == MD5["codamd.csv"]}
    except Exception as e:  # noqa: BLE001 - informative only, never a gate
        r["ceti_copy"] = {"error": str(e)[:200]}
    if not ok:
        r["verdict"] = "DATA_MISMATCH"
    else:
        md, dc, dl = (tables["codamd.csv"], tables["DominicaCodas.csv"],
                      tables["sperm-whale-dialogues.csv"])
        codas, counts = join(md[0], md[1], dc[0], dc[1], dl[0], dl[1])
        r["join_counts"] = counts
        pub, timed, dset = build(md[0], md[1], codas)
        r["n_timed"] = len(timed)
        log("pub %d timed %d dset %d" % (len(pub), len(timed), len(dset)))
        r.update(analyse(pub, dset, log=log))
    r["seconds"] = round(time.time() - t0, 1)
    r["utc_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    r = jsonable(r)
    with open(os.path.join(a.out_dir, "vowel2_results.json"), "w") as f:
        json.dump(r, f, indent=1, sort_keys=True)
    keys = ("verdict", "level", "n_pub", "n_dur", "predictions", "brier")
    print(json.dumps({k: r.get(k) for k in keys}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
