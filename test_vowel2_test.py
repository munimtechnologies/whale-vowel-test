# SPDX-License-Identifier: Apache-2.0
# test_vowel2_test.py: unit tests of vowel2_test.py (VOWEL2-PREREG.md). Synthetic data only;
# every exact value is worked out by hand in the comments. Needs numpy, describe_vowels.py and
# vowel_test.py (commit eff4365) next to it. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI
# agents. Apache-2.0.
import unittest

import numpy as np

import vowel2_test as v2


class TestLabels(unittest.TestCase):
    def test_vowel_of(self):
        self.assertEqual(v2.vowel_of("a"), 1)
        self.assertEqual(v2.vowel_of(" i "), 0)
        self.assertEqual(v2.vowel_of("ai"), 1)     # the R rule grepl("^a") takes it as a
        self.assertEqual(v2.vowel_of("i?"), 0)
        self.assertIsNone(v2.vowel_of(""))
        self.assertIsNone(v2.vowel_of("?"))
        self.assertIsNone(v2.vowel_of(None))


def coda(join, t=None, rec=None, num=None, date=None):
    return {"join": join, "t": t, "rec": rec, "codanum": num, "date": date}


class TestBuild(unittest.TestCase):
    def test_build(self):
        h = ["codanum", "focal", "whale", "codatype", "Duration", "handv"]
        rows = [["1", "True", "ATWOOD", "1+1+3", "1.2", "a"],
                ["2", "True", "ATWOOD", "1+1+3", "1.0", "i"],
                ["3", "True", "ATWOOD", "5R1", "0.9", "i"],
                ["4", "True", "SAM", "1+1+3", "1.1", "a"],
                ["5", "True", "", "1+1+3", "1.1", "a"],
                ["6", "True", "FORK", "1+1+3", "", "a"],
                ["7", "True", "FORK", "1+1+3", "1.3", "?"]]
        codas = [coda("dialogue", 10.0, "sw061b001_1", 1, "2015-01-01"),
                 coda("dialogue", 5.0, "sw061b001_1", 2, "2015-01-01"),
                 coda("dialogue", 100.0, "sw061b001_2", 3, "2015-01-01"),
                 coda("date_only", None, None, 4, "2015-01-02"),
                 coda("dialogue", 1.0, "sw061b001_3", 5, "2015-01-01"),
                 coda("dialogue", 3.0, "sw070a002_5", 6, "2016-02-02"),
                 coda("dialogue", 4.0, "sw070a002_5", 7, "2016-02-02")]
        pub, timed, dset = v2.build(h, rows, codas)
        # pub: rows 1 and 2 only (SAM is not one of the four, row 6 has no duration)
        self.assertEqual([u["i"] for u in pub], [0, 1])
        # timed: rows 1, 2, 3 (ATWOOD, by time 5, 10, 100) and 6 (FORK)
        self.assertEqual([u["i"] for u in timed], [1, 0, 2, 5])
        # gap 10 -> 100 is 90 s > 60 s: new bout; FORK is a new run
        self.assertEqual([u["bout"] for u in timed], [0, 0, 1, 2])
        self.assertEqual([u["dep"] for u in timed], ["sw061b", "sw061b", "sw061b", "sw070a"])
        # dset: the timed 1+1+3 codas of the four whales with a duration
        self.assertEqual([u["i"] for u in dset], [1, 0])
        self.assertEqual([u["y"] for u in dset], [0, 1])


