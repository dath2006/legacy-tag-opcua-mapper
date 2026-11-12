# Phase 1 — TODO

Legend: [x] done · [ ] pending

## P1.0 Setup
- [x] Research realistic industrial data generation + real datasets (`phase1_plan.md` Parts C, D)
- [x] Python 3.13 venv (`.venv`) + `requirements.txt`
- [x] Folder layout with generator / learner isolation

## P1.1 Data generation (generator/)
- [x] Run schedules (production runs, micro-stops, planned breaks)
- [x] Physics: FOPDT, PI + on/off temperature loops, pump / compressor / hydraulic / plant-air pressure, inrush + VFD current, cycle counters with rollover/reset
- [x] Machine archetypes: molder, pump station, compressor, conveyor, oven
- [x] Imperfections: AR(1) noise per sensor type, drift, spikes, stuck sensor, historian deadband, ADC/register scaling, dropouts, comm loss
- [x] Naming: ISA-5.1, shorthand (typos, unseen vocab), opaque PLC addresses, 5% repurposed names, inverted STOP bits
- [x] Look-alike `Other` tags: flow, level, speed, setpoint, controller output, alarm
- [x] Train plant A (80 machines, 510 tags) + holdout plant B (30 machines, 212 tags)
- [x] Sample signal plots per signal type

## P1.2 Name analysis (mapper/names.py)
- [x] Tokenizer, ISA-5.1 rules, abbreviation vocabulary, rapidfuzz fuzzy match → 6 scores

## P1.3 Behaviour analysis (mapper/behaviour.py)
- [x] 17 basic scale-invariant features (binary, monotonic, step regularity, roughness, reversals, periodicity, floor time, correlation to binary tags, ...)

## P1.4 Models & evaluation (mapper/train_eval.py)
- [x] Name-only rule, behaviour-only XGBoost, hybrid XGBoost (+ modality dropout)
- [x] GroupKFold by machine on plant A + holdout on unseen plant B
- [x] Metrics, confusion matrices, per-style and per-signal-type tables, bar chart, feature importance
- [x] Inference table with confidence + ACCEPT/REVIEW (threshold 0.8) and showcase cases

## P1.5 Verification & report
- [x] `check.py` passes (isolation, name rules, feature sanity)
- [x] `results/summary.md` + figures; results snapshot in `phase1_plan.md` Part E

## P1.6 For the team (not code)
- [ ] Clone HAI + SKAB; submit SWaT/WADI request (`phase1_plan.md` Part D)
- [ ] Build slides from `results/` (outline in B12)
- [ ] Find a citation for the "time-series-only < 65%" claim, or drop it

## P1.7 Real-data check (HAI 21.03)
- [x] HAI hand labels (`real/hai_21.03_labels.csv`) + `mapper/eval_hai.py`
- [x] Round 1 (train1): 49% accuracy; diagnosed constant signals, narrow "Other", site prefix
- [x] Decision gate: constant signal → REVIEW, unfamiliar signal → REVIEW, low confidence → REVIEW (`mapper/decide.py`)
- [x] Wider simulated "Other": vibration, power, voltage, frequency, valve position; equipment that never changes state
- [x] Generic vocabulary for those quantities; site prefix rule (`SITE_PREFIX`)
- [x] Round 2 on a fresh file (train2): 81% accuracy, 97.5% precision of auto-accepted, 0 wrong claims auto-accepted
- [x] Results + slides added (`results/hai/`, `results/slides_guide.md` slides 13–14)

## P1.8 Classifier comparison
- [x] `mapper/compare_models.py`: XGBoost vs Random Forest, Logistic Regression, k-NN, Decision Tree on identical features and splits
- [x] Result: XGBoost kept (top-tier accuracy + reliable confidence); Logistic Regression is a strong runner-up; Random Forest confidence unreliable (`results/model_comparison.md`)

## Final phase
- [ ] Re-run the classifier comparison on a second real plant; tune the non-XGBoost baselines for a fully fair comparison
- [ ] General abbreviation expansion (PP = pump, R/D suffixes, ...) via embeddings / LLM, not hand-tuned per dataset
- [ ] Second real plant: SWaT/WADI, SKAB; HAI files with operating changes
- [ ] Physics features: lagged cross-correlation to run signals, autocorrelation decay, spectral ratios (target: Pressure / Level errors)
- [ ] Split `Other` into named concepts (15–20 total); more Level/Flow examples
- [ ] Unseen naming style + shifted-distribution plant test
- [ ] Real-data validation: HAI / SKAB, then SWaT / WADI
- [ ] Probability calibration + auto-accept vs precision curve
- [ ] Modbus serving + ingestion (pymodbus)
- [ ] Review UI (FastAPI/Streamlit + SQLite)
- [ ] OPC UA server publishing (asyncua) + UaExpert demo
