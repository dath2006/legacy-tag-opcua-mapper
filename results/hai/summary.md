# Real-data test: HAI 21.03

Model trained only on simulated plants (866 tags). Tested on 79 real tags; 4 h windows, probabilities averaged per tag. `train1` was used to diagnose failures; `train2` is a fresh 60 h period never looked at while fixing. HAI classes: Other, Pressure, RunStatus, Temperature (no motor-current or counter tags). Site rule: strip `^P\d_`.

## Metrics

| File               | Method                 |   Accuracy |   Target recall (15) |   Other rejected (64) |   Precision of target claims |   Auto-accepted |   Precision of auto-accepted |
|:-------------------|:-----------------------|-----------:|---------------------:|----------------------:|-----------------------------:|----------------:|-----------------------------:|
| train1 (diagnosis) | Name-only (raw names)  |      0.481 |                0.533 |                 0.469 |                        0.163 |         nan     |                      nan     |
| train1 (diagnosis) | Name-only (site rule)  |      0.57  |                0.533 |                 0.578 |                        0.615 |         nan     |                      nan     |
| train1 (diagnosis) | Behaviour-only         |      0.671 |                0.6   |                 0.688 |                        0.31  |         nan     |                      nan     |
| train1 (diagnosis) | Hybrid + decision gate |      0.835 |                0.933 |                 0.812 |                        0.538 |           0.519 |                        0.976 |
| train2 (fresh)     | Name-only (raw names)  |      0.481 |                0.533 |                 0.469 |                        0.163 |         nan     |                      nan     |
| train2 (fresh)     | Name-only (site rule)  |      0.57  |                0.533 |                 0.578 |                        0.615 |         nan     |                      nan     |
| train2 (fresh)     | Behaviour-only         |      0.684 |                0.667 |                 0.688 |                        0.333 |         nan     |                      nan     |
| train2 (fresh)     | Hybrid + decision gate |      0.81  |                0.8   |                 0.812 |                        0.5   |           0.506 |                        0.975 |

## train2 (fresh): review reasons

| reason          |   tags |
|:----------------|-------:|
| constant signal |     22 |
| low confidence  |     17 |

## train2 (fresh): auto-accepted tags

