# SPDX-License-Identifier: Apache-2.0
# Tests for vowel_test.py (VOWEL-PREREG.md). Every expected value is worked out by hand or by
# exhaustive enumeration. No real data are read.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import itertools
import math
import unittest

import numpy as np

import vowel_test as vt


def U(i, whale, dep, file, t, y, typ="1+1+3"):
    return {"i": i, "whale": whale, "dep": dep, "file": file, "type": typ, "t": t, "y": y,
            "num": i}


class TestPairs(unittest.TestCase):
    def test_pairs_and_bouts(self):
        us = [U(0, "A", "d1", "f1", 0.0, 1), U(1, "A", "d1", "f1", 5.0, 1),
              U(2, "A", "d1", "f1", 100.0, 0), U(3, "A", "d1", "f2", 101.0, 0),
              U(4, "A", "d2", "g1", 0.0, 1), U(5, "B", "d1", "h1", 1.0, 0)]
        self.assertEqual(vt.pairs_of(us), [(0, 1, 5.0), (1, 2, 95.0)])
        self.assertEqual(vt.bout_ids(us).tolist(), [0, 0, 1, 2, 3, 4])

    def test_build_units(self):
        h = ["codanum", "focal", "whale", "codatype", "Duration", "handv"]
        rows = [["1", "1", "A", "1+1+3", "0.9", "a"], ["2", "1", "A", "5R1", "0.8", "i"],
                ["3", "1", "A", "5R1", "0.8", "x"], ["4", "1", "A", "5R1", "0.8", "a"],
                ["5", "1", "", "5R1", "0.8", "a"]]

        def c(num, whale, typ, rec, t, how="dialogue"):
            return {"codanum": num, "whale": whale or None, "codatype": typ, "rec": rec,
                    "t": t, "join": how}
        codas = [c(1, "A", "1+1+3", "sw061b001_1", 50.0), c(2, "A", "5R1", "sw061b001_2", 10.0),
                 c(3, "A", "5R1", "sw061b001_3", 20.0),
                 c(4, "A", "5R1", None, None, "date_only"), c(5, "", "5R1", "sw061b001_5", 5.0)]
        us = vt.build_units(h, rows, codas)
        self.assertEqual([u["num"] for u in us], [2, 1])
        self.assertEqual([u["y"] for u in us], [0, 1])
        self.assertEqual(us[0]["dep"], "sw061b")
        self.assertEqual(us[0]["file"], "sw061b001")
        self.assertEqual(us[1]["type"], "1+1+3")


class TestStats(unittest.TestCase):
    def test_switches(self):
        y = np.array([1, 1, 0, 0, 1], dtype=np.int8)
        i1, i2 = np.array([0, 1, 2, 3]), np.array([1, 2, 3, 4])
        self.assertEqual(int(vt.switches(y, i1, i2)), 2)
        Y = np.array([[1, 1, 0, 0, 1], [0, 0, 0, 0, 0]], dtype=np.int8)
        self.assertEqual(vt.switches(Y, i1, i2).tolist(), [2, 0])

    def test_expected_exhaustive(self):
        y = np.array([1, 0, 1, 0, 1], dtype=np.int8)
        strata = np.array([0, 0, 0, 1, 1])
        i1, i2 = np.array([0, 1, 2, 3]), np.array([1, 2, 3, 4])
        # 2/3 + 2/3 + 1/2 + 1 = 17/6
        self.assertAlmostEqual(vt.expected_switches(y, strata, i1, i2), 17 / 6, places=12)
        tot, cnt = 0, 0
        for p0 in itertools.permutations([0, 1, 2]):
            for p1 in itertools.permutations([3, 4]):
                z = y.copy()
                z[[0, 1, 2]] = y[list(p0)]
                z[[3, 4]] = y[list(p1)]
                tot += int(vt.switches(z, i1, i2))
                cnt += 1
        self.assertAlmostEqual(tot / cnt, 17 / 6, places=12)
        self.assertEqual(vt.expected_switches(y, strata, np.array([], dtype=np.int64),
                                              np.array([], dtype=np.int64)), 0.0)

    def test_permute_within(self):
        y = np.array([1, 1, 0, 0, 0, 1], dtype=np.int8)
        strata = np.array([0, 1, 0, 1, 0, 1])
        Y = vt.permute_within(y, strata, 600, np.random.default_rng(3))
        self.assertEqual(Y.shape, (600, 6))
        self.assertTrue((Y[:, [0, 2, 4]].sum(axis=1) == 1).all())
        self.assertTrue((Y[:, [1, 3, 5]].sum(axis=1) == 2).all())
        seen = {tuple(r) for r in Y[:, [0, 2, 4]].tolist()}
        self.assertEqual(seen, {(1, 0, 0), (0, 1, 0), (0, 0, 1)})
        Z = vt.permute_within(y, np.arange(6), 5, np.random.default_rng(4))
        self.assertTrue((Z == y[None, :]).all())

    def test_pvalues(self):
        null = np.array([1, 2, 3, 4])
        self.assertEqual(vt.p_low(2, null), 0.6)
        self.assertEqual(vt.p_high(2, null), 0.8)
        self.assertEqual(vt.p_low(0, null), 0.2)

    def test_g(self):
        us = [U(k, "A", "d1" if k < 3 else "d2", "f", float(k), 1 if k < 3 else 0)
              for k in range(6)]
        y = np.array([u["y"] for u in us], dtype=np.int8)
        s, c, nc, cell_s = vt.g_setup(us)
        self.assertEqual(nc.tolist(), [3.0, 3.0])
        self.assertAlmostEqual(float(vt.g_values(y, c, nc, cell_s)[0]), 12 * math.log(2),
                               places=10)
        y2 = np.array([1, 0, 0, 1, 0, 0], dtype=np.int8)
        self.assertAlmostEqual(float(vt.g_values(y2, c, nc, cell_s)[0]), 0.0, places=12)
        Y = np.vstack([y, y2])
        g = vt.g_values(Y, c, nc, cell_s)
        self.assertEqual(g.shape, (2,))

    def test_dep_units(self):
        us = ([U(k, "A", "d1", "f", float(k), 1) for k in range(10)]
              + [U(10 + k, "A", "d2", "f", float(k), 0) for k in range(10)]
              + [U(20 + k, "A", "d3", "f", float(k), 0) for k in range(9)]
              + [U(30 + k, "B", "d1", "f", float(k), 0) for k in range(30)])
        du = vt.dep_units(us)
        self.assertEqual(len(du), 20)
        self.assertEqual({u["dep"] for u in du}, {"d1", "d2"})


