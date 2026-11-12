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

## Final phase
- [ ] Physics features: lagged cross-correlation to run signals, autocorrelation decay, spectral ratios (target: Pressure / Level errors)
- [ ] Split `Other` into named concepts (15–20 total); more Level/Flow examples
- [ ] Unseen naming style + shifted-distribution plant test
- [ ] Real-data validation: HAI / SKAB, then SWaT / WADI
- [ ] Probability calibration + auto-accept vs precision curve
- [ ] Modbus serving + ingestion (pymodbus)
- [ ] Review UI (FastAPI/Streamlit + SQLite)
- [ ] OPC UA server publishing (asyncua) + UaExpert demo
