# SmartFood Match Completion Training Dataset

## Dataset purpose

The dataset is used to train a binary classifier that predicts
whether an approved donation-receiver match will reach confirmed
completion.

## Prediction target

Target column:

`target_completed`

Values:

- `1`: The selected match reached receiver-confirmed `COMPLETED`.
- `0`: The selected match reached a resolved non-completion status,
  such as `FAILED`, `CANCELLED`, or `EXPIRED`.

Pending and unresolved matches are not included.

## Unit of observation

One row represents one approved donation-receiver match.

A receiver that appeared in recommendations but was not selected
does not become a training row.

## Model input features

- `distance`
- `quantity_match`
- `availability_overlap`
- `transport_readiness`
- `category_name`
- `unit`
- `donation_quantity`
- `remaining_capacity`
- `approximate_distance_km`
- `maximum_service_distance_km`
- `active_allocations`
- `maximum_active_allocations`

All input features must come from the feature snapshot saved when
the recommendation was generated.

## Label and audit columns

The following fields are retained for labels, auditing, grouping,
or chronological splitting. They must not be passed directly to
the classifier:

- `target_completed`
- `failure_reason`
- `approved_at`
- `outcome_at`
- `recommendation_timestamp`
- `baseline_score`
- `baseline_version`
- Database identifiers
- `dataset_source`

## Dataset sources

Each record has one explicit source:

- `REAL`: Actual platform transaction.
- `PILOT`: Controlled pilot or user-acceptance test.
- `SYNTHETIC`: Programmatically generated development data.

Sources must not be silently mixed. Evaluation results should
either report each source separately or clearly document the
combination used.

## Inclusion rules

A row is included only when:

1. A receiver was selected through an approved request.
2. The transaction reached a resolved terminal status.
3. A recommendation-time feature snapshot exists.
4. The recommendation existed before receiver approval.
5. The outcome timestamp is not before the approval timestamp.

## Exclusion rules

The following are excluded:

- Unselected receivers.
- Rejected requests.
- Withdrawn requests.
- Pending receiver requests.
- Active or unresolved donations.
- Records without recommendation-time features.
- Records with invalid timestamp ordering.

## Leakage prevention

Pickup confirmation, delivery confirmation, receipt quantity,
failure reports, final donation status and outcome timestamps occur
after recommendation time.

They must not be used as model inputs.

They may only be used to calculate the target or audit the record.

## Generated files

The collection command creates:

- `ml/data/processed/smartfood_training_data.csv`
- `ml/data/processed/smartfood_training_metadata.json`

Generated datasets should usually be excluded from public Git when
they contain real participant information.