# HAI 23.05 test: findings (branch `hai-23.05-test`)

**Setup.** This is the same model as on `main`, **unchanged**: trained only on simulated plants, with
the same decision gate and the same site rule (strip `P\d_`). Nothing was tuned for this run.
It is tested on **HAI 23.05** `hai-train3.csv`: a newer release of the HAI testbed, collected in a
different campaign (2022), with **86 tags** (7 tags more than 21.03, including boiler-DCS internal
points). 35 h at 1 Hz → 8 four-hour windows. Labels: `real/hai_23.05_labels.csv` (21.03 labels reused for
the shared tags; new tags labelled from the HAI technical manual).

Classes present: 4 Temperature, 4 Pressure, 9 RunStatus, 69 Other (no motor current, no counters).

## Results

| Method | Accuracy (86 tags) | Target recall (17) | Other rejected (69) |
|---|---|---|---|
| Name-only (raw names) | 57% | 53% | 58% |
| Name-only (site rule) | 64% | 53% | 67% |
| Behaviour-only | 67% | 71% | 67% |
| **Hybrid + decision gate** | **84%** | **88%** | **83%** |

- **Auto-accepted: 51% of tags (44), and 43 of them are correct = 97.7% precision.**
- **0 wrong target claims auto-accepted.** All 12 tags wrongly predicted as a target went to REVIEW.
- Review reasons: 22 constant signal, 17 low confidence, 3 unfamiliar signal.

### Consistency with HAI 21.03 (held-out `train2`)

| | HAI 21.03 train2 | HAI 23.05 train3 |
|---|---|---|
| Hybrid accuracy | 81% | **84%** |
| Behaviour-only | 68% | 67% |
| Name-only (site rule) | 57% | 64% |
| Auto-accepted | 51% | 51% |
| Precision of auto-accepted | 97.5% | **97.7%** |

The pattern is stable across dataset versions: hybrid > behaviour > name, and roughly half the tags are
auto-accepted at about 97–98% precision.

## Notable cases
- **`P1_PP04D`** (cooling-pump start command) is the first run signal in HAI that actually switches. It
  was identified as RunStatus **from behaviour alone** with confidence 0.995, even though the name gives no
  hint (name-only: Unknown).
- **New tag types were handled.** All 7 boiler-DCS internal points (`x1001_05_SETPOINT_OUT`, …) were
  correctly mapped to Other and auto-accepted. So were the new cooler-pump output, the speed controller
  output and 2 of the vibration probes.
- **The unfamiliar-signal check fired for the first time on real data:** `P2_VIBTR01`, `P2_VIBTR02` (shaft
  vibration) and `P2_VT01` (key-phasor phase) are unlike any simulated signal, so they went to REVIEW even
  though the model's guess (Other) was right.
- **The one accepted error** is again `P4_ST_PT01` (steam pressure, raw 0–27648) predicted as Other. It is
  a miss on the safe side, not a false claim, and it is the same tag as in 21.03, so it's a systematic case
  for the final phase's pressure work.
- Temperature: 3 of 4 correct; `P1_TIT02` was predicted Other at low confidence (0.52), so it went to REVIEW.

## Caveats
- **Same testbed** as HAI 21.03 (newer version, different campaign, more tags), not a different plant.
  A different plant (SWaT/WADI, SKAB) is still the strongest next test.
- The 8 constant RunStatus tags are guessed right only through a learned prior; they go to REVIEW.
- The labels for the `x…` DCS points are inferred: the manual only says "Output of 1001.05". Changing them
  would affect at most 7 tags, which are currently all predicted Other.

## Reproduce
```
mkdir -p external/hai2305
curl -L -o external/hai2305/hai-train3.csv https://media.githubusercontent.com/media/icsdataset/hai/master/hai-23.05/hai-train3.csv
.venv/Scripts/python mapper/eval_hai.py --version 23.05
```
