"""Behaviour analysis (LEARNER side): raw time series -> basic, scale-invariant features.

Phase 1 uses BASIC features only. Physics features (lagged cross-correlation to run signals,
autocorrelation decay, spectral energy ratios) are deliberately left for the final phase.
"""
import numpy as np
import pandas as pd


def tag_features(x, binaries):
    """x: raw values (NaN = missing). binaries: dict name -> 0/1 series of other binary tags."""
    miss = float(np.isnan(x).mean())
    s = pd.Series(x).ffill().bfill().to_numpy()
    v = x[~np.isnan(x)]
    uniq = np.unique(v)
    d = np.diff(s)
    nz = d[d != 0]
    sd = s.std()
    span = np.percentile(v, 99) - np.percentile(v, 1) if len(v) else 0.0
    pos = nz[nz > 0]
    modal = np.bincount(np.abs(pos).astype(np.int64)).argmax() if len(pos) else 0

    # periodicity: dominant period and how much power sits in it
    z = s - s.mean()
    p = np.abs(np.fft.rfft(z)) ** 2
    p[0] = 0
    k = int(p.argmax())
    period = len(z) / k if k else len(z)

    corr = 0.0
    for b in binaries.values():
        if b.std() > 0 and sd > 0:
            corr = max(corr, abs(np.corrcoef(s, b)[0, 1]))

    return {
        "missing_frac": miss,
        "log_unique": np.log10(len(uniq) + 1),
        "is_binary": float(len(uniq) <= 2),
        "top_value_frac": float(pd.Series(v).value_counts(normalize=True).iloc[0]) if len(v) else 1.0,
        "change_frac": float((d != 0).mean()),
        "up_frac": float((nz > 0).mean()) if len(nz) else 0.5,
        "step_regularity": float((np.abs(pos) == modal).mean()) if len(pos) else 0.0,
        "big_drop_rate": float((d < -0.5 * span).sum() / len(d)) if span else 0.0,
        "roughness": float(np.std(d) / sd) if sd else 0.0,
        "cv": float(sd / (abs(s.mean()) + 1e-9)),
        "skew": float(pd.Series(v).skew()) if len(v) > 2 else 0.0,
        "kurtosis": float(pd.Series(v).kurt()) if len(v) > 3 else 0.0,
        "floor_frac": float((v <= np.percentile(v, 1) + 0.02 * span).mean()) if span else 1.0,
        "reversal_frac": float((np.diff(np.sign(nz)) != 0).mean()) if len(nz) > 1 else 0.0,
        "log_period": float(np.log10(period)),
        "peak_power_frac": float(p[k] / p.sum()) if p.sum() else 0.0,
        "corr_binary": float(corr),
    }


def machine_features(csv_path):
    return device_features(pd.read_csv(csv_path).drop(columns="timestamp"))


def device_features(df):
    """All tags of one device (one Modbus slave / PLC). Binary detection is behavioural, no labels."""
    df = df.astype(float)
    binary = {c: df[c].ffill().bfill().to_numpy() for c in df if df[c].dropna().nunique() <= 2}
    rows = []
    for c in df:
        others = {k: v for k, v in binary.items() if k != c}
        rows.append({"tag": c, **tag_features(df[c].to_numpy(), others)})
    return pd.DataFrame(rows)
