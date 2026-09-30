# SmartFood — Machine Learning (`ml/ml.md`)

## 1. Overview

The SmartFood machine-learning component currently implements a **match-completion prediction pipeline**.

Its purpose is to estimate the probability that an **eligible and approved donation-receiver match** will reach confirmed completion.

The ML model operates after SmartFood's hard eligibility rules. The model does **not** determine whether a receiver is eligible.

```text
Donation
   ↓
Hard eligibility rules
   ↓
Eligible receiver candidates
   ↓
Recommendation / matching
   ↓
Approved donation-receiver match
   ↓
Completion probability model
   ↓
Predicted completion probability
```

The current implementation is an experimental prototype trained on **synthetic data**.

---

# 2. ML Directory Structure

The supplied project structure is:

```text
ml/
├── data/
│   ├── processed/
│   │   ├── smartfood_training_data.csv
│   │   └── smartfood_training_metadata.json
│   │
│   └── synthetic/
│       ├── generation_metadata.json
│       └── smartfood_synthetic_matches.csv
│
├── evaluation/
│   ├── calibration_plot.png
│   ├── confusion_matrix.png
│   ├── evaluation_report.json
│   ├── evaluation_report.md
│   └── test_predictions.csv
│
├── models/
│   ├── completion_pipeline.joblib
│   └── model_metadata.json
│
├── myenv/
│
├── notebooks/
│
├── training/
│   ├── generate_synthetic_data.py
│   └── train_model.py
│
├── requirements.txt
└── ml.md
```

The supplied artifacts indicate that:

- synthetic data is generated into `ml/data/synthetic/`
- processed training data is stored under `ml/data/processed/`
- trained model artifacts are stored under `ml/models/`
- evaluation outputs are stored under `ml/evaluation/`
- model training code is under `ml/training/`

---

# 3. Prediction Objective

## Target

The prediction target is:

```text
target_completed
```

Binary values:

```text
1 = confirmed completion
0 = resolved non-completion
```

The supplied dataset documentation defines a positive outcome as a selected match that reaches receiver-confirmed `COMPLETED` status.

Negative outcomes include resolved statuses such as:

```text
FAILED
CANCELLED
EXPIRED
```

Pending and unresolved transactions are not included as training observations.

---

# 4. Unit of Observation

One ML row represents:

> **One approved donation-receiver match.**

A receiver who appeared in recommendations but was not selected does not become a training row.

This prevents the training target from being defined from recommendation exposure alone.

---

# 5. Dataset Sources

Every match-training record has an explicit source.

```text
REAL
PILOT
SYNTHETIC
```

### REAL

Actual platform transaction data.

### PILOT

Controlled pilot or user-acceptance test data.

### SYNTHETIC

Programmatically generated development/testing data.

Sources should not be silently mixed.

Evaluation should either report source-specific metrics or clearly identify the source combination used.

---

# 6. Current Dataset

The current model artifacts identify the active training source as:

```text
SYNTHETIC
```

The synthetic dataset metadata reports:

```text
Dataset name:
SmartFood Synthetic Match Completion Dataset

Dataset version:
synthetic-1.0

Random seed:
42

Rows:
3000
```

Target distribution:

| Target | Rows |
|---|---:|
| Completed | 2108 |
| Not completed | 892 |

Completion rate:

```text
2108 / 3000 ≈ 70.27%
```

---

# 7. Synthetic Dataset Categories

The supplied synthetic-generation metadata reports these category counts:

| Category | Rows |
|---|---:|
| Beverages | 457 |
| Bakery | 428 |
| Dairy Products | 447 |
| Prepared Meals | 417 |
| Dry Food | 410 |
| Fruits and Vegetables | 448 |
| Packaged Food | 393 |

---

# 8. Synthetic Failure Reasons

The supplied synthetic dataset contains these failure-reason categories:

| Failure reason | Count |
|---|---:|
| MISSED_RECEIVING_WINDOW | 134 |
| COLLECTION_DISTANCE_PROBLEM | 215 |
| QUANTITY_REQUIREMENT_CHANGED | 224 |
| DELIVERY_REJECTED | 34 |
| RECEIVER_CANCELLED | 40 |
| TRANSPORT_FAILURE | 145 |
| OPERATIONAL_FAILURE | 37 |
| DONOR_CANCELLED | 32 |
| FOOD_UNAVAILABLE_AT_PICKUP | 31 |

These fields are outcome information and must not be used directly as model inputs.

---

# 9. Model Input Features

The model uses the following features.

## Numeric features

```text
distance
quantity_match
availability_overlap
transport_readiness
donation_quantity
remaining_capacity
approximate_distance_km
maximum_service_distance_km
active_allocations
maximum_active_allocations
```

## Categorical features

```text
category_name
unit
```

The final model feature set is:

```text
10 numeric features
+
2 categorical features
=
12 input features
```

---

# 10. Feature Definitions

The supplied dataset metadata defines or describes the main recommendation-time inputs as follows.

### `distance`

Normalized proximity within the receiver's maximum service distance.

### `quantity_match`

Fraction of remaining receiver need satisfied by the donation.

### `availability_overlap`

Fraction of the pickup window overlapping receiver availability.

### `transport_readiness`

Remaining operational allocation capacity.

### `category_name`

Food category available at recommendation time.

### `unit`

Donation quantity unit available at recommendation time.

### `donation_quantity`

Donation quantity available at recommendation time.

The trained model also explicitly accepts:

```text
remaining_capacity
approximate_distance_km
maximum_service_distance_km
active_allocations
maximum_active_allocations
```

These fields are point-in-time recommendation features.

---

# 11. Point-in-Time Feature Rule

All model input features must come from the feature snapshot captured when the recommendation was generated.

The key rule is:

```text
Model inputs must be available at recommendation time.
```

Later events must not influence the model input.

This protects the model from target leakage.

---

# 12. Leakage Prevention

The following fields are explicitly excluded from model inputs:

```text
target_completed
failure_reason
approved_at
outcome_at
baseline_score
training_record_id
donation_request_id
donation_id
receiver_id
requested_revision_id
recommendation_evaluation_id
dataset_source
recommendation_timestamp
```

These fields may be retained for:

- labels
- auditing
- chronological splitting
- grouping
- traceability
- evaluation

but they are not model features.

---

# 13. Outcome Leakage Rules

The following events happen after recommendation time and therefore must not be used as prediction inputs:

```text
approval
pickup confirmation
delivery confirmation
receipt quantity
failure reports
final donation status
outcome timestamp
```

They may be used to determine or audit the final training label.

Conceptually:

```text
Recommendation-time features
        ↓
      INPUT
        ↓
  Completion model
        ↓
Predicted probability

Later transaction outcome
        ↓
     TARGET ONLY
```

---

# 14. Baseline Recommendation

The current synthetic-data metadata identifies the rule-based baseline as:

```text
baseline-2.0
```

Baseline weights:

| Feature | Weight |
|---|---:|
| distance | 0.30 |
| quantity_match | 0.30 |
| availability_overlap | 0.20 |
| transport_readiness | 0.20 |

The baseline score is represented on a `0..100` scale.

The training/evaluation code converts it to a probability-like value by:

```text
baseline_probability = baseline_score / 100
```

The baseline threshold is:

```text
0.50
```

---

# 15. Synthetic Data Generation

The project contains:

```text
ml/training/generate_synthetic_data.py
```

The supplied metadata identifies:

```text
Dataset version:
synthetic-1.0

Dataset source:
SYNTHETIC

Random seed:
42
```

The generated CSV is:

```text
ml/data/synthetic/smartfood_synthetic_matches.csv
```

The corresponding metadata file is:

```text
ml/data/synthetic/generation_metadata.json
```

