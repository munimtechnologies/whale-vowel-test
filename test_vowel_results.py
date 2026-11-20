# SPDX-License-Identifier: Apache-2.0
# test_vowel_results.py: the grader for the pre-registered sperm whale coda-vowel persistence
# test (VOWEL-PREREG.md, job vowel-test-v1), written and published BEFORE the job has produced
# any result. With its own code (it does not import vowel_test.py) it re-derives, from the raw
# job output (results/vowel/vowel_results.json): the gates of VOWEL-PREREG.md section 3 and 7;
# Q = S/E; the place of p_low and p_high on the permutation lattice (1 + k) / (B + 1) and inside
# the bounds that the stored null minimum and maximum allow; the agreement of the null mean with
# the exact expectation E (within 5 standard errors); the size and power counts from the stored
# calibration p values; the matched eps (ties to the smaller); the verdict (section 7, in order);
# predictions Q1-Q7 and the Brier score (section 8). It checks that the pair, bout, gap-profile
# and per-whale counts add up, that the settings equal the registration, and that the job's own
# verdict, predictions and Brier score agree with the regrade.
# It fixes now the exact lines RESULTS-VOWEL.md must contain (render_md_lines) and can write the
# whole document: python test_vowel_results.py --render <vowel_results.json> <RESULTS-VOWEL.md>.
# Until results/vowel/vowel_results.json exists the result tests are skipped; the toy tests
# always run. Stdlib only. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import copy
import json
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "vowel", "vowel_results.json")
MD = os.path.join(HERE, "RESULTS-VOWEL.md")
HAVE = os.path.exists(RES)

VERSION = "whale-vowel-test-1"
MD5 = {"codamd.csv": "be50098e0e806d6df7cd2144b80d900d",
       "DominicaCodas.csv": "46c2ff249bc6fa327d5bbe596f06be63",
       "sperm-whale-dialogues.csv": "eeeeb20cda64d88320b6ccee1185379a"}
FILE_ORDER = ("codamd.csv", "DominicaCodas.csv", "sperm-whale-dialogues.csv")
EPS_POWER_KEYS = ("0.05", "0.10", "0.20", "0.30")
EPS_MATCH = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
SETTINGS = {"gap": 60.0, "b_primary": 9999, "b_dep": 9999, "r_cal": 200, "b_cal": 999,
            "eps_power": [0.05, 0.1, 0.2, 0.3], "eps_match": EPS_MATCH, "r_match": 20,
            "alpha": 0.05, "q_strong": 0.5, "size_max": 0.1, "power_min": 0.8,
            "power_eps": 0.2, "min_wb_pairs": 200, "min_dep_units": 10,
            "seeds": {"primary": 20261201, "dep": 20261202, "coda_world": 20261203,
                      "bout_world": 20261204, "match": 20261205}}
B_PRIMARY = 9999
B_DEP = 9999
R_CAL = 200
B_CAL = 999
R_MATCH = 20
ALPHA = 0.05
Q_STRONG = 0.5
SIZE_MAX = 0.10
POWER_MIN = 0.80
POWER_KEY = "0.20"
MIN_WB_PAIRS = 200
MIN_DEP_UNITS = 10
GAP_BINS = ("0-10", "10-60", "60-300", "300+")
ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PRIORS = {"Q1": 0.70, "Q2": 0.40, "Q3": 0.55, "Q4": 0.85, "Q5": 0.97, "Q6": 0.65, "Q7": 0.05}
PRED_TEXT = {
    "Q1": "primary within-bout test detects clustering, p_low <= 0.05",
    "Q2": "Q = S/E <= 0.5 (at most half the expected switches)",
    "Q3": "vowels differ between tag deployments of the same whale, p_dep <= 0.05",
    "Q4": "power at eps = 0.20 >= 0.80",
    "Q5": "coda-world size <= 0.10",
    "Q6": "between-bout switch share exceeds the within-bout share",
    "Q7": "p_high <= 0.05 (vowels alternate more than chance)"}
DM = "DATA_MISMATCH"
INS = "INSUFFICIENT_DATA"
INC = "INCOMPLETE"
COUNT_KEYS = ("n_units", "n_whales", "n_deployments", "n_files", "n_bouts", "n_strata",
              "informative_strata", "units_in_informative_strata", "n_pairs",
              "n_within_bout_pairs", "n_between_bout_pairs")
STAT_KEYS = ("within", "between", "gap_profile", "per_whale", "deployment_test", "calibration",
             "match")


# --------------------------------------------------------------------------
# small helpers
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


def p_ok(p, b):
    """p = (1 + k) / (1 + b) for an integer 0 <= k <= b."""
    if not finite(p):
        return False
    k = p * (b + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= b


def le_alpha(p):
    return finite(p) and p <= ALPHA


def n_rej(ps):
    return sum(1 for p in ps if le_alpha(p))


def fmt(x, spec):
    return format(x, spec) if finite(x) else "n/a"


def ratio(a, b, spec):
    return format(a / b, spec) if finite(a) and finite(b) and b > 0 else "n/a"


# --------------------------------------------------------------------------
# independent re-implementation of VOWEL-PREREG.md sections 3, 6, 7 and 8
# --------------------------------------------------------------------------
def files_gate(r):
    files = r.get("files")
    if not isinstance(files, dict) or sorted(files) != sorted(MD5):
        return INC
    if not all(isinstance(files[k], dict) and files[k].get("md5_ok") is True for k in files):
        return DM
    return None


def complete(r):
    c = r.get("calibration")
    m = r.get("match")
    return (isinstance(r.get("within"), dict) and isinstance(r.get("between"), dict)
            and isinstance(r.get("gap_profile"), list) and isinstance(r.get("per_whale"), dict)
            and isinstance(r.get("deployment_test"), dict) and isinstance(c, dict)
            and isinstance(c.get("coda_world"), dict) and isinstance(c.get("bout_world"), dict)
            and all(isinstance(c["bout_world"].get(k), dict) for k in EPS_POWER_KEYS)
            and all(isinstance(c["bout_world"][k].get("p"), list) for k in EPS_POWER_KEYS)
            and isinstance(c["coda_world"].get("p"), list) and isinstance(m, dict)
            and isinstance(m.get("mean_q"), list) and len(m["mean_q"]) == len(EPS_MATCH))


def verdict_of(n_wb, e_null, size, pl, q, power20):
    if n_wb < MIN_WB_PAIRS or not (finite(e_null) and e_null > 0):
        return INS
    if not finite(size) or size > SIZE_MAX:
        return "CALIBRATION_FAILED"
    if le_alpha(pl):
        return "VOWELS_CLUSTER_STRONGLY" if q <= Q_STRONG else "VOWELS_CLUSTER_WEAKLY"
    if finite(power20) and power20 >= POWER_MIN:
        return "NO_CLUSTERING_WITH_POWER"
    return "UNDERPOWERED"


def matched_index(mean_q, q):
    """Index of the grid value whose mean Q is closest to q (first one on ties)."""
    d = [abs(m - q) if finite(m) else float("inf") for m in mean_q]
    best = 0
    for i in range(1, len(d)):
        if d[i] < d[best]:
            best = i
    return best


def regrade(r):
    out = {"verdict": files_gate(r), "S": None, "E": None, "q": None, "size": None,
           "size_k": None, "power": None, "power_k": None, "matched_eps": None,
           "predictions": None, "brier": None, "n_true": None}
    if out["verdict"]:
        return out
    n_wb = r.get("n_within_bout_pairs")
    if not is_int(n_wb):
        out["verdict"] = INC
        return out
    w = r.get("within")
    if n_wb < MIN_WB_PAIRS or not isinstance(w, dict):
        # without "within" the job found E <= 0 (section 7, rule 1)
        out["verdict"] = INS
        return out
    if not (finite(w.get("expected")) and w["expected"] > 0):
        out["verdict"] = INS
        return out
    if not complete(r):
        out["verdict"] = INC
        return out
    S, E = w["switches"], w["expected"]
    q = S / E
    c = r["calibration"]
    size_k = n_rej(c["coda_world"]["p"])
    size = size_k / len(c["coda_world"]["p"]) if c["coda_world"]["p"] else float("nan")
    power_k = {k: n_rej(c["bout_world"][k]["p"]) for k in EPS_POWER_KEYS}
    power = {k: (power_k[k] / len(c["bout_world"][k]["p"]) if c["bout_world"][k]["p"]
                 else float("nan")) for k in EPS_POWER_KEYS}
    mi = matched_index(r["match"]["mean_q"], q)
    share_w = S / n_wb
    nb = r.get("n_between_bout_pairs")
    share_b = r["between"]["switches"] / nb if is_int(nb) and nb > 0 else float("nan")
    pdep = r["deployment_test"].get("p")
    pred = {"Q1": le_alpha(w["p_low"]), "Q2": q <= Q_STRONG, "Q3": le_alpha(pdep),
            "Q4": finite(power[POWER_KEY]) and power[POWER_KEY] >= POWER_MIN,
            "Q5": finite(size) and size <= SIZE_MAX,
            "Q6": finite(share_b) and share_b > share_w, "Q7": le_alpha(w["p_high"])}
    pred = {k: bool(pred[k]) for k in ORDER}
    brier = sum((PRIORS[k] - (1.0 if pred[k] else 0.0)) ** 2 for k in ORDER) / len(ORDER)
    out.update(verdict=verdict_of(n_wb, E, size, w["p_low"], q, power[POWER_KEY]), S=S, E=E,
               q=q, size=size, size_k=size_k, power=power, power_k=power_k,
               matched_eps=EPS_MATCH[mi], predictions=pred, brier=brier,
               n_true=sum(1 for k in ORDER if pred[k]))
    return out


# --------------------------------------------------------------------------
# internal consistency of the raw output
# --------------------------------------------------------------------------
def check_counts(r):
    v = {k: r.get(k) for k in COUNT_KEYS}
    if not all(is_int(x) and x >= 0 for x in v.values()):
        return ["counts missing"]
    bad = []
    if v["n_pairs"] != v["n_within_bout_pairs"] + v["n_between_bout_pairs"]:
        bad.append("pairs do not add up")
    if v["n_pairs"] != v["n_units"] - v["n_files"]:
        bad.append("pairs != units - files")
    if v["n_bouts"] != v["n_files"] + v["n_between_bout_pairs"]:
        bad.append("bouts != files + between-bout pairs")
    if not (v["n_whales"] <= v["n_deployments"] <= v["n_files"] <= v["n_units"]):
        bad.append("whales, deployments, files, units out of order")
    if (v["informative_strata"] > v["n_strata"] or v["n_strata"] > v["n_units"]
            or v["units_in_informative_strata"] > v["n_units"]
            or v["units_in_informative_strata"] < 2 * v["informative_strata"]):
        bad.append("strata")
    sa = r.get("share_a")
    if v["n_units"] > 0 and not (finite(sa) and 0.0 <= sa <= 1.0):
        bad.append("share_a")
    return bad


def check_within(r):
    w = r["within"]
    n_wb = r["n_within_bout_pairs"]
    b = w.get("B")
    S, E = w.get("switches"), w.get("expected")
    if b != B_PRIMARY:
        return ["within: B"]
    if not (is_int(S) and 0 <= S <= n_wb and finite(E) and 0 < E <= n_wb):
        return ["within: S or E"]
    bad = []
    if not close(w.get("q"), S / E):
        bad.append("within: q")
    pl, ph = w.get("p_low"), w.get("p_high")
    if not (p_ok(pl, b) and p_ok(ph, b)):
        return bad + ["within: p lattice"]
    lo, hi = w.get("null_min"), w.get("null_max")
    mu, sd = w.get("null_mean"), w.get("null_sd")
    if not (is_int(lo) and is_int(hi) and 0 <= lo <= hi <= n_wb and finite(mu) and finite(sd)
            and sd >= 0 and lo - 1e-9 <= mu <= hi + 1e-9):
        return bad + ["within: null summary"]
    one, top, eps = 1.0 / (b + 1), b / (b + 1.0), 1e-12
    ok = True
    if S < lo:
        ok = abs(pl - one) < eps and abs(ph - 1.0) < eps
    elif S > hi:
        ok = abs(pl - 1.0) < eps and abs(ph - one) < eps
    else:
        ok = pl >= 2 * one - eps and ph >= 2 * one - eps
        if S == lo:
            ok = ok and abs(ph - 1.0) < eps
        if S == hi:
            ok = ok and abs(pl - 1.0) < eps
        if lo < S < hi:
            ok = ok and pl <= top + eps and ph <= top + eps
    if not ok or pl + ph < 1.0 + one - 1e-9:
        bad.append("within: p outside its null")
    if abs(mu - E) > 5.0 * sd / math.sqrt(b) + 1e-6:
        bad.append("within: null mean far from E")
    return bad


def check_between(r):
    bt = r["between"]
    nb = r["n_between_bout_pairs"]
    s, e = bt.get("switches"), bt.get("expected")
    if not (is_int(s) and 0 <= s <= nb and finite(e) and 0 <= e <= nb + 1e-9):
        return ["between"]
    if e > 0 and not close(bt.get("q"), s / e):
        return ["between: q"]
    if e == 0 and bt.get("q") is not None:
        return ["between: q"]
    return []


def check_gaps(r):
    g = r["gap_profile"]
    if [x.get("bin") for x in g if isinstance(x, dict)] != list(GAP_BINS):
        return ["gap profile bins"]
    if not all(is_int(x.get("pairs")) and is_int(x.get("switches")) and finite(x.get("expected"))
               and 0 <= x["switches"] <= x["pairs"] and 0 <= x["expected"] <= x["pairs"] + 1e-9
               for x in g):
        return ["gap profile values"]
    bad = []
    if sum(x["pairs"] for x in g) != r["n_pairs"]:
        bad.append("gap profile pairs")
    wi, be = g[:2], g[2:]
    if (sum(x["pairs"] for x in wi) != r["n_within_bout_pairs"]
            or sum(x["switches"] for x in wi) != r["within"]["switches"]
            or not close(sum(x["expected"] for x in wi), r["within"]["expected"], 1e-7)):
        bad.append("gap profile within bouts")
    if (sum(x["pairs"] for x in be) != r["n_between_bout_pairs"]
            or sum(x["switches"] for x in be) != r["between"]["switches"]
            or not close(sum(x["expected"] for x in be), r["between"]["expected"], 1e-7)):
        bad.append("gap profile between bouts")
    return bad


def check_whales(r):
    pw = r["per_whale"]
    vals = list(pw.values())
    if not all(isinstance(x, dict) and is_int(x.get("units")) and is_int(x.get("within_pairs"))
               and is_int(x.get("switches")) and finite(x.get("expected"))
               and 0 <= x["switches"] <= x["within_pairs"] < max(1, x["units"])
               for x in vals):
        return ["per whale values"]
    bad = []
    if len(pw) != r["n_whales"] or sum(x["units"] for x in vals) != r["n_units"]:
        bad.append("per whale units")
    if (sum(x["within_pairs"] for x in vals) != r["n_within_bout_pairs"]
            or sum(x["switches"] for x in vals) != r["within"]["switches"]
            or not close(sum(x["expected"] for x in vals), r["within"]["expected"], 1e-7)):
        bad.append("per whale pairs")
    return bad


def check_dep(r):
    d = r["deployment_test"]
    if "skipped" in d:
        return [] if d.get("p") is None else ["deployment test: p despite skip"]
    whales, deps = d.get("whales"), d.get("deployments")
    if not (isinstance(whales, list) and isinstance(deps, list) and whales == sorted(set(whales))
            and deps == sorted(set(deps))):
        return ["deployment test: lists"]
    per = {}
    for x in deps:
        per[x.split("/")[0]] = per.get(x.split("/")[0], 0) + 1
    bad = []
    if sorted(per) != whales or any(v < 2 for v in per.values()):
        bad.append("deployment test: whales need 2 deployments")
    if not (is_int(d.get("n_units")) and MIN_DEP_UNITS * len(deps) <= d["n_units"] <= r["n_units"]
            and is_int(d.get("n_cells")) and len(deps) <= d["n_cells"] <= d["n_units"]):
        bad.append("deployment test: sizes")
    if d.get("B") != B_DEP or not p_ok(d.get("p"), B_DEP):
        bad.append("deployment test: p lattice")
    if not (finite(d.get("g_obs")) and d["g_obs"] >= -1e-9 and finite(d.get("null_mean"))
            and d["null_mean"] >= -1e-9 and finite(d.get("null_q95"))):
        bad.append("deployment test: G")
    return bad


def check_cal(r, rg):
    c = r["calibration"]
    bad = []
    cw = c["coda_world"]
    if (cw.get("R") != R_CAL or cw.get("B") != B_CAL or len(cw["p"]) != R_CAL
            or not all(p_ok(p, B_CAL) for p in cw["p"])):
        bad.append("coda world")
    elif not close(cw.get("size"), rg["size"]):
        bad.append("coda world size")
    if sorted(c["bout_world"]) != list(EPS_POWER_KEYS):
        bad.append("bout world keys")
    for k in EPS_POWER_KEYS:
        bw = c["bout_world"][k]
        if (bw.get("R") != R_CAL or bw.get("B") != B_CAL or len(bw["p"]) != R_CAL
                or not all(p_ok(p, B_CAL) for p in bw["p"])):
            bad.append("bout world " + k)
        elif not close(bw.get("power"), rg["power"][k]):
            bad.append("bout world power " + k)
    m = r["match"]
    if (m.get("R") != R_MATCH or not isinstance(m.get("eps"), list)
            or len(m["eps"]) != len(EPS_MATCH)
            or not all(close(a, b) for a, b in zip(m["eps"], EPS_MATCH))):
        bad.append("match grid")
    elif not all(x is None or finite(x) for x in m["mean_q"]):
        bad.append("match values")
    return bad


def check_result(r):
    bad = []
    if r.get("version") != VERSION:
        bad.append("version")
    if r.get("settings") != SETTINGS:
        bad.append("settings")
    files = r.get("files")
    if not isinstance(files, dict) or sorted(files) != sorted(MD5):
        return bad + ["files"]
    for k, v in files.items():
        if not isinstance(v, dict) or v.get("md5_ok") is not (v.get("md5") == MD5[k]):
            bad.append("md5 flag " + k)
    g = files_gate(r)
    if r.get("md5_ok") is not (g != DM):
        bad.append("md5_ok")
    if g == DM:
        if r.get("verdict") != DM or any(k in r for k in COUNT_KEYS + STAT_KEYS):
            bad.append("results despite a data mismatch")
        return bad
    bad += check_counts(r)
    if bad and "counts missing" in bad:
        return bad
    rg = regrade(r)
    if rg["verdict"] == INC:
        return bad + ["incomplete"]
    if rg["verdict"] == INS:
        if any(k in r for k in STAT_KEYS) and r["n_within_bout_pairs"] < MIN_WB_PAIRS:
            bad.append("statistics despite too few pairs")
        if r.get("predictions") is not None or r.get("brier") is not None:
            bad.append("predictions despite " + INS)
        return bad
    bad += check_within(r)
    bad += check_between(r)
    bad += check_gaps(r)
    bad += check_whales(r)
    bad += check_dep(r)
    bad += check_cal(r, rg)
    return bad


def compare_job(r, rg):
    """Mismatches between the job's own verdict and grading and the regrade."""
    bad = []
    if r.get("verdict") != rg["verdict"]:
        bad.append("verdict")
    if r.get("predictions") != rg["predictions"]:
        bad.append("predictions")
    if not close(r.get("brier"), rg["brier"]):
        bad.append("brier")
    if rg["predictions"] is not None:
        if not close(r["match"].get("matched_eps"), rg["matched_eps"]):
            bad.append("matched eps")
    return bad


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-VOWEL.md must contain these lines)
# --------------------------------------------------------------------------
def yes_no(v):
    return "not run" if v is None else ("yes" if v else "no")


