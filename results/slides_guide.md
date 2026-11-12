# Phase 1 Slides Guide

How to build the Phase 1 review deck from the files in `results/`. Each slide below lists what to show,
which image or table to use, and what to say. Numbers come from `summary.md` (simulated) and
`hai/summary.md` (real data). If you regenerate anything, re-check the numbers there.

**Files**

| File | What it is |
|---|---|
| `samples_plant_a.png` | 2 raw signal examples for each of the 16 signal types, as the learner sees them (raw register values) |
| `comparison.png` | Bar chart: name-only vs behaviour-only vs hybrid (macro-F1, CV and holdout) |
| `confusion_matrices.png` | 3 confusion matrices on the simulated holdout plant |
| `feature_importance.png` | Top 12 features of the hybrid model |
| `summary.md` | Simulated results: methods, naming style, signal type, decision gate, showcase cases |
| `inference_table.csv` | Every simulated holdout tag: prediction, confidence, ACCEPT/REVIEW, reason, truth |
| `hai/hai_confusion.png` | 3 confusion matrices on **real** HAI data (fresh file) |
| `hai/hai_gate.png` | Real data: share auto-accepted vs precision of auto-accepted |
| `hai/findings.md` | Full development log of the real-data work (team reference, not for slides) |
| `hai/summary.md`, `hai/hai_predictions_train2.csv` | Real-data numbers and per-tag table |

**Suggested length:** 17 slides, 13–15 minutes.

---

## Slide 1 — Title
- Project title, team, guide, date. Subtitle: *"Phase 1: does name + behaviour beat either alone?"*

## Slide 2 — Problem recap (reuse Slide 3 from `idea.md`)
- Legacy tags have cryptic names (`T1_PV`, `M2_RUN`, `HR40012`). Mapping them to OPC UA by hand is slow, costly and error-prone.
- Modbus gives register addresses only. Documentation is lost. Small plants can't afford manual mapping.
- **Say:** "Phase 1 tests the core idea: can we infer what a tag *is* automatically, and know when we're unsure?"

## Slide 3 — Approach (pipeline diagram, draw it in PPT)
No image exists for this one; draw it with PPT shapes:
```
 Raw tag (name + time series)
        │
   ┌────┴─────┐
 Name analysis      Behaviour analysis
 (ISA-5.1, abbrev.,  (17 features: binary, monotonic,
  fuzzy match)        roughness, periodicity, correlation…)
   └────┬─────┘
   Hybrid XGBoost  ──►  concept + confidence
        │
   Decision gate:  constant signal? unfamiliar signal? confidence < 0.8?
        │                       │
     ACCEPT                HUMAN REVIEW (with reason)
```
- Mark what is **done in Phase 1** (everything above) and what comes later (Modbus, review UI, OPC UA).

## Slide 4 — Phase 1 scope
- Two columns: **Done now** vs **Final phase** (from `docs/phase1_plan.md` B2).
- Targets: Temperature, Pressure, RunStatus, MotorCurrent, Counter, plus **Other** (look-alike tags outside our vocabulary).
- **Bonus done in Phase 1:** a first real-data test (HAI). Results on slides 13–15.

## Slide 5 — Data generation: built to be realistic
Six bullets (details in `docs/phase1_plan.md` Part C1):
- Physics: first-order-plus-dead-time processes, PI and on/off temperature control, motor inrush, compressor load/unload
- 5 machine types: molder, pump station, compressor, conveyor, oven
- Real-world defects: coloured noise, drift, spikes, stuck sensors, historian deadband, missing data, comm loss, equipment that never changes state
- Raw Modbus integers (×10/×100 or ADC counts 0–4095 / 0–27648), so no engineering units
- 3 naming styles: ISA-5.1 (`TT101`), shorthand (`T1_PV`, typos), opaque PLC addresses (`HR40012`, `N7:3`), plus 5% misleading names
- **Dataset:** plant A = 80 machines / 613 tags (training); plant B = 30 machines / 253 tags (**unseen holdout**); 4 h at 1 Hz; 16 signal types

## Slide 6 — What the signals look like
- **Image:** `samples_plant_a.png`. It's very tall (16 rows), so crop to 5 rows: **Counter, MotorCurrent, Pressure, RunStatus, Temperature**.
- Point out on the slide: inrush spikes on current, counter rollover, comm-loss gaps, step-like deadband on temperature, the compressor sawtooth.

