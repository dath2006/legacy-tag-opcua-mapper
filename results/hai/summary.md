# Real-data test: HAI 21.03 (train1)

Model trained only on simulated plants (722 tags); tested on 79 real tags (15 × 4 h windows, predictions averaged per tag). Classes present in HAI: Other, Pressure, RunStatus, Temperature (HAI has no motor current or counter tags).

## Metrics

| Method                     |   Accuracy (79 tags) |   Target-tag recall (15) |   Other correctly rejected (64) |   Precision of target claims |   Auto-accepted |   Precision of auto-accepted |
|:---------------------------|---------------------:|-------------------------:|--------------------------------:|-----------------------------:|----------------:|-----------------------------:|
| Name-only (raw names)      |                0.38  |                    0.533 |                           0.344 |                        0.14  |         nan     |                      nan     |
| Name-only (stripped names) |                0.468 |                    0.533 |                           0.453 |                        0.615 |         nan     |                      nan     |
| Behaviour-only             |                0.418 |                    0.4   |                           0.422 |                        0.136 |           0.62  |                        0.531 |
| Hybrid (raw names)         |                0.468 |                    0.467 |                           0.469 |                        0.171 |           0.646 |                        0.549 |
| Hybrid (stripped names)    |                0.494 |                    0.467 |                           0.5   |                        0.179 |           0.696 |                        0.509 |

## Target tags (Temperature / Pressure / RunStatus)

| tag        | true        | description                                                       | name_only   | behaviour   | hybrid      |   confidence | decision   |
|:-----------|:------------|:------------------------------------------------------------------|:------------|:------------|:------------|-------------:|:-----------|
| P1_PIT01   | Pressure    | Heat-exchanger outlet pressure                                    | Pressure    | Pressure    | Pressure    |        0.797 | REVIEW     |
| P1_PIT02   | Pressure    | Water supply pressure of the heating water pump                   | Pressure    | Pressure    | Pressure    |        0.799 | REVIEW     |
| P1_PP01AD  | RunStatus   | Start command of the main water pump PP01A                        | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_PP01AR  | RunStatus   | Running state of the main water pump PP01A                        | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_PP01BD  | RunStatus   | Start command of the main water pump PP01B                        | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_PP01BR  | RunStatus   | Running state of the main water pump PP01B                        | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_PP02D   | RunStatus   | Start command of the heating water pump PP02                      | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_PP02R   | RunStatus   | Running state of the heating water pump PP02                      | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P1_STSP    | RunStatus   | Start/stop command of the boiler DCS                              | RunStatus   | Other       | Other       |        1     | ACCEPT     |
| P1_TIT01   | Temperature | Heat-exchanger outlet temperature                                 | Temperature | Temperature | Temperature |        0.984 | ACCEPT     |
| P1_TIT02   | Temperature | Temperature of the heating water tank                             | Temperature | Temperature | Temperature |        0.982 | ACCEPT     |
| P2_OnOff   | RunStatus   | On/off switch of the turbine DCS                                  | Unknown     | Other       | Other       |        1     | ACCEPT     |
| P3_PIT01   | Pressure    | Pressure of water flowing into the upper water tank (raw 0-27648) | Pressure    | Pressure    | Pressure    |        0.515 | REVIEW     |
| P4_ST_PT01 | Pressure    | Digital value of steam pressure of STM (raw 0-27648)              | Pressure    | Temperature | Pressure    |        0.405 | REVIEW     |
| P4_ST_TT01 | Temperature | Digital value of steam temperature of STM (raw 0-27648)           | Temperature | Temperature | Temperature |        0.995 | ACCEPT     |

## 'Other' tags wrongly claimed as a target (32)