def md5_line(r):
    f = r.get("files") or {}
    return "Code version `{}`; data files md5 match: {}".format(
        r.get("version"), ", ".join("%s %s" % (k, yes_no((f.get(k) or {}).get("md5_ok")))
                                    for k in FILE_ORDER))


def join_line(r):
    j = r["join_counts"]
    return ("Join: {:,} of {:,} codamd rows matched to a unique DSWP recording time ({:,} "
            "ambiguous, {:,} unmatched, {:,} not found by coda number)").format(
        j.get("dialogue_matched", 0), j.get("codamd_rows", 0), j.get("dialogue_ambiguous", 0),
        j.get("dialogue_unmatched", 0), j.get("dc_missing", 0))


def units_line(r):
    return ("Units: **{:,}** labelled, timed codas of {} whales in {} whale-deployments, {} files "
            "and {} bouts (gap <= 60 s); share of a {}").format(
        r["n_units"], r["n_whales"], r["n_deployments"], r["n_files"], r["n_bouts"],
        fmt(r.get("share_a"), ".3f"))


def strata_line(r):
    return ("Strata (whale x deployment x coda type): {}; {} hold both vowels, with {:,} "
            "codas").format(r["n_strata"], r["informative_strata"],
                            r["units_in_informative_strata"])


def pairs_line(r):
    return "Neighbouring pairs: {:,} ({:,} within bouts, {:,} between bouts)".format(
        r["n_pairs"], r["n_within_bout_pairs"], r["n_between_bout_pairs"])


