# SmartFood Database Documentation Notes

This file records boundaries and source limitations for the current database documentation.

## Source of Truth

The supplied Django model definitions are treated as authoritative for this documentation set.

No fields, relationships, constraints, or table names have been invented for models whose definitions were not supplied.

## Supplied Tables

The supplied source defines these 31 tables:

```text
accounts_user
food_categories
donations
donation_revisions
donation_requests
donation_images
donation_status_history
handover_records
delivery_records
receipt_confirmations
volunteer_profiles
volunteer_capacities
volunteer_availability
volunteer_tasks
volunteer_task_history
volunteer_failure_reports
verification_submissions
verification_documents
verification_history
notifications
operational_issues
background_jobs
service_areas
receiver_profiles
receiver_preferences
receiver_requirements
receiver_availability
recommendation_runs
recommendation_evaluations
recommendation_candidates
match_training_records
```

## Referenced but Not Supplied

The following models are imported by the supplied code but their definitions are not included:

```text
Complaint
AuditEvent
OutcomeCorrection
```

Their schema should be documented only after their actual model definitions are available.

## Recommendation / ML Boundary

The supplied `MatchTrainingRecord` docstring states:

> Only the saved recommendation-time feature snapshot is used as model input. Outcome information is stored as label metadata and must not be used as input features.

This distinction should be preserved in future ML documentation.

## Important Integrity Rules

The database explicitly protects several lifecycle rules:

1. A donation has at most one current revision.
2. A donation can have at most one approved request.
3. A receiver can have at most one pending/approved request for a donation.
4. A donation has at most one handover record.
5. A donation has at most one delivery record.
6. A donation has at most one receipt confirmation.
7. A donation has at most one volunteer task.
8. Receiver food preferences are unique per receiver/category.
9. Receiver requirements are unique per receiver/category/unit.
10. Volunteer capacity is unique per volunteer/unit.
11. Verification allows only one pending submission per user.
12. Recommendation evaluations are unique per run/receiver.
13. Recommendation candidates are unique per run/receiver and run/rank.
14. Training records are unique per donation request.

These constraints should be retained when database migrations are created or modified.
