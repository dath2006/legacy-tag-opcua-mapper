"""Legacy plant simulator (GENERATOR side).

Writes ONLY:
  data/<plant>/raw/<machine>.csv   timestamp + raw register values under cryptic tag names
  data/<plant>/labels.csv          ground truth (machine, tag, concept, ...) - training/eval only

The learner (mapper/) must never import this file; it only reads those CSVs.

Realism ingredients (docs/phase1_plan.md, Part C): FOPDT dynamics, PI and on/off temperature
loops, run schedules with micro-stops and breaks, pump / compressor / hydraulic pressure,
inrush and VFD motor current, cycle counters with rollover and reset, AR(1) coloured noise,
drift, spikes, stuck sensors, historian deadband, ADC / register scaling, dropouts, comm loss,
ISA / shorthand / opaque naming, and a few repurposed (misleading) tag names.

Usage:  python generator/simulate.py --plant plant_a --machines 40 --seed 1
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import lfilter

DT = 1.0  # s, Modbus poll interval
ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- signal primitives
def ar1(n, rng, sigma, tau):
    """Coloured noise: std `sigma`, correlation time `tau` seconds."""
    phi = np.exp(-DT / max(tau, DT))
    return lfilter([sigma * np.sqrt(1 - phi**2)], [1, -phi], rng.standard_normal(n))


def fopdt(u, K, tau, dead=0.0):
    """First-order-plus-dead-time response to input u, starting at steady state."""
    u = np.asarray(u, float)
    d = int(round(dead / DT))
    if d:
        u = np.concatenate([np.full(d, u[0]), u[:-d]])
    a = np.exp(-DT / tau)
    y, _ = lfilter([K * (1 - a)], [1, -a], u, zi=[K * u[0] * a])
    return y


def schedule(n, rng, run=(5, 45), stop=(1, 12), p_on=0.75):
    """Boolean run state: production runs, micro-stops, optional planned break."""
    s = np.zeros(n, bool)
    t, on = 0, rng.random() < p_on
    while t < n:
        lo, hi = run if on else stop
        L = int(rng.uniform(lo, hi) * 60)
        s[t:t + L] = on
        t += L
        on = not on
    if rng.random() < 0.5:  # lunch / shift break
        b = rng.integers(0, max(1, n - 2700))
        s[b:b + int(rng.uniform(20, 45) * 60)] = False
    return s


def since_start(run):
    """Seconds since the most recent off->on transition (large while off)."""
    idx = np.arange(len(run))
    starts = run & ~np.concatenate([[False], run[:-1]])
    last = np.maximum.accumulate(np.where(starts, idx, 0))
    return (idx - last) * DT


def cycles(run, rng, ct_range):
    """Machine cycles that advance only while running. Returns (cycle_index, phase 0..1)."""
    runtime = np.cumsum(run) * DT
    ct = rng.uniform(*ct_range)
    n_cyc = int(runtime[-1] / (ct * 0.8)) + 2
    bounds = np.concatenate([[0], np.cumsum(ct * np.clip(1 + 0.1 * rng.standard_normal(n_cyc), 0.6, 1.5))])
    idx = np.searchsorted(bounds, runtime, side="right") - 1
    phase = (runtime - bounds[idx]) / (bounds[idx + 1] - bounds[idx])
    return idx, phase


# ---------------------------------------------------------------- physical components
def motor_current(run, rng, load=None, vfd=None):
    n = len(run)
    rated = rng.uniform(5, 120)
    if load is None:
        load = np.clip(rng.uniform(0.5, 0.9) + ar1(n, rng, 0.06, rng.uniform(20, 200)), 0.2, 1.1)
    vfd = rng.random() < 0.4 if vfd is None else vfd
    if vfd:  # soft ramp, no inrush
        I = rated * load * fopdt(run, 1, rng.uniform(3, 10))
    else:  # direct-on-line: inrush 4-7x decaying in ~1 s
        k, tau_i = rng.uniform(4, 7), rng.uniform(0.5, 2)
        I = rated * load * run * (1 + (k - 1) * np.exp(-since_start(run) / tau_i))
    I = I + rng.uniform(0, 0.02) * rated  # CT offset when idle
    return I, (0, rated * 1.5)  # CT range clips inrush - realistic


def heater_zone(run, rng, amb):
    """Temperature zone under PI or on/off (thermostat) control, with dead time and load dips."""
    n = len(run)
    sp = np.full(n, rng.uniform(60, 250))
    for _ in range(rng.integers(0, 3)):  # operator setpoint changes
        sp[rng.integers(0, n):] += rng.uniform(-30, 30)
    enabled = run if rng.random() < 0.5 else np.ones(n, bool)
    tau, dead = rng.uniform(200, 1500), rng.uniform(5, 60)
    K = (sp.max() - amb.mean()) * rng.uniform(1.3, 2.0)
    onoff, hyst = rng.random() < 0.4, rng.uniform(1, 5)
    kp, ti = tau / (K * (rng.uniform(0.5, 1.5) * tau + dead)), tau
    load_dip = rng.uniform(0, 0.1) * K  # cold material entering while producing
    d = int(dead / DT)
    ubuf = np.zeros(n + d)  # controller output, delayed by dead time
    T = sp[0] if rng.random() < 0.6 else amb[0]
    out, integ, u = np.empty(n), 0.0, 0.0
    for t in range(n):
        target = sp[t] if enabled[t] else amb[t]
        e = target - T
        if not enabled[t]:
            u = 0.0
        elif onoff:
            u = 1.0 if T < target - hyst else 0.0 if T > target + hyst else u
        else:
            integ = np.clip(integ + e * DT / ti, -1 / kp, 1 / kp)  # anti-windup
            u = float(np.clip(kp * (e + integ), 0, 1))
        ubuf[t + d] = u
        T += DT / tau * (K * ubuf[t] - (T - amb[t]) - load_dip * run[t])
        out[t] = T
    return out, (0, float(rng.choice([200, 300, 400, 600]))), sp, ubuf[d:d + n]


def pump_pressure(run, rng):
    n = len(run)
    p_on = rng.uniform(2, 8)
    p_off = rng.uniform(0, 0.1) * p_on
    demand = 1 + ar1(n, rng, 0.04, rng.uniform(30, 150))
    p = fopdt(p_off + (p_on - p_off) * run * demand, 1, rng.uniform(0.5, 4), rng.uniform(0, 1))
    t = np.arange(n) * DT
    p += run * rng.uniform(0.005, 0.02) * p_on * np.sin(2 * np.pi * rng.uniform(0.05, 0.45) * t)  # aliased pulsation
    return p, (0, float(rng.choice([10, 16, 25])))


def receiver_pressure(run, rng):
    """Compressor receiver: load/unload sawtooth between cut-in and cut-out. Returns (p, loaded)."""
    n = len(run)
    lo = rng.uniform(5.5, 7)
    hi = lo + rng.uniform(0.7, 1.5)
    fill = rng.uniform(0.01, 0.05)
    use = np.abs(rng.uniform(0.3, 0.8) * fill * (1 + ar1(n, rng, 0.3, 120)))
    p, loaded = rng.uniform(lo, hi), True
    P, L = np.empty(n), np.zeros(n, bool)
    for t in range(n):
        if run[t]:
            if loaded:
                p += fill - use[t]
                loaded = p < hi
            else:
                p -= use[t]
                loaded = p <= lo
        else:
            p = max(p - 0.3 * use[t], 0.0)
        P[t], L[t] = p, loaded and run[t]
    return P, L, (0, 16)


def press_pressure(phase, run, rng):
    """Hydraulic press: pressure pulse during each stroke."""
    duty = rng.uniform(0.2, 0.5)
    base, peak = rng.uniform(5, 20), rng.uniform(100, 200)
    stroke = (phase < duty) & run
    return base + (peak - base) * fopdt(stroke, 1, rng.uniform(0.3, 1.5)), (0, 250)


def counter(cyc_idx, rng):
    """Part counter: offset, parts/cycle, optional shift reset, 16-bit rollover."""
    v = rng.integers(0, 65536) + rng.integers(1, 5) * cyc_idx
    if rng.random() < 0.3:
        r = rng.integers(0, len(v))
        v[r:] -= v[r]
    return v % (65536 if rng.random() < 0.5 else 32768)


def ambient(n, rng):
    return rng.uniform(24, 34) + np.linspace(0, rng.uniform(-2, 2), n) + ar1(n, rng, 0.3, 600)


# ---------------------------------------------------------------- imperfections
NOISE = {"Temperature": (0.0005, 0.003), "Pressure": (0.002, 0.01), "MotorCurrent": (0.003, 0.015),
         "Flow": (0.003, 0.015), "Level": (0.001, 0.005), "Speed": (0.001, 0.005)}  # x span
TARGETS = {"Temperature", "Pressure", "RunStatus", "MotorCurrent", "Counter"}  # everything else -> "Other"


def degrade(x, rng, lo, hi, noise):
    """Sensor noise, drift, spikes, stuck sensor, historian deadband."""
    n, span = len(x), hi - lo
    x = x + ar1(n, rng, span * rng.uniform(*noise), rng.uniform(1, 10))
    if rng.random() < 0.2:
        x += np.linspace(0, span * rng.uniform(-0.03, 0.03), n)
    if rng.random() < 0.3:
        for i in rng.integers(0, n, rng.poisson(3)):
            x[i] += span * rng.uniform(0.1, 0.5) * rng.choice([-1, 1])
    if rng.random() < 0.1:
        s = rng.integers(0, n)
        x[s:s + int(rng.uniform(5, 30) * 60)] = x[s]
    if rng.random() < 0.3:  # report-by-exception deadband
        db, last = span * rng.uniform(0.002, 0.01), x[0]
        for i in range(n):
            if abs(x[i] - last) > db:
                last = x[i]
            x[i] = last
    return x


def encode(x, rng, lo, hi):
    """Engineering value -> raw register: either eng*scale (int16) or raw ADC counts."""
    if rng.random() < 0.4:
        full = float(rng.choice([4095, 27648, 32767]))  # 12-bit, Siemens S7, 15-bit
        return np.round(np.clip((x - lo) / (hi - lo) * full, -0.02 * full, 1.18 * full))
    scales = [s for s in (1, 10, 100) if 1000 <= hi * s < 32767] or [10]  # keep >=1000 counts
    return np.clip(np.round(x * rng.choice(scales)), -32768, 32767)


# ---------------------------------------------------------------- machines
def build_machine(kind, n, rng):
    """Returns list of channels: (subtype, values, lo, hi, signal_type).
    signal_type: analog (noisy sensor) | exact (computed value, e.g. setpoint) | binary | counter."""
    run, amb, ch = schedule(n, rng), ambient(n, rng), []

    def analog(concept, x_rng):
        x, (lo, hi) = x_rng
        ch.append((concept, x, lo, hi, "analog"))

    def motor(run_sig, load=None):
        I, rng_ = motor_current(run_sig, rng, load)
        ch.append(("RunStatus", run_sig.astype(float), 0, 1, "binary"))
        ch.append(("MotorCurrent", I, *rng_, "analog"))
        if rng.random() < 0.3:  # VFD speed feedback: follows run like current does
            rpm = rng.choice([1450, 2900, 960])
            analog("Speed", (rpm * fopdt(run_sig, 1, rng.uniform(2, 10)), (0, rpm * 1.2)))
        return I, rng_[1] / 1.5

    def zone():
        T, trng, sp, u = heater_zone(run, rng, amb)
        analog("Temperature", (T, trng))
        if rng.random() < 0.5:
            ch.append(("Setpoint", sp, *trng, "exact"))
        if rng.random() < 0.4:
            ch.append(("CtrlOutput", 100 * u, 0, 100, "exact"))

    if kind == "molder":
        for _ in range(rng.integers(1, 4)):
            zone()
        cyc, phase = cycles(run, rng, (8, 40))
        load = 0.4 + 0.5 * ((phase < 0.4) & run)
        motor(run, load)
        analog("Pressure", press_pressure(phase, run, rng))
        ch.append(("Counter", counter(cyc, rng), 0, 65535, "counter"))
    elif kind == "pump_station":
        for _ in range(rng.integers(1, 3)):
            r = schedule(n, rng, run=(10, 60), stop=(2, 20))
            I, rated = motor(r)
            analog("Pressure", pump_pressure(r, rng))
            if rng.random() < 0.4:
                analog("Temperature", (amb + fopdt((I / rated) ** 2, rng.uniform(15, 45), rng.uniform(600, 2400)), (0, 200)))
            if rng.random() < 0.6:  # flow: same on/off shape as pressure
                q = rng.uniform(20, 300)
                analog("Flow", (fopdt(q * r * (1 + ar1(n, rng, 0.05, 60)), 1, rng.uniform(1, 5)), (0, q * 1.5)))
            if rng.random() < 0.4:  # tank level: slow integrator, looks like temperature
                qout = rng.uniform(0.0005, 0.002)
                qin = qout * r.mean() * rng.uniform(0.9, 1.1)
                L = np.clip(rng.uniform(0.3, 0.7) + np.cumsum(qin * (1 + ar1(n, rng, 0.2, 300)) - qout * r), 0.05, 0.98)
                analog("Level", (100 * L, (0, 100)))
    elif kind == "compressor":
        p, loaded, prng = receiver_pressure(run, rng)
        motor(run, np.where(loaded, rng.uniform(0.8, 1.0), rng.uniform(0.3, 0.45)))
        analog("Pressure", (p, prng))
        analog("Temperature", (amb + fopdt(loaded, rng.uniform(40, 70), rng.uniform(60, 300)), (0, 200)))
    elif kind == "conveyor":
        cyc, _ = cycles(run, rng, (3, 20))
        I, rated = motor(run)
        ch.append(("Counter", counter(cyc, rng), 0, 65535, "counter"))
        if rng.random() < 0.6:
            analog("Temperature", (amb + fopdt((I / rated) ** 2, rng.uniform(15, 45), rng.uniform(600, 2400)), (0, 150)))
    elif kind == "oven":
        for _ in range(rng.integers(1, 4)):
            zone()
        motor(run)  # circulation fan
        if rng.random() < 0.5:
            cyc, _ = cycles(run, rng, (600, 1800))  # batch / tray counter: rarely moves
            ch.append(("Counter", counter(cyc, rng), 0, 65535, "counter"))
        if rng.random() < 0.5:  # plant air supply: not tied to machine run
            dips = fopdt(16.0 * (rng.random(n) < 0.003), 1, 20)  # ~0.8 bar dips when others draw air
            analog("Pressure", (rng.uniform(5.5, 7) + ar1(n, rng, 0.15, 60) - dips, (0, 10)))
    if rng.random() < 0.5:  # alarm / fault bit: binary like a run signal, but rare
        a = np.zeros(n, bool)
        for s in rng.integers(0, n, rng.poisson(2)):
            a[s:s + int(rng.uniform(10, 300))] = True
        ch.append(("Alarm", a.astype(float), 0, 1, "binary"))
    return ch


# ---------------------------------------------------------------- naming
POOLS = {
    "isa": {
        "Temperature": ["TT{n}", "TI{n}", "TIC{n}_PV", "TE{n}", "TT-{n}", "TIT{n}"],
        "Pressure": ["PT{n}", "PI{n}", "PIT{n}", "PIC{n}_PV", "PT-{n}"],
        "RunStatus": ["YS{n}", "M{n}_RUN", "MTR{n}_RUN_FB", "P{n}_RUN", "XS{n}"],
        "MotorCurrent": ["IT{n}", "II{n}", "M{n}_AMPS", "IIT{n}"],
        "Counter": ["QI{n}", "QT{n}", "QQI{n}", "CNT{n}"],
        "Flow": ["FT{n}", "FIT{n}", "FI{n}", "FIC{n}_PV"],
        "Level": ["LT{n}", "LIT{n}", "LI{n}", "LIC{n}_PV"],
        "Speed": ["ST{n}", "SI{n}", "SIC{n}_PV", "M{n}_RPM"],
        "Setpoint": ["TIC{n}_SP", "TC{n}_SP", "TIC{n}.SP"],
        "CtrlOutput": ["TY{n}", "TIC{n}_OUT", "TIC{n}_CV", "TV{n}"],
        "Alarm": ["XA{n}", "TAH{n}", "PAL{n}", "M{n}_FLT", "YA{n}"],
    },
    "shorthand": {
        "Temperature": ["T{n}", "TEMP{n}", "TMP_Z{n}", "OVEN_T{n}", "BRG_TMP{n}", "T{n}_PV", "ZONE{n}_DEGC", "THM{n}", "MOT_TEMP{n}", "TEMPR{n}"],
        "Pressure": ["P{n}", "PRES{n}", "PRS_HYD{n}", "BAR{n}", "DISCH_P{n}", "P{n}_PV", "HYD_PSI{n}", "AIR_KPA{n}", "PR{n}", "PRESR{n}"],
        "RunStatus": ["M{n}_RUN", "RUN{n}", "MTR_ON{n}", "PUMP{n}_STS", "FAN_ON{n}", "RUNNING{n}", "ON_OFF{n}"],
        "MotorCurrent": ["AMP{n}", "M{n}_I", "CUR{n}", "MTR_AMPS{n}", "LOAD_A{n}", "I{n}", "CURNT{n}"],
        "Counter": ["CNT{n}", "CTR{n}", "PART_CNT{n}", "PCS{n}", "QTY{n}", "CYC_CNT{n}", "SHOTS{n}", "GOOD_PCS{n}"],
        "Flow": ["FLOW{n}", "FLW{n}", "Q{n}", "LPM{n}", "M3H{n}", "F{n}"],
        "Level": ["LVL{n}", "LEVEL{n}", "TANK_L{n}", "L{n}", "TNK_LVL{n}"],
        "Speed": ["RPM{n}", "SPD{n}", "SPEED{n}", "M{n}_HZ", "N{n}"],
        "Setpoint": ["SP{n}", "T{n}_SP", "SET_T{n}", "TEMP_SET{n}", "SETPT{n}"],
        "CtrlOutput": ["HTR_OUT{n}", "OUT{n}", "HEAT_PCT{n}", "CV{n}", "MV{n}"],
        "Alarm": ["ALM{n}", "FAULT{n}", "TRIP{n}", "FLT{n}", "M{n}_ALM", "ERR{n}"],
    },
}
STOP_NAMES = {"isa": ["YS{n}_STP", "M{n}_STOP"], "shorthand": ["M{n}_STOP", "STOPPED{n}", "STOP{n}"]}
OPAQUE_ANALOG = ["HR4{a:04d}", "IR3{a:04d}", "N7:{k}", "%MW{w}", "AI_{k:02d}", "TAG{k:03d}", "REG{a}"]
OPAQUE_BINARY = ["C{a:05d}", "%IX0.{b}", "DI_{k:02d}", "B3:0/{k}"]


def name_tags(channels, style, rng, m_idx):
    """Assign cryptic names; returns (names, inverted_flags, misleading_flags)."""
    names, inv, mis, used = [], [], [], set()
    fa, fb = rng.choice(OPAQUE_ANALOG), rng.choice(OPAQUE_BINARY)  # one PLC dialect per machine
    for i, (concept, *_rest, sig) in enumerate(channels):
        k, a = i + 1, int(rng.integers(1, 9000))
        inverted = concept == "RunStatus" and rng.random() < 0.1
        misleading = False
        if style == "opaque":
            tpl = fb if sig == "binary" and rng.random() < 0.7 else fa
        elif inverted:
            tpl = rng.choice(STOP_NAMES[style])
        else:
            src = concept
            if rng.random() < 0.05:  # repurposed tag: name says something else
                src = rng.choice([c for c in POOLS[style] if c != concept])
                misleading = True
            tpl = rng.choice(POOLS[style][src])
        num = 100 * (m_idx % 9 + 1) + k if style == "isa" else k
        name = tpl.format(n=num, a=a, k=k, w=2 * a, b=k % 8)
        while name in used:
            name += "_" + str(rng.integers(1, 9))
        used.add(name)
        names.append(name)
        inv.append(inverted)
        mis.append(misleading)
    return names, inv, mis


# ---------------------------------------------------------------- plant
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plant", default="plant_a")
    ap.add_argument("--machines", type=int, default=40)
    ap.add_argument("--hours", type=float, default=4)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    n = int(args.hours * 3600 / DT)
    out = ROOT / "data" / args.plant
    (out / "raw").mkdir(parents=True, exist_ok=True)
    ts = pd.date_range("2026-01-05 06:00", periods=n, freq=f"{int(DT)}s") + pd.Timedelta(days=args.seed)

    kinds = ["molder", "pump_station", "compressor", "conveyor", "oven"]
    labels = []
    for m in range(args.machines):
        mid = f"M{m + 1:02d}"
        kind = rng.choice(kinds)
        style = rng.choice(["isa", "shorthand", "opaque"], p=[0.35, 0.4, 0.25])
        chans = build_machine(kind, n, rng)
        names, inv, mis = name_tags(chans, style, rng, m)
        cols = {}
        for (sub, x, lo, hi, sig), name, iv, ms in zip(chans, names, inv, mis):
            if sig == "analog":
                v = encode(degrade(x.copy(), rng, lo, hi, NOISE[sub]), rng, lo, hi)
            elif sig == "exact":
                v = encode(x.copy(), rng, lo, hi)
            elif sig == "binary":
                v = (1 - x) if iv else x.copy()
            else:
                v = x.astype(float)
            v[rng.random(n) < rng.uniform(0, 0.03)] = np.nan  # per-tag dropouts
            cols[name] = v
            labels.append(dict(machine=mid, tag=name, concept=sub if sub in TARGETS else "Other",
                               subtype=sub, style=style,
                               archetype=kind, inverted=iv, misleading=ms))
        df = pd.DataFrame(cols)
        for _ in range(rng.integers(0, 4)):  # comm loss: whole device silent
            s = rng.integers(0, n)
            df.iloc[s:s + int(rng.uniform(30, 600))] = np.nan
        df = df.astype("Int64")
        df.insert(0, "timestamp", ts)
        df.to_csv(out / "raw" / f"{mid}.csv", index=False)
    pd.DataFrame(labels).to_csv(out / "labels.csv", index=False)
    lab = pd.DataFrame(labels)
    print(f"{args.plant}: {args.machines} machines, {len(lab)} tags, {n} samples/tag")
    print(lab.subtype.value_counts().to_string())


if __name__ == "__main__":
    main()
