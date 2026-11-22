# SPDX-License-Identifier: Apache-2.0
# test_vowel3b_test.py: unit tests for vowel3b_test.py (VOWEL3-AMENDMENT-1.md). Every expected
# value below is worked out by hand in the comments. Standard library only.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import os
import random
import shutil
import tempfile
import unittest

import vowel3b_test as v


def P_of(c_pairs, n_pairs):
    return [(True, a, b) for a, b in c_pairs] + [(False, a, b) for a, b in n_pairs]


class Parsing(unittest.TestCase):
    def test_mismatch_and_type(self):
        self.assertEqual(v.mismatch("a", 1), 0)
        self.assertEqual(v.mismatch("i", 2), 0)
        self.assertEqual(v.mismatch("a", 2), 1)
        self.assertEqual(v.mismatch("i", 1), 1)
        self.assertIsNone(v.mismatch("a", 3))
        self.assertIsNone(v.mismatch("", 1))
        self.assertIsNone(v.mismatch("a", None))
        self.assertEqual(v.change_type("aa"), "N")
        self.assertEqual(v.change_type("ii"), "N")
        self.assertEqual(v.change_type("ia"), "C")
        self.assertEqual(v.change_type("ai"), "C")
        self.assertIsNone(v.change_type("ab"))

    def test_load_rows(self):
        # 7 rows: r1 kept (N, mf 0, ml 0); r2 out of window (12); r3 bad deltasec; r4 other whale;
        # r5 kept (C: handvcat a with 2 peaks -> mf 1; prev i with 2 peaks -> ml 0);
        # r6 no type (coart ab); r7 out of window (0 is not > 0).
        head = "deltasec,whale,coart,prevhandvcat,handvcat,tagondt,numpks,prevnumpks\n"
        body = ("1.0,ATWOOD,aa,a,a,t1,1,1\n"
                "12.0,ATWOOD,aa,a,a,t1,1,1\n"
                "x,ATWOOD,aa,a,a,t1,1,1\n"
                "2.0,BOB,aa,a,a,t1,1,1\n"
                "3.0,FORK,ia,i,a,t2,2,2\n"
                "4.0,FORK,ab,a,b,t2,1,1\n"
                "0.0,FORK,aa,a,a,t2,1,1\n")
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "x.csv")
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(head + body)
            rows, issues = v.load_rows(path)
        finally:
            shutil.rmtree(d)
        self.assertEqual(issues, {"rows": 7, "bad_deltasec": 1, "out_of_window": 2,
                                  "other_whale": 1, "no_type": 1})
        self.assertEqual(len(rows), 2)
        self.assertEqual(v.pairs(rows), [(False, 0, 0), (True, 1, 0)])


