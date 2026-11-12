# Legacy Tag → OPC UA Semantic Mapper

Infers what a cryptic legacy machine tag is (Temperature, Pressure, RunStatus, MotorCurrent, Counter, Other)
from its **name** and its **time-series behaviour**, with a confidence score so only uncertain tags go to
human review.

- `idea.md` — project idea
- `docs/phase1_plan.md` — discussion, Phase 1 plan, data-realism research, real datasets, results
- `docs/TODO.md` — tasks by phase
- `generator/` — realistic legacy-plant simulator (never imported by the learner)
- `mapper/` — name analysis, behaviour features, models & evaluation
- `results/` — figures, `summary.md`, `slides_guide.md`

## Run
```
uv venv --python 3.13 .venv && uv pip install --python .venv -r requirements.txt
.venv/Scripts/python generator/simulate.py --plant plant_a --machines 80 --seed 1
.venv/Scripts/python generator/simulate.py --plant plant_b --machines 30 --seed 2
.venv/Scripts/python generator/plot_samples.py plant_a
.venv/Scripts/python mapper/train_eval.py --train plant_a --test plant_b
.venv/Scripts/python check.py
```

## Real-data test (HAI 21.03)
```
mkdir -p external/hai
curl -L -o external/hai/train1.csv.gz https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03/train1.csv.gz
curl -L -o external/hai/train2.csv.gz https://raw.githubusercontent.com/icsdataset/hai/master/hai-21.03/train2.csv.gz
.venv/Scripts/python mapper/eval_hai.py
```
Results and the story behind them: `results/hai/findings.md`.

## Classifier comparison
```
.venv/Scripts/python mapper/compare_models.py    # needs the plants + HAI train2 features from eval_hai.py
```
Results: `results/model_comparison.md`.
