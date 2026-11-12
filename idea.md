# Slide 3: Core Problem Statement

Problem Definition:
Old factory machines send data under cryptic tag names (such as T1\_PV, M2\_RUN). Connecting them to Industry 4.0 systems requires manually mapping each tag to a standard OPC UA meaning. With hundreds of tags per machine, this process is slow, costly, and highly error-prone.

Why it Exists (Root Causes & Technical Limits):

  * Personal Shorthand: Tag names were created without shared naming standards.
  * Protocol Limits: Modbus exposes register addresses only, not names.
  * Missing Docs: Documentation is lost after years of operational use.
  * Current AI Gap: Existing automatic tools use names or behaviour alone. Time-series-only methods stay below 65% accuracy.

Context (Small Manufacturers' Reality):

  * Legacy Constraints: Small plants run legacy machines they cannot afford to replace.
  * Resource Gap: Large enterprises afford manual mapping or replacement; small ones cannot.
  * Domain Unexplored: Most prior work targets building automation (Brick schema). Very little addresses industrial machine tags to OPC UA.

Significance (Value & Contributions):

  * Efficiency: Human review is restricted to uncertain tags only, saving massive time & cost.
  * SDG 9 Inclusion: Provides small manufacturers an accessible path to Industry 4.0.
  * Research Breakthrough: Tests if hybrid signals (name + data behaviour) outperform single-method approaches in legacy manufacturing.

# Slide 10: Methodology

Overview of Methodology Steps:

1.  Data Generation:

<!-- end list -->

  * Process & Implementation Details: Simulate machines with tags of known type (temperature, run signal, pressure, motor current, counter). Add cryptic names, noise, and missing values; serve via Modbus.
  * Tools & Libraries: Python, NumPy, pandas, pymodbus

<!-- end list -->

2.  Name Analysis:

<!-- end list -->

  * Process & Implementation Details: Split names into components, expand abbreviations, and match against standard vocabulary (15–20 concepts) via sentence embeddings.
  * Tools & Libraries: Python, rapidfuzz, sentence-transformers (local model / Ollama)

<!-- end list -->

3.  Behaviour Analysis:

<!-- end list -->

  * Process & Implementation Details: Extract time-series features per tag: normalized range, rate of change, cycling, periodicity, state signal vs continuous, and cross-tag correlation.
  * Tools & Libraries: pandas, SciPy, scikit-learn

<!-- end list -->

4.  Combination & Confidence:

<!-- end list -->

  * Process & Implementation Details: Fuse lexical and behavioral scores into a unified confidence metric. Automatically accept mappings above threshold; flag low-confidence tags for review.
  * Tools & Libraries: scikit-learn, XGBoost (lightweight classifier)

<!-- end list -->

5.  Review & Publishing:

<!-- end list -->

  * Process & Implementation Details: Human verifies or corrects uncertain mappings in a simple web interface. Final confirmed model is published as an OPC UA server.
  * Tools & Libraries: FastAPI, Streamlit / React, SQLite, asyncua