class TestContrast(unittest.TestCase):
    def test_hand_example(self):
        # group 0: a 3 vs i 1, 2 -> diff 1.5, W = 1*2/3; group 1: a 5 vs i 1 -> diff 4, W = 1/2
        # D = (2/3*1.5 + 1/2*4) / (7/6) = 3 / (7/6) = 18/7; K = 1*6/3 + 1*6/2 = 5
        # group 2 holds only a: left out
        g = np.array([0, 0, 0, 1, 1, 2, 2])
        y = np.array([1, 0, 0, 1, 0, 1, 1], dtype=np.int8)
        d = np.array([3.0, 1.0, 2.0, 5.0, 1.0, 9.0, 9.0])
        s = v2.contrast_setup(y, d, g)
        self.assertAlmostEqual(s["W"], 7.0 / 6.0, places=12)
        self.assertAlmostEqual(s["K"], 5.0, places=12)
        self.assertEqual((s["groups"], s["minority"], s["units"]), (2, 2, 5))
        self.assertAlmostEqual(float(v2.contrast(y, d, s)), 18.0 / 7.0, places=12)
        # a relabelling with the same counts: group 0 a on the 2, group 1 a on the 1
        # diffs 2 - mean(3, 1) = 0 and 1 - 5 = -4 -> (0 - 2) / (7/6) = -12/7 (= (2 + 1 - 5) / W)
        y2 = np.array([0, 0, 1, 0, 1, 1, 1], dtype=np.int8)
        self.assertAlmostEqual(float(v2.contrast(y2, d, s)), -12.0 / 7.0, places=12)
        # shifting every a-coda by delta shifts D by exactly delta
        s3 = v2.contrast_setup(y, d + 0.25 * y, g)
        self.assertAlmostEqual(float(v2.contrast(y, d + 0.25 * y, s3)), 18.0 / 7.0 + 0.25,
                               places=12)

    def test_perm_test(self):
        g = np.zeros(6, dtype=np.int64)
        y = np.array([1, 1, 1, 0, 0, 0], dtype=np.int8)
        d = np.array([3.0, 3.0, 3.0, 1.0, 1.0, 1.0])
        r = v2.perm_test(y, d, g, 999, np.random.default_rng(5))
        self.assertAlmostEqual(r["d"], 2.0, places=12)
        self.assertEqual(r["p_low"], 1.0)            # every relabelling gives D <= 2
        # D = 2 only for the original split: chance 1/20, so p_high is near 0.05
        self.assertTrue(0.02 < r["p_high"] < 0.10)
        k = r["p_high"] * 1000 - 1
        self.assertAlmostEqual(k, round(k), places=6)
        none = v2.perm_test(np.ones(6, dtype=np.int8), d, g, 99, np.random.default_rng(1))
        self.assertIsNone(none["d"])
        self.assertEqual((none["p_high"], none["p_low"], none["groups"]), (1.0, 1.0, 0))

    def test_rotation(self):
        g = np.array([0, 0, 0, 0, 1, 1, 1, 2])
        y = np.array([1, 1, 0, 0, 1, 0, 0, 1], dtype=np.int8)
        idx = v2.group_index(g)
        self.assertEqual([list(ix) for ix in idx], [[0, 1, 2, 3], [4, 5, 6]])
        rng = np.random.default_rng(3)
        for _ in range(20):
            yr = v2.rotate_within(y, idx, rng)
            self.assertEqual(list(np.bincount(g, weights=yr)), [2.0, 1.0, 1.0])
            # a rotation keeps the run structure: group 0 is a cyclic shift of 1100
            self.assertIn("".join(str(int(x)) for x in yr[:4]),
                          ("1100", "0110", "0011", "1001"))
        p = v2.rotation_p(y, np.arange(8, dtype=float), g, 99, np.random.default_rng(4))
        k = p * 100 - 1
        self.assertAlmostEqual(k, round(k), places=6)
        self.assertTrue(0.0 < p <= 1.0)


class TestModes(unittest.TestCase):
    def test_split_point(self):
        # [1, 1.1, 1.2 | 3, 3.1]: SS 0.02 + 0.005 beats every other split
        self.assertAlmostEqual(v2.split_point([3.1, 1.0, 1.2, 3.0, 1.1]), 2.1, places=12)
        self.assertAlmostEqual(v2.split_point([1.0, 2.0, 10.0, 11.0]), 6.0, places=12)
        self.assertIsNone(v2.split_point([1.0, 2.0, 3.0]))
        self.assertIsNone(v2.split_point([1.0, 1.0, 1.0, 1.0]))


