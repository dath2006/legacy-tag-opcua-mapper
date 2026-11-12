# Real-data test: HAI 23.05

Model trained only on simulated plants (866 tags); HAI is never used for training. Tested on 86 real tags; 4 h windows, probabilities averaged per tag. `train3` = new version, untouched. HAI classes: Other, Pressure, RunStatus, Temperature (no motor-current or counter tags). Site rule: strip `^P\d_`.

## Metrics

| File                            | Method                 |   Accuracy |   Target recall (17) |   Other rejected (69) |   Precision of target claims |   Auto-accepted |   Precision of auto-accepted |
|:--------------------------------|:-----------------------|-----------:|---------------------:|----------------------:|-----------------------------:|----------------:|-----------------------------:|
| train3 (new version, untouched) | Name-only (raw names)  |      0.57  |                0.529 |                 0.58  |                        0.196 |         nan     |                      nan     |
| train3 (new version, untouched) | Name-only (site rule)  |      0.64  |                0.529 |                 0.667 |                        0.529 |         nan     |                      nan     |
| train3 (new version, untouched) | Behaviour-only         |      0.674 |                0.706 |                 0.667 |                        0.343 |         nan     |                      nan     |
| train3 (new version, untouched) | Hybrid + decision gate |      0.837 |                0.882 |                 0.826 |                        0.556 |           0.512 |                        0.977 |

## train3: review reasons

| reason            |   tags |
|:------------------|-------:|
| constant signal   |     22 |
| low confidence    |     17 |
| unfamiliar signal |      3 |

## train3: auto-accepted tags

