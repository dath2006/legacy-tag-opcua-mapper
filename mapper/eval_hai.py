"""Test the Phase 1 model on REAL data: HAI 21.03 (boiler / turbine / water-treatment testbed).

The model is trained ONLY on the simulated plants (plant_a + plant_b) and never sees HAI during training.
HAI train1 (~60 h at 1 Hz) is cut into 4-hour windows, the same length as the simulated data. Each
process P1..P4 is treated as one device. Predictions are averaged over the windows for each tag.

Name variants:
  raw       tag names as-is (P1_TIT01): the 'P1_' process prefix looks like an ISA 'P' = pressure hint
  stripped  site prefix removed (TIT01): the one-line site rule an integrator would configure

  python mapper/eval_hai.py      (needs external/hai/train1.csv.gz and real/hai_21.03_labels.csv)
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from behaviour import device_features  # noqa: E402
from names import CONCEPTS, name_rule, name_scores  # noqa: E402
from train_eval import THRESHOLD, fit, load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "hai"
WIN = 4 * 3600


def hai_features():
    cache = OUT / "features_hai.csv"
    if cache.exists():
        return pd.read_csv(cache)
    raw = pd.read_csv(ROOT / "external" / "hai" / "train1.csv.gz")
    raw = raw.drop(columns=[c for c in raw.columns if c == "time" or c.startswith("attack")])
    frames = []
    for w in range(len(raw) // WIN):
        win = raw.iloc[w * WIN:(w + 1) * WIN]
        for proc in sorted({c.split("_")[0] for c in win.columns}):
            f = device_features(win[[c for c in win.columns if c.startswith(proc + "_")]])
            f.insert(0, "window", w)
            frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(cache, index=False)
    return df


def strip(tag):
    return re.sub(r"^P\d_", "", tag)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sim = pd.concat([load("plant_a"), load("plant_b")], ignore_index=True)
    beh = [c for c in sim.columns if c not in ("machine", "tag", "concept", "subtype", "style", "archetype",
                                               "inverted", "misleading") and not c.startswith("name_")]
    hyb = beh + [f"name_{c}" for c in CONCEPTS]
    enc = {c: i for i, c in enumerate(CONCEPTS)}
    y = sim.concept.map(enc).to_numpy()
    m_beh, m_hyb = fit(sim, y, beh), fit(sim, y, hyb)

    H = hai_features()
    lab = pd.read_csv(ROOT / "real" / "hai_21.03_labels.csv")
    tags = lab.tag.tolist()
    preds, probas = {}, {}

    def per_tag(proba):
        """Average class probabilities over windows -> one prediction per tag."""
        P = pd.DataFrame(proba, columns=CONCEPTS).assign(tag=H.tag.values).groupby("tag").mean().loc[tags]
        return P.idxmax(axis=1).to_numpy(), P.max(axis=1).to_numpy()

    preds["Behaviour-only"], probas["Behaviour-only"] = per_tag(m_beh.predict_proba(H[beh]))
    for variant, fn in (("raw", lambda t: t), ("stripped", strip)):
        ns = pd.DataFrame([name_scores(fn(t)) for t in H.tag]).add_prefix("name_")
        X = pd.concat([H.reset_index(drop=True), ns], axis=1)
        preds[f"Hybrid ({variant} names)"], probas[f"Hybrid ({variant} names)"] = per_tag(m_hyb.predict_proba(X[hyb]))
        preds[f"Name-only ({variant} names)"] = np.array([name_rule(fn(t)) for t in tags])
        probas[f"Name-only ({variant} names)"] = None

    order = ["Name-only (raw names)", "Name-only (stripped names)", "Behaviour-only",
             "Hybrid (raw names)", "Hybrid (stripped names)"]
    truth = lab.concept.to_numpy()
    targets = truth != "Other"
    rows = []
    for m in order:
        p = preds[m]
        claimed = (p != "Other") & (p != "Unknown")
        row = {"Method": m, "Accuracy (79 tags)": accuracy_score(truth, p),
               "Target-tag recall (15)": (p[targets] == truth[targets]).mean(),
               "Other correctly rejected (64)": (p[~targets] == "Other").mean(),
               "Precision of target claims": (p[claimed] == truth[claimed]).mean() if claimed.any() else np.nan}
        if probas[m] is not None:
            acc = probas[m] >= THRESHOLD
            row["Auto-accepted"] = acc.mean()
            row["Precision of auto-accepted"] = (p[acc] == truth[acc]).mean() if acc.any() else np.nan
        rows.append(row)
    metrics = pd.DataFrame(rows)

    best = "Hybrid (stripped names)"
    table = lab[["tag", "concept", "description"]].rename(columns={"concept": "true"}).assign(
        name_only=preds["Name-only (stripped names)"], behaviour=preds["Behaviour-only"],
        hybrid=preds[best], confidence=probas[best].round(3),
        decision=np.where(probas[best] >= THRESHOLD, "ACCEPT", "REVIEW"))
    table["correct"] = table.hybrid == table.true
    table.to_csv(OUT / "hai_predictions.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    present = [c for c in CONCEPTS if c in set(truth)]
    for ax, m in zip(axes, ["Name-only (stripped names)", "Behaviour-only", best]):
        used = CONCEPTS + (["Unknown"] if m.startswith("Name") else [])
        cm = confusion_matrix(truth, preds[m], labels=used)
        cm = cm[[used.index(c) for c in present]]
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, v, ha="center", va="center", fontsize=9, color="white" if v > cm.max() / 2 else "black")
        ax.set_xticks(range(len(used)), used, rotation=35, ha="right", fontsize=8)
        ax.set_yticks(range(len(present)), present, fontsize=8)
        ax.set_title(f"{m} — HAI (real)", fontsize=10)
        ax.set_xlabel("predicted")
    axes[0].set_ylabel("true")
    fig.tight_layout()
    fig.savefig(OUT / "hai_confusion.png", dpi=130)

    targets_tbl = table[table.true != "Other"]
    wrong_other = table[(table.true == "Other") & ~table.correct]
    with open(OUT / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Real-data test: HAI 21.03 (train1)\n\n"
                f"Model trained only on simulated plants ({len(sim)} tags); tested on 79 real tags "
                f"({len(H) // 79} × 4 h windows, predictions averaged per tag). Classes present in HAI: "
                f"{', '.join(present)} (HAI has no motor current or counter tags).\n\n")
        f.write("## Metrics\n\n" + metrics.round(3).to_markdown(index=False) + "\n\n")
        f.write("## Target tags (Temperature / Pressure / RunStatus)\n\n"
                + targets_tbl.drop(columns="correct").to_markdown(index=False) + "\n\n")
        f.write(f"## 'Other' tags wrongly claimed as a target ({len(wrong_other)})\n\n"
                + wrong_other.drop(columns="correct").to_markdown(index=False) + "\n\n")
        f.write("Full table: `hai_predictions.csv`. Figure: `hai_confusion.png`.\n")
    print((OUT / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