def primary_line(r):
    w = r["within"]
    return ("Within-bout switches S = **{:,}**; expected under shuffling E = {:.2f}; "
            "Q = S/E = **{:.4f}**").format(w["switches"], w["expected"],
                                           w["switches"] / w["expected"])


def p_line(r):
    w = r["within"]
    return ("Primary test (B = 9,999 permutations within whale x deployment x coda type): "
            "p_low = **{:.4f}**, p_high = {:.4f}; null mean {:.2f}, sd {:.2f}, range {:,} to "
            "{:,}").format(w["p_low"], w["p_high"], w["null_mean"], w["null_sd"],
                           w["null_min"], w["null_max"])


def between_line(r):
    bt = r["between"]
    return "Between-bout switches {:,} of {:,} pairs; expected {:.2f}; Q = {}".format(
        bt["switches"], r["n_between_bout_pairs"], bt["expected"],
        ratio(bt["switches"], bt["expected"], ".4f"))


def gap_row(g):
    """| gap | pairs | switches | expected | Q |"""
    return "| {} s | {:,} | {:,} | {:.2f} | {} |".format(
        g["bin"], g["pairs"], g["switches"], g["expected"],
        ratio(g["switches"], g["expected"], ".3f"))


def whale_row(name, x):
    """| whale | codas | within-bout pairs | switches | expected | Q |"""
    return "| {} | {:,} | {:,} | {:,} | {:.2f} | {} |".format(
        name, x["units"], x["within_pairs"], x["switches"], x["expected"],
        ratio(x["switches"], x["expected"], ".3f"))