| tag                   | true        | description                                                         | name_only   | behaviour   | hybrid      |   confidence |   novelty | decision   | reason   |
|:----------------------|:------------|:--------------------------------------------------------------------|:------------|:------------|:------------|-------------:|----------:|:-----------|:---------|
| P1_FCV01D             | Other       | Position command for the FCV01 valve                                | Other       | Other       | Other       |        0.967 |      0.35 | ACCEPT     |          |
| P1_FCV01Z             | Other       | Current position of the FCV01 valve                                 | Other       | Other       | Other       |        0.939 |      0.37 | ACCEPT     |          |
| P1_FCV02D             | Other       | Position command for the FCV02 valve                                | Other       | Other       | Other       |        0.997 |      0.64 | ACCEPT     |          |
| P1_FCV02Z             | Other       | Current position of the FCV02 valve                                 | Other       | Other       | Other       |        0.996 |      0.46 | ACCEPT     |          |
| P1_FCV03D             | Other       | Position command for the FCV03 valve                                | Other       | Other       | Other       |        0.973 |      0.23 | ACCEPT     |          |
| P1_FCV03Z             | Other       | Current position of the FCV03 valve                                 | Other       | Other       | Other       |        0.962 |      0.29 | ACCEPT     |          |
| P1_FT01               | Other       | Measured flowrate of the return water tank                          | Other       | Other       | Other       |        0.851 |      0.31 | ACCEPT     |          |
| P1_FT01Z              | Other       | Water inflow rate converted from P1_FT01                            | Other       | Other       | Other       |        0.848 |      0.31 | ACCEPT     |          |
| P1_FT02               | Other       | Measured flowrate of heating water tank                             | Other       | Other       | Other       |        0.999 |      0.36 | ACCEPT     |          |
| P1_FT02Z              | Other       | Water outflow rate converted from P1_FT02                           | Other       | Other       | Other       |        0.999 |      0.34 | ACCEPT     |          |
| P1_FT03               | Other       | Measured flowrate of the return water tank                          | Other       | Other       | Other       |        0.971 |      0.31 | ACCEPT     |          |
| P1_FT03Z              | Other       | Water outflow rate converted from P1_FT03                           | Other       | Other       | Other       |        0.987 |      0.31 | ACCEPT     |          |
| P1_LCV01D             | Other       | Position command for the LCV01 valve                                | Other       | Other       | Other       |        0.983 |      0.32 | ACCEPT     |          |
| P1_LCV01Z             | Other       | Current position of the LCV01 valve                                 | Other       | Other       | Other       |        0.969 |      0.35 | ACCEPT     |          |
| P1_LIT01              | Other       | Water level of the return water tank                                | Other       | Other       | Other       |        0.941 |      0.23 | ACCEPT     |          |
| P1_PCV01D             | Other       | Position command for the PCV01 valve                                | Pressure    | Other       | Other       |        0.963 |      0.35 | ACCEPT     |          |
| P1_PCV02Z             | Other       | Current position of the PCV02 valve                                 | Pressure    | Other       | Other       |        0.98  |      0.91 | ACCEPT     |          |
| P1_PIT01              | Pressure    | Heat-exchanger outlet pressure                                      | Pressure    | Pressure    | Pressure    |        0.85  |      0.25 | ACCEPT     |          |
| P1_PIT02              | Pressure    | Water supply pressure of the heating water pump                     | Pressure    | Pressure    | Pressure    |        0.954 |      0.24 | ACCEPT     |          |
| P1_PP04               | Other       | Control out of the cooler pump                                      | Unknown     | Other       | Other       |        0.989 |      0.55 | ACCEPT     |          |
| P1_PP04D              | RunStatus   | Start command of the cooling water pump PP04                        | Unknown     | RunStatus   | RunStatus   |        0.995 |      0.34 | ACCEPT     |          |
| P1_TIT03              | Temperature | Temperature of the main water tank                                  | Temperature | Other       | Temperature |        0.838 |      0.43 | ACCEPT     |          |
| P2_24Vdc              | Other       | DCS 24V input voltage                                               | Other       | Other       | Other       |        0.993 |      0.68 | ACCEPT     |          |
| P2_SCO                | Other       | Control output value of the speed controller                        | Unknown     | Other       | Other       |        0.948 |      0.51 | ACCEPT     |          |
| P2_SCST               | Other       | Speed change proportional to frequency change of the STM            | Other       | Other       | Other       |        0.974 |      0.29 | ACCEPT     |          |
| P2_SIT01              | Other       | Current turbine RPM measured by speed probe                         | Other       | Other       | Other       |        0.965 |      0.38 | ACCEPT     |          |
| P2_VIBTR03            | Other       | Shaft vibration Y displacement (2nd, near mass wheel)               | Other       | Other       | Other       |        0.976 |      0.83 | ACCEPT     |          |
| P2_VIBTR04            | Other       | Shaft vibration X displacement (2nd, near mass wheel)               | Other       | Other       | Other       |        0.959 |      0.55 | ACCEPT     |          |
| P3_LCV01D             | Other       | Position command for the valve LCV01                                | Other       | Other       | Other       |        0.955 |      0.42 | ACCEPT     |          |
| P3_PIT01              | Pressure    | Pressure of water flowing into the upper water tank (raw 0-27648)   | Pressure    | Pressure    | Pressure    |        0.957 |      0.52 | ACCEPT     |          |
| P4_HT_FD              | Other       | Frequency deviation of HTM                                          | Unknown     | Other       | Other       |        0.818 |      0.63 | ACCEPT     |          |
| P4_LD                 | Other       | Total electrical load demand                                        | Unknown     | Other       | Other       |        0.822 |      0.26 | ACCEPT     |          |
| P4_ST_FD              | Other       | Frequency deviation of STM                                          | Other       | Other       | Other       |        0.946 |      0.54 | ACCEPT     |          |
| P4_ST_LD              | Other       | Electrical load demand of STM                                       | Other       | Other       | Other       |        0.865 |      0.24 | ACCEPT     |          |
| P4_ST_PO              | Other       | Output power of STM                                                 | Other       | Other       | Other       |        0.886 |      0.3  | ACCEPT     |          |
| P4_ST_PT01            | Pressure    | Digital value of steam pressure of STM (raw 0-27648)                | Pressure    | Other       | Other       |        0.828 |      0.36 | ACCEPT     |          |
| P4_ST_TT01            | Temperature | Digital value of steam temperature of STM (raw 0-27648)             | Temperature | Other       | Temperature |        0.918 |      0.37 | ACCEPT     |          |
| x1001_05_SETPOINT_OUT | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.959 |      0.53 | ACCEPT     |          |
| x1001_15_ASSIGN_OUT   | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.971 |      0.25 | ACCEPT     |          |
| x1002_07_SETPOINT_OUT | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.96  |      0.59 | ACCEPT     |          |
| x1002_08_SETPOINT_OUT | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.972 |      0.55 | ACCEPT     |          |
| x1003_10_SETPOINT_OUT | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.999 |      0.34 | ACCEPT     |          |
| x1003_18_SETPOINT_OUT | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.961 |      0.88 | ACCEPT     |          |
| x1003_24_SUM_OUT      | Other       | Boiler DCS internal function-block output (manual: 'Output of ...') | Other       | Other       | Other       |        0.985 |      0.26 | ACCEPT     |          |

