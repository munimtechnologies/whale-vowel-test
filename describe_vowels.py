# SPDX-License-Identifier: Apache-2.0
# describe_vowels.py: label-structure description for a planned, pre-registered test of the
# sperm whale "coda vowel" claim (Begus, Sprouse, Leban, Silva & Gero 2025, Open Mind,
# doi 10.1162/opmi.a.252; data OSF a32ke). It joins the paper's hand vowel labels (codamd.csv)
# to the Dominica Sperm Whale Project coda tables of Sharma et al. 2024 (GitHub
# pratyushasharma/sw-combinatoriality: DominicaCodas.csv by coda number, sperm-whale-dialogues.csv
# by exact click timing), which adds the recording date, the tag recording (REC) and the time of
# each coda. It reports ONLY how the labelled codas are spread over whales, dates, tag
# deployments, files and bouts, plus match rates. It computes no statistic of the vowel labels by
# group (no vowel share per whale, day, deployment or bout): the test is to be registered first.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict

VERSION = "vowel-describe-1"
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com)"
SOURCES = {
    "codamd.csv": "https://osf.io/download/8jmp7/",
    "DominicaCodas.csv": "https://raw.githubusercontent.com/pratyushasharma/"
                         "sw-combinatoriality/main/data/DominicaCodas.csv",
    "sperm-whale-dialogues.csv": "https://raw.githubusercontent.com/pratyushasharma/"
                                 "sw-combinatoriality/main/data/sperm-whale-dialogues.csv",
}
GAPS = (30.0, 60.0, 300.0)
MIN_UNIT = (5, 10, 20)
DUR_TOL = 1e-6


# ----------------------------------------------------------------------- pure helpers
def fnum(s):
    try:
        x = float((s or "").strip())
    except ValueError:
        return None
    return x if x == x and abs(x) != float("inf") else None


def inum(s):
    x = fnum(s)
    return int(x) if x is not None and x == int(x) else None


def read_table(text):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return [], []
    return [h.strip() for h in rows[0]], rows[1:]


def getter(header):
    idx = {h: i for i, h in enumerate(header)}
    low = {h.lower(): i for i, h in enumerate(header)}

    def g(row, name):
        i = idx.get(name)
        if i is None:
            i = low.get(name.lower())
        if i is None or i >= len(row):
            return ""
        return row[i].strip()
    return g


def ici_list(g, row, n_clicks, max_ici):
    """The first min(nClicks - 1, max_ici) inter-click intervals, as floats."""
    k = max(0, min((n_clicks or 0) - 1, max_ici))
    out = []
    for j in range(1, k + 1):
        v = fnum(g(row, "ICI%d" % j))
        if v is None:
            return None
        out.append(v)
    return out


def timing_key(n_clicks, duration, icis):
    """Exact-timing key shared by both DSWP tables (rounded to 1e-5 s)."""
    if n_clicks is None or duration is None or icis is None:
        return None
    return (n_clicks, round(duration, 5)) + tuple(round(v, 5) for v in icis)


def deployment_of(rec):
    """Tag deployment of a DTAG recording name, e.g. 'sw061b001_124' -> 'sw061b'."""
    m = re.match(r"([a-z]{2}\d{2,3}[a-z])", (rec or "").strip().lower())
    return m.group(1) if m else None


def file_of(rec):
    return (rec or "").strip().split("_")[0] or None


def bouts(times, gap):
    """Sizes of the bouts in a list of times (a new bout after a silence longer than gap)."""
    ts = sorted(times)
    if not ts:
        return []
    sizes = [1]
    for a, b in zip(ts, ts[1:]):
        if b - a > gap:
            sizes.append(1)
        else:
            sizes[-1] += 1
    return sizes