class TestDecision(unittest.TestCase):
    def test_verdicts(self):
        f = v2.verdict_of
        self.assertEqual(f(None, True, 0.0, 0.01, 0.99, 0.9), "INSUFFICIENT_DATA")
        self.assertEqual(f("bout", False, 0.0, 0.01, 0.99, 0.9), "NOT_REPRODUCED")
        self.assertEqual(f("bout", True, 0.105, 0.01, 0.99, 0.9),
                         "CALIBRATION_FAILED_WITHIN_BOUTS")
        self.assertEqual(f("bout", True, float("nan"), 0.01, 0.99, 0.9),
                         "CALIBRATION_FAILED_WITHIN_BOUTS")
        self.assertEqual(f("bout", True, 0.10, 0.05, 0.99, 0.1),
                         "DURATION_DIFFERENCE_WITHIN_BOUTS")
        self.assertEqual(f("deployment", True, 0.05, 0.3, 0.05, 0.9),
                         "REVERSED_WITHIN_DEPLOYMENTS")
        self.assertEqual(f("bout", True, 0.05, 0.3, 0.7, 0.80),
                         "NO_DIFFERENCE_WITH_POWER_WITHIN_BOUTS")
        self.assertEqual(f("deployment", True, 0.05, 0.3, 0.7, 0.795),
                         "UNDERPOWERED_WITHIN_DEPLOYMENTS")
        self.assertEqual(f("bout", True, 0.05, 0.3, 0.7, float("nan")),
                         "UNDERPOWERED_WITHIN_BOUTS")

    def test_level(self):
        t = {"within_bout": {"groups": 5, "minority": 14},
             "within_dep": {"groups": 5, "minority": 15}}
        self.assertEqual(v2.level_of(t), "deployment")
        t["within_bout"]["minority"] = 15
        self.assertEqual(v2.level_of(t), "bout")
        t["within_bout"]["groups"] = 4
        t["within_dep"]["groups"] = 4
        self.assertIsNone(v2.level_of(t))


class TestSynthetic(unittest.TestCase):
    def test_effect_found_within_bouts(self):
        # every bout holds both vowels at eps 0.3; a-codas 0.3 s longer; noise sd 0.02
        u = v2.synthetic(seed=3, effect=0.3, eps=0.3, tempo_sd=0.05)
        y = np.array([x["y"] for x in u], dtype=np.int8)
        d = np.array([x["dur"] for x in u])
        g = v2.strata_ids(u, ("bout",))
        r = v2.perm_test(y, d, g, 99, np.random.default_rng(1))
        self.assertTrue(abs(r["d"] - 0.3) < 0.05)
        self.assertEqual(r["p_high"], 0.01)

    def test_analyse_runs(self):
        u = v2.synthetic(seed=4, effect=0.0, eps=0.15)
        r = v2.analyse(u, u, b_main=99, b_rot=99, r_cal=4, b_cal=49)
        self.assertEqual(r["n_pub"], 256)
        self.assertEqual(r["n_dur"], 256)
        self.assertEqual(r["n_bouts_dur"], 32)
        self.assertEqual(r["n_deployments_dur"], 8)
        self.assertIn(r["level"], ("bout", "deployment", None))
        self.assertEqual(sorted(r["predictions"]), list(v2.ORDER))
        self.assertTrue(0.0 <= r["brier"] <= 1.0)
        self.assertEqual(len(r["per_deployment"]), 8)
        self.assertEqual(sorted(r["modes"]["per_whale"]), sorted(v2.FOUR))
        if r["level"] is not None:
            c = r["calibration"]
            self.assertEqual(len(c["size"]["p"]), 4)
            self.assertEqual(len(c["false_alarm"]["naive_p_high"]), 4)
        v, pred, brier = v2.grade(r)
        self.assertEqual((v, pred, brier), (r["verdict"], r["predictions"], r["brier"]))
        # the same seeds give the same result
        r2 = v2.analyse(u, u, b_main=99, b_rot=99, r_cal=4, b_cal=49)
        self.assertEqual(r2["tests"]["within_bout"], r["tests"]["within_bout"])


if __name__ == "__main__":
    unittest.main()