## train3: target tags

| tag        | true        | description                                                       | name_only   | behaviour   | hybrid      |   confidence |   novelty | decision   | reason          |
|:-----------|:------------|:------------------------------------------------------------------|:------------|:------------|:------------|-------------:|----------:|:-----------|:----------------|
| P1_PIT01   | Pressure    | Heat-exchanger outlet pressure                                    | Pressure    | Pressure    | Pressure    |        0.85  |      0.25 | ACCEPT     |                 |
| P1_PIT02   | Pressure    | Water supply pressure of the heating water pump                   | Pressure    | Pressure    | Pressure    |        0.954 |      0.24 | ACCEPT     |                 |
| P1_PP01AD  | RunStatus   | Start command of the main water pump PP01A                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01AR  | RunStatus   | Running state of the main water pump PP01A                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01BD  | RunStatus   | Start command of the main water pump PP01B                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01BR  | RunStatus   | Running state of the main water pump PP01B                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP02D   | RunStatus   | Start command of the heating water pump PP02                      | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP02R   | RunStatus   | Running state of the heating water pump PP02                      | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP04D   | RunStatus   | Start command of the cooling water pump PP04                      | Unknown     | RunStatus   | RunStatus   |        0.995 |      0.34 | ACCEPT     |                 |
| P1_STSP    | RunStatus   | Start/stop command of the boiler DCS                              | RunStatus   | RunStatus   | RunStatus   |        0.948 |      0.82 | REVIEW     | constant signal |
| P1_TIT01   | Temperature | Heat-exchanger outlet temperature                                 | Temperature | Other       | Temperature |        0.752 |      0.38 | REVIEW     | low confidence  |
| P1_TIT02   | Temperature | Temperature of the heating water tank                             | Temperature | Other       | Other       |        0.521 |      0.35 | REVIEW     | low confidence  |
| P1_TIT03   | Temperature | Temperature of the main water tank                                | Temperature | Other       | Temperature |        0.838 |      0.43 | ACCEPT     |                 |
| P2_OnOff   | RunStatus   | On/off switch of the turbine DCS                                  | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P3_PIT01   | Pressure    | Pressure of water flowing into the upper water tank (raw 0-27648) | Pressure    | Pressure    | Pressure    |        0.957 |      0.52 | ACCEPT     |                 |
| P4_ST_PT01 | Pressure    | Digital value of steam pressure of STM (raw 0-27648)              | Pressure    | Other       | Other       |        0.828 |      0.36 | ACCEPT     |                 |
| P4_ST_TT01 | Temperature | Digital value of steam temperature of STM (raw 0-27648)           | Temperature | Other       | Temperature |        0.918 |      0.37 | ACCEPT     |                 |

Per-tag tables: `hai_predictions_train3.csv`. Figures: `hai_confusion.png`, `hai_gate.png`.