def dep_line(r):
    d = r["deployment_test"]
    if "skipped" in d:
        return "Deployment test: skipped ({})".format(d["skipped"])
    return ("Deployment test (whales {}; {} deployments, {:,} codas, {} whale x coda type x "
            "deployment cells): G = {:.3f} (null mean {:.3f}, 95th percentile {:.3f}), p_dep = "
            "**{:.4f}** (B = 9,999)").format(", ".join(d["whales"]), len(d["deployments"]),
                                             d["n_units"], d["n_cells"], d["g_obs"],
                                             d["null_mean"], d["null_q95"], d["p"])


def size_line(rg):
    return ("Coda world (independent codas, R = 200, B = 999): size **{:.3f}** ({} of 200 "
            "rejected; calibration fails above 0.10)").format(rg["size"], rg["size_k"])


def power_row(k, rg):
    """| eps | rejected | power |"""
    return "| {} | {} of 200 | {:.3f} |".format(k, rg["power_k"][k], rg["power"][k])


def power_line(rg):
    return ("Power at eps = 0.20: **{:.3f}** (0.80 or more needed for "
            "NO_CLUSTERING_WITH_POWER)").format(rg["power"][POWER_KEY])


def match_row(i, r):
    """| eps | mean Q |"""
    return "| {:.2f} | {} |".format(EPS_MATCH[i], fmt(r["match"]["mean_q"][i], ".4f"))


def match_line(rg):
    return "Matched eps (exploratory): **{:.2f}** (observed Q {:.4f})".format(
        rg["matched_eps"], rg["q"])


def verdict_line(rg):
    return "Verdict: **`%s`**" % rg["verdict"]


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def pred_row(k, rg):
    pr = rg["predictions"] or {}
    return "| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, pr.get(k)))


def data_lines(r):
    out = [md5_line(r)]
    if isinstance(r.get("join_counts"), dict):
        out.append(join_line(r))
    if all(is_int(r.get(k)) for k in COUNT_KEYS):
        out += [units_line(r), strata_line(r), pairs_line(r)]
    return out


def score_lines(rg):
    if rg["predictions"] is None:
        return ["0 of 0 graded predictions true"]
    return ["%d of %d graded predictions true" % (rg["n_true"], len(ORDER)),
            "Brier score **%.3f**" % rg["brier"]]


def stat_lines(r, rg):
    if rg["predictions"] is None:
        return []
    out = [primary_line(r), p_line(r), between_line(r)]
    out += [gap_row(g) for g in r["gap_profile"]]
    out += [whale_row(k, r["per_whale"][k]) for k in sorted(r["per_whale"])]
    out += [dep_line(r), size_line(rg)] + [power_row(k, rg) for k in EPS_POWER_KEYS]
    out += [power_line(rg)] + [match_row(i, r) for i in range(len(EPS_MATCH))]
    return out + [match_line(rg)]


def required_strings(r, rg):
    return data_lines(r) + stat_lines(r, rg) + [verdict_line(rg)] + score_lines(rg)


def render_md_lines(r, rg):
    """Every fixed line, in one list (prediction rows included)."""
    return required_strings(r, rg) + [pred_row(k, rg) for k in ORDER]


def check_md(md, r, rg):
    """List of required lines missing from md (empty list = all present)."""
    missing = [s for s in required_strings(r, rg) if s not in md]
    pr = rg["predictions"] or {}
    lines = md.splitlines()
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, pr.get(k))):
            missing.append("prediction row " + k)
    return missing


def render_markdown(r, rg):
    """The whole RESULTS-VOWEL.md (every required line, inside headings and table headers)."""
    L = ["# RESULTS-VOWEL: do sperm whale coda vowels persist through bouts?", "",
         "Graded by `test_vowel_results.py` (published before the result was read) from "
         "`results/vowel/vowel_results.json`, the output of `vowel_test.py` registered in "
         "`VOWEL-PREREG.md`. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; not yet "
         "checked by a human expert. Text CC BY 4.0.", "", "## Verdict", "", verdict_line(rg), ""]
    for s in score_lines(rg):
        L += [s, ""]
    L += ["## Data", ""]
    for s in data_lines(r):
        L += [s, ""]
    if rg["predictions"] is not None:
        L += ["## Primary test: switches between neighbouring codas within bouts", "",
              primary_line(r), "", p_line(r), "", between_line(r), "",
              "## Gap profile (exploratory)", "",
              "| gap | pairs | switches | expected | Q |", "|---|---|---|---|---|"]
        L += [gap_row(g) for g in r["gap_profile"]]
        L += ["", "## Per whale (exploratory)", "",
              "| whale | codas | within-bout pairs | switches | expected | Q |",
              "|---|---|---|---|---|---|"]
        L += [whale_row(k, r["per_whale"][k]) for k in sorted(r["per_whale"])]
        L += ["", "## Deployment test (secondary)", "", dep_line(r), "",
              "## Calibration on the real timeline", "", size_line(rg), "",
              "| eps (bout world) | rejected | power |", "|---|---|---|"]
        L += [power_row(k, rg) for k in EPS_POWER_KEYS]
        L += ["", power_line(rg), "", "## Matching (exploratory)", "", "| eps | mean Q |",
              "|---|---|"]
        L += [match_row(i, r) for i in range(len(EPS_MATCH))]
        L += ["", match_line(rg), ""]
    L += ["## Predictions (priors fixed in VOWEL-PREREG.md)", "",
          "| id | prediction | prior | came true |", "|---|---|---|---|"]
    L += [pred_row(k, rg) for k in ORDER]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# result tests (skipped until the job's output is published)
# --------------------------------------------------------------------------
@unittest.skipUnless(HAVE, "results/vowel/vowel_results.json not published yet")
class TestVowelResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)
        cls.md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""

    def test_consistency(self):
        self.assertEqual(check_result(self.r), [])

    def test_job_matches_regrade(self):
        self.assertEqual(compare_job(self.r, self.rg), [])

    @unittest.skipUnless(os.path.exists(MD), "RESULTS-VOWEL.md not written yet")
    def test_md_lines(self):
        self.assertEqual(check_md(self.md, self.r, self.rg), [])