The synthetic-data metadata explicitly states that the dataset is intended to demonstrate the technical ML pipeline.

---

# 16. Dataset Inclusion Rules

A record is included only when all required conditions are met.

1. A receiver request was selected and approved.
2. The donation reached a resolved terminal status.
3. A valid recommendation-time feature snapshot exists.
4. The recommendation existed before receiver approval.
5. Outcome timing is valid.

The supplied database-model documentation additionally requires:

```text
outcome_at >= approved_at
```

for training records.

---

# 17. Dataset Exclusion Rules

Excluded records include:

```text
Unselected receivers
Rejected requests
Withdrawn requests
Pending transactions
Active or unresolved donations
Records without recommendation-time features
Records with invalid timestamp ordering
```

---

# 18. Training and Evaluation Pipeline

The training implementation is:

```text
ml/training/train_model.py
```

The pipeline performs:

```text
Load dataset
   ↓
Validate required columns
   ↓
Validate target classes
   ↓
Parse timestamps
   ↓
Convert numeric features
   ↓
Convert categorical features
   ↓
Chronological transaction split
   ↓
Preprocessing
   ↓
Train candidate models
   ↓
Evaluate on validation set
   ↓
Select model
   ↓
Evaluate selected model on test set
   ↓
Evaluate rule-based baseline
   ↓
Save model
   ↓
Generate evaluation artifacts
   ↓
Save metadata
```

---

# 19. Dataset Validation

The supplied training code validates:

### Required columns

All model features plus:

```text
target_completed
recommendation_timestamp
donation_id
baseline_score
dataset_source
```

### Dataset size

At least:

```text
100 resolved records
```

### Target classes

Both binary classes must exist:

```text
0
1
```

### Donation identifier

Every row must contain:

```text
donation_id
```

### Recommendation timestamp

Every row must contain a valid recommendation timestamp after parsing.

---

# 20. Chronological Split

The model uses a chronological:

```text
70% train
15% validation
15% test
```

split.

The split is grouped by:

```text
donation_id
```

This ensures all rows belonging to one donation remain in the same split.

The purpose is to prevent transaction leakage.

---

# 21. Current Dataset Split

The trained-model metadata reports:

| Split | Rows | Completed | Not completed |
|---|---:|---:|---:|
| Train | 2100 | 1481 | 619 |
| Validation | 450 | 317 | 133 |
| Test | 450 | 310 | 140 |
| **Total** | **3000** | **2108** | **892** |

All three splits contain both target classes.

### Date ranges

The training artifact reports:

**Train**

```text
2025-01-01T07:54:42+00:00
→
2026-02-26T19:44:52+00:00
```

**Validation**

```text
2026-02-26T20:08:38+00:00
→
2026-05-28T10:27:07+00:00
```

**Test**

```text
2026-05-28T15:39:16+00:00
→
2026-08-31T17:08:18+00:00
```

---

# 22. Preprocessing

The supplied training pipeline uses a `ColumnTransformer`.

## Numeric pipeline

```text
SimpleImputer(strategy="median")
        ↓
StandardScaler
```

## Categorical pipeline

```text
SimpleImputer(strategy="most_frequent")
        ↓
OneHotEncoder(handle_unknown="ignore")
```

Other columns are dropped:

```text
remainder = drop
```

---

# 23. Candidate Models

The supplied training implementation evaluates two machine-learning candidates.

## Logistic Regression

```text
LogisticRegression(
    max_iter=2000,
    random_state=42
)
```

It is used inside the preprocessing pipeline.

## Random Forest

```text
RandomForestClassifier(
    n_estimators=350,
    max_depth=12,
    min_samples_leaf=4,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1
)
```

It is also used inside the preprocessing pipeline.

---

# 24. Model Selection Rule

The supplied training implementation selects the candidate model using:

```text
Lowest validation Brier score
then highest validation F1
```

The selected model in the current artifact is:

```text
logistic_regression
```

with model version:

```text
completion-model-1.0
```

---

# 25. Validation Results

The supplied evaluation metadata reports the following validation results.

## Logistic Regression

| Metric | Value |
|---|---:|
| Accuracy | 0.7222 |
| Precision | 0.7233 |
| Recall | 0.9811 |
| F1 | 0.8327 |
| ROC-AUC | 0.6662 |
| Average precision | 0.8122 |
| Brier score | 0.1924 |
| Log loss | 0.5699 |

Confusion matrix:

```text
[[14, 119],
 [ 6, 311]]
```

## Random Forest

| Metric | Value |
|---|---:|
| Accuracy | 0.7044 |
| Precision | 0.7556 |
| Recall | 0.8580 |
| F1 | 0.8035 |
| ROC-AUC | 0.6651 |
| Average precision | 0.8208 |
| Brier score | 0.2051 |
| Log loss | 0.5982 |

Confusion matrix:

```text
[[45, 88],
 [45, 272]]
```

The selection rule is based on validation Brier score first and validation F1 second.

---

# 26. Current Test Evaluation

The current selected model is:

```text
Logistic Regression
```

Model version:

```text
completion-model-1.0
```

Dataset source:

```text
SYNTHETIC
```

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

Confusion matrix:

```text
[[  4, 136],
 [  2, 308]]
```

The corresponding class-level test results reported by the supplied evaluation artifact are:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Not completed | 0.6667 | 0.0286 | 0.0548 | 140 |
| Completed | 0.6937 | 0.9935 | 0.8170 | 310 |

Macro averages:

| Metric | Value |
|---|---:|
| Precision | 0.6802 |
| Recall | 0.5111 |
| F1 | 0.4359 |

Weighted averages:

| Metric | Value |
|---|---:|
| Precision | 0.6853 |
| Recall | 0.6933 |
| F1 | 0.5799 |

---

# 27. Rule-Based Baseline Test Results

The supplied evaluation artifact reports the rule-based baseline metrics on the test split.

| Metric | Value |
|---|---:|
| Accuracy | 0.6644 |
| Precision | 0.7227 |
| Recall | 0.8323 |
| F1 | 0.7736 |
| ROC-AUC | 0.6015 |
| Average precision | 0.7587 |
| Brier score | 0.2171 |
| Log loss | 0.6245 |

Confusion matrix:

```text
[[ 41, 99],
 [ 52, 258]]
```

These figures describe the supplied evaluation artifact and should be interpreted in the context of the synthetic dataset.

---

# 28. Model Output

The training pipeline calls:

```python
pipeline.predict_proba(features)[:, 1]
```

and uses:

```text
probability >= 0.50
```

to create the binary prediction.

The model output therefore represents a **predicted completion probability** for the transaction represented by the supplied recommendation-time features.

It should not be interpreted as a guarantee of completion.

---

# 29. Business-Rule Boundary

The ML model does not replace SmartFood eligibility rules.

The intended decision flow is:

```text
Hard eligibility rules
       ↓
Eligible receivers
       ↓
Recommendation logic
       ↓
Completion model
       ↓
Probability / ranking signal
```

A high predicted completion probability cannot make an otherwise ineligible receiver eligible.

---

# 30. Model Artifact

Current artifact:

```text
ml/models/completion_pipeline.joblib
```

Model name:

```text
logistic_regression
```

Model version:

```text
completion-model-1.0
```

The supplied model metadata reports the artifact SHA-256:

```text
e87fce4f69a0206a83fc7782628f1ccca27c6527a6003fc72db6c68654905697
```

The model is an end-to-end scikit-learn pipeline containing preprocessing and the classifier.

---

# 31. Model Metadata

The supplied artifact reports:

```text
Python:
3.11.9

pandas:
3.0.6

NumPy:
2.4.6

scikit-learn:
1.9.1

joblib:
1.6.0
```

