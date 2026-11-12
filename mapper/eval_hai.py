"""Test the Phase 1 model on REAL data: HAI 21.03 (boiler / turbine / water-treatment testbed).

The model is trained ONLY on the simulated plants (plant_a + plant_b); HAI is never used for training.
Each HAI file (~60 h at 1 Hz) is cut into 4-hour windows (same length as the simulated data); each
process P1..P4 is treated as one device; class probabilities are averaged over windows per tag.

  train1  diagnosis set: used to find the failure modes that led to the generic fixes
  train2  fresh set: a different 60 h period, never looked at while fixing

Site rule: HAI prefixes every tag with its process ('P1_'). An integrator configures this once per site
(SITE_PREFIX); without it, 'P' + digit reads as an ISA pressure hint.

  python mapper/eval_hai.py      (needs external/hai/train{1,2}.csv.gz, real/hai_21.03_labels.csv)
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from behaviour import device_features  # noqa: E402
from decide import Gate  # noqa: E402
from names import CONCEPTS, name_rule, name_scores  # noqa: E402
from train_eval import fit, load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "hai"
WIN = 4 * 3600
SITE_PREFIX = r"^P\d_"
FILES = {"train1": "diagnosis", "train2": "fresh"}


def hai_features(name):
    cache = OUT / f"features_{name}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    raw = pd.read_csv(ROOT / "external" / "hai" / f"{name}.csv.gz")
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


def site(tag):
    return re.sub(SITE_PREFIX, "", tag)


def scores(truth, pred, decision=None):
    t = truth != "Other"
    claimed = (pred != "Other") & (pred != "Unknown")
    r = {"Accuracy": (pred == truth).mean(),
         "Target recall (15)": (pred[t] == truth[t]).mean(),
         "Other rejected (64)": (pred[~t] == "Other").mean(),
         "Precision of target claims": (pred[claimed] == truth[claimed]).mean() if claimed.any() else np.nan}
    if decision is not None:
        a = decision == "ACCEPT"
        r["Auto-accepted"] = a.mean()
        r["Precision of auto-accepted"] = (pred[a] == truth[a]).mean() if a.any() else np.nan
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sim = pd.concat([load("plant_a"), load("plant_b")], ignore_index=True)
    beh = [c for c in sim.columns if c not in ("machine", "tag", "concept", "subtype", "style", "archetype",
                                               "inverted", "misleading") and not c.startswith("name_")]
    hyb = beh + [f"name_{c}" for c in CONCEPTS]
    y = sim.concept.map({c: i for i, c in enumerate(CONCEPTS)}).to_numpy()
    m_beh, m_hyb, gate = fit(sim, y, beh), fit(sim, y, hyb), Gate(sim[beh])

    lab = pd.read_csv(ROOT / "real" / "hai_21.03_labels.csv")
    tags, truth = lab.tag.tolist(), lab.concept.to_numpy()
    name_raw = np.array([name_rule(t) for t in tags])
    name_site = np.array([name_rule(site(t)) for t in tags])

    rows, tables, preds_by_file = [], {}, {}
    for fname, role in FILES.items():
        H = hai_features(fname)
        ns = pd.DataFrame([name_scores(site(t)) for t in H.tag]).add_prefix("name_")
        X = pd.concat([H.reset_index(drop=True), ns], axis=1)

        def per_tag(values, how="mean"):
            return pd.DataFrame(values).assign(tag=H.tag.values).groupby("tag").agg(how).loc[tags]

        Pb = per_tag(m_beh.predict_proba(X[beh]))
        Ph = per_tag(m_hyb.predict_proba(X[hyb]))
        beh_pred = np.array(CONCEPTS)[Pb.to_numpy().argmax(1)]
        hyb_pred = np.array(CONCEPTS)[Ph.to_numpy().argmax(1)]
        conf = Ph.to_numpy().max(1)
        constant = per_tag({"c": H.change_frac.values}, "max")["c"].to_numpy() == 0
        novelty = per_tag({"n": gate.novelty(X[beh])}, "median")["n"].to_numpy()
        decision, reason = gate.decide(conf, constant, novelty)
        final = hyb_pred

        for meth, p, d in (("Name-only (raw names)", name_raw, None), ("Name-only (site rule)", name_site, None),
                           ("Behaviour-only", beh_pred, None), ("Hybrid + decision gate", final, decision)):
            rows.append({"File": f"{fname} ({role})", "Method": meth} | scores(truth, p, d))
        preds_by_file[fname] = {"Name-only (site rule)": name_site, "Behaviour-only": beh_pred, "Hybrid + gate": final}
        tables[fname] = lab[["tag", "concept", "description"]].rename(columns={"concept": "true"}).assign(
            name_only=name_site, behaviour=beh_pred, hybrid=final, confidence=conf.round(3),
            novelty=novelty.round(2), decision=decision, reason=reason)
        tables[fname]["correct"] = tables[fname].hybrid == tables[fname].true
        tables[fname].to_csv(OUT / f"hai_predictions_{fname}.csv", index=False)
    metrics = pd.DataFrame(rows)

    # figure 1: confusion matrices on the fresh file
    present = [c for c in CONCEPTS if c in set(truth)]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (meth, p) in zip(axes, preds_by_file["train2"].items()):
        used = CONCEPTS + ["Unknown"]
        cm = confusion_matrix(truth, p, labels=used)[[used.index(c) for c in present]]
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, v, ha="center", va="center", fontsize=9, color="white" if v > cm.max() / 2 else "black")
        ax.set_xticks(range(len(used)), used, rotation=35, ha="right", fontsize=8)
        ax.set_yticks(range(len(present)), present, fontsize=8)
        ax.set_title(f"{meth} — HAI train2 (real, fresh)", fontsize=10)
        ax.set_xlabel("predicted")
    axes[0].set_ylabel("true")
    fig.tight_layout()
    fig.savefig(OUT / "hai_confusion.png", dpi=130)

    # figure 2: the safety story — what gets auto-accepted, and how often it is right
    g = metrics[metrics.Method == "Hybrid + decision gate"]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(g))
    for i, (col, lab_) in enumerate((("Auto-accepted", "share auto-accepted"),
                                     ("Precision of auto-accepted", "precision of auto-accepted"))):
        bars = ax.bar(x + (i - 0.5) * 0.38, g[col], 0.38, label=lab_)
        ax.bar_label(bars, fmt="%.2f", fontsize=8)
    ax.set_xticks(x, g.File)
    ax.set_ylim(0, 1.1)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title("Real data: hybrid + decision gate")
    fig.tight_layout()
    fig.savefig(OUT / "hai_gate.png", dpi=130)

    t2 = tables["train2"]
    with open(OUT / "summary.md", "w", encoding="utf-8") as f:
        f.write("# Real-data test: HAI 21.03\n\n"
                f"Model trained only on simulated plants ({len(sim)} tags). Tested on 79 real tags; "
                "4 h windows, probabilities averaged per tag. `train1` was used to diagnose failures; "
                "`train2` is a fresh 60 h period never looked at while fixing. HAI classes: "
                f"{', '.join(present)} (no motor-current or counter tags). Site rule: strip `{SITE_PREFIX}`.\n\n")
        f.write("## Metrics\n\n" + metrics.round(3).to_markdown(index=False) + "\n\n")
        f.write("## train2 (fresh): review reasons\n\n"
                + t2[t2.decision == "REVIEW"].reason.value_counts().to_frame("tags").to_markdown() + "\n\n")
        f.write("## train2 (fresh): auto-accepted tags\n\n"
                + t2[t2.decision == "ACCEPT"].drop(columns="correct").to_markdown(index=False) + "\n\n")
        f.write("## train2 (fresh): target tags\n\n"
                + t2[t2.true != "Other"].drop(columns="correct").to_markdown(index=False) + "\n\n")
        f.write("Per-tag tables: `hai_predictions_train1.csv`, `hai_predictions_train2.csv`. "
                "Figures: `hai_confusion.png`, `hai_gate.png`.\n")
    print((OUT / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