# --------------------------------------------------------------------------
# toy tests (always run; every expected value worked out by hand)
# --------------------------------------------------------------------------
def plist(n_hit, n_miss, hit=0.001, miss=0.3):
    return [hit] * n_hit + [miss] * n_miss


def toy_result():
    """Default: S 60, E 120, Q 0.5, p_low 0.0001 -> VOWELS_CLUSTER_STRONGLY; size 8 of 200;
    power 40, 120, 180, 200 of 200; p_dep 0.0123; matched eps 0.30."""
    gaps = [{"bin": "0-10", "pairs": 200, "switches": 40, "expected": 96.0},
            {"bin": "10-60", "pairs": 50, "switches": 20, "expected": 24.0},
            {"bin": "60-300", "pairs": 30, "switches": 15, "expected": 12.0},
            {"bin": "300+", "pairs": 15, "switches": 10, "expected": 8.0}]
    pw = {"A": {"units": 150, "within_pairs": 130, "switches": 30, "expected": 60.0},
          "B": {"units": 100, "within_pairs": 80, "switches": 20, "expected": 40.0},
          "C": {"units": 50, "within_pairs": 40, "switches": 10, "expected": 20.0}}
    bw = {}
    for k, n in zip(EPS_POWER_KEYS, (40, 120, 180, 200)):
        ps = plist(n, 200 - n)
        bw[k] = {"R": 200, "B": 999, "p": ps, "power": n / 200}
    cwp = plist(8, 192, hit=0.01, miss=0.5)
    mq = [0.0, 0.08, 0.17, 0.26, 0.35, 0.44, 0.53, 0.62, 0.71, 0.80, 0.89]
    r = {"version": VERSION, "python": "3.12.8", "numpy": "2.1.3",
         "utc_start": "2026-11-21T00:00:00Z", "settings": copy.deepcopy(SETTINGS),
         "files": {k: {"md5": v, "md5_ok": True, "rows": 10} for k, v in MD5.items()},
         "md5_ok": True,
         "join_counts": {"codamd_rows": 1375, "dialogue_matched": 1316,
                         "dialogue_ambiguous": 2, "dialogue_unmatched": 53, "dc_missing": 4},
         "n_units": 300, "n_whales": 3, "n_deployments": 4, "n_files": 5, "n_bouts": 50,
         "n_strata": 12, "informative_strata": 9, "units_in_informative_strata": 280,
         "share_a": 0.6, "n_pairs": 295, "n_within_bout_pairs": 250,
         "n_between_bout_pairs": 45,
         "within": {"switches": 60, "expected": 120.0, "q": 0.5, "p_low": 0.0001,
                    "p_high": 1.0, "B": 9999, "null_mean": 120.05, "null_sd": 7.5,
                    "null_min": 90, "null_max": 150},
         "between": {"switches": 25, "expected": 20.0, "q": 1.25},
         "gap_profile": gaps, "per_whale": pw,
         "deployment_test": {"whales": ["A"], "deployments": ["A/d1", "A/d2"],
                             "n_units": 150, "n_cells": 6, "g_obs": 12.5, "B": 9999,
                             "p": 0.0123, "null_mean": 5.0, "null_q95": 11.0},
         "calibration": {"coda_world": {"R": 200, "B": 999, "p": cwp, "size": 0.04},
                         "bout_world": bw},
         "match": {"eps": list(EPS_MATCH), "mean_q": mq, "R": 20, "matched_eps": 0.3}}
    return r


def attach(r):
    """Add the job's own grading fields, as vowel_test.analyse writes them."""
    rg = regrade(r)
    r["verdict"] = rg["verdict"]
    r["predictions"] = rg["predictions"]
    r["brier"] = rg["brier"]
    return r


def toy_insufficient():
    r = toy_result()
    for k in STAT_KEYS:
        del r[k]
    r.update(n_units=160, n_files=5, n_pairs=155, n_within_bout_pairs=150,
             n_between_bout_pairs=5, n_bouts=10, units_in_informative_strata=150)
    return attach(r)


def toy_mismatch():
    r = toy_result()
    for k in COUNT_KEYS + STAT_KEYS + ("join_counts", "share_a", "n_whales"):
        r.pop(k, None)
    r["files"]["DominicaCodas.csv"] = {"md5": "0" * 32, "md5_ok": False, "rows": 10}
    r["md5_ok"] = False
    return attach(r)


