# Legacy Tag → OPC UA Semantic Mapping — Discussion & Phase 1 Plan

> Project has **two phases**: **Phase 1** (partial results) and **Final Phase**.
> Source idea: [`../idea.md`](../idea.md)

---

## Part A — Discussion Summary

### A1. Verdict on the idea
Solid and well-scoped. The real problem (cryptic legacy tags, manual mapping) plus a clear research
question (does name + behaviour beat either alone?) makes it a strong EL project.

### A2. Suggestions / risks

1. **Synthetic-data circularity (biggest risk).** If we generate signals, names and labels ourselves,
   the model may just learn our generator. Mitigations:
   - **Split by machine / naming style, never random rows** (tags of one machine must not appear in
     both train and test).
   - **Add a real dataset in the final phase**: SWaT / WADI (iTrust, Singapore) have real cryptic
     tags like `FIT101`, `LIT301`, `MV201` — free access via request form.
2. **Use ISA-5.1 tag conventions** (TT = temperature, PT = pressure, FT = flow, LT = level).
   Embeddings alone won't understand `T1_PV`; an abbreviation + ISA dictionary does most of the work,
   embeddings handle leftover fuzzy cases. Gives a cited grounding for the vocabulary.
3. **Be honest about behaviour-only limits.** Temperature vs pressure look alike on basic statistics.
   This limitation is the strongest argument for the hybrid — put it on a slide.
4. **Fuse features, not scores.** One XGBoost on [name-similarity-per-concept + behaviour features];
   its calibrated probability is the confidence.
5. **Headline metric = auto-accept curve.** Plot *precision of auto-accepted tags* vs *% of tags
   auto-accepted* across thresholds. e.g. "auto-accept 70% of tags at 97% precision, flag 30%".
6. **Cite or drop the "<65% accuracy" claim** — examiners will ask.

### A3. Distinguishing same-looking tags (temperature vs pressure)
They only look alike on naive stats. Physically they differ, and that is measurable:

| Signal | Feature | Temperature | Pressure |
|---|---|---|---|
| Thermal inertia | Autocorrelation decay time | Long | Short |
| Fast fluctuation | High-frequency energy ratio (FFT) | Low | Higher |
| Step response | Shape after a change | Smooth first-order curve | Jump, overshoot, settle |
| **Lag to run signal** (strongest) | Lag at peak cross-correlation | Minutes after heater ON | ~1 s after pump ON |
| Raw range | Value magnitude | e.g. 20–200 | e.g. 0–10 (weak: Modbus scaling) |
| Sibling tags | Loop grouping `T1_PV/T1_SP/T1_OUT` | Group context | Group context |

- **Name** resolves most remaining cases — that's the point of the hybrid.
- **Both ambiguous → flag for human review.** Honest "unsure" beats confident wrong; the auto-accept
  curve measures exactly this.
- **Warning:** the simulator must use realistic physics (first-order lag for temperature, fast
  pump-coupled pressure), not hand-coded speed differences — otherwise the circularity objection returns.
  Real-data validation in the final phase settles it.

### A4. Phase split (agreed direction)
- **Phase 1:** offline pipeline — simulator, name-only, behaviour-only (basic features), first hybrid.
  Show temp/pressure confusion as a known limitation.
- **Final:** advanced physics features (lag, autocorrelation, spectral) showing confusion drop, live
  Modbus, 15–20 concepts, real dataset, review UI, OPC UA publishing.

---

## Part B — Phase 1 Plan

### B1. Goal
Prove, with numbers, that **hybrid (name + behaviour) beats name-only and behaviour-only** on
simulated legacy machine tags, and show a working inference table with confidence + accept/flag.

### B2. Scope

| In Phase 1 | Deferred to Final |
|---|---|
| Physics-based simulator, CSV output | Serving over Modbus (pymodbus), live ingestion |
| 5 concepts | 15–20 concepts |
| 3 naming styles | Unseen naming style test + real dataset (SWaT/WADI) |
| Name analysis: tokenizer + abbreviation/ISA dictionary + rapidfuzz | Sentence embeddings / local LLM for leftovers |
| Basic behaviour features | Lag, autocorrelation-decay, spectral features |
| XGBoost hybrid, basic confidence | Calibration, threshold tuning, auto-accept curve |
| Static inference table | Review web UI (FastAPI/Streamlit + SQLite) |
| — | OPC UA server publishing (asyncua), UaExpert demo |

### B3. Concepts (5 targets + Other)
`Temperature`, `Pressure`, `RunStatus` (binary), `MotorCurrent`, `Counter`, plus **`Other`**.

