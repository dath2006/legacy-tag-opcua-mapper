"""Plot two example raw signals per concept (for slides). Usage: python generator/plot_samples.py plant_a"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
plant = sys.argv[1] if len(sys.argv) > 1 else "plant_a"
lab = pd.read_csv(ROOT / "data" / plant / "labels.csv")
concepts = sorted(lab.subtype.unique())
fig, axes = plt.subplots(len(concepts), 2, figsize=(13, 2.3 * len(concepts)))
for r, c in enumerate(concepts):
    picks = lab[lab.subtype == c].sample(2, random_state=3)
    for k, (_, row) in enumerate(picks.iterrows()):
        s = pd.read_csv(ROOT / "data" / plant / "raw" / f"{row.machine}.csv", usecols=[row.tag])[row.tag]
        ax = axes[r, k]
        ax.plot(s.values, lw=0.6)
        ax.set_title(f"{c}  |  {row.machine}/{row.tag}  ({row.archetype}, {row.style})", fontsize=9)
        ax.tick_params(labelsize=7)
axes[-1, 0].set_xlabel("time [s]")
axes[-1, 1].set_xlabel("time [s]")
fig.suptitle("Raw register values (as the learner sees them)", fontsize=11)
fig.tight_layout()
out = ROOT / "results"
out.mkdir(exist_ok=True)
fig.savefig(out / f"samples_{plant}.png", dpi=130)
print("saved", out / f"samples_{plant}.png")
