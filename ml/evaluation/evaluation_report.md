# SmartFood Model Evaluation Report

- Model version: `completion-model-1.0`
- Dataset source: `SYNTHETIC`
- Selected model: `logistic_regression`
- Selection rule: lowest validation Brier score, then highest validation F1

## Dataset split

| Split | Rows | Completed | Not completed |
|---|---:|---:|---:|
| Train | 2100 | 1481 | 619 |
| Validation | 450 | 317 | 133 |
| Test | 450 | 310 | 140 |

## Selected model test metrics

| Metric | Value |
|---|---:|
| Accuracy | 0.6933 |
| Precision | 0.6937 |
| Recall | 0.9935 |
| F1 | 0.8170 |
| ROC-AUC | 0.6036 |
| Average precision | 0.7641 |
| Brier score | 0.2071 |
| Log loss | 0.6041 |

## Rule-based baseline test metrics

| Metric | Value |
|---|---:|
| Accuracy | 0.6644 |
| Precision | 0.7227 |
| Recall | 0.8323 |
| F1 | 0.7736 |
| ROC-AUC | 0.6015 |
| Brier score | 0.2171 |
| Log loss | 0.6245 |

## Interpretation

The model estimates the probability that an eligible and approved donation-receiver match will reach confirmed completion.

Eligibility remains controlled by Django business rules. A high model probability cannot make an ineligible receiver eligible.

## Limitation

The current evaluation uses synthetic data. It demonstrates technical feasibility and must not be presented as validated real-world predictive performance.