class Statistics(unittest.TestCase):
    def test_counts_and_deltas(self):
        # C: (1,0) (1,0) (0,1) (1,1) -> b 2, c 1, both 1; N: (0,0) (0,0) (1,0) (0,1) (0,0)
        # -> b 1, c 1, neither 3. Delta_first = 3/4 - 1/5 = 0.55; Delta_last = 2/4 - 1/5 = 0.3;
        # A = (2 - 1)/4 - (1 - 1)/5 = 0.25 = 0.55 - 0.3.
        P = P_of([(1, 0), (1, 0), (0, 1), (1, 1)], [(0, 0), (0, 0), (1, 0), (0, 1), (0, 0)])
        cnt = v.counts(P)
        self.assertEqual(cnt["C"], {"n": 4, "b": 2, "c": 1, "both": 1, "neither": 0})
        self.assertEqual(cnt["N"], {"n": 5, "b": 1, "c": 1, "both": 0, "neither": 3})
        df, dl, a = v.deltas(cnt)
        self.assertAlmostEqual(df, 0.55, places=12)
        self.assertAlmostEqual(dl, 0.3, places=12)
        self.assertAlmostEqual(a, 0.25, places=12)

    def test_binom(self):
        self.assertEqual(v.binom_half(0), [1.0])
        self.assertEqual(v.binom_half(2), [0.25, 0.5, 0.25])
        self.assertAlmostEqual(sum(v.binom_half(760)), 1.0, places=9)

    def test_exact_one_sided(self):
        # C: two first-only pairs (kC 2), N: two concordant pairs (kN 0). A = 2/2 = 1.
        # Null a = (2x - 2)/2 in {-1, 0, 1} with 1/4, 1/2, 1/4 -> p_high 0.25, p_low 1.
        cnt = v.counts(P_of([(1, 0), (1, 0)], [(0, 0), (0, 0)]))
        t = v.exact_test(cnt, want_crit=True)
        self.assertAlmostEqual(t["obs"], 1.0, places=12)
        self.assertAlmostEqual(t["p_high"], 0.25, places=12)
        self.assertAlmostEqual(t["p_low"], 1.0, places=12)
        self.assertIsNone(t["a_crit"])  # P(A* >= 1) = 0.25 > 0.05

    def test_exact_two_groups_with_ties(self):
        # C: (1,0) (0,1): kC 2, S_C 0; N: (1,0) (0,0): kN 1, S_N 1, nN 2. A = 0 - 1/2 = -0.5.
        # S_C/2 in {-1, 0, 1} (1/4, 1/2, 1/4); S_N/2 in {-0.5, 0.5} (1/2 each).
        # a = sc - sn: -0.5 (1/8), -1.5 (1/8), 0.5 (1/4), -0.5 (1/4), 1.5 (1/8), 0.5 (1/8).
        # p_high = P(a >= -0.5) = 1 - 1/8 = 0.875; p_low = P(a <= -0.5) = 1/8 + 1/8 + 1/4 = 0.5.
        cnt = v.counts(P_of([(1, 0), (0, 1)], [(1, 0), (0, 0)]))
        t = v.exact_test(cnt)
        self.assertAlmostEqual(t["obs"], -0.5, places=12)
        self.assertAlmostEqual(t["p_high"], 0.875, places=12)
        self.assertAlmostEqual(t["p_low"], 0.5, places=12)
        self.assertNotIn("a_crit", t)
        self.assertAlmostEqual(sum(p for _, p in v.sign_flip_null(cnt)), 1.0, places=12)

    def test_critical_value(self):
        # C: five first-only pairs (nC 5), N: one concordant pair. a = (2x - 5)/5:
        # 1.0 has 1/32 = 0.03125 <= 0.05; adding 0.6 (5/32) gives 0.1875 -> a_crit = 1.0.
        # Observed A = 1.0 -> p_high 1/32.
        cnt = v.counts(P_of([(1, 0)] * 5, [(0, 0)]))
        t = v.exact_test(cnt, want_crit=True)
        self.assertAlmostEqual(t["a_crit"], 1.0, places=12)
        self.assertAlmostEqual(t["p_high"], 1 / 32, places=12)
        # ties are grouped: null [(1, .03), (1, .03), (0, .94)] -> 1 has tail .06 > .05 -> None
        self.assertIsNone(v.critical_value([(1.0, 0.03), (1.0, 0.03), (0.0, 0.94)]))
        self.assertEqual(v.critical_value([(2.0, 0.01), (1.0, 0.03), (0.0, 0.96)]), 1.0)

    def test_mcnemar(self):
        # b 5, c 0 -> P(X >= 5) = 1/32, P(X <= 5) = 1. b 1, c 1 -> P(X >= 1) = 3/4 = P(X <= 1).
        m = v.mcnemar_change(v.counts(P_of([(1, 0)] * 5, [(0, 0)])))
        self.assertEqual((m["b"], m["c"]), (5, 0))
        self.assertAlmostEqual(m["p_high"], 1 / 32, places=12)
        self.assertAlmostEqual(m["p_low"], 1.0, places=12)
        m = v.mcnemar_change(v.counts(P_of([(1, 0), (0, 1)], [(0, 0)])))
        self.assertAlmostEqual(m["p_high"], 0.75, places=12)
        self.assertAlmostEqual(m["p_low"], 0.75, places=12)


class Worlds(unittest.TestCase):
    def test_swap_keeps_each_pair(self):
        P = P_of([(1, 0), (0, 1), (1, 1), (0, 0)] * 5, [(1, 0), (0, 0), (0, 1)] * 10)
        W = v.world(P, random.Random(1), 0.0)
        self.assertEqual(len(W), len(P))
        for (c1, a1, b1), (c2, a2, b2) in zip(P, W):
            self.assertEqual(c1, c2)
            self.assertEqual(sorted((a1, b1)), sorted((a2, b2)))

    def test_plant_full(self):
        # delta 1: k = min(1, 1 * nC / #matching) = 1 -> every change row's first click mismatches;
        # no-change rows are only swapped.
        P = P_of([(1, 0), (0, 1), (0, 0), (1, 1)] * 3, [(1, 0), (0, 0)] * 4)
        W = v.world(P, random.Random(7), 1.0)
        self.assertTrue(all(a == 1 for c, a, _ in W if c))
        for (c1, a1, b1), (c2, a2, b2) in zip(P, W):
            if not c1:
                self.assertEqual(sorted((a1, b1)), sorted((a2, b2)))

    def test_w0_size_is_exact(self):
        # In a symmetric world the exact test cannot fire more than 5% of the time beyond Monte
        # Carlo error: 300 worlds of 30 change pairs (15 first-only, 15 last-only) and 60 no-change.
        P = P_of([(1, 0), (0, 1)] * 15, [(1, 0), (0, 1), (0, 0)] * 20)
        rng = random.Random(3)
        fires = sum(int(v.exact_test(v.counts(v.world(P, rng, 0.0)))["p_high"] <= 0.05)
                    for _ in range(300))
        self.assertLessEqual(fires / 300, 0.10)


