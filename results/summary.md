# Phase 1 results

Train/CV: `plant_a` (510 tags, 80 machines) · Holdout: `plant_b` (212 tags, 30 machines, never seen in training)

## Method comparison

| Method         |   CV plant A acc |   CV plant A macro-F1 |   Holdout plant B acc |   Holdout plant B macro-F1 |
|:---------------|-----------------:|----------------------:|----------------------:|---------------------------:|
| Name-only      |            0.635 |                 0.747 |                 0.618 |                      0.706 |
| Behaviour-only |            0.914 |                 0.911 |                 0.929 |                      0.926 |
| Hybrid         |            0.929 |                 0.93  |                 0.939 |                      0.937 |

## Accuracy by naming style (CV A + holdout B pooled)

| style     |   Name-only |   Behaviour-only |   Hybrid |   tags |
|:----------|------------:|-----------------:|---------:|-------:|
| isa       |       0.833 |            0.94  |    0.952 |    252 |
| opaque    |       0.033 |            0.892 |    0.892 |    212 |
| shorthand |       0.922 |            0.919 |    0.946 |    258 |

## Accuracy by true signal type (look-alikes are labelled 'Other')

| subtype      |   Name-only |   Behaviour-only |   Hybrid |   tags |
|:-------------|------------:|-----------------:|---------:|-------:|
| Alarm        |       0.447 |            1     |    1     |     47 |
| Counter      |       0.652 |            0.957 |    0.978 |     46 |
| CtrlOutput   |       0.541 |            0.973 |    1     |     37 |
| Flow         |       0.4   |            0.85  |    0.9   |     20 |
| Level        |       0.375 |            0.375 |    0.25  |      8 |
| MotorCurrent |       0.685 |            0.968 |    0.968 |    124 |
| Pressure     |       0.559 |            0.667 |    0.742 |     93 |
| RunStatus    |       0.613 |            1     |    1     |    124 |
| Setpoint     |       0.75  |            0.977 |    0.977 |     44 |
| Speed        |       0.774 |            1     |    0.968 |     31 |
| Temperature  |       0.696 |            0.919 |    0.932 |    148 |

## Confidence gating (hybrid, holdout B, threshold 0.8)

- Auto-accepted: 194/212 tags (92%)
- Precision of auto-accepted: 97.4%
- Sent to human review: 18 tags; hybrid accuracy on those: 55.6%

## Showcase cases

| machine   | tag      | predicted    |   confidence | decision   | true         | name_only    | behaviour_only   | style     | case                          |
|:----------|:---------|:-------------|-------------:|:-----------|:-------------|:-------------|:-----------------|:----------|:------------------------------|
| M02       | REG2325  | RunStatus    |        0.998 | ACCEPT     | RunStatus    | Unknown      | RunStatus        | opaque    | name wrong, hybrid right      |
| M02       | REG3646  | MotorCurrent |        0.997 | ACCEPT     | MotorCurrent | Unknown      | MotorCurrent     | opaque    | name wrong, hybrid right      |
| M02       | REG30    | Pressure     |        0.991 | ACCEPT     | Pressure     | Unknown      | Pressure         | opaque    | name wrong, hybrid right      |
| M02       | REG1566  | Temperature  |        0.842 | ACCEPT     | Temperature  | Unknown      | Temperature      | opaque    | name wrong, hybrid right      |
| M07       | DISCH_P3 | Pressure     |        0.722 | REVIEW     | Pressure     | Pressure     | Temperature      | shorthand | behaviour wrong, hybrid right |
| M21       | TIT304   | Temperature  |        0.581 | REVIEW     | Temperature  | Temperature  | Other            | isa       | behaviour wrong, hybrid right |
| M26       | AI_03    | Pressure     |        0.612 | REVIEW     | Pressure     | Unknown      | Other            | opaque    | behaviour wrong, hybrid right |
| M02       | REG4335  | Other        |        0.571 | REVIEW     | Pressure     | Unknown      | Other            | opaque    | hybrid wrong                  |
| M04       | IR30857  | Temperature  |        0.499 | REVIEW     | Other        | MotorCurrent | Other            | opaque    | hybrid wrong                  |
| M06       | PI603    | Temperature  |        0.768 | REVIEW     | Pressure     | Pressure     | Temperature      | isa       | hybrid wrong                  |
| M07       | THM4     | Other        |        0.585 | REVIEW     | Temperature  | Unknown      | Other            | shorthand | hybrid wrong                  |

Figures: `comparison.png`, `confusion_matrices.png`, `feature_importance.png`, `samples_plant_a.png`. Full table: `inference_table.csv`.