| tag       | true   | description                                                       | name_only   | behaviour   | hybrid      |   confidence | decision   |
|:----------|:-------|:------------------------------------------------------------------|:------------|:------------|:------------|-------------:|:-----------|
| P1_B2016  | Other  | Pressure demand for thermal power output control                  | Unknown     | Temperature | Temperature |        0.818 | ACCEPT     |
| P1_B4005  | Other  | Temperature PID control output                                    | Unknown     | Temperature | Temperature |        0.486 | REVIEW     |
| P1_B400B  | Other  | Water outflow rate setpoint (heating water tank)                  | Unknown     | Pressure    | Pressure    |        0.532 | REVIEW     |
| P1_B4022  | Other  | Temperature demand for thermal power output control               | Unknown     | Temperature | Temperature |        0.809 | ACCEPT     |
| P1_FCV03D | Other  | Position command for the FCV03 valve                              | Other       | Temperature | Temperature |        0.683 | REVIEW     |
| P1_FCV03Z | Other  | Current position of the FCV03 valve                               | Other       | Temperature | Temperature |        0.517 | REVIEW     |
| P1_FT01   | Other  | Measured flowrate of the return water tank                        | Other       | Temperature | Temperature |        0.577 | REVIEW     |
| P1_FT01Z  | Other  | Water inflow rate converted from P1_FT01                          | Other       | Temperature | Temperature |        0.525 | REVIEW     |
| P1_FT03   | Other  | Measured flowrate of the return water tank                        | Other       | Temperature | Pressure    |        0.469 | REVIEW     |
| P1_FT03Z  | Other  | Water outflow rate converted from P1_FT03                         | Other       | Temperature | Pressure    |        0.469 | REVIEW     |
| P1_LCV01D | Other  | Position command for the LCV01 valve                              | Other       | Temperature | Temperature |        0.836 | ACCEPT     |
| P1_LCV01Z | Other  | Current position of the LCV01 valve                               | Other       | Temperature | Temperature |        0.629 | REVIEW     |
| P1_LIT01  | Other  | Water level of the return water tank                              | Other       | Temperature | Temperature |        0.801 | ACCEPT     |
| P1_PCV01Z | Other  | Current position of the PCV01 valve                               | Pressure    | Temperature | Temperature |        0.693 | REVIEW     |
| P1_PCV02Z | Other  | Current position of the PCV02 valve                               | Pressure    | Pressure    | Pressure    |        0.551 | REVIEW     |
| P2_24Vdc  | Other  | DCS 24V input voltage                                             | Unknown     | Pressure    | Pressure    |        0.995 | ACCEPT     |
| P2_CO_rpm | Other  | Speed controller output (not in manual table; inferred from name) | Other       | Pressure    | Pressure    |        0.992 | ACCEPT     |
| P2_HILout | Other  | HIL simulator output (not in manual table; inferred from name)    | Unknown     | Pressure    | Pressure    |        0.99  | ACCEPT     |
| P2_SIT01  | Other  | Current turbine RPM measured by speed probe                       | Other       | Pressure    | Pressure    |        0.971 | ACCEPT     |
| P2_SIT02  | Other  | Turbine RPM (second speed probe)                                  | Other       | Pressure    | Pressure    |        0.984 | ACCEPT     |
| P2_VT01   | Other  | Phase lag signal of the key phasor probe                          | Unknown     | Pressure    | Pressure    |        0.974 | ACCEPT     |
| P2_VXT02  | Other  | Shaft vibration X displacement                                    | Unknown     | Pressure    | Pressure    |        0.923 | ACCEPT     |
| P2_VXT03  | Other  | Shaft vibration X displacement                                    | Unknown     | Pressure    | Pressure    |        0.736 | REVIEW     |
| P2_VYT02  | Other  | Shaft vibration Y displacement                                    | Unknown     | Pressure    | Pressure    |        0.939 | ACCEPT     |
| P2_VYT03  | Other  | Shaft vibration Y displacement                                    | Unknown     | Pressure    | Pressure    |        0.896 | ACCEPT     |
| P3_LIT01  | Other  | Water level of the upper water tank                               | Other       | Temperature | Temperature |        0.972 | ACCEPT     |
| P4_HT_FD  | Other  | Frequency deviation of HTM                                        | Unknown     | Pressure    | Pressure    |        0.931 | ACCEPT     |
| P4_LD     | Other  | Total electrical load demand                                      | Unknown     | Temperature | Temperature |        0.87  | ACCEPT     |
| P4_ST_FD  | Other  | Frequency deviation of STM                                        | Other       | Pressure    | Pressure    |        0.994 | ACCEPT     |
| P4_ST_GOV | Other  | Gate opening rate of STM                                          | Other       | Temperature | Temperature |        0.808 | ACCEPT     |
| P4_ST_LD  | Other  | Electrical load demand of STM                                     | Other       | Pressure    | Pressure    |        0.507 | REVIEW     |
| P4_ST_PO  | Other  | Output power of STM                                               | Other       | Temperature | Temperature |        0.85  | ACCEPT     |

Full table: `hai_predictions.csv`. Figure: `hai_confusion.png`.
