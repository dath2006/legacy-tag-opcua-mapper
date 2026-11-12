# Classifier comparison

Same hybrid features (17 behaviour + 6 name scores), same modality dropout, same splits:
5-fold GroupKFold on simulated plant A, unseen simulated plant B, and real HAI 21.03 `train2` (held-out; models trained on all simulated data). Non-tree models use median imputation + scaling. Run time covers CV + holdout + final fit.

| Model               |   CV plant A macro-F1 |   Holdout plant B macro-F1 |   HAI real accuracy |   HAI auto-accepted (conf >= 0.8) |   HAI precision of auto-accepted |   Run time (s) |
|:--------------------|----------------------:|---------------------------:|--------------------:|----------------------------------:|---------------------------------:|---------------:|
| XGBoost             |                 0.898 |                      0.931 |               0.81  |                             0.57  |                            0.978 |          8.764 |
| Random Forest       |                 0.937 |                      0.93  |               0.81  |                             0.291 |                            0.739 |          5.156 |
| Decision Tree       |                 0.84  |                      0.844 |               0.658 |                             0.709 |                            0.625 |          0.146 |
| Logistic Regression |                 0.88  |                      0.895 |               0.848 |                             0.595 |                            0.979 |          0.388 |
| k-NN (k=5)          |                 0.865 |                      0.867 |               0.797 |                             0.759 |                            0.883 |          0.258 |

Figure: `model_comparison.png`

## Reading the results

- **No single model wins every column.** Random Forest is best on simulated cross-validation, Logistic Regression is best on real-data accuracy, and XGBoost ties for best on the simulated holdout.
- **What our system needs most is trustworthy confidence**, because the decision gate auto-accepts anything at or above 0.8. On real data only XGBoost and Logistic Regression keep auto-accepted tags about 98% correct. Random Forest's probabilities are poorly suited: it accepts few tags, and about a quarter of those are wrong. k-NN and a single Decision Tree are clearly weaker.
- **Why we keep XGBoost:** it is top-tier on every accuracy column, its confidence is reliable, it handles missing values natively, and it explains itself through feature importance.
- **Logistic Regression is a strong, simpler runner-up.** That's a useful finding: the features carry most of the signal, not the model's complexity. Worth re-testing on a second real plant.
- **Caveats:** HAI has 79 tags, so a gap of 0.04 in accuracy is about 3 tags, which is not significant. XGBoost's settings were chosen during the project; the other models use library defaults. 'Auto-accepted' here uses confidence only; the full decision gate also sends constant and unfamiliar signals to review (51% auto-accepted for XGBoost in `hai/summary.md`).
