"""Sanity checks. Run: .venv/Scripts/python check.py"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "mapper"))
from behaviour import tag_features  # noqa: E402
from names import name_rule, name_scores  # noqa: E402

# 1. Isolation: learner never imports the generator, and only train_eval touches labels.
for f in (ROOT / "mapper").glob("*.py"):
    src = f.read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+(generator|simulate)", src, re.M), f"{f.name} imports generator"
    if f.name != "train_eval.py":
        assert '"labels.csv"' not in src, f"{f.name} reads labels"

# 2. Name analysis
assert name_rule("TIC101_PV") == "Temperature"
assert name_rule("PT-204") == "Pressure"
assert name_rule("M1_RUN") == "RunStatus"
assert name_rule("MTR_AMPS3") == "MotorCurrent"
assert name_rule("PART_CNT2") == "Counter"
assert name_rule("FIT301") == "Other"
assert name_rule("TEMPR4") == "Temperature"  # fuzzy typo
assert name_rule("HR40012") == "Unknown"  # opaque address carries no evidence
s = name_scores("P101_RUN")  # pump run: name hints both pressure (P) and run
assert s["RunStatus"] > s["Pressure"] > 0

# 3. Behaviour features
rng = np.random.default_rng(0)
run = (np.arange(3600) // 300 % 2).astype(float)
f = tag_features(run, {})
assert f["is_binary"] == 1
cnt = np.cumsum(rng.random(3600) < 0.1).astype(float) + 100
f = tag_features(cnt, {})
assert f["up_frac"] == 1 and f["step_regularity"] == 1
cur = run * 50 + rng.normal(0, 1, 3600)
assert tag_features(cur, {"r": run})["corr_binary"] > 0.95
x = cur.copy()
x[::7] = np.nan
assert abs(tag_features(x, {})["missing_frac"] - 1 / 7) < 0.01

print("all checks passed")
