# HAI real-data test: findings (branch `hai-test`)

**Setup.** The Phase 1 hybrid model was trained **only on simulated plants** (722 tags). It was tested on
the real **HAI 21.03** testbed (boiler, turbine, water treatment, power-grid HIL): 79 tags from `train1`
(~60 h at 1 Hz), cut into 15 four-hour windows, with predictions averaged per tag. Labels were made by
hand from the HAI technical manual (`real/hai_21.03_labels.csv`).
HAI has 3 Temperature, 4 Pressure and 8 RunStatus tags; the other 64 are outside our vocabulary (Other).
It has no motor-current or counter tags.

Full numbers: `summary.md` · per-tag table: `hai_predictions.csv` · figure: `hai_confusion.png`

## Headline

| | Result |
|---|---|
| Overall accuracy (79 tags) | **49%** (hybrid, prefix-stripped names), vs 94% on the simulated holdout |
| Temperature + Pressure tags found | **7 / 7 (100%)** |
| RunStatus tags found | **0 / 8**: every one is constant for the full 60 h (see 1) |
| Other tags correctly rejected | 32 / 64 (50%) |
| Precision of auto-accepted (≥ 0.8) | 51%, so the confidence is **not calibrated** on real data |

There is a large **sim-to-real gap**, and it has two clear causes. Both are fixable, and both were
predicted by the Phase 1 limitations.

## What we learned

### 1. Constant signals cannot be identified, but the model was overconfident about them
22 of the 79 HAI tags never change during normal operation. All 8 RunStatus tags are among them: the
pumps stay on or off for 60 h, and `P1_PP01AD` is even a packed word with the value 540833. No
behaviour method can classify a flat line. **The bug** is that the model answered "Other" with
confidence 1.0 instead of saying "not enough evidence → REVIEW". It learned that from simulated alarm
bits that never fired.
**Fix:** a guard so that a constant signal means no behaviour evidence: rely on the name only, and
always send it to review.

### 2. Open-set problem: real plants have many more kinds of "Other"
The 32 false target claims are all continuous analog signals the simulator never produced:
shaft vibration, turbine RPM, electrical power and load, grid frequency deviation, valve positions,
tank level, 24 V supply. The model only knows 5 targets plus a narrow "Other" (flow, level, speed,
setpoint, controller output, alarm), so any smooth analog signal looks like Pressure or Temperature.
**Fix:** more kinds of Other in the simulator (vibration, electrical, valve position, frequency), the
planned growth to 15–20 concepts, and an "unfamiliar signal" score (distance to the training data) that
forces review.

### 3. Names: site conventions matter
- HAI prefixes every tag with its process (`P1_`). Read as ISA, `P` + digit becomes a false
  "pressure" hint: name-only precision is **14% with raw names vs 62% with the prefix stripped**.
  A one-line site rule (strip `P\d_`) fixes it, which is realistic integrator configuration.
- Our vocabulary doesn't know `PP` = pump, the `R` suffix = running, or the `D` suffix = demand/command.
  Real names need a larger abbreviation list or the final phase's embedding/LLM step.

### 4. What did transfer well
- **Every non-constant target tag was found (7/7).** That includes `P3_PIT01`, `P4_ST_PT01` and
  `P4_ST_TT01`, which are raw 0–27648 Siemens-style integers. That validates the raw-register realism in
  the simulator.
- `P4_ST_PT01`: behaviour said Temperature, the name said Pressure, and the hybrid chose Pressure (but
  sent it to REVIEW at 0.41). That is exactly the hybrid mechanism we hoped for, now on real data.

## Implications for the final phase (added to `docs/TODO.md`)
1. Constant/flat-signal guard → REVIEW.
2. Wider "Other" in the simulator + 15–20 concepts.
3. Out-of-distribution / novelty score, plus probability calibration on real data.
4. Configurable site naming rules (prefix stripping) and a richer abbreviation dictionary (PP, R, D, …).
5. Use HAI windows with operating changes (`test*.csv` files and later versions) so the run signals
   actually move.

## Reproduce
```
mkdir -p external/hai
curl -L -o external/hai/train1.csv.gz https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03/train1.csv.gz
.venv/Scripts/python mapper/eval_hai.py
```
(The simulated plants must exist first; see the README.)