def summary(v):
    v = sorted(v)
    if not v:
        return {"n": 0}
    return {"n": len(v), "min": v[0], "median": v[len(v) // 2], "max": v[-1],
            "sum": sum(v)}


# ----------------------------------------------------------------------- the join
def join(md_h, md_rows, dc_h, dc_rows, dl_h, dl_rows):
    gm, gc, gd = getter(md_h), getter(dc_h), getter(dl_h)
    dc = {}
    for row in dc_rows:
        k = inum(gc(row, "codaNUM2018"))
        if k is not None:
            dc[k] = row
    dl = defaultdict(list)
    for row in dl_rows:
        n = inum(gd(row, "nClicks"))
        key = timing_key(n, fnum(gd(row, "Duration")), ici_list(gd, row, n, 9))
        if key is not None:
            dl[key].append(row)
    counts = Counter()
    out = []
    for row in md_rows:
        counts["codamd_rows"] += 1
        num = inum(gm(row, "codanum"))
        rec = {"codanum": num, "whale": gm(row, "whale") or None,
               "codatype": gm(row, "codatype") or None,
               "labelled": gm(row, "handv") in ("a", "i"),
               "date": None, "idn": None, "unit": None, "rec": None, "dlg_whale": None,
               "t": None, "join": "none"}
        if rec["labelled"]:
            counts["labelled"] += 1
        if rec["whale"]:
            counts["with_whale_name"] += 1
        d = dc.get(num)
        dur = fnum(gm(row, "Duration"))
        if d is None:
            counts["dc_missing"] += 1
        elif dur is None or fnum(gc(d, "Duration")) is None \
                or abs(fnum(gc(d, "Duration")) - dur) > DUR_TOL:
            counts["dc_duration_mismatch"] += 1
        else:
            counts["dc_matched"] += 1
            rec.update(date=gc(d, "Date") or None, idn=gc(d, "IDN") or None,
                       unit=gc(d, "Unit") or None)
            if (gc(d, "CodaType") or None) != rec["codatype"]:
                counts["dc_codatype_differs"] += 1
            n = inum(gc(d, "nClicks"))
            key = timing_key(n, fnum(gc(d, "Duration")), ici_list(gc, d, n, 9))
            hits = dl.get(key, []) if key is not None else []
            if len(hits) == 1:
                h = hits[0]
                counts["dialogue_matched"] += 1
                rec.update(rec=gd(h, "REC") or None, dlg_whale=gd(h, "Whale") or None,
                           t=fnum(gd(h, "TsTo")), join="dialogue")
            elif len(hits) > 1:
                counts["dialogue_ambiguous"] += 1
                recs = sorted({gd(h, "REC") for h in hits})
                rec["join"] = "ambiguous"
                if len(recs) == 1:
                    counts["dialogue_ambiguous_same_rec"] += 1
            else:
                counts["dialogue_unmatched"] += 1
                rec["join"] = "date_only"
        out.append(rec)
    return out, dict(counts)


def describe(codas):
    """Label-free structure of the labelled, named codas (no vowel statistic by group)."""
    lab = [c for c in codas if c["labelled"] and c["whale"]]
    by_whale = defaultdict(list)
    for c in lab:
        by_whale[c["whale"]].append(c)
    whales = {}
    units = {"whale_date": Counter(), "whale_deployment": Counter(), "whale_file": Counter()}
    bout_units = {str(g): [] for g in GAPS}
    t_ok = 0
    for w in sorted(by_whale):
        cs = by_whale[w]
        dates = Counter(c["date"] for c in cs if c["date"])
        deps = Counter(d for d in (deployment_of(c["rec"]) for c in cs) if d)
        files = Counter(f for f in (file_of(c["rec"]) for c in cs if c["rec"]) if f)
        for k, v in dates.items():
            units["whale_date"][(w, k)] = v
        for k, v in deps.items():
            units["whale_deployment"][(w, k)] = v
        for k, v in files.items():
            units["whale_file"][(w, k)] = v
        per_dep = {}
        for dname in sorted(deps):
            ts = [c["t"] for c in cs if c["rec"] and deployment_of(c["rec"]) == dname
                  and c["t"] is not None]
            t_ok += len(ts)
            entry = {"codas": deps[dname],
                     "time_span_s": round(max(ts) - min(ts), 3) if ts else None,
                     "dates": sorted({c["date"] for c in cs if c["rec"]
                                      and deployment_of(c["rec"]) == dname and c["date"]})}
            for g in GAPS:
                b = bouts(ts, g)
                entry["bouts_gap_%g" % g] = summary(b)
                bout_units[str(g)] += b
            per_dep[dname] = entry
        whales[w] = {"labelled_codas": len(cs),
                     "idn": dict(Counter(c["idn"] for c in cs if c["idn"])),
                     "dialogue_whale_codes": dict(Counter(
                         "%s/%s" % (deployment_of(c["rec"]), c["dlg_whale"])
                         for c in cs if c["rec"])),
                     "dates": dict(sorted(dates.items())), "deployments": per_dep,
                     "files": dict(sorted(files.items())),
                     "coda_types": dict(Counter(c["codatype"] or "" for c in cs)
                                        .most_common()),
                     "join": dict(Counter(c["join"] for c in cs))}

    def unit_table(cnt):
        sizes = list(cnt.values())
        return {"units": len(sizes), "sizes": summary(sizes),
                "with_at_least": {str(m): sum(1 for s in sizes if s >= m) for m in MIN_UNIT},
                "codas_in_units_with_at_least": {str(m): sum(s for s in sizes if s >= m)
                                                 for m in MIN_UNIT}}
    return {"labelled_named_codas": len(lab), "with_time": t_ok, "whales": whales,
            "units": {k: unit_table(v) for k, v in units.items()},
            "bouts": {g: {"bouts": len(v), "sizes": summary(v),
                          "with_at_least": {str(m): sum(1 for s in v if s >= m)
                                            for m in MIN_UNIT}}
                      for g, v in bout_units.items()},
            "deployments_per_whale": {w: len(whales[w]["deployments"]) for w in whales},
            "dates_per_whale": {w: len(whales[w]["dates"]) for w in whales}}


# ----------------------------------------------------------------------- I/O
def fetch(name, url, data_dir):
    path = os.path.join(data_dir, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            b = f.read()
        return b, hashlib.md5(b).hexdigest()
    last = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                b = r.read()
            with open(path + ".part", "wb") as f:
                f.write(b)
            os.replace(path + ".part", path)
            return b, hashlib.md5(b).hexdigest()
        except Exception as e:  # noqa: BLE001 - retried, then re-raised
            last = e
            time.sleep(5 * (i + 1))
    raise last


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)
    r = {"version": VERSION, "python": sys.version.split()[0],
         "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": {}}
    tables = {}
    for name, url in SOURCES.items():
        b, h = fetch(name, url, a.data_dir)
        r["files"][name] = {"url": url, "bytes": len(b), "md5": h}
        tables[name] = read_table(b.decode("utf-8-sig", errors="replace"))
        r["files"][name]["header"] = tables[name][0]
        r["files"][name]["rows"] = len(tables[name][1])
    md, dc, dl = (tables["codamd.csv"], tables["DominicaCodas.csv"],
                  tables["sperm-whale-dialogues.csv"])
    codas, counts = join(md[0], md[1], dc[0], dc[1], dl[0], dl[1])
    r["join_counts"] = counts
    r["describe"] = describe(codas)
    r["recordings_in_dialogues"] = len({getter(dl[0])(row, "REC") for row in dl[1]})
    r["deployments_in_dialogues"] = sorted({deployment_of(getter(dl[0])(row, "REC"))
                                            for row in dl[1]} - {None})
    with open(os.path.join(a.out_dir, "vowel_describe.json"), "w") as f:
        json.dump(r, f, indent=1, sort_keys=True)
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