class Verdicts(unittest.TestCase):
    def test_rules(self):
        f = v.verdict
        self.assertEqual(f(True, 9, 10, 0.0, 0.5, 0.5, 1.0), "INSUFFICIENT_DATA")
        self.assertEqual(f(True, 10, 0, 0.0, 0.5, 0.5, 1.0), "INSUFFICIENT_DATA")
        self.assertEqual(f(False, 10, 10, 0.0, 0.5, 0.5, 1.0), "REPRO_FAILED")
        self.assertEqual(f(True, 10, 10, 0.11, 0.01, 0.99, 1.0), "CALIBRATION_FAILED")
        self.assertEqual(f(True, 10, 10, 0.10, 0.05, 0.99, 0.0), "CARRYOVER_SPECIFIC")
        self.assertEqual(f(True, 10, 10, 0.10, 0.99, 0.05, 1.0), "REVERSED_ASYMMETRY")
        self.assertEqual(f(True, 10, 10, 0.10, 0.5, 0.5, 0.80), "SYMMETRIC_WITH_POWER")
        self.assertEqual(f(True, 10, 10, 0.10, 0.5, 0.5, 0.799), "UNDERPOWERED")


class EndToEnd(unittest.TestCase):
    def rows(self, c_pairs, n_pairs):
        return ([{"whale": "FORK", "type": "C", "mf": a, "ml": b} for a, b in c_pairs]
                + [{"whale": "FORK", "type": "N", "mf": a, "ml": b} for a, b in n_pairs])

    def test_repro_gate(self):
        r = v.run(self.rows([(1, 0)] * 12, [(0, 0)] * 20), R=5, log=lambda s: None)
        self.assertEqual(r["verdict"], "REPRO_FAILED")
        self.assertFalse(r["repro"]["ok"])
        self.assertIsNone(r["main"])
        self.assertIn("REPRO_FAILED", v.render(r))

    def test_strong_carryover(self):
        # 12 change pairs, all first-only; 20 concordant no-change pairs.
        # A = 12/12 - 0 = 1; exact p_high = 2^-12. In W0 the test fires only when at least 10
        # of the 12 signs are positive (P(X >= 10) = 79/4096 = 0.019; P(X >= 9) = 0.073), so
        # a_crit = (20 - 12)/12 = 2/3, and the verdict is CARRYOVER_SPECIFIC unless the 20
        # simulated W0 worlds happen to give 3 or more fires. Mismatch counts: mfC 12, rest 0.
        r = v.run(self.rows([(1, 0)] * 12, [(0, 0)] * 20), R=20, expected=None,
                  log=lambda s: None)
        self.assertEqual(r["repro"]["got"], {"nC": 12, "nN": 20, "mfC": 12, "mfN": 0,
                                             "mlC": 0, "mlN": 0})
        self.assertAlmostEqual(r["main"]["asym"]["obs"], 1.0, places=12)
        self.assertAlmostEqual(r["main"]["asym"]["p_high"], 2.0 ** -12, places=15)
        self.assertAlmostEqual(r["main"]["asym"]["a_crit"], 2.0 / 3.0, places=12)
        size = r["calibration"]["W0"]["asym_reject"]
        self.assertEqual(r["verdict"], "CARRYOVER_SPECIFIC" if size <= 0.10 else "CALIBRATION_FAILED")
        self.assertFalse(r["predictions"]["Q1"]["outcome"])
        md = v.render(r)
        self.assertIn("**CARRYOVER_SPECIFIC**", md)
        self.assertIn("| vowel change | 12 | 12 | 0 | 0 | 0 |", md)

    def test_symmetric(self):
        # 10 first-only and 10 last-only change pairs: A = 0, p_high = P(Bin(20,.5) >= 10)
        # = 0.5 + C(20,10)/2^21 = 0.5 + 184756/2097152 > 0.05 -> not carryover-specific.
        r = v.run(self.rows([(1, 0), (0, 1)] * 10, [(0, 0)] * 30), R=20, expected=None,
                  log=lambda s: None)
        self.assertAlmostEqual(r["main"]["asym"]["obs"], 0.0, places=12)
        self.assertAlmostEqual(r["main"]["asym"]["p_high"], 0.5 + 184756 / 2097152, places=12)
        # (CALIBRATION_FAILED only if 3+ of 20 W0 worlds fire at a per-world size of 0.021)
        self.assertIn(r["verdict"], ("SYMMETRIC_WITH_POWER", "UNDERPOWERED", "CALIBRATION_FAILED"))
        self.assertTrue(r["predictions"]["Q3"]["outcome"])  # 20 discordant change pairs >= 16


if __name__ == "__main__":
    unittest.main()