| tag        | true        | description                                                       | name_only   | behaviour   | hybrid      |   confidence |   novelty | decision   | reason   |
|:-----------|:------------|:------------------------------------------------------------------|:------------|:------------|:------------|-------------:|----------:|:-----------|:---------|
| P1_B2016   | Other       | Pressure demand for thermal power output control                  | Unknown     | Other       | Other       |        0.814 |      0.27 | ACCEPT     |          |
| P1_B3005   | Other       | Discharge flowrate setpoint (return water tank)                   | Unknown     | Other       | Other       |        0.803 |      0.88 | ACCEPT     |          |
| P1_B4005   | Other       | Temperature PID control output                                    | Unknown     | Other       | Other       |        0.984 |      0.64 | ACCEPT     |          |
| P1_B400B   | Other       | Water outflow rate setpoint (heating water tank)                  | Unknown     | Other       | Other       |        0.951 |      0.72 | ACCEPT     |          |
| P1_B4022   | Other       | Temperature demand for thermal power output control               | Unknown     | Other       | Other       |        0.926 |      0.25 | ACCEPT     |          |
| P1_FCV01D  | Other       | Position command for the FCV01 valve                              | Other       | Other       | Other       |        0.899 |      0.82 | ACCEPT     |          |
| P1_FCV01Z  | Other       | Current position of the FCV01 valve                               | Other       | Other       | Other       |        0.97  |      0.59 | ACCEPT     |          |
| P1_FCV02D  | Other       | Position command for the FCV02 valve                              | Other       | Other       | Other       |        0.9   |      0.82 | ACCEPT     |          |
| P1_FCV02Z  | Other       | Current position of the FCV02 valve                               | Other       | Other       | Other       |        0.988 |      0.64 | ACCEPT     |          |
| P1_FCV03D  | Other       | Position command for the FCV03 valve                              | Other       | Other       | Other       |        0.989 |      0.27 | ACCEPT     |          |
| P1_FCV03Z  | Other       | Current position of the FCV03 valve                               | Other       | Other       | Other       |        0.986 |      0.34 | ACCEPT     |          |
| P1_FT01    | Other       | Measured flowrate of the return water tank                        | Other       | Other       | Other       |        0.873 |      0.27 | ACCEPT     |          |
| P1_FT01Z   | Other       | Water inflow rate converted from P1_FT01                          | Other       | Other       | Other       |        0.951 |      0.29 | ACCEPT     |          |
| P1_FT02    | Other       | Measured flowrate of heating water tank                           | Other       | Other       | Other       |        0.988 |      0.72 | ACCEPT     |          |
| P1_FT02Z   | Other       | Water outflow rate converted from P1_FT02                         | Other       | Other       | Other       |        0.987 |      0.72 | ACCEPT     |          |
| P1_FT03    | Other       | Measured flowrate of the return water tank                        | Other       | Other       | Other       |        0.983 |      0.33 | ACCEPT     |          |
| P1_FT03Z   | Other       | Water outflow rate converted from P1_FT03                         | Other       | Other       | Other       |        0.988 |      0.33 | ACCEPT     |          |
| P1_LCV01D  | Other       | Position command for the LCV01 valve                              | Other       | Other       | Other       |        0.953 |      0.26 | ACCEPT     |          |
| P1_LCV01Z  | Other       | Current position of the LCV01 valve                               | Other       | Other       | Other       |        0.912 |      0.29 | ACCEPT     |          |
| P1_LIT01   | Other       | Water level of the return water tank                              | Other       | Other       | Other       |        0.914 |      0.3  | ACCEPT     |          |
| P1_PCV01D  | Other       | Position command for the PCV01 valve                              | Pressure    | Other       | Other       |        0.911 |      0.34 | ACCEPT     |          |
| P1_PCV02Z  | Other       | Current position of the PCV02 valve                               | Pressure    | Other       | Other       |        0.972 |      0.92 | ACCEPT     |          |
| P1_PIT01   | Pressure    | Heat-exchanger outlet pressure                                    | Pressure    | Pressure    | Pressure    |        0.846 |      0.23 | ACCEPT     |          |
| P1_TIT02   | Temperature | Temperature of the heating water tank                             | Temperature | Other       | Temperature |        0.83  |      0.33 | ACCEPT     |          |
| P2_24Vdc   | Other       | DCS 24V input voltage                                             | Other       | Other       | Other       |        0.99  |      0.81 | ACCEPT     |          |
| P2_CO_rpm  | Other       | Speed controller output (not in manual table; inferred from name) | Other       | Other       | Other       |        0.986 |      0.44 | ACCEPT     |          |
| P2_HILout  | Other       | HIL simulator output (not in manual table; inferred from name)    | Unknown     | Other       | Other       |        0.913 |      0.65 | ACCEPT     |          |
| P2_SIT01   | Other       | Current turbine RPM measured by speed probe                       | Other       | Other       | Other       |        0.996 |      0.34 | ACCEPT     |          |
| P2_SIT02   | Other       | Turbine RPM (second speed probe)                                  | Other       | Other       | Other       |        0.999 |      0.33 | ACCEPT     |          |
| P2_VXT03   | Other       | Shaft vibration X displacement                                    | Unknown     | Other       | Other       |        0.873 |      0.34 | ACCEPT     |          |
| P2_VYT02   | Other       | Shaft vibration Y displacement                                    | Other       | Other       | Other       |        0.913 |      0.4  | ACCEPT     |          |
| P2_VYT03   | Other       | Shaft vibration Y displacement                                    | Other       | Other       | Other       |        0.978 |      0.36 | ACCEPT     |          |
| P3_FIT01   | Other       | Flow rate into the upper water tank                               | Other       | Pressure    | Other       |        0.806 |      0.48 | ACCEPT     |          |
| P3_LCV01D  | Other       | Position command for the valve LCV01                              | Other       | Other       | Other       |        0.944 |      0.44 | ACCEPT     |          |
| P3_PIT01   | Pressure    | Pressure of water flowing into the upper water tank (raw 0-27648) | Pressure    | Pressure    | Pressure    |        0.944 |      0.52 | ACCEPT     |          |
| P4_HT_FD   | Other       | Frequency deviation of HTM                                        | Unknown     | Other       | Other       |        0.822 |      0.63 | ACCEPT     |          |
| P4_ST_FD   | Other       | Frequency deviation of STM                                        | Other       | Other       | Other       |        0.928 |      0.56 | ACCEPT     |          |
| P4_ST_LD   | Other       | Electrical load demand of STM                                     | Other       | Other       | Other       |        0.852 |      0.26 | ACCEPT     |          |
| P4_ST_PO   | Other       | Output power of STM                                               | Other       | Other       | Other       |        0.822 |      0.31 | ACCEPT     |          |
| P4_ST_PT01 | Pressure    | Digital value of steam pressure of STM (raw 0-27648)              | Pressure    | Other       | Other       |        0.933 |      0.38 | ACCEPT     |          |

