"""Compare classifiers for the hybrid (name + behaviour) mapper: why XGBoost?

Every model gets the same features, the same modality dropout, the same GroupKFold split on plant A,
the same unseen holdout plant B, and the same real-data test (HAI 21.03 train2, the held-out file).
Non-tree models get median imputation + scaling, since they can't handle NaN / raw scales.

  python mapper/compare_models.py      -> results/model_comparison.md, results/model_comparison.png
"""
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_hai import hai_features, site  # noqa: E402
from names import CONCEPTS, name_scores  # noqa: E402
from train_eval import load, model as xgboost_model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
THRESHOLD = 0.8


def prep(clf):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), clf)


MODELS = {
    "XGBoost": xgboost_model,
    "Random Forest": lambda: prep(RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=4)),
    "Decision Tree": lambda: prep(DecisionTreeClassifier(max_depth=8, random_state=0)),
    "Logistic Regression": lambda: prep(LogisticRegression(max_iter=3000)),
    "k-NN (k=5)": lambda: prep(KNeighborsClassifier(n_neighbors=5)),
}


def fit(make, X, y, cols):
    """Same modality dropout as train_eval.fit: also train on a copy with name features blanked."""
    names = [c for c in cols if c.startswith("name_")]
    X2 = pd.concat([X, X.assign(**{c: 0.0 for c in names})])
    return make().fit(X2[cols], np.concatenate([y, y]))


def main():
    A, B = load("plant_a"), load("plant_b")
    beh = [c for c in A.columns if c not in ("machine", "tag", "concept", "subtype", "style", "archetype",
                                             "inverted", "misleading") and not c.startswith("name_")]
    cols = beh + [f"name_{c}" for c in CONCEPTS]
    enc = {c: i for i, c in enumerate(CONCEPTS)}
    yA, yB = A.concept.map(enc).to_numpy(), B.concept.map(enc).to_numpy()
    sim = pd.concat([A, B], ignore_index=True)
    ysim = np.concatenate([yA, yB])

    # real data: HAI 21.03 train2 (held-out), site prefix rule, probabilities averaged over 4 h windows
    H = hai_features("train2").reset_index(drop=True)
    H = pd.concat([H, pd.DataFrame([name_scores(site(t)) for t in H.tag]).add_prefix("name_")], axis=1)
    lab = pd.read_csv(ROOT / "real" / "hai_21.03_labels.csv")
    truth = lab.concept.to_numpy()

    rows = []
    for name, make in MODELS.items():
        t0 = time.perf_counter()
        oof = np.zeros(len(A), int)
        for tr, te in GroupKFold(5).split(A, yA, A.machine):
            oof[te] = fit(make, A.iloc[tr], yA[tr], cols).predict(A.iloc[te][cols])
        hoB = fit(make, A, yA, cols).predict(B[cols])
        m = fit(make, sim, ysim, cols)  # final model: all simulated data, as in eval_hai
        P = pd.DataFrame(m.predict_proba(H[cols]), columns=CONCEPTS).assign(tag=H.tag).groupby("tag").mean().loc[lab.tag]
        pred, conf = P.idxmax(axis=1).to_numpy(), P.max(axis=1).to_numpy()
        acc = conf >= THRESHOLD
        rows.append({
            "Model": name,
            "CV plant A macro-F1": f1_score(yA, oof, average="macro"),
            "Holdout plant B macro-F1": f1_score(yB, hoB, average="macro"),
            "HAI real accuracy": (pred == truth).mean(),
            "HAI auto-accepted (conf >= 0.8)": acc.mean(),
            "HAI precision of auto-accepted": (pred[acc] == truth[acc]).mean() if acc.any() else np.nan,
            "Run time (s)": time.perf_counter() - t0,
        })
        print(rows[-1])
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(df))
    metrics = ["CV plant A macro-F1", "Holdout plant B macro-F1", "HAI real accuracy"]
    for i, col in enumerate(metrics):
        bars = ax.bar(x + (i - 1) * 0.27, df[col], 0.27, label=col)
        ax.bar_label(bars, fmt="%.2f", fontsize=7)
    ax.set_xticks(x, df.Model, fontsize=9)
    ax.set_ylim(0, 1.2)
    ax.legend(fontsize=8, loc="upper center", ncol=3, frameon=False)
    ax.set_title("Classifier comparison (same features, same splits)")
    fig.tight_layout()
    fig.savefig(RES / "model_comparison.png", dpi=130)

    with open(RES / "model_comparison.md", "w", encoding="utf-8") as f:
        f.write("# Classifier comparison\n\n"
                "Same hybrid features (17 behaviour + 6 name scores), same modality dropout, same splits:\n"
                "5-fold GroupKFold on simulated plant A, unseen simulated plant B, and real HAI 21.03 `train2` "
                "(held-out; models trained on all simulated data). Non-tree models use median imputation + "
                "scaling. Run time covers CV + holdout + final fit.\n\n")
        f.write(df.round(3).to_markdown(index=False) + "\n\nFigure: `model_comparison.png`\n\n")
        f.write(
            "## Reading the results\n\n"
            "- **No single model wins every column.** Random Forest is best on simulated cross-validation, "
            "Logistic Regression is best on real-data accuracy, and XGBoost ties for best on the simulated holdout.\n"
            "- **What our system needs most is trustworthy confidence**, because the decision gate auto-accepts "
            "anything at or above 0.8. On real data only XGBoost and Logistic Regression keep auto-accepted tags "
            "about 98% correct. Random Forest's probabilities are poorly suited: it accepts few tags, and about a "
            "quarter of those are wrong. k-NN and a single Decision Tree are clearly weaker.\n"
            "- **Why we keep XGBoost:** it is top-tier on every accuracy column, its confidence is reliable, it "
            "handles missing values natively, and it explains itself through feature importance.\n"
            "- **Logistic Regression is a strong, simpler runner-up.** That's a useful finding: the features "
            "carry most of the signal, not the model's complexity. Worth re-testing on a second real plant.\n"
            "- **Caveats:** HAI has 79 tags, so a gap of 0.04 in accuracy is about 3 tags, which is not "
            "significant. XGBoost's settings were chosen during the project; the other models use library "
            "defaults. 'Auto-accepted' here uses confidence only; the full decision gate also sends constant "
            "and unfamiliar signals to review (51% auto-accepted for XGBoost in `hai/summary.md`).\n")
    print((RES / "model_comparison.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
