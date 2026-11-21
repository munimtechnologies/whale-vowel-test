# VOWEL2-PREREG: do sperm whale "long and short vowels" hold within a bout?

Pre-registration, written 2026-11-21 before any duration statistic of these codas was computed by
vowel, bout, deployment or mode. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; not
yet checked by a human expert. Text CC BY 4.0, code Apache-2.0.

## 1. The claim and why it needs this test

Begus, Dabkowski, Sprouse, Gruber and Gero (2026), *The phonology of sperm whale coda vowels*,
Proc. R. Soc. B 293: 20252994 (doi 10.1098/rspb.2025.2994; preprint bioRxiv
10.1101/2025.06.09.658556) report five vowel-like properties of sperm whale codas. Two concern
duration: (ii) a-coda vowels are longer than i-coda vowels, and (iii) i-vowel durations are
bimodal, read as short i versus long i ("like in Latin, whales have short and long vowels", as
the first author summarised it). In a public reply to a critic (comments on "If We Could Talk
to the Animals, Sperm Whale Redux", goflaw.substack.com), the first author named the
"length-vowel dependency" as one of the patterns an artefact explanation would have to explain.

Their public code (`PhonologyCodaVowel.R`, github.com/Project-CETI/coda-vowel-phonology, commit
be751b8) fits `lmer(Duration ~ Vowel + (Vowel | whale))` to the 1+1+3 codas of ATWOOD, FORK,
PINCHY and TBB, and runs Hartigan's dip test on each whale's a- and i-durations. Apart from the
whale, every coda counts as an independent observation.

Our earlier registered test on the same labels (VOWEL-PREREG.md; RESULTS-VOWEL.md, verdict
VOWELS_CLUSTER_STRONGLY) found that the vowel of neighbouring codas in a bout switches about a
fifth as often as independence predicts (75 switches where 352.23 were expected), and that one
whale's vowel mix differs between tag deployments (p_dep 0.0001). Coda duration also changes
gradually across neighbouring codas ("rubato", Sharma et al. 2024, Nature Communications). If
both vowel and tempo are states of the bout or the
deployment, a whale-level duration contrast compares bouts and recording days, not vowels, and its
p value counts about a thousand correlated codas as independent evidence. The clean question is
whether a- and i-codas differ in duration **inside the same bout**, where the recording, the depth
and the tempo of the moment are shared.

## 2. Data (unchanged from VOWEL-PREREG.md)

* `codamd.csv`, OSF a32ke (md5 be50098e0e806d6df7cd2144b80d900d): hand vowel labels (`handv`),
  whale, coda type and duration. The copy in Project-CETI/coda-vowel-phonology (commit be751b8)
  is fetched too and compared by md5 (reported, not a gate).
* `DominicaCodas.csv` (md5 46c2ff249bc6fa327d5bbe596f06be63) and `sperm-whale-dialogues.csv`
  (md5 eeeeb20cda64d88320b6ccee1185379a), github.com/pratyushasharma/sw-combinatoriality (Sharma
  et al. 2024): recording, tag deployment and time of each coda, joined exactly as in
  `describe_vowels.py`. These tables carry no licence file; they are read inside the job only and
  only aggregate numbers are published.
* Any md5 mismatch of the three registered files: verdict DATA_MISMATCH, nothing computed.

## 3. Units

* Vowel: the R script's rule. A `handv` starting with "a" is a, with "i" is i; anything else is
  dropped.
* **Published subset**: codas of type 1+1+3 of ATWOOD, FORK, PINCHY and TBB with a vowel and a
  duration (the R script's `codas` after its filters).
* **Timed codas**: every vowel-labelled, named coda with a unique recording time and a tag
  deployment. Bouts are cut on this full timeline as in VOWEL-PREREG.md: a new bout at a new
  whale, deployment or file, or after a silence of more than 60 s.
* **Duration set**: the timed codas of the published subset, each with its bout.

## 4. The statistic

For a grouping (whale, deployment, or bout), over the groups that hold both vowels:
D = sum_g W_g (mean duration of a in g - mean duration of i in g) / sum_g W_g, with
W_g = n_a n_i / (n_a + n_i). D > 0 means a-codas are longer. p_high and p_low come from B
permutations of the vowel labels within the groups: p = (1 + number of permuted D at least / at
most the observed D) / (B + 1).

## 5. Tests

* **T0, reproduction (published style).** D within whale on the published subset, labels
  permuted within whale (B = 9,999). This stands in for the paper's mixed model; it makes the same
  independence assumption. REPRODUCED if D > 0 and p_high <= 0.05.
* **T1, primary.** D within bout on the duration set (B = 9,999). If fewer than 5 bouts hold both
  vowels, or those bouts hold fewer than 15 codas of their minority vowel, the test moves to the
  tag deployment (whale x deployment) with the same thresholds; if that also falls short:
  INSUFFICIENT_DATA. The level used is reported.
* **Secondary.** D within whale on the duration set and D within deployment, each with its
  permutation p (B = 9,999); a rotation p for the level tested: the label sequence of each group
  turned by a random offset (runs of one vowel kept), B = 9,999.
* **Calibration, size (C1).** 200 worlds: durations with the observed level effect removed
  (duration - D_level for a-codas), labels rotated within groups, tested as T1 with B = 999. Size
  = share of worlds with p_high <= 0.05. CALIBRATION_FAILED above 0.10.
* **Calibration, power (C2).** 200 worlds each at delta = D(T0) and delta = D(T0) / 2: labels
  permuted within groups, delta added to the durations of the a-labelled codas (effect-removed
  durations as in C1), tested as T1 with B = 999. Power = share with p_high <= 0.05. Run only if
  D(T0) > 0.
* **Calibration, false alarm of the published style (C3).** 200 worlds: real durations of the
  duration set; synthetic labels with no relation to duration, one vowel per bout drawn from the
  whale's share of a, each coda flipped with probability 0.05 (the persistence matched in
  RESULTS-VOWEL.md). Report the share of worlds where the within-whale test gives p_high <= 0.05
  (the false-alarm rate F), where it gives either p <= 0.025, and where the within-bout test gives
  p_high <= 0.05.
* **Secondary, i-vowel length modes (M).** For each of the four whales, the i-durations of the
  published subset: Hartigan's dip and its table p value (Python package diptest 0.12.0, as the
  paper's R dip.test), and the exact two-means split (the threshold between the two groups that
  minimises the within-group sum of squares, each group at least 2 codas). Each timed i-coda is
  short or long by its whale's split. (M1) Persistence: switches between consecutive i-codas of
  one whale within a bout, against the exact expectation and B = 9,999 permutations within whale x
  deployment; Q = switches / expected. (M2) The short/long mix by deployment within whale: G and
  B = 9,999 permutations, as the deployment test of VOWEL-PREREG.md (whales with at least 2
  deployments of at least 10 i-codas).
