# Phase 1 results

Train/CV: `plant_a` (613 tags, 80 machines) · Holdout: `plant_b` (253 tags, 30 machines, never seen in training)

## Method comparison

| Method         |   CV plant A acc |   CV plant A macro-F1 |   Holdout plant B acc |   Holdout plant B macro-F1 |
|:---------------|-----------------:|----------------------:|----------------------:|---------------------------:|
| Name-only      |            0.692 |                 0.79  |                 0.66  |                      0.769 |
| Behaviour-only |            0.778 |                 0.795 |                 0.866 |                      0.868 |
| Hybrid         |            0.889 |                 0.898 |                 0.921 |                      0.931 |

## Accuracy by naming style (CV A + holdout B pooled)

| style     |   Name-only |   Behaviour-only |   Hybrid |   tags |
|:----------|------------:|-----------------:|---------:|-------:|
| isa       |       0.872 |            0.807 |    0.931 |    305 |
| opaque    |       0.02  |            0.81  |    0.805 |    200 |
| shorthand |       0.889 |            0.798 |    0.922 |    361 |

## Accuracy by true signal type (look-alikes are labelled 'Other')

| subtype      |   Name-only |   Behaviour-only |   Hybrid |   tags |
|:-------------|------------:|-----------------:|---------:|-------:|
| Alarm        |       0.473 |            1     |    0.982 |     55 |
| Counter      |       0.717 |            0.967 |    0.95  |     60 |
| CtrlOutput   |       0.714 |            0.964 |    0.964 |     28 |
| Flow         |       0.429 |            0.893 |    0.964 |     28 |
| Frequency    |       0.917 |            0.833 |    0.917 |     12 |
| Level        |       0.667 |            0.5   |    0.75  |     24 |
| MotorCurrent |       0.686 |            0.653 |    0.785 |    121 |
| Power        |       0.821 |            0.256 |    0.718 |     39 |
| Pressure     |       0.729 |            0.6   |    0.835 |     85 |
| RunStatus    |       0.636 |            0.95  |    0.959 |    121 |
| Setpoint     |       0.824 |            0.794 |    0.971 |     34 |
| Speed        |       0.73  |            0.973 |    1     |     37 |
| Temperature  |       0.712 |            0.885 |    0.921 |    139 |
| ValvePos     |       0.76  |            0.6   |    0.84  |     25 |
| Vibration    |       0.543 |            0.857 |    0.943 |     35 |
| Voltage      |       0.739 |            1     |    0.957 |     23 |

## Confidence gating (hybrid, holdout B, threshold 0.8)

- Auto-accepted: 216/253 tags (85%)
- Precision of auto-accepted: 96.3%
- Sent to human review: 37 tags; hybrid accuracy on those: 67.6%
- Review reasons: {'low confidence': 31, 'constant signal': 4, 'unfamiliar signal': 2}

## Showcase cases

| machine   | tag       | predicted    |   confidence | decision   | reason         | true         | name_only    | behaviour_only   | style     | case                          |
|:----------|:----------|:-------------|-------------:|:-----------|:---------------|:-------------|:-------------|:-----------------|:----------|:------------------------------|
| M01       | PAL108    | Other        |        0.999 | ACCEPT     |                | Other        | Pressure     | Other            | isa       | name wrong, hybrid right      |
| M02       | LOAD_A2   | MotorCurrent |        0.58  | REVIEW     | low confidence | MotorCurrent | Unknown      | MotorCurrent     | shorthand | name wrong, hybrid right      |
| M02       | Q5        | Other        |        0.831 | ACCEPT     |                | Other        | Counter      | Other            | shorthand | name wrong, hybrid right      |
| M06       | N7:1      | Temperature  |        0.708 | REVIEW     | low confidence | Temperature  | Unknown      | Temperature      | opaque    | name wrong, hybrid right      |
| M02       | PRS_HYD3  | Pressure     |        0.961 | ACCEPT     |                | Pressure     | Pressure     | MotorCurrent     | shorthand | behaviour wrong, hybrid right |
| M03       | CUR7      | MotorCurrent |        0.721 | REVIEW     | low confidence | MotorCurrent | MotorCurrent | Other            | shorthand | behaviour wrong, hybrid right |
| M05       | P4_PV     | Pressure     |        0.835 | ACCEPT     |                | Pressure     | Pressure     | MotorCurrent     | shorthand | behaviour wrong, hybrid right |
| M11       | M204_KW   | Other        |        0.701 | REVIEW     | low confidence | Other        | Other        | MotorCurrent     | isa       | behaviour wrong, hybrid right |
| M02       | LEVEL6    | Temperature  |        0.506 | REVIEW     | low confidence | Other        | Other        | Temperature      | shorthand | hybrid wrong                  |
| M03       | P_KW9     | MotorCurrent |        0.497 | REVIEW     | low confidence | Other        | Other        | MotorCurrent     | shorthand | hybrid wrong                  |
| M03       | CTR10     | Other        |        0.419 | REVIEW     | low confidence | Counter      | Counter      | Counter          | shorthand | hybrid wrong                  |
| M03       | HYD_PSI11 | Other        |        0.505 | REVIEW     | low confidence | Pressure     | Pressure     | Other            | shorthand | hybrid wrong                  |

Figures: `comparison.png`, `confusion_matrices.png`, `feature_importance.png`, `samples_plant_a.png`. Full table: `inference_table.csv`.
