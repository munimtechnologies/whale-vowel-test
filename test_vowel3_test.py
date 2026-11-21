# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made with AI agents working in MV2's name.
"""Unit tests for vowel3_test.py (no real data needed)."""
import csv
import json
import math
import os
import tempfile
import unittest
from itertools import combinations

import numpy as np

import vowel3_test as v3

HEADER = ["whale", "coart", "prevhandvcat", "handvcat", "tagondt", "deltasec", "numpks", "prevnumpks"]
VERDICTS = {"INSUFFICIENT_DATA", "NOT_REPRODUCED", "CALIBRATION_FAILED", "CARRYOVER_SPECIFIC",
            "REVERSED_ASYMMETRY", "SYMMETRIC_WITH_POWER", "UNDERPOWERED"}


def row(whale, typ, mf, ml, dep="T1", gap=2.0):
    return {"whale": whale, "dep": whale + "|" + dep, "type": typ, "coart": "aa" if typ == "N" else "ai",
            "deltasec": gap, "mf": mf, "ml": ml}


class Parsing(unittest.TestCase):
    def test_mismatch_table(self):
        self.assertEqual(v3.mismatch("a", 1), 0)
        self.assertEqual(v3.mismatch("i", 2), 0)
        self.assertEqual(v3.mismatch("a", 2), 1)
        self.assertEqual(v3.mismatch("i", 1), 1)
        self.assertIsNone(v3.mismatch("a", 3))
        self.assertIsNone(v3.mismatch("", 1))
        self.assertIsNone(v3.mismatch("i", None))

    def test_change_type(self):
        self.assertEqual(v3.change_type("aa"), "N")
        self.assertEqual(v3.change_type("ii"), "N")
        self.assertEqual(v3.change_type("ai"), "C")
        self.assertEqual(v3.change_type("ia"), "C")
        self.assertIsNone(v3.change_type("ab"))
        self.assertIsNone(v3.change_type(""))

    def test_numbers(self):
        self.assertEqual(v3.to_int("2.0"), 2)
        self.assertEqual(v3.to_int(" 1 "), 1)
        self.assertIsNone(v3.to_int("2.5"))
        self.assertIsNone(v3.to_int(""))
        self.assertIsNone(v3.to_int("nan"))
        self.assertIsNone(v3.to_float("NA"))
        self.assertEqual(v3.to_float("4.5"), 4.5)

    def test_load_rows_filters(self):
        data = [
            ["PINCHY", "aa", "a", "a", "T1", "5.0", "1", "1"],
            ["PINCHY", "ai", "a", "i", "T1", "3.0", "1", "1"],
            ["FORK", "ia", "i", "a", "T2", "0", "1", "2"],
            ["FORK", "ia", "i", "a", "T2", "10", "1", "2"],
            ["SAM", "aa", "a", "a", "T9", "2.0", "1", "1"],
            ["TBB", "ab", "a", "b", "T3", "2.0", "1", "1"],
            ["ATWOOD", "ii", "i", "a", "T4", "1.5", "2.0", ""],
            ["ATWOOD", "aa", "a", "a", "T4", "NA", "1", "1"],
        ]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv")
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(HEADER)
                w.writerows(data)
            rows, issues = v3.load_rows(p)
        self.assertEqual(issues, {"rows": 8, "bad_deltasec": 1, "out_of_window": 2, "other_whale": 1,
                                  "no_type": 1, "coart_conflicts": 1})
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["type"], "N")
        self.assertEqual((rows[0]["mf"], rows[0]["ml"]), (0, 0))
        self.assertEqual(rows[1]["type"], "C")
        self.assertEqual((rows[1]["mf"], rows[1]["ml"]), (1, 0))
        self.assertEqual(rows[1]["dep"], "PINCHY|T1")
        self.assertEqual(rows[2]["type"], "N")
        self.assertEqual(rows[2]["mf"], 1)
        self.assertIsNone(rows[2]["ml"])
        P = v3.paired(rows)[0]
        self.assertEqual(len(P), 2)


class Statistics(unittest.TestCase):
    def test_delta_is_linear(self):
        rng = np.random.default_rng(1)
        mf = (rng.random(50) < 0.3).astype(float)
        ml = (rng.random(50) < 0.2).astype(float)
        c = rng.random(50) < 0.25
        c[0], c[1] = True, False
        self.assertAlmostEqual(v3.delta(mf - ml, c), v3.delta(mf, c) - v3.delta(ml, c), places=12)
        self.assertTrue(math.isnan(v3.delta(mf, np.zeros(50, dtype=bool))))

    def test_perm_null_constant_when_strata_pure(self):
        y = np.array([1.0, 0.0, 1.0, 1.0])
        s = np.array([0, 0, 1, 1])
        c = np.array([True, True, False, False])
        null = v3.perm_null([y], s, c, np.random.default_rng(2), 50)
        self.assertEqual(null.shape, (1, 50))
        self.assertTrue(np.allclose(null[0], v3.delta(y, c)))

    def test_perm_null_values_are_relabellings(self):
        y = np.array([0.0, 1.0, 1.0, 0.0, 1.0, 0.0])
        s = np.zeros(6, dtype=int)
        c = np.array([True, True, False, False, False, False])
        possible = set()
        for sel in combinations(range(6), 2):
            cc = np.zeros(6, dtype=bool)
            cc[list(sel)] = True
            possible.add(round(v3.delta(y, cc), 9))
        null = v3.perm_null([y], s, c, np.random.default_rng(3), 400)[0]
        for v in null:
            self.assertIn(round(float(v), 9), possible)
        self.assertGreater(len(set(np.round(null, 9))), 1)

    def test_perm_null_centred(self):
        rng = np.random.default_rng(4)
        y = rng.random(60)
        s = np.repeat([0, 1, 2], 20)
        c = rng.random(60) < 0.3
        c[0], c[25], c[45] = True, True, True
        c[1], c[26], c[46] = False, False, False
        null = v3.perm_null([y], s, c, np.random.default_rng(5), 2000)[0]
        # each stratum's change count is kept, so the expectation is the stratified mean difference
        nC = c.sum()
        nN = 60 - nC
        exp_sumC = sum(c[s == k].sum() * y[s == k].mean() for k in range(3))
        expected = exp_sumC / nC - (y.sum() - exp_sumC) / nN
        self.assertLess(abs(null.mean() - expected), 4 * null.std() / math.sqrt(2000) + 1e-12)

    def test_p_values(self):
        null = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(v3.p_low(null, 2.0), 0.75)
        self.assertAlmostEqual(v3.p_high(null, 2.0), 0.75)
        self.assertAlmostEqual(v3.p_high(null, 5.0), 0.25)
        self.assertAlmostEqual(v3.p_low(null, 5.0), 1.0)


class Worlds(unittest.TestCase):
    def test_world_swap_keeps_each_pair(self):
        rng = np.random.default_rng(6)
        mf = (rng.random(200) < 0.4).astype(float)
        ml = (rng.random(200) < 0.1).astype(float)
        a, b = v3.world_swap(mf, ml, rng)
        for i in range(200):
            self.assertEqual(sorted([a[i], b[i]]), sorted([mf[i], ml[i]]))
        self.assertTrue(np.any(a != mf))

    def test_plant(self):
        rng = np.random.default_rng(7)
        c = np.zeros(300, dtype=bool)
        c[:100] = True
        mf = np.zeros(300)
        out = v3.plant(mf, c, 0.5, rng)
        self.assertTrue(np.all(out[100:] == 0))
        self.assertTrue(np.all(out >= mf))
        self.assertTrue(0.3 < out[:100].mean() < 0.7)
        self.assertTrue(np.array_equal(v3.plant(mf, c, 0.0, rng), mf))


class Verdicts(unittest.TestCase):
    def test_rules(self):
        V = v3.verdict
        self.assertEqual(V(5, 0.01, 0.1, 0.01, 0.99, 0.05, 0.9), "INSUFFICIENT_DATA")
        self.assertEqual(V(20, 0.2, 0.1, 0.01, 0.99, 0.05, 0.9), "NOT_REPRODUCED")
        self.assertEqual(V(20, 0.01, -0.1, 0.01, 0.99, 0.05, 0.9), "NOT_REPRODUCED")
        self.assertEqual(V(20, 0.01, 0.1, 0.5, 0.5, 0.2, 0.9), "CALIBRATION_FAILED")
        self.assertEqual(V(20, 0.01, 0.1, 0.5, 0.5, float("nan"), 0.9), "CALIBRATION_FAILED")
        self.assertEqual(V(20, 0.01, 0.1, 0.03, 0.98, 0.05, 0.9), "CARRYOVER_SPECIFIC")
        self.assertEqual(V(20, 0.01, 0.1, 0.99, 0.02, 0.05, 0.9), "REVERSED_ASYMMETRY")
        self.assertEqual(V(20, 0.01, 0.1, 0.5, 0.5, 0.05, 0.85), "SYMMETRIC_WITH_POWER")
        self.assertEqual(V(20, 0.01, 0.1, 0.5, 0.5, 0.05, 0.5), "UNDERPOWERED")


class EndToEnd(unittest.TestCase):
    def test_planted_carryover(self):
        rows = []
        for dep in ("T1", "T2"):
            for k in range(20):
                rows.append(row("PINCHY", "C", 1, 0, dep, gap=1.0 + 0.1 * k))
            for k in range(100):
                both = 1 if k < 5 else 0
                rows.append(row("PINCHY", "N", both, both, dep, gap=1.0 + 0.05 * k))
        res = v3.run(rows, B=199, R=3, Bc=99, log=lambda s: None)
        m = res["main"]
        self.assertAlmostEqual(m["first"]["obs"], 0.95, places=12)
        self.assertAlmostEqual(m["last"]["obs"], -0.05, places=12)
        self.assertAlmostEqual(m["asym"]["obs"], 1.0, places=12)
        self.assertAlmostEqual(m["first"]["p_high"], 1 / 200)
        self.assertAlmostEqual(m["asym"]["p_high"], 1 / 200)
        self.assertEqual(res["n_paired"], 240)
        self.assertEqual(res["n_change"], 40)
        self.assertEqual(res["n_deployments"], 2)
        self.assertIn(res["verdict"], VERDICTS)
        self.assertTrue(res["predictions"]["P1"]["outcome"])
        self.assertFalse(res["predictions"]["P2"]["outcome"])
        cleaned = v3.clean(res)
        json.dumps(cleaned, allow_nan=False, sort_keys=True)
        md = v3.render(cleaned)
        self.assertIn("RESULTS-COART", md)
        self.assertIn("first-click mismatch", md)

    def test_no_change_rows(self):
        rows = [row("FORK", "N", 0, 0, gap=1.0 + k) for k in range(5)]
        res = v3.run(rows, B=99, R=2, Bc=49, log=lambda s: None)
        self.assertEqual(res["verdict"], "INSUFFICIENT_DATA")
        md = v3.render(v3.clean(res))
        self.assertIn("INSUFFICIENT_DATA", md)


if __name__ == "__main__":
    unittest.main()