## train2 (fresh): target tags

| tag        | true        | description                                                       | name_only   | behaviour   | hybrid      |   confidence |   novelty | decision   | reason          |
|:-----------|:------------|:------------------------------------------------------------------|:------------|:------------|:------------|-------------:|----------:|:-----------|:----------------|
| P1_PIT01   | Pressure    | Heat-exchanger outlet pressure                                    | Pressure    | Pressure    | Pressure    |        0.846 |      0.23 | ACCEPT     |                 |
| P1_PIT02   | Pressure    | Water supply pressure of the heating water pump                   | Pressure    | Other       | Other       |        0.602 |      0.66 | REVIEW     | low confidence  |
| P1_PP01AD  | RunStatus   | Start command of the main water pump PP01A                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01AR  | RunStatus   | Running state of the main water pump PP01A                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01BD  | RunStatus   | Start command of the main water pump PP01B                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP01BR  | RunStatus   | Running state of the main water pump PP01B                        | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP02D   | RunStatus   | Start command of the heating water pump PP02                      | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_PP02R   | RunStatus   | Running state of the heating water pump PP02                      | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P1_STSP    | RunStatus   | Start/stop command of the boiler DCS                              | RunStatus   | RunStatus   | RunStatus   |        0.948 |      0.82 | REVIEW     | constant signal |
| P1_TIT01   | Temperature | Heat-exchanger outlet temperature                                 | Temperature | Other       | Temperature |        0.729 |      0.35 | REVIEW     | low confidence  |
| P1_TIT02   | Temperature | Temperature of the heating water tank                             | Temperature | Other       | Temperature |        0.83  |      0.33 | ACCEPT     |                 |
| P2_OnOff   | RunStatus   | On/off switch of the turbine DCS                                  | Unknown     | RunStatus   | RunStatus   |        0.798 |      0.82 | REVIEW     | constant signal |
| P3_PIT01   | Pressure    | Pressure of water flowing into the upper water tank (raw 0-27648) | Pressure    | Pressure    | Pressure    |        0.944 |      0.52 | ACCEPT     |                 |
| P4_ST_PT01 | Pressure    | Digital value of steam pressure of STM (raw 0-27648)              | Pressure    | Other       | Other       |        0.933 |      0.38 | ACCEPT     |                 |
| P4_ST_TT01 | Temperature | Digital value of steam temperature of STM (raw 0-27648)           | Temperature | Other       | Other       |        0.5   |      0.42 | REVIEW     | low confidence  |

Per-tag tables: `hai_predictions_train1.csv`, `hai_predictions_train2.csv`. Figures: `hai_confusion.png`, `hai_gate.png`.