Prediction threshold:

```text
0.50
```

Positive class:

```text
confirmed completion
```

---

# 32. Evaluation Artifacts

The ML evaluation directory contains:

```text
ml/evaluation/
├── calibration_plot.png
├── confusion_matrix.png
├── evaluation_report.json
├── evaluation_report.md
└── test_predictions.csv
```

## `confusion_matrix.png`

Visualizes predicted versus actual completion classes.

## `calibration_plot.png`

Visualizes predicted completion probabilities against observed completion rates.

## `evaluation_report.json`

Machine-readable training and evaluation metadata.

## `evaluation_report.md`

Human-readable model evaluation report.

## `test_predictions.csv`

Stores test-set predictions and probabilities.

---

# 33. Calibration

The training code creates a calibration curve using:

```text
10 bins
strategy = quantile
```

The chart compares:

```text
Predicted completion probability
vs.
Observed completion rate
```

It also plots the rule-based baseline when baseline data is available.

The Brier score is included as a probability-quality metric.

---

# 34. Evaluation Metrics

The pipeline reports:

```text
Accuracy
Precision
Recall
F1
ROC-AUC
Average Precision
Brier Score
Log Loss
Confusion Matrix
Classification Report
```

These metrics should be read together rather than relying on a single value.

For a completion-probability system, probability-sensitive metrics such as Brier score and log loss are especially relevant because the system uses `predict_proba()` outputs.

---

# 35. Training Command

The supplied training script supports:

```bash
python ml/training/train_model.py
```

It also supports command-line overrides.

### Dataset

```bash
python ml/training/train_model.py \
  --dataset <path-to-training-csv>
```

### Model directory

```bash
python ml/training/train_model.py \
  --model-directory <model-output-directory>
```

### Evaluation directory

```bash
python ml/training/train_model.py \
  --evaluation-directory <evaluation-output-directory>
```

Defaults are derived from the training script location:

```text
ml/data/synthetic/smartfood_synthetic_matches.csv
ml/models/
ml/evaluation/
```

---

# 36. Reproducibility

The training configuration defines:

```text
RANDOM_STATE = 42
```

The synthetic-data generation metadata also reports:

```text
random_seed = 42
```

The chronological split is deterministic with respect to the sorted recommendation timestamps and the configured fractions:

```text
70 / 15 / 15
```

---

# 37. Data Quality and Integrity Requirements

The training code checks:

```text
Required columns exist
Both target classes exist
At least 100 records exist
Every row has donation_id
Every row has recommendation_timestamp
No forbidden feature has been configured
```

It also verifies that transaction identifiers do not overlap between:

```text
train and validation
train and test
validation and test
```

---

# 38. Training Data Governance

The model documentation distinguishes between:

```text
feature data
label/outcome data
audit metadata
```

Feature data should be captured at recommendation time.

Outcome information should be retained for:

```text
target generation
evaluation
auditing
```

but not included as prediction inputs.

This separation is especially important because the outcome fields describe events that occur after the recommendation.

---

# 39. Current ML Model Summary

| Item | Current value |
|---|---|
| Task | Binary completion prediction |
| Target | `target_completed` |
| Positive class | Confirmed completion |
| Dataset source | `SYNTHETIC` |
| Dataset version | `synthetic-1.0` |
| Dataset rows | 3000 |
| Train rows | 2100 |
| Validation rows | 450 |
| Test rows | 450 |
| Candidate models | Logistic Regression, Random Forest |
| Selected model | `logistic_regression` |
| Model version | `completion-model-1.0` |
| Threshold | 0.50 |
| Split | Chronological 70/15/15 grouped by `donation_id` |
| Selection criterion | Validation Brier score, then validation F1 |
| Saved artifact | `ml/models/completion_pipeline.joblib` |

---

# 40. Important Limitation

The current model was trained and evaluated on:

```text
SYNTHETIC
```

data.

