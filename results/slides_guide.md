# Phase 1 Slides Guide

How to build the Phase 1 review deck from the files in this folder. Each slide below lists what to
show, which image or table to use, and what to say. All numbers come from `summary.md`. If you
regenerate the data, re-check the numbers there.

**Files in this folder**

| File | What it is |
|---|---|
| `samples_plant_a.png` | 2 raw signal examples for each of the 11 signal types, shown as the learner sees them (raw register values) |
| `comparison.png` | Bar chart: name-only vs behaviour-only vs hybrid (macro-F1, CV and holdout) |
| `confusion_matrices.png` | 3 confusion matrices on the holdout plant |
| `feature_importance.png` | Top 12 features of the hybrid model |
| `summary.md` | All tables: methods, naming style, signal type, confidence gating, showcase cases |
| `inference_table.csv` | Every holdout tag: prediction, confidence, ACCEPT/REVIEW, true label |

**Suggested length:** 14 slides, 10–12 minutes.

---

## Slide 1 — Title
- Project title, team, guide, date. Subtitle: *"Phase 1: does name + behaviour beat either alone?"*

## Slide 2 — Problem recap (reuse Slide 3 from `idea.md`)
- Legacy tags have cryptic names (`T1_PV`, `M2_RUN`, `HR40012`). Mapping them to OPC UA by hand is slow, costly and error-prone.
- Modbus gives register addresses only. Documentation is lost. Small plants can't afford manual mapping.
- **Say:** "Phase 1 tests the core idea: can we infer what a tag *is* automatically?"

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
  ≥ 0.8 → ACCEPT     < 0.8 → HUMAN REVIEW