*Update during build:* with only the 5 targets, behaviour-only hit ~97%, which is unrealistically easy
(real machines contain look-alike tags). Simulated machines now also carry **Flow, Level, Speed, Setpoint,
Controller output, Alarm** tags, labelled `Other`. The final phase splits `Other` into named concepts
(→ 15–20).

### B4. Step 1 — Data Generation (simulator)
- **Machines:** ~10 simulated machines, each with 1–2 of: heater+temperature loop, pump+pressure,
  motor+run+current, part counter → ~8–12 tags per machine, ~100 tags total.
- **Physics (keep realistic, see A3 warning):**
  - Temperature: first-order lag toward setpoint when heater ON (time constant: minutes).
  - Pressure: fast response to pump run state (seconds), small overshoot.
  - MotorCurrent: tracks motor run signal with startup spike + load noise.
  - RunStatus: binary on/off with random duty cycles.
  - Counter: monotonic increments while machine runs, occasional reset/rollover.
- **Realism:** Gaussian noise, 2–5% missing values, slow drift, integer scaling (Modbus-style ×10/×100).
- **Sampling:** 1 Hz, 2–4 hours per machine.
- **Naming styles:**

  | Style | Examples | Name informativeness |
  |---|---|---|
  | A — ISA-like | `TT101`, `PT204`, `MTR3_RUN` | High |
  | B — Shorthand | `T1_PV`, `P2`, `M1_RUN`, `CNT1`, `AMP_M2` | Medium |
  | C — Opaque | `R40001`, `TAG_17`, `AI3` | None (behaviour only) |

- **Output:** `data/timeseries.csv` (timestamp, machine, tag, value), `data/labels.csv` (machine, tag, concept, style).
- **Tools:** Python, NumPy, pandas.

### B5. Step 2 — Name Analysis
1. Split tag names on `_`, digits, case changes → tokens (`T1_PV` → `T`, `PV`).
2. Expand via abbreviation dictionary + ISA-5.1 first letters (`T/TT/TMP → temperature`, `P/PT → pressure`,
   `RUN/ON/STS → run status`, `AMP/I/CUR → current`, `CNT/CTR/QTY → counter`).
3. Fuzzy-match tokens against each concept's vocabulary (rapidfuzz) → **5-dim name-score vector**.
4. Opaque names → near-zero vector (honest "no information").
- **Tools:** Python, rapidfuzz.

### B6. Step 3 — Behaviour Analysis (basic features only)
Per tag:
- distinct-value count / is-binary
- monotonic-increase ratio (counter detector)
- normalized range, std, mean |Δ| (rate of change)
- zero-crossing / transition rate
- dominant FFT period (periodicity)
- missing ratio
- max zero-lag correlation with any binary tag on same machine
- **Tools:** pandas, NumPy, SciPy.

(Lag / autocorrelation-decay / spectral-ratio features are intentionally held for the final phase.)

### B7. Step 4 (first version) — Models & Evaluation
- **Models:**
  1. Name-only: argmax of name-score vector (rule baseline).
  2. Behaviour-only: XGBoost on behaviour features.
  3. Hybrid: XGBoost on [name scores + behaviour features].
- **Split:** GroupKFold by machine (no machine in both train and test).
- **Metrics:** accuracy, macro-F1, per-class F1, confusion matrix, results per naming style.
- **Confidence:** max predicted probability; simple fixed threshold (e.g. 0.8) → accepted / flagged.
- **Tools:** scikit-learn, XGBoost, matplotlib.

### B8. Expected results (hypotheses to show)
- Name-only: strong on style A, weaker on B, fails on C.
- Behaviour-only: separates RunStatus / Counter / continuous well; **confuses Temperature vs Pressure**.
- Hybrid: best overall; fixes cases where one source is wrong.

### B9. Deliverables for the Phase 1 review
1. Simulator + dataset stats table + sample signal plots (one per concept).
2. Bar chart: name-only vs behaviour-only vs hybrid (accuracy & macro-F1).
3. Confusion matrices for all three (highlight temp/pressure confusion).
4. Per-naming-style accuracy table.
5. Inference table: `tag → predicted concept → confidence → accepted/flagged`, with 2–3 showcase
   cases where behaviour rescued a misleading name and vice versa.
6. "What's next" slide listing the Final-phase items from B2.

### B10. Folder layout
```
SEM 5 Main EL/
├── idea.md
├── docs/phase1_plan.md
├── docs/TODO.md
├── check.py              # isolation + sanity asserts
├── requirements.txt
├── generator/            # SIMULATOR (never imported by mapper/)
│   ├── simulate.py       # Step 1 -> data/<plant>/raw/*.csv + labels.csv
│   └── plot_samples.py
├── mapper/               # LEARNER (reads CSVs only)
│   ├── names.py          # Step 2
│   ├── behaviour.py      # Step 3
│   └── train_eval.py     # Step 4 + plots + inference table
├── data/                 # generated
└── results/              # figures, tables, summary.md
```