Therefore the supplied evaluation demonstrates **technical pipeline feasibility**, not validated real-world predictive performance.

The current results must not be presented as evidence that the model has established predictive validity on actual SmartFood transactions.

---

# 41. Additional Limitations

The supplied model documentation identifies these limitations:

1. The current dataset is synthetic.
2. Evaluation metrics demonstrate technical feasibility rather than real-world predictive validity.
3. The model only scores receivers who have already passed hard eligibility rules.
4. The model is an experimental prototype.
5. The output is dependent on recommendation-time feature quality.
6. Changing business rules or feature definitions can change model behavior.
7. Historical outcome fields must remain separated from model inputs to avoid leakage.

---

# 42. Production Transition Requirements

Before using the completion model as a production predictive system, the project should establish:

```text
Real transaction data
        ↓
Validated point-in-time features
        ↓
Leakage checks
        ↓
Chronological evaluation
        ↓
Calibration analysis
        ↓
Monitoring
        ↓
Model/version tracking
```

The current documentation does not claim that these production-validation requirements have already been completed.

---

# 43. Recommended Future ML Workflow

```text
1. Collect real resolved match records
          ↓
2. Persist recommendation-time feature snapshots
          ↓
3. Validate outcome labels
          ↓
4. Check for feature leakage
          ↓
5. Split chronologically by transaction
          ↓
6. Train baseline and candidate models
          ↓
7. Compare validation metrics
          ↓
8. Evaluate once on held-out test data
          ↓
9. Inspect calibration and confusion matrix
          ↓
10. Register model artifact and metadata
          ↓
11. Monitor production performance
          ↓
12. Retrain using approved data/version
```

---

# 44. ML/Data Documentation Files

The project contains or references these important ML artifacts:

```text
ml/data/processed/smartfood_training_data.csv
ml/data/processed/smartfood_training_metadata.json

ml/data/synthetic/smartfood_synthetic_matches.csv
ml/data/synthetic/generation_metadata.json

ml/evaluation/evaluation_report.json
ml/evaluation/evaluation_report.md
ml/evaluation/test_predictions.csv
ml/evaluation/confusion_matrix.png
ml/evaluation/calibration_plot.png

ml/models/completion_pipeline.joblib
ml/models/model_metadata.json

ml/training/generate_synthetic_data.py
ml/training/train_model.py
```

---

# 45. ML Safety and Interpretation

The completion model should be understood as a **decision-support signal for recommendation/matching workflows**.

It should not be represented as:

```text
guaranteed completion
guaranteed delivery
guaranteed acceptance
certain outcome
```

The predicted probability is an estimate generated by a statistical model from the provided features.

The existing hard eligibility logic remains authoritative for eligibility.

---

# 46. Current Status

The supplied ML artifacts indicate that the SmartFood completion-prediction pipeline is implemented through:

```text
Synthetic data generation
        ✓
Dataset validation
        ✓
Point-in-time feature definition
        ✓
Leakage exclusion
        ✓
Chronological grouped split
        ✓
Candidate model training
        ✓
Validation evaluation
        ✓
Model selection
        ✓
Held-out test evaluation
        ✓
Rule-based baseline evaluation
        ✓
Model artifact persistence
        ✓
Evaluation report generation
        ✓
Confusion matrix generation
        ✓
Calibration plot generation
        ✓
Prediction export
        ✓
Model metadata persistence
        ✓
```

The major remaining qualification is that the current model is supported by synthetic-data evaluation rather than real-world validation.

---

# 47. Source-of-Truth Notes

This document consolidates the following supplied source materials:

```text
Model evaluation report
Training dataset documentation
Processed dataset metadata
Synthetic dataset generation metadata
Training/evaluation metadata
Model metadata
ml/training/train_model.py
```

The documented values above are preserved from those supplied materials.

Where the source materials describe a limitation, that limitation is retained rather than replaced with an inferred conclusion.