```
- Mark which parts are **done in Phase 1** (everything above) and which come later (Modbus, review UI, OPC UA).

## Slide 4 — Phase 1 scope
- Two columns: **Done now** vs **Final phase**. Copy from `docs/phase1_plan.md` section B2.
- Concepts: Temperature, Pressure, RunStatus, MotorCurrent, Counter, plus **Other** (look-alike tags outside our vocabulary).

## Slide 5 — Data generation: built to be realistic
- **Image:** a table or icon list. Use the left column of `docs/phase1_plan.md` Part C1, but keep only these 6 bullets:
  - Physics: first-order-plus-dead-time processes, PI and on/off temperature control, motor inrush
  - 5 machine types: molder, pump station, compressor, conveyor, oven
  - Real-world defects: coloured noise, drift, spikes, stuck sensors, historian deadband, missing data, comm loss
  - Raw Modbus integers (scaled ×10/×100 or ADC counts), so no engineering units
  - 3 naming styles: ISA-5.1 (`TT101`), shorthand (`T1_PV`, typos), opaque PLC addresses (`HR40012`, `N7:3`), plus 5% misleading names
  - **Dataset:** plant A = 80 machines / 510 tags (training); plant B = 30 machines / 212 tags (**unseen holdout**); 4 h at 1 Hz
- **Say:** "Every parameter is randomised per machine, so the model can't memorise a signature."

## Slide 6 — What the signals look like
- **Image:** `samples_plant_a.png`. It's tall (11 rows), so crop it to 4–6 rows. Recommended rows:
  **Counter, MotorCurrent, Pressure, RunStatus, Temperature**.
- Point out on the slide: inrush spikes on current, counter rollover, gaps from comm loss, step-like deadband on temperature, the compressor sawtooth.

## Slide 7 — Why it's hard: look-alike tags
- **Image:** crop the rows **Pressure, Flow, Temperature, Level** from `samples_plant_a.png` side by side.
- **Say:** "Pressure and flow both follow the pump. Level and temperature are both slow. Behaviour alone can't always tell them apart, which is why the name matters."
- Mention that an earlier run without look-alike tags scored 97% behaviour-only. We added them because that was unrealistically easy.

## Slide 8 — Fair evaluation (separating generator from learner)
- Generator and learner are separate code. The learner reads only CSV files of raw values and never sees generator code.
- The learner's vocabulary comes from ISA-5.1 and common abbreviations. The generator also uses words the learner doesn't know (`THM`, `HYD`, `SHOTS`), typos (`TEMPR`) and misleading names (`IR3xxxx`).
- The model is always tested on machines it never trained on (GroupKFold) **and** on a completely separate plant.
- **Be honest:** "Final validation on real data (HAI, SWaT) is planned for the final phase."

## Slide 9 — Main result ⭐
- **Image:** `comparison.png`
- Table (holdout plant B):

  | Method | Accuracy | Macro-F1 |
  |---|---|---|
  | Name-only | 62% | 0.71 |
  | Behaviour-only | 93% | 0.93 |
  | **Hybrid** | **94%** | **0.94** |

- **Say:** "The hybrid wins on both the training plant (CV) and the unseen plant."

## Slide 10 — Where each method fails
- **Image:** `confusion_matrices.png`
- Read it left to right:
  - **Name-only:** big "Unknown" column. Opaque names carry no information (3% accuracy on opaque names).
  - **Behaviour-only:** Pressure leaks into Temperature and Other. That's the look-alike problem.
  - **Hybrid:** cleanest diagonal.
- Optional small table from `summary.md` (accuracy by naming style):

  | Naming style | Name | Behaviour | Hybrid |
  |---|---|---|---|
  | ISA | 83% | 94% | **95%** |
  | Shorthand | 92% | 92% | **95%** |
  | Opaque | 3% | 89% | **89%** |

- **Say:** "On shorthand names, name and behaviour each get 92%, but together they reach 95%. They fix each other's mistakes."

## Slide 11 — The model uses names exactly where behaviour fails
- **Image:** `feature_importance.png`
- **Say:** "The most important feature is the name's pressure score, and pressure is exactly where behaviour struggles (67% → 74% with the hybrid)."
- Mention modality dropout in one line: "During training we also show the model tags with their names hidden, so it falls back on behaviour when a name is meaningless."

## Slide 12 — Confidence gating and inference demo ⭐
- Headline: **92% of tags auto-accepted at 97.4% precision; 8% sent to human review.**
- Table: pick 5–6 rows from `summary.md` → *Showcase cases*. Recommended:

  | Tag | Name says | Behaviour says | Hybrid | Confidence | Decision |
  |---|---|---|---|---|---|
  | `REG2325` | Unknown | RunStatus | RunStatus ✔ | 0.998 | ACCEPT |
  | `REG1566` | Unknown | Temperature | Temperature ✔ | 0.842 | ACCEPT |
  | `DISCH_P3` | Pressure | Temperature | Pressure ✔ | 0.722 | REVIEW |
  | `AI_03` | Unknown | Other | Pressure ✔ | 0.612 | REVIEW |
  | `PI603` | Pressure | Temperature | Temperature ✘ | 0.768 | REVIEW |

- **Key point:** every wrong hybrid prediction in the showcase landed in **REVIEW**. The confidence score catches the mistakes, which is the whole point of human-in-the-loop.
- The full list is in `inference_table.csv` (filter `decision = REVIEW`).

## Slide 13 — Limitations and final-phase roadmap
- **Limitations (be upfront):**
  - Pressure is still the main error (74%). Level is weak (only 8 examples).
  - The data is simulated, so real-data validation is still pending.
- **Final phase:**
  1. Physics features: response lag after a pump or heater starts, autocorrelation decay, spectral ratios → targets the pressure/temperature confusion
  2. Grow from 5 concepts to 15–20 (split "Other")
  3. Real data: HAI and SKAB (free), SWaT and WADI (requested)
  4. Calibrated confidence and an auto-accept vs precision curve
  5. Live Modbus ingestion, review web UI, OPC UA server publishing (demo in UaExpert)

## Slide 14 — Thank you / Q&A

---

## Likely examiner questions (prepare answers)

| Question | Answer |
|---|---|
| "Didn't it work only because you generated the data?" | Generator and learner are separate code. The vocabulary is independent and includes unseen words and misleading names. Testing uses an unseen plant. Real-data validation (HAI/SWaT) is in the final phase. |
| "Why is behaviour-only so high compared with the literature?" | 6 coarse classes and clean physics. Accuracy drops as concepts grow to 15–20 and on real data. The look-alike "Other" tags already pulled it down from 97%. |
| "Why XGBoost and not deep learning?" | 700 tags is small data. Tree models handle mixed, scale-free features, train in seconds and show which features matter. |
| "What happens to a tag that isn't in your vocabulary?" | It's predicted as "Other" or gets low confidence, so it goes to human review. |
| "How do you pick the 0.8 threshold?" | It's fixed for now. The final phase plots precision vs the share auto-accepted and picks the threshold from that curve. |

## Design tips
- One message per slide; put the number in the title (e.g. *"Hybrid: 94% on an unseen plant"*).
- Slides 9 and 12 are the money slides. Give them the most space.
- Use consistent colours: name = one colour, behaviour = another, hybrid = a highlight colour.
