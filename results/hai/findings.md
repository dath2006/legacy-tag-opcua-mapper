# HAI real-data test: findings

**Setup.** The hybrid model is trained **only on simulated plants**; HAI is never used for training.
It is tested on the real **HAI 21.03** testbed (boiler, turbine, water treatment, power-grid HIL):
79 tags, cut into 4-hour windows, with probabilities averaged per tag. Labels were made by hand from the
HAI technical manual (`real/hai_21.03_labels.csv`). HAI has 3 Temperature, 4 Pressure, 8 RunStatus and
64 out-of-vocabulary (Other) tags; it has no motor-current or counter tags.

- `train1` (60 h) was used to **diagnose** failures (round 1).
- `train2` (a different 60 h) is the **fresh** test, never looked at while fixing (round 2).

Numbers: `summary.md` · per-tag: `hai_predictions_train1.csv`, `hai_predictions_train2.csv` ·
figures: `hai_confusion.png`, `hai_gate.png`

## Before vs after the fixes

| | Round 1 (train1, before) | Round 2 (train2, fresh, after) |
|---|---|---|
| Hybrid accuracy (79 tags) | 49% | **81%** |
| Target tags correct (15) | 47% | **80%** |
| Other correctly rejected (64) | 50% | **81%** |
| Auto-accepted | 70% | 51% |
| **Precision of auto-accepted** | 51% | **97.5%** (39 of 40 correct) |
| Wrong target claims auto-accepted | 19 | **0**: all 12 false claims go to REVIEW |

The one auto-accepted error (`P4_ST_PT01`, a pressure predicted as Other) is on the safe side: it
misses a target rather than falsely claiming one.

## Round 1 diagnosis (what was wrong)

1. **Constant signals.** 22 of the 79 tags never change during normal operation, including all 8
   RunStatus tags. The model still answered with confidence 1.0.
2. **Open-set problem.** The simulator's "Other" was too narrow, so real vibration, electrical power,
   frequency and valve-position signals were claimed as Pressure or Temperature.
3. **Site naming convention.** The `P1_` process prefix looks like an ISA "P" (pressure) hint.

## Fixes (all general, none tuned to individual HAI tags)

| Fix | Where |
|---|---|
| Decision gate: **constant signal → always REVIEW** (no behaviour evidence) | `mapper/decide.py` |
| Decision gate: **unfamiliar signal → REVIEW** (distance to the nearest training tags beyond the 99th percentile) | `mapper/decide.py` |
| Simulator: wider "Other" (vibration, electrical power, supply voltage, grid frequency, valve position) and equipment that never changes state in a window | `generator/simulate.py` |
| Generic engineering vocabulary for those quantities (VIB, KW, VOLT, FREQ, POS, VALVE; ISA J/E/V/Z) | `mapper/names.py` |
| Site rule: strip `P\d_`, configured once per site | `mapper/eval_hai.py` (`SITE_PREFIX`) |

**Deliberately not done:** adding HAI-specific abbreviations (`PP` = pump, the `R`/`D` suffixes). They
would only help on this one dataset and would contaminate the test. That belongs to the final phase's
general abbreviation expansion (embeddings / LLM).

## Honest caveats
- The categories of the new simulated "Other" signals were **informed by the round 1 diagnosis**. That
  is why round 2 uses a fresh file, but it is the same plant, so a second real plant (SWaT/WADI, SKAB) is
  still needed.
- The 8 constant RunStatus tags are "correct" only through a learned prior (constant binary → usually a
  run signal), not through evidence. They are all correctly sent to REVIEW.
- The unfamiliar-signal check fired 0 times on HAI (2 times on the simulated holdout). After the simulator
  fix, HAI's signals fall inside the training range; low confidence did the filtering instead.
- Pressure is still the hardest class (2 of 4 found on train2), consistent with the simulated results.

## Reproduce
```
mkdir -p external/hai
curl -L -o external/hai/train1.csv.gz https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03/train1.csv.gz
curl -L -o external/hai/train2.csv.gz https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03/train2.csv.gz
.venv/Scripts/python mapper/eval_hai.py
```
(The simulated plants must exist first; see the README.)