## Slide 7 — Why it's hard: look-alike tags
- **Image:** crop these pairs from `samples_plant_a.png` side by side: **Pressure vs Flow**, **Temperature vs Level**, **MotorCurrent vs Power**.
- **Say:** "Flow follows the pump just like pressure. Level is slow like temperature. Electrical power has exactly the same shape as motor current. Behaviour alone can't separate these. Behaviour-only gets power right only 26% of the time."
- Mention that an early version without look-alikes scored 97% behaviour-only. We made it harder because that was unrealistic.

## Slide 8 — Fair evaluation (separating generator from learner)
- Generator and learner are separate code; the learner only reads CSVs of raw values.
- The learner's vocabulary comes from ISA-5.1 and common abbreviations. The generator also uses words the learner doesn't know (`THM`, `HYD`, `SHOTS`), typos (`TEMPR`) and misleading names (`IR3xxxx`, `Q` = flow).
- The model is always tested on machines it never trained on (GroupKFold), on a separate simulated plant, **and on real data** (slides 13–15).

## Slide 9 — Main result (simulated) ⭐
- **Image:** `comparison.png`
- Table (holdout plant B):

  | Method | Accuracy | Macro-F1 |
  |---|---|---|
  | Name-only | 66% | 0.77 |
  | Behaviour-only | 87% | 0.87 |
  | **Hybrid** | **92%** | **0.93** |

- **Say:** "The hybrid beats both, on the training plant (CV) and on the unseen plant."

## Slide 10 — Where each method fails
- **Image:** `confusion_matrices.png`
- Table from `summary.md` (accuracy by true signal type), showing the look-alike rows:

  | True signal | Name | Behaviour | Hybrid |
  |---|---|---|---|
  | Pressure | 73% | 60% | **84%** |
  | MotorCurrent | 69% | 65% | **79%** |
  | Power (Other) | 82% | 26% | **72%** |
  | Temperature | 71% | 89% | **92%** |