* **Exploratory, labelled so.** Per-whale means of the published subset; per deployment: first
  date, bouts, codas and mean durations by vowel, number of long i-codas.

Seeds: naive_pub 20261211, naive_timed 20261212, dep 20261213, bout 20261214, rot 20261215,
size 20261216, power 20261217 (+10 x fraction), false_alarm 20261218, mode 20261219, mode_dep
20261220.

## 6. Verdict (applied in this order)

1. DATA_MISMATCH: a registered file's md5 differs.
2. INSUFFICIENT_DATA: neither bouts nor deployments meet the thresholds of T1.
3. NOT_REPRODUCED: T0 is not reproduced (nothing to explain).
4. CALIBRATION_FAILED_WITHIN_<LEVEL>: C1 size above 0.10.
5. DURATION_DIFFERENCE_WITHIN_<LEVEL>: T1 p_high <= 0.05 (a longer than i inside the level).
6. REVERSED_WITHIN_<LEVEL>: T1 p_low <= 0.05 (i longer).
7. NO_DIFFERENCE_WITH_POWER_WITHIN_<LEVEL>: C2 power at delta = D(T0) at least 0.80.
8. UNDERPOWERED_WITHIN_<LEVEL>: otherwise.

<LEVEL> is BOUTS or DEPLOYMENTS.

## 7. Readings fixed now

* DURATION_DIFFERENCE_WITHIN_BOUTS: the length-vowel dependency survives the strictest public
  control we can build; it is a property of the coda, not of the moment. This would strengthen
  the published claim, and we will say so.
* NO_DIFFERENCE_WITH_POWER_WITHIN_<LEVEL>: inside a bout (or deployment) a- and i-codas do not
  differ in duration, although a difference as large as the whale-level one would have been
  found; the whale-level difference is then a difference between bouts or recording days. This
  would not show that vowels are artefacts; it would remove duration as independent evidence for
  them.
* UNDERPOWERED or INSUFFICIENT_DATA: the public data cannot separate a vowel duration effect from
  bout or deployment effects; the published p values rest on between-bout comparisons.
* REVERSED: reported as found.
* C3: a false-alarm rate F well above 0.05 means the published-style test is not calibrated for
  data in which vowels come in bouts, whatever T1 says.
* M: persistence (Q <= 0.5 with p_low <= 0.05) or a deployment effect in the short/long split
  means that the "long i" is, at least partly, a state of the bout or the recording; neither
  rules out a length contrast.

## 8. Predictions (priors, for a Brier score)

| id | prediction | prior |
|---|---|---|
| P1 | published-style contrast reproduced: a longer than i, p_high <= 0.05 | 0.80 |
| P2 | a longer than i within the level tested, p_high <= 0.05 | 0.35 |
| P3 | power at the published-style effect size >= 0.80 | 0.50 |
| P4 | rotation-world size <= 0.10 | 0.90 |
| P5 | published-style false-alarm rate in bout-clustered worlds > 0.10 | 0.75 |
| P6 | within-level contrast below half the within-whale contrast on the same codas | 0.60 |
| P7 | i-vowel short/long modes persist within bouts (p_low <= 0.05 and Q <= 0.5) | 0.55 |
| P8 | i-vowel short/long mix differs between deployments of a whale, p <= 0.05 | 0.60 |

## 9. Procedure and files

* `vowel2_test.py` (analysis), `test_vowel2_test.py` (unit tests on synthetic data),
  `test_vowel2_results.py` (independent stdlib grader and renderer of RESULTS-DUR.md), all
  published with this file before the job runs. The job (vowel2-test-v1) first runs `gate.py`,
  which stops unless these four files are public on main and identical to the job's copies, and
  takes `describe_vowels.py` and `vowel_test.py` from commit eff4365.
* The job writes `vowel2_results.json` and renders RESULTS-DUR.md with the grader. Both are
  committed unchanged. A reading written after the result will be labelled so.
* Anything changed after this point goes into a dated AMENDMENT section, labelled post hoc.

## 10. Limits known now

* The labels are the authors' hand labels. Only focal-whale codas are labelled.
* T0 is a permutation stand-in for the paper's mixed model, not a re-fit of it; its job is to
  check direction and significance under the same independence assumption.
* Rotation keeps runs but assumes no long-range order within a bout beyond them.
* Bouts that hold both vowels are where vowels switch; if switches happen at special moments
  (for example a change of tempo), a within-bout contrast measures those moments.