### B11. Timeline (suggested, ~4 weeks)

| Week | Work |
|---|---|
| 1 | Simulator with physics + naming styles; dataset plots |
| 2 | Name analysis + behaviour features |
| 3 | Three models, GroupKFold evaluation, confusion matrices |
| 4 | Inference table, figures, slides, rehearsal |

### B12. Phase 1 slide outline
1. Problem recap → 2. Approach (hybrid pipeline diagram) → 3. Simulator & dataset →
4. Name analysis → 5. Behaviour analysis → 6. Results comparison → 7. Confusion matrices &
known limitation (temp vs pressure) → 8. Inference demo table → 9. Final-phase roadmap.

---

## Part C — Research: making simulated data close to the real world

### C1. What real legacy-plant data looks like (and what the simulator reproduces)

| Real-world property | How it is simulated (`generator/simulate.py`) |
|---|---|
| Process dynamics are first-order-plus-dead-time (FOPDT), the standard control-engineering model | `fopdt()` used for pressure, flow, speed, motor/discharge temperature |
| Temperature loops are PI-controlled **or** simple on/off thermostats (common in small plants) | `heater_zone()`: PI with anti-windup or hysteresis on/off, dead time 5–60 s, τ 200–1500 s, setpoint changes, load dips |
| Machines run in production runs, micro-stops and planned breaks | `schedule()` |
| Direct-on-line motors draw 4–7× inrush; VFD motors ramp softly | `motor_current()`; CT range clips inrush |
| Different pressure behaviours: pump (fast), compressor (load/unload sawtooth), hydraulic press (per-stroke pulses), plant air (independent of machine) | `pump_pressure`, `receiver_pressure`, `press_pressure`, oven air supply |
| Counters: 16-bit rollover, shift resets, multiple parts/cycle, rarely-moving batch counters | `counter()`, `cycles()` |
| Sensor noise is coloured, not white; noise level depends on sensor type (thermocouples quiet, pressure/current noisy) | `ar1()` + per-type `NOISE` |
| Drift, spikes, stuck/flat-lined sensors | `degrade()` |
| Historians store by exception (deadband), giving step-like signals | `degrade()` deadband hold |
| Modbus exposes **raw integers**: eng×10/×100 or ADC counts (0–4095 12-bit, 0–27648 Siemens S7, 0–32767) | `encode()` — learner never sees engineering units |
| Missing values and device comm loss | per-tag dropouts + whole-device NaN blocks |
| Naming: ISA-5.1, personal shorthand (with typos), opaque PLC addresses (`HR40012`, `N7:3`, `%MW100`, `B3:0/2`), repurposed tags | `POOLS`, `OPAQUE_*`, 5% misleading names |
| Look-alike tags outside the target vocabulary (flow, level, speed, setpoint, controller output, alarm) | labelled `Other` |
| Physics randomised per machine (domain randomisation) so no fixed signature can be memorised | every parameter drawn from a range |

### C2. Generator ↔ learner encapsulation
- `generator/` writes only `data/<plant>/raw/*.csv` (timestamp + raw integers under cryptic names) and a
  separate `data/<plant>/labels.csv`.
- `mapper/` never imports the generator; features are computed from raw CSVs only. Labels are read only in
  `train_eval.py`, as training targets and for scoring. Enforced by `check.py`.
- The learner's vocabulary (`mapper/names.py`) is built from ISA-5.1 + common abbreviations, **not** copied
  from the generator. The generator deliberately uses terms the learner doesn't know (`THM`, `BRG`, `HYD`,
  `LOAD_A`, `SHOTS`, `GOOD`), typos (`TEMPR`, `CURNT`), and misleading hints (`IR3xxxx` = input register, but
  ISA reads "I" as current; `Q` = flow in shorthand but quantity in ISA; `TAH` = an alarm with a temperature letter).
- Evaluation is grouped by machine (GroupKFold) plus a **separate holdout plant** (different seed, never
  seen in training).
- Remaining honest limitation: one team wrote both sides, so validation on real data (Part D) is the
  final answer.

### C3. Sources
- Synthetic industrial time series survey: https://arxiv.org/pdf/2407.11480
- Industrial signal generators (noise, gaps, irregular sampling): https://indsl.docs.cognite.com/signals.html
- Historian deadband / swinging-door compression: https://docs.aveva.com/bundle/sp-historian/page/67236.html ,
  https://www.influxdata.com/learn/why-do-data-historians-compress-data/