class TestToy(unittest.TestCase):
    def test_default(self):
        r = toy_result()
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "VOWELS_CLUSTER_STRONGLY")
        self.assertEqual((rg["S"], rg["E"], rg["q"]), (60, 120.0, 0.5))
        self.assertEqual((rg["size_k"], rg["size"]), (8, 0.04))
        self.assertEqual([rg["power_k"][k] for k in EPS_POWER_KEYS], [40, 120, 180, 200])
        self.assertEqual(rg["power"]["0.20"], 0.9)
        self.assertEqual(rg["matched_eps"], 0.3)
        # share between 25/45 = 0.556 > share within 60/250 = 0.24
        self.assertEqual([rg["predictions"][k] for k in ORDER],
                         [True, True, True, True, True, True, False])
        # .09 + .36 + .2025 + .0225 + .0009 + .1225 + .0025 = .8009
        self.assertAlmostEqual(rg["brier"], 0.8009 / 7, places=12)
        self.assertEqual(rg["n_true"], 6)
        self.assertEqual(check_result(r), [])
        self.assertEqual(compare_job(r, rg), ["verdict", "predictions", "brier"])
        attach(r)
        r2 = json.loads(json.dumps(r))
        self.assertEqual(check_result(r2), [])
        self.assertEqual(compare_job(r2, regrade(r2)), [])
        r2["brier"] = 0.1
        r2["predictions"]["Q7"] = True
        r2["match"]["matched_eps"] = 0.25
        self.assertEqual(compare_job(r2, regrade(r2)), ["predictions", "brier", "matched eps"])

    def test_verdicts(self):
        v = verdict_of
        self.assertEqual(v(199, 10.0, 0.0, 0.01, 0.2, 0.9), INS)
        self.assertEqual(v(300, 0.0, 0.0, 0.01, 0.2, 0.9), INS)
        self.assertEqual(v(300, 10.0, 0.105, 0.01, 0.2, 0.9), "CALIBRATION_FAILED")
        self.assertEqual(v(300, 10.0, float("nan"), 0.01, 0.2, 0.9), "CALIBRATION_FAILED")
        self.assertEqual(v(300, 10.0, 0.10, 0.05, 0.5, 0.9), "VOWELS_CLUSTER_STRONGLY")
        self.assertEqual(v(300, 10.0, 0.05, 0.05, 0.6, 0.1), "VOWELS_CLUSTER_WEAKLY")
        self.assertEqual(v(300, 10.0, 0.05, 0.0501, 0.9, 0.8), "NO_CLUSTERING_WITH_POWER")
        self.assertEqual(v(300, 10.0, 0.05, 0.2, 0.9, 0.795), "UNDERPOWERED")
        # regrade on variants (only the inputs of the verdict change)
        r = toy_result()
        r["within"]["switches"] = 72                  # Q = 0.6
        self.assertEqual(regrade(r)["verdict"], "VOWELS_CLUSTER_WEAKLY")
        self.assertFalse(regrade(r)["predictions"]["Q2"])
        r = toy_result()
        r["within"].update(p_low=0.4, p_high=0.7)
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "NO_CLUSTERING_WITH_POWER")
        r["calibration"]["bout_world"]["0.20"]["p"] = plist(159, 41)    # 0.795
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "UNDERPOWERED")
        self.assertFalse(rg["predictions"]["Q4"])
        r["calibration"]["bout_world"]["0.20"]["p"] = plist(160, 40)    # exactly 0.80
        self.assertEqual(regrade(r)["verdict"], "NO_CLUSTERING_WITH_POWER")
        r = toy_result()
        r["calibration"]["coda_world"]["p"] = plist(21, 179, hit=0.05)   # 0.105
        rg = regrade(r)
        self.assertEqual(rg["verdict"], "CALIBRATION_FAILED")
        self.assertFalse(rg["predictions"]["Q5"])
        r["calibration"]["coda_world"]["p"] = plist(20, 180, hit=0.05)   # exactly 0.10
        self.assertEqual(regrade(r)["verdict"], "VOWELS_CLUSTER_STRONGLY")
        r = toy_result()
        r["deployment_test"] = {"skipped": "fewer than 2 eligible deployments", "p": None}
        rg = regrade(r)
        self.assertFalse(rg["predictions"]["Q3"])
        self.assertEqual(check_result(r), [])
        r = toy_result()
        r["between"]["switches"] = 10                 # 10/45 = 0.222 < 0.24
        self.assertFalse(regrade(r)["predictions"]["Q6"])

    def test_match_ties(self):
        self.assertEqual(matched_index([0.0, 0.25, 0.75, 1.0], 0.5), 1)
        self.assertEqual(matched_index([None, 0.5, 0.5], 0.5), 1)
        self.assertEqual(matched_index([None, None], 0.5), 0)
        r = toy_result()
        r["match"]["mean_q"][6] = None
        self.assertEqual(regrade(r)["matched_eps"], 0.25)
        self.assertEqual(check_result(r), [])

    def test_gates(self):
        r = toy_insufficient()
        rg = regrade(r)
        self.assertEqual(rg["verdict"], INS)
        self.assertIsNone(rg["predictions"])
        self.assertEqual(check_result(r), [])
        self.assertEqual(compare_job(r, rg), [])
        self.assertEqual(len(render_md_lines(r, rg)), 14)
        self.assertEqual(check_md(render_markdown(r, rg), r, rg), [])
        r["predictions"] = {k: True for k in ORDER}
        self.assertEqual(check_result(r), ["predictions despite " + INS])
        r = toy_mismatch()
        rg = regrade(r)
        self.assertEqual(rg["verdict"], DM)
        self.assertEqual(check_result(r), [])
        self.assertEqual(compare_job(r, rg), [])
        lines = render_md_lines(r, rg)
        self.assertEqual(len(lines), 10)
        self.assertEqual(lines[0], "Code version `whale-vowel-test-1`; data files md5 match: "
                                   "codamd.csv yes, DominicaCodas.csv no, "
                                   "sperm-whale-dialogues.csv yes")
        self.assertEqual(lines[1], "Verdict: **`DATA_MISMATCH`**")
        r["n_units"] = 3
        self.assertEqual(check_result(r), ["results despite a data mismatch"])
        r = toy_result()
        del r["match"]
        self.assertEqual(regrade(r)["verdict"], INC)
        self.assertIn("incomplete", check_result(r))

    def test_consistency_catches_errors(self):
        r = toy_result()
        r["within"]["p_low"] = 0.00015                # not on the 1/10000 lattice
        r["between"]["q"] = 1.3
        r["settings"]["b_cal"] = 99
        self.assertEqual(sorted(check_result(r)),
                         sorted(["settings", "within: p lattice", "between: q"]))
        r = toy_result()
        r["within"]["p_low"] = 0.0002                 # S below every null value: must be 0.0001
        self.assertEqual(check_result(r), ["within: p outside its null"])
        r = toy_result()
        r["within"]["null_mean"] = 121.0              # 5 x 7.5 / 99.995 = 0.375 allowed
        self.assertEqual(check_result(r), ["within: null mean far from E"])
        r = toy_result()
        r["within"]["q"] = 0.4
        self.assertEqual(check_result(r), ["within: q"])
        r = toy_result()
        r["n_bouts"] = 51
        self.assertEqual(check_result(r), ["bouts != files + between-bout pairs"])
        r = toy_result()
        r["gap_profile"][1]["switches"] = 21
        self.assertEqual(check_result(r), ["gap profile within bouts"])
        r = toy_result()
        r["per_whale"]["C"]["expected"] = 21.0
        self.assertEqual(check_result(r), ["per whale pairs"])
        r = toy_result()
        r["calibration"]["coda_world"]["size"] = 0.05
        r["calibration"]["bout_world"]["0.10"]["power"] = 0.5
        self.assertEqual(check_result(r), ["coda world size", "bout world power 0.10"])
        r = toy_result()
        r["deployment_test"]["deployments"] = ["A/d1"]
        self.assertEqual(check_result(r), ["deployment test: whales need 2 deployments"])
        r = toy_result()
        r["deployment_test"]["p"] = 0.01234
        self.assertEqual(check_result(r), ["deployment test: p lattice"])

    def test_p_bounds(self):
        r = toy_result()
        w = r["within"]
        w.update(switches=150, q=1.25, p_low=1.0, p_high=0.0001)     # S = null max: p_high > 1/B+1
        r["gap_profile"][0]["switches"] = 130
        r["per_whale"]["A"]["switches"] = 120
        self.assertEqual(check_result(r), ["within: p outside its null"])
        w["p_high"] = 0.0002
        self.assertEqual(check_result(r), [])
        w.update(switches=100, q=100 / 120.0, p_low=0.0001, p_high=0.9)  # inside: p_low >= 2/B+1
        r["gap_profile"][0]["switches"] = 80
        r["per_whale"]["A"]["switches"] = 70
        self.assertEqual(check_result(r), ["within: p outside its null"])
        w["p_low"] = 0.2
        self.assertEqual(check_result(r), [])
        self.assertTrue(p_ok(0.0001, 9999))
        self.assertTrue(p_ok(0.05, 999))
        self.assertFalse(p_ok(0.0, 999))
        self.assertFalse(p_ok(0.0105, 999))

    def test_formats(self):
        r = attach(toy_result())
        rg = regrade(r)
        self.assertEqual(join_line(r), "Join: 1,316 of 1,375 codamd rows matched to a unique "
                                       "DSWP recording time (2 ambiguous, 53 unmatched, 4 not "
                                       "found by coda number)")
        self.assertEqual(units_line(r), "Units: **300** labelled, timed codas of 3 whales in 4 "
                                        "whale-deployments, 5 files and 50 bouts (gap <= 60 s); "
                                        "share of a 0.600")
        self.assertEqual(strata_line(r), "Strata (whale x deployment x coda type): 12; 9 hold "
                                         "both vowels, with 280 codas")
        self.assertEqual(pairs_line(r), "Neighbouring pairs: 295 (250 within bouts, 45 between "
                                        "bouts)")
        self.assertEqual(primary_line(r), "Within-bout switches S = **60**; expected under "
                                          "shuffling E = 120.00; Q = S/E = **0.5000**")
        self.assertEqual(p_line(r), "Primary test (B = 9,999 permutations within whale x "
                                    "deployment x coda type): p_low = **0.0001**, p_high = "
                                    "1.0000; null mean 120.05, sd 7.50, range 90 to 150")
        self.assertEqual(between_line(r), "Between-bout switches 25 of 45 pairs; expected "
                                          "20.00; Q = 1.2500")
        self.assertEqual(gap_row(r["gap_profile"][0]), "| 0-10 s | 200 | 40 | 96.00 | 0.417 |")
        self.assertEqual(whale_row("A", r["per_whale"]["A"]),
                         "| A | 150 | 130 | 30 | 60.00 | 0.500 |")
        self.assertEqual(dep_line(r), "Deployment test (whales A; 2 deployments, 150 codas, 6 "
                                      "whale x coda type x deployment cells): G = 12.500 (null "
                                      "mean 5.000, 95th percentile 11.000), p_dep = **0.0123** "
                                      "(B = 9,999)")
        self.assertEqual(size_line(rg), "Coda world (independent codas, R = 200, B = 999): "
                                        "size **0.040** (8 of 200 rejected; calibration fails "
                                        "above 0.10)")
        self.assertEqual(power_row("0.20", rg), "| 0.20 | 180 of 200 | 0.900 |")
        self.assertEqual(power_line(rg), "Power at eps = 0.20: **0.900** (0.80 or more needed "
                                         "for NO_CLUSTERING_WITH_POWER)")
        self.assertEqual(match_row(6, r), "| 0.30 | 0.5300 |")
        self.assertEqual(match_line(rg), "Matched eps (exploratory): **0.30** (observed Q "
                                         "0.5000)")
        self.assertEqual(verdict_line(rg), "Verdict: **`VOWELS_CLUSTER_STRONGLY`**")
        self.assertEqual(score_lines(rg), ["6 of 7 graded predictions true",
                                           "Brier score **0.114**"])
        self.assertEqual(pred_row("Q7", rg), "| Q7 | p_high <= 0.05 (vowels alternate more "
                                             "than chance) | 0.05 | **false** |")
        r["deployment_test"] = {"skipped": "fewer than 2 eligible deployments", "p": None}
        self.assertEqual(dep_line(r), "Deployment test: skipped (fewer than 2 eligible "
                                      "deployments)")

    def test_md_check(self):
        r = attach(toy_result())
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        # 5 data + 3 primary + 4 gaps + 3 whales + dep + size + 4 power + power line
        # + 11 match + match line + verdict + 2 scores + 7 predictions
        self.assertEqual(len(lines), 44)
        md = render_markdown(r, rg)
        self.assertEqual(check_md(md, r, rg), [])
        v = verdict_line(rg)
        self.assertEqual(check_md(md.replace(v, "Verdict: none"), r, rg), [v])
        no_q3 = "\n".join(ln for ln in md.splitlines() if not ln.startswith("| Q3 |"))
        self.assertEqual(check_md(no_q3, r, rg), ["prediction row Q3"])
        self.assertTrue(all(ord(ch) < 128 for ch in md))


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