- By naming style: ISA 87/81/**93**, shorthand 89/80/**92**, opaque 2/81/81 (name / behaviour / hybrid).
- **Say:** "When names are informative, they fix the behaviour mistakes. When names are meaningless, the hybrid falls back on behaviour (that's modality dropout in training)."

## Slide 11 — What the model relies on
- **Image:** `feature_importance.png`
- **Say:** "First it splits binary vs analog signals. Then it leans on the name scores for pressure, motor current and temperature, which are exactly the classes behaviour confuses."

## Slide 12 — Decision gate and inference demo (simulated) ⭐
- **The gate's three checks:** constant signal → REVIEW · unfamiliar signal (far from all training tags) → REVIEW · confidence < 0.8 → REVIEW.
- Headline: **85% of holdout tags auto-accepted at 96.3% precision**; 37 sent to review (31 low confidence, 4 constant, 2 unfamiliar).
- Example rows (from `summary.md` → Showcase):

  | Tag | Name says | Behaviour says | Hybrid | Conf. | Decision |
  |---|---|---|---|---|---|
  | `PRS_HYD3` | Pressure | MotorCurrent | Pressure ✔ | 0.96 | ACCEPT |
  | `Q5` | Counter | Other (flow) | Other ✔ | 0.83 | ACCEPT |
  | `M204_KW` | Other | MotorCurrent | Other ✔ | 0.70 | REVIEW |
  | `N7:1` | Unknown | Temperature | Temperature ✔ | 0.71 | REVIEW |
  | `HYD_PSI11` | Pressure | Other | Other ✘ | 0.51 | REVIEW |

- **Say:** "Every wrong hybrid prediction in the showcase landed in REVIEW."

## Slide 13 — The real dataset: what HAI is
- **HAI** = *HIL-based Augmented ICS* dataset, a public dataset from the **Affiliated Institute of ETRI (Daejeon, South Korea)**, a government research institute. Free on GitHub: https://github.com/icsdataset/hai
- It is recorded from a **real laboratory industrial plant** built from real industrial equipment and controllers:

  | Process | What it is | Real controller |
  |---|---|---|
  | P1 Boiler | water heating / heat exchange | Emerson Ovation DCS |
  | P2 Turbine | rotating-machine rotor kit | GE Mark VIe DCS |
  | P3 Water treatment | pumps water up to a tank and back | Siemens S7-300 PLC |
  | P4 HIL simulator | links the three into a virtual steam-turbine + pumped-storage hydro power plant | dSPACE SCALEXIO + Siemens S7-1500 |

- Data was collected through an **OPC UA gateway** (the same standard our project maps to), once per second, with the plant's own tag names (`P1_PIT01`, `P2_SIT01`, …).
- **Why it exists:** it was built for cybersecurity research (detecting attacks on control systems). We use **only the normal-operation files**, purely as a source of real tag names and real signals.
- **Version used:** HAI 21.03 (released 2021, 79 tags).
- **Image idea:** a simple 4-box diagram of P1–P4 (draw in PPT) or the testbed figure from the HAI technical manual (cite it).
- **Be precise if asked:** it's a lab-scale testbed with real industrial controllers, not a production factory. The power-plant link (P4) is simulated.

## Slide 14 — Real-data setup
- **Dataset:** HAI 21.03 (see slide 13). 79 real tags at 1 Hz; labels from the HAI technical manual.
- **Model trained only on simulated data.** HAI is never used for training.
- **Protocol (standard dev/test split):**
  - `train1` (60 h) = **development set**, used to check and refine the design (decision gate, signal coverage, site naming rule)
  - `train2` (a different 60 h) = **held-out test set**, untouched until the final evaluation
- Site configuration: one rule strips the plant's `P1_`/`P2_` process prefix, as an integrator would set up once per site.
- Real-world challenge worth stating: 22 of 79 tags are constant for the whole period (e.g. pumps that never switch), and 64 of 79 are outside our vocabulary.

## Slide 15 — Real-data result (held-out test set) ⭐
- **Image:** `hai/hai_gate.png` (main), `hai/hai_confusion.png` (backup or appendix).
- Table (`train2`, from `hai/summary.md`):

  | Method | Accuracy (79 real tags) |
  |---|---|
  | Name-only (site rule) | 57% |
  | Behaviour-only | 68% |
  | **Hybrid** | **81%** |

  - **Auto-accepted: 51% of tags, 97.5% correct (39 of 40)**
  - **0 wrong target claims auto-accepted.** Every uncertain tag, including all 22 constant signals, goes to review.
- **Say:** "The same pattern as in simulation, now on a real plant: the hybrid beats both single methods, and what it accepts automatically is almost always right."
- **Be upfront:** one real plant so far. A second one (SWaT) is planned for the final phase.

## Slide 16 — Limitations and final-phase roadmap
- **Limitations:**
  - Pressure is still the hardest class (84% simulated, 2 of 4 on HAI).
  - Only half of the real tags are auto-accepted.
  - One real plant so far.
- **Final phase:**
  1. Physics features: response lag after a pump/heater starts, autocorrelation decay, spectral ratios → pressure/temperature/flow confusion
  2. Grow from 5 concepts to 15–20 (split "Other"), plus general abbreviation expansion (embeddings/LLM)
  3. More real data: SWaT/WADI (requested), SKAB, HAI files with operating changes
  4. Calibrated confidence and an auto-accept vs precision curve
  5. Live Modbus ingestion, review web UI, OPC UA server publishing (demo in UaExpert)

## Slide 17 — Thank you / Q&A

---

## Likely examiner questions (prepare answers)

| Question | Answer |
|---|---|
| "What is HAI, is it really real?" | A public dataset from a South Korean government research institute (ETRI), recorded from a lab plant built with real industrial controllers (Emerson, GE, Siemens), collected via OPC UA. Lab-scale, not a factory; the power-plant link is simulated. |
| "Doesn't it work only because you generated the data?" | Separate code, independent vocabulary, unseen plant, **and a real-data test**: 81% accuracy and 97.5% precision of auto-accepted tags on a fresh HAI file. |
| "Didn't you tune to HAI?" | We used HAI `train1` as a development set to refine the design, as is standard. The reported numbers come from `train2`, which was held out until the end. No HAI-specific rules were added (e.g. no `PP` = pump abbreviation). Same plant for dev and test, so a second plant (SWaT) comes next. |
| "Why only 51% auto-accepted on real data?" | By design: 22 of 79 tags are constant (impossible to verify from behaviour) and the rest are uncertain. Safe beats fast. Raising coverage is the final-phase goal. |
| "Why is behaviour-only high compared with the literature?" | Coarse classes and clean physics in simulation. On real HAI, behaviour-only drops to 68%, which is close to the literature. |
| "Why XGBoost, not deep learning?" | ~900 tags is small data. Trees handle mixed, scale-free features, train in seconds and are explainable. |
| "What happens to a tag outside your vocabulary?" | It's predicted as "Other", or the gate flags it (low confidence / unfamiliar), so it goes to review. |
| "How was 0.8 chosen?" | Fixed for Phase 1. The final phase picks it from the precision vs auto-accept curve. |

## Design tips
- One message per slide, with the number in the title (e.g. *"Real data: 97.5% of auto-accepted tags correct"*).
- Slides 9, 12 and 15 carry the story: hybrid wins → the gate catches mistakes → it holds up on real data.
- Use consistent colours: name = one colour, behaviour = another, hybrid = a highlight colour.