- Closest prior work (building automation, names + time series, 70–90% accuracy):
  Mishra et al., NREL — https://arxiv.org/abs/2003.07690 ; PNNL BACnet→Brick LLM tagging —
  https://www.pnnl.gov/publications/automated-tagging-and-semantic-mapping-bacnet-metadata-brick-schema-building

---

## Part D — Real datasets (how to get them)

| Dataset | What it has | Access | Use |
|---|---|---|---|
| **HAI** (HIL-based Augmented ICS, boiler / turbine / water treatment) | Real testbed, many cryptic tags with a P1_/P2_/P3_ process prefix, 1 Hz | **Free, no request**: https://github.com/icsdataset/hai (also on Kaggle) | Best first real test: names + behaviour. Labels come from the tag descriptions in the repo docs |
| **SKAB** (Skoltech Anomaly Benchmark, water-circulation pump testbed) | Real pump-rig signals incl. current, pressure, temperature, flow, vibration (verify column names in repo) | **Free**: https://github.com/waico/SKAB | Behaviour-only validation on real temperature vs pressure vs current |
| **SWaT** (water treatment) | 51 tags with ISA-like names (`FIT101`, `LIT101`, `MV101`, `P101`), 1 s | **Request form** on the iTrust (SUTD) website, approval can take days to weeks | Final-phase real test |
| **WADI** (water distribution) | 123 tags | Same iTrust request as SWaT | Final-phase real test |

**What to do now:** clone HAI and SKAB (free), and **submit the SWaT/WADI request today**, so it arrives
before the final phase. Labelling a real dataset means mapping each tag to our concepts from its
documentation; budget an afternoon per dataset.

---

## Part E — Phase 1 build: how to run & results

### E1. Run
```
uv venv --python 3.13 .venv && uv pip install --python .venv -r requirements.txt
.venv/Scripts/python generator/simulate.py --plant plant_a --machines 80 --seed 1   # train plant
.venv/Scripts/python generator/simulate.py --plant plant_b --machines 30 --seed 2   # holdout plant
.venv/Scripts/python generator/plot_samples.py plant_a
.venv/Scripts/python mapper/train_eval.py --train plant_a --test plant_b
.venv/Scripts/python check.py
```
(Delete `results/features_*.csv` after regenerating data; they cache features.)

### E2. Results snapshot (full tables in `results/summary.md`)
Plant A: 613 tags / 80 machines (5-fold GroupKFold) · Plant B: 253 tags / 30 machines (unseen holdout) ·
16 signal types (5 targets + 11 look-alikes labelled Other)

| Method | CV A macro-F1 | Holdout B macro-F1 | Holdout B accuracy |
|---|---|---|---|
| Name-only | 0.79 | 0.77 | 0.66 |
| Behaviour-only | 0.80 | 0.87 | 0.87 |
| **Hybrid** | **0.90** | **0.93** | **0.92** |

Key observations for the slides:
- Look-alikes defeat behaviour alone: Pressure 60%, MotorCurrent 65%, Power 26% behaviour-only. The
  hybrid lifts them to 84%, 79% and 72%: names fix exactly the classes behaviour confuses.
- Name-only collapses on opaque names (2%); behaviour carries those (81%).
- **Modality dropout** (training on a copy with names blanked) stops the hybrid from over-trusting names.
- **Decision gate** (`mapper/decide.py`): constant signal → REVIEW, unfamiliar signal → REVIEW,
  confidence < 0.8 → REVIEW. **85% of holdout tags auto-accepted at 96.3% precision.**
- History: the first version (5 targets only) scored 97% behaviour-only (too easy); the look-alikes and the
  HAI-driven fixes (Part F) made the simulation harder and more realistic.

---

## Part F — Real-data test (HAI 21.03)

Model trained only on simulated plants, tested on 79 real tags. Details: `results/hai/findings.md`.

| | Round 1 (train1, before fixes) | Round 2 (train2, fresh, after fixes) |
|---|---|---|
| Hybrid accuracy | 49% | **81%** |
| Target tags correct (15) | 47% | **80%** |
| Precision of auto-accepted | 51% | **97.5%** (39/40) |
| Wrong claims auto-accepted | 19 | **0** |

- Round 1 diagnosed three failure modes: constant signals, a too-narrow "Other", and the site prefix.
- Fixes were general (decision gate, wider simulator, generic vocabulary, a one-line site prefix rule);
  HAI-specific abbreviations were deliberately not added.
- Caveat: same plant for both rounds. A second real plant (SWaT/WADI, SKAB) is a final-phase item.
