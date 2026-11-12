"""Phase 1 models & evaluation (LEARNER side).

Features are computed from raw CSVs only (no labels). Labels are joined here, solely as
training targets and for scoring. The generator code is never imported.

  python mapper/train_eval.py --train plant_a --test plant_b
Outputs -> results/
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from behaviour import machine_features  # noqa: E402
from decide import THRESHOLD, Gate  # noqa: E402
from names import CONCEPTS, name_rule, name_scores  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
METHODS = ["Name-only", "Behaviour-only", "Hybrid"]


def plant_features(plant):
    """Name + behaviour features for every tag of a plant (cached)."""
    cache = RES / f"features_{plant}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    frames = []
    for f in sorted((ROOT / "data" / plant / "raw").glob("*.csv")):
        b = machine_features(f)
        b.insert(0, "machine", f.stem)
        frames.append(b)
    df = pd.concat(frames, ignore_index=True)
    ns = pd.DataFrame([name_scores(t) for t in df.tag]).add_prefix("name_")
    df = pd.concat([df, ns], axis=1)
    df.to_csv(cache, index=False)
    return df


def model():
    return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9,
                         colsample_bytree=0.9, random_state=0, n_jobs=4)


def fit(X, y, cols):
    """Train XGBoost. If name features are used, also train on a copy with names blanked
    (modality dropout) so the model falls back on behaviour when a name is uninformative."""
    names = [c for c in cols if c.startswith("name_")]
    if names:
        X = pd.concat([X, X.assign(**{c: 0.0 for c in names})])
        y = np.concatenate([y, y])
    return model().fit(X[cols], y)


def load(plant):
    X = plant_features(plant)
    y = pd.read_csv(ROOT / "data" / plant / "labels.csv")
    return X.merge(y, on=["machine", "tag"], validate="1:1")


def run(train, test):
    RES.mkdir(exist_ok=True)
    A, B = load(train), load(test)
    beh = [c for c in A.columns if c not in ("machine", "tag") and not c.startswith("name_")
           and c not in ("concept", "subtype", "style", "archetype", "inverted", "misleading")]
    hyb = beh + [f"name_{c}" for c in CONCEPTS]
    enc = {c: i for i, c in enumerate(CONCEPTS)}
    yA, yB = A.concept.map(enc).to_numpy(), B.concept.map(enc).to_numpy()

    out = {}
    # --- cross-validation on train plant, grouped by machine
    cv = {"Name-only": A.tag.map(name_rule).to_numpy()}
    for meth, cols in (("Behaviour-only", beh), ("Hybrid", hyb)):
        proba = np.zeros((len(A), len(CONCEPTS)))
        for tr, te in GroupKFold(5).split(A, yA, A.machine):
            proba[te] = fit(A.iloc[tr], yA[tr], cols).predict_proba(A.iloc[te][cols])
        cv[meth] = np.array(CONCEPTS)[proba.argmax(1)]
    out["cv"] = cv
    # --- holdout: train on whole train plant, test on unseen plant
    ho, probaB = {"Name-only": B.tag.map(name_rule).to_numpy()}, {}
    for meth, cols in (("Behaviour-only", beh), ("Hybrid", hyb)):
        m = fit(A, yA, cols)
        probaB[meth] = m.predict_proba(B[cols])
        ho[meth] = np.array(CONCEPTS)[probaB[meth].argmax(1)]
        if meth == "Hybrid":
            imp = pd.Series(m.feature_importances_, index=cols).sort_values()[-12:]
    out["holdout"] = ho

    # --- metrics table
    rows = []
    for meth in METHODS:
        r = {"Method": meth}
        for split, df, preds in (("CV plant A", A, cv), ("Holdout plant B", B, ho)):
            r[f"{split} acc"] = accuracy_score(df.concept, preds[meth])
            r[f"{split} macro-F1"] = f1_score(df.concept, preds[meth], labels=CONCEPTS, average="macro")
        rows.append(r)
    metrics = pd.DataFrame(rows)

    # --- per naming style (both splits pooled for more tags)
    pooled = pd.concat([A.assign(**{m: cv[m] for m in METHODS}), B.assign(**{m: ho[m] for m in METHODS})])
    style = pooled.groupby("style").apply(
        lambda g: pd.Series({m: (g[m] == g.concept).mean() for m in METHODS} | {"tags": len(g)}),
        include_groups=False)
    by_sub = pooled.groupby("subtype").apply(
        lambda g: pd.Series({m: (g[m] == g.concept).mean() for m in METHODS} | {"tags": len(g)}),
        include_groups=False)

    # --- figures
    x = np.arange(len(METHODS))
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (col, lab) in enumerate((("CV plant A macro-F1", "CV plant A"), ("Holdout plant B macro-F1", "Holdout plant B"))):
        bars = ax.bar(x + (i - 0.5) * 0.38, metrics[col], 0.38, label=lab)
        ax.bar_label(bars, fmt="%.2f", fontsize=8)
    ax.set_xticks(x, METHODS)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("macro-F1")
    ax.legend()
    ax.set_title("Name vs behaviour vs hybrid")
    fig.tight_layout()
    fig.savefig(RES / "comparison.png", dpi=130)

    labs = CONCEPTS + ["Unknown"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, meth in zip(axes, METHODS):
        used = labs if meth == "Name-only" else CONCEPTS
        cm = confusion_matrix(B.concept, ho[meth], labels=used)[: len(CONCEPTS)]
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, v, ha="center", va="center", fontsize=9, color="white" if v > cm.max() / 2 else "black")
        ax.set_xticks(range(len(used)), used, rotation=35, ha="right", fontsize=8)
        ax.set_yticks(range(len(CONCEPTS)), CONCEPTS, fontsize=8)
        ax.set_title(f"{meth} (holdout plant B)")
        ax.set_xlabel("predicted")
    axes[0].set_ylabel("true")
    fig.tight_layout()
    fig.savefig(RES / "confusion_matrices.png", dpi=130)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(imp.index, imp.values)
    ax.set_title("Hybrid model: top feature importances")
    fig.tight_layout()
    fig.savefig(RES / "feature_importance.png", dpi=130)

    # --- inference table (holdout plant B, hybrid)
    P = probaB["Hybrid"]
    gate = Gate(A[beh])
    final = ho["Hybrid"]
    decision, reason = gate.decide(P.max(1), (B.change_frac == 0).to_numpy(), gate.novelty(B[beh]))
    inf = pd.DataFrame({
        "machine": B.machine, "tag": B.tag,
        "predicted": final, "confidence": P.max(1).round(3), "decision": decision, "reason": reason,
        "true": B.concept, "correct": final == B.concept,
        "name_only": ho["Name-only"], "behaviour_only": ho["Behaviour-only"], "style": B["style"],
    })
    inf.to_csv(RES / "inference_table.csv", index=False)
    acc = inf[inf.decision == "ACCEPT"]

    show = pd.concat([
        inf[(inf.name_only != inf.true) & inf.correct].assign(case="name wrong, hybrid right").head(4),
        inf[(inf.behaviour_only != inf.true) & inf.correct].assign(case="behaviour wrong, hybrid right").head(4),
        inf[~inf.correct].assign(case="hybrid wrong").head(4),
    ])

    # --- summary
    with open(RES / "summary.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 1 results\n\nTrain/CV: `{train}` ({len(A)} tags, {A.machine.nunique()} machines) · "
                f"Holdout: `{test}` ({len(B)} tags, {B.machine.nunique()} machines, never seen in training)\n\n")
        f.write("## Method comparison\n\n" + metrics.round(3).to_markdown(index=False) + "\n\n")
        f.write("## Accuracy by naming style (CV A + holdout B pooled)\n\n" + style.round(3).to_markdown() + "\n\n")
        f.write("## Accuracy by true signal type (look-alikes are labelled 'Other')\n\n"
                + by_sub.round(3).to_markdown() + "\n\n")
        f.write(f"## Confidence gating (hybrid, holdout B, threshold {THRESHOLD})\n\n"
                f"- Auto-accepted: {len(acc)}/{len(inf)} tags ({len(acc) / len(inf):.0%})\n"
                f"- Precision of auto-accepted: {acc.correct.mean():.1%}\n"
                f"- Sent to human review: {len(inf) - len(acc)} tags; hybrid accuracy on those: "
                f"{inf[inf.decision == 'REVIEW'].correct.mean():.1%}\n"
                f"- Review reasons: {inf[inf.decision == 'REVIEW'].reason.value_counts().to_dict()}\n\n")
        f.write("## Showcase cases\n\n" + show.drop(columns="correct").to_markdown(index=False) + "\n\n")
        f.write("Figures: `comparison.png`, `confusion_matrices.png`, `feature_importance.png`, `samples_plant_a.png`. "
                "Full table: `inference_table.csv`.\n")
    print((RES / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="plant_a")
    ap.add_argument("--test", default="plant_b")
    a = ap.parse_args()
    run(a.train, a.test)
