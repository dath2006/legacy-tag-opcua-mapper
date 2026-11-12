"""Name analysis (LEARNER side): tag name -> one score per concept.

Knowledge sources (written independently of the generator):
  * ISA-5.1 instrument letters: first letter = measured variable (T, P, I=current, Q=quantity,
    Y=event/state), succeeding letters = function (T transmitter, I indicator, C controller, ...).
  * Common engineering abbreviations, matched exactly or fuzzily (rapidfuzz) for typos.
"""
import re

from rapidfuzz import fuzz, process

CONCEPTS = ["Counter", "MotorCurrent", "Other", "Pressure", "RunStatus", "Temperature"]

VOCAB = {
    # known engineering quantities that are NOT in our target vocabulary -> "Other"
    "Other": ["FLOW", "FLW", "LEVEL", "LVL", "SPEED", "SPD", "RPM", "HZ", "SP", "SET", "SETPT", "SETPOINT",
              "OUT", "OUTPUT", "PCT", "CV", "MV", "ALM", "ALARM", "FAULT", "FLT", "TRIP", "ERR"],
    "Temperature": ["TEMP", "TMP", "TEMPERATURE", "DEGC", "DEGF", "THERMO", "TC", "RTD", "HEAT"],
    "Pressure": ["PRESSURE", "PRES", "PRESS", "PRS", "PSI", "BAR", "KPA", "MPA"],
    "RunStatus": ["RUN", "RUNNING", "ON", "STS", "STATUS", "STATE", "STOP", "STOPPED", "FB", "ACTIVE", "START"],
    "MotorCurrent": ["AMP", "AMPS", "AMPERE", "CUR", "CURR", "CURRENT"],
    "Counter": ["CNT", "COUNT", "COUNTER", "CTR", "QTY", "QUANTITY", "TOT", "TOTAL", "PCS", "PARTS", "CYC", "CYCLE", "CYCLES"],
}
TERMS = {t: c for c, ts in VOCAB.items() for t in ts}
ISA_FIRST = {"T": "Temperature", "P": "Pressure", "I": "MotorCurrent", "Q": "Counter", "Y": "RunStatus",
             "F": "Other", "L": "Other", "S": "Other"}  # F flow, L level, S speed
ISA_SUCC = set("TICERSQVYAHL")  # transmitter, indicator, controller, element, ..., alarm, high, low


def tokens(name):
    """'TIC101_PV' -> [('TIC', True), ('PV', False)]; bool = token directly followed by digits."""
    parts = re.findall(r"[A-Z]+|\d+", name.upper())
    return [(p, i + 1 < len(parts) and parts[i + 1].isdigit()) for i, p in enumerate(parts) if p.isalpha()]


def name_scores(name):
    s = dict.fromkeys(CONCEPTS, 0.0)

    def bump(c, v):
        s[c] = max(s[c], v)

    for tok, before_digit in tokens(name):
        if tok in TERMS:
            bump(TERMS[tok], 1.0)
        elif len(tok) >= 3:  # fuzzy only for longer tokens; short ones are too ambiguous
            term, score, _ = process.extractOne(tok, TERMS.keys(), scorer=fuzz.ratio)
            if score >= 75:
                bump(TERMS[term], score / 100)
        if tok[0] in ISA_FIRST and len(tok) <= 4 and set(tok[1:]) <= ISA_SUCC:
            bump(ISA_FIRST[tok[0]], 0.7 if len(tok) == 1 else 0.9 if before_digit else 0.6)
    return s


def name_rule(name, min_score=0.5):
    """Name-only baseline: best concept, or 'Unknown' when the name carries no evidence."""
    s = name_scores(name)
    best = max(s, key=s.get)
    return best if s[best] >= min_score else "Unknown"
