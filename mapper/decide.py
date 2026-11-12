"""Decision gate (LEARNER side): turn model probabilities into ACCEPT / REVIEW, with a reason.

Three checks, in order:
  1. constant signal   no behaviour evidence at all -> always REVIEW
  2. unfamiliar signal behaviour features far from anything seen in training -> REVIEW
  3. low confidence    max probability below threshold -> REVIEW
Otherwise ACCEPT.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

THRESHOLD = 0.8


class Gate:
    def __init__(self, X_beh, k=5, quantile=0.99):
        """X_beh: behaviour features of the (non-constant) training tags."""
        X = X_beh[X_beh.change_frac > 0].fillna(0)
        self.scaler = StandardScaler().fit(X)
        Z = self.scaler.transform(X)
        self.k = k
        self.nn = NearestNeighbors(n_neighbors=k + 1).fit(Z)
        d, _ = self.nn.kneighbors(Z)
        self.limit = np.quantile(d[:, 1:].mean(1), quantile)  # skip self-distance

    def novelty(self, X_beh):
        """Mean distance to the k nearest training tags, divided by the 99th-percentile training distance."""
        d, _ = self.nn.kneighbors(self.scaler.transform(X_beh.fillna(0)), n_neighbors=self.k)
        return d.mean(1) / self.limit

    def decide(self, conf, constant, novelty):
        """Arrays in, arrays out: (decision, reason). The prediction itself is never changed; the gate
        only decides whether a human must confirm it (the reviewer still sees the model's best guess)."""
        reason = np.select([constant, novelty > 1, conf < THRESHOLD],
                           ["constant signal", "unfamiliar signal", "low confidence"], "")
        return np.where(reason == "", "ACCEPT", "REVIEW"), reason