class TestDecision(unittest.TestCase):
    def test_verdicts(self):
        v = vt.verdict_of
        self.assertEqual(v(199, 10.0, 0.0, 0.01, 0.2, 0.9), "INSUFFICIENT_DATA")
        self.assertEqual(v(300, 0.0, 0.0, 0.01, 0.2, 0.9), "INSUFFICIENT_DATA")
        self.assertEqual(v(300, 10.0, 0.15, 0.01, 0.2, 0.9), "CALIBRATION_FAILED")
        self.assertEqual(v(300, 10.0, float("nan"), 0.01, 0.2, 0.9), "CALIBRATION_FAILED")
        self.assertEqual(v(300, 10.0, 0.10, 0.01, 0.5, 0.9), "VOWELS_CLUSTER_STRONGLY")
        self.assertEqual(v(300, 10.0, 0.05, 0.05, 0.6, 0.1), "VOWELS_CLUSTER_WEAKLY")
        self.assertEqual(v(300, 10.0, 0.05, 0.2, 0.9, 0.8), "NO_CLUSTERING_WITH_POWER")
        self.assertEqual(v(300, 10.0, 0.05, 0.2, 0.9, 0.79), "UNDERPOWERED")

    def test_grade(self):
        r = {"n_within_bout_pairs": 100, "n_between_bout_pairs": 10,
             "within": {"switches": 20, "p_low": 0.01, "p_high": 0.99, "q": 0.4},
             "between": {"switches": 5},
             "deployment_test": {"p": 0.2},
             "calibration": {"coda_world": {"size": 0.05},
                             "bout_world": {"0.20": {"power": 0.9}}}}
        pred, brier = vt.grade(r)
        self.assertEqual([pred[k] for k in vt.ORDER],
                         [True, True, False, True, True, True, False])
        # .09 + .36 + .3025 + .0225 + .0009 + .1225 + .0025 = .9009
        self.assertAlmostEqual(brier, 0.9009 / 7, places=12)


class TestEndToEnd(unittest.TestCase):
    def test_bout_world_clusters(self):
        us = vt.synthetic_units(seed=11, eps=0.0)
        r = vt.analyse(us, b_primary=199, b_dep=199, r_cal=10, b_cal=99, r_match=2)
        self.assertEqual(r["n_units"], 768)
        self.assertEqual(r["n_within_bout_pairs"], 672)
        self.assertEqual(r["within"]["switches"], 0)
        self.assertEqual(r["within"]["p_low"], 1 / 200)
        self.assertEqual(r["within"]["q"], 0.0)
        self.assertIn(r["verdict"], ("VOWELS_CLUSTER_STRONGLY", "CALIBRATION_FAILED"))
        self.assertEqual(sorted(r["calibration"]["bout_world"]), ["0.05", "0.10", "0.20",
                                                                  "0.30"])
        self.assertEqual(len(r["match"]["mean_q"]), 11)
        self.assertEqual(sorted(r["predictions"]), list(vt.ORDER))
        self.assertTrue(r["deployment_test"]["n_units"] > 0)

    def test_insufficient(self):
        us = vt.synthetic_units(seed=12, whales=1, deps=1, files=1, bouts_per_file=3)
        r = vt.analyse(us, b_primary=99, b_dep=99, r_cal=2, b_cal=19, r_match=1)
        self.assertEqual(r["n_within_bout_pairs"], 21)
        self.assertEqual(r["verdict"], "INSUFFICIENT_DATA")
        self.assertIsNone(r["predictions"])


if __name__ == "__main__":
    unittest.main()
