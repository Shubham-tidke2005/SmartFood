# SmartFood Database Schema — Current

> Source of truth: Django model definitions supplied for the SmartFood project.
>
> This document describes only the models and constraints present in the supplied source. It does not infer fields for imported models whose definitions were not included.

## 1. Database Overview

SmartFood uses a Django ORM schema centered around food donation, receiver matching, volunteer logistics, verification, notifications, operational processing, and recommendation/ML tracking.

The supplied model definitions represent **31 database tables**.

### Domain groups

| Domain | Tables |
|---|---|
| Accounts | `accounts_user` |
| Food & Donations | `food_categories`, `donations`, `donation_revisions`, `donation_requests`, `donation_images`, `donation_status_history` |
| Handover & Delivery | `handover_records`, `delivery_records`, `receipt_confirmations` |
| Volunteer Logistics | `volunteer_profiles`, `volunteer_capacities`, `volunteer_availability`, `volunteer_tasks`, `volunteer_task_history`, `volunteer_failure_reports` |
| Receivers | `service_areas`, `receiver_profiles`, `receiver_preferences`, `receiver_requirements`, `receiver_availability` |
| Verification | `verification_submissions`, `verification_documents`, `verification_history` |
| Notifications & Operations | `notifications`, `operational_issues`, `background_jobs` |
| Recommendation / ML | `recommendation_runs`, `recommendation_evaluations`, `recommendation_candidates`, `match_training_records` |

---

## 2. Identity

### `accounts_user`

Custom Django user model based on `AbstractUser`.

**Primary key:** `id` — UUID

Important fields:

- `email` — unique login identifier
- `display_name`
- `mobile`
- `role`
- `verification_status`
- `contact_verified_at`
- `auth_version`
- `created_at`
- `updated_at`

Username-based authentication is disabled:

```text
username = None
USERNAME_FIELD = email
```

### User roles

```text
DONOR
RECEIVER
VOLUNTEER
ADMIN
```

### Verification status

```text
PENDING
VERIFIED
REJECTED
SUSPENDED
```

---

## 3. Food & Donation Domain

### `food_categories`

Defines reusable food categories.

Fields:

- `id`
- `code` — unique slug
- `name`
- `active`
- `requires_preparation_time`
- `requires_use_by`
- `created_at`
- `updated_at`

---

### `donations`

Represents a food donation lifecycle.

Relationships:

```text
User ──< Donation
Donation ──< DonationRevision
Donation ──< DonationRequest
Donation ──< DonationStatusHistory
Donation ──1 HandoverRecord
Donation ──1 DeliveryRecord
Donation ──1 ReceiptConfirmation
Donation ──1 VolunteerTask
```

Statuses:

```text
AVAILABLE
RESERVED
PICKED_UP
DELIVERED
COMPLETED
CANCELLED
EXPIRED
FAILED
```

Important fields:

- `donor`
- `status`
- `custody_hold`
- `published_at`
- `closed_at`
- `created_at`
- `updated_at`

---

### `donation_revisions`

Stores versioned donation information.

Relationships:

```text
Donation ──< DonationRevision
FoodCategory ──< DonationRevision
User ──< DonationRevision (proposed_by)
DonationRevision ──< DonationImage
DonationRevision ──< DonationRequest
```

Units:

```text
KG
LITRE
PORTION
PACKAGE
```

Important fields:

- `number`
- `is_current`
- `food_name`
- `category`
- `quantity`
- `unit`
- `description`
- `storage_condition`
- `pickup_address`
- `pickup_starts_at`
- `pickup_deadline`
- `proposed_by`
- `prepared_at`
- `use_by_at`
- `pickup_area`

---

### `donation_requests`

Represents a receiver request for a donation.

Relationships:

```text
Donation ──< DonationRequest
User ──< DonationRequest (receiver)
DonationRevision ──< DonationRequest
```

Statuses:

```text
PENDING
APPROVED
REJECTED
WITHDRAWN
EXPIRED
CANCELLED
```

Transport modes:

```text
RECEIVER_COLLECTION
DONOR_DELIVERY
VOLUNTEER_DELIVERY
```

Business constraints:

- A receiver can have only one `PENDING` or `APPROVED` request for a donation.
- A donation can have only one `APPROVED` request.

---

### `donation_images`

Stores images attached to a donation revision.

Fields:

- `revision`
- `image`
- `original_name`
- `mime_type`
- `size_bytes`
- `position`
- `created_at`

Image positions are unique within a revision.

---

### `donation_status_history`

Immutable-style status transition history for donations.

Fields:

- `donation`
- `actor`
- `event_type`
- `from_status`
- `to_status`
- `reason`
- `created_at`

`actor` may be null, allowing system-generated events.

---

## 4. Handover & Delivery

### `handover_records`

Records physical handover of a donation.

One-to-one relationships:

```text
Donation ──1 HandoverRecord
DonationRequest ──1 HandoverRecord
```

Fields:

- `revision`
- `confirmed_by`
- `actual_quantity`
- `unit`
- `notes`
- `handed_over_at`
- `created_at`
- `updated_at`

`actual_quantity` must be greater than zero.

---

### `delivery_records`

Records delivery following a handover.

Relationships:

```text
Donation ──1 DeliveryRecord
DonationRequest ──1 DeliveryRecord
HandoverRecord ──1 DeliveryRecord
```

Fields:

- `delivered_by`
- `actual_quantity`
- `unit`
- `notes`
- `delivered_at`
- `created_at`
- `updated_at`

`actual_quantity` must be greater than zero.

---

### `receipt_confirmations`

Records receiver-side receipt confirmation.

Relationships:

```text
Donation ──1 ReceiptConfirmation
DonationRequest ──1 ReceiptConfirmation
HandoverRecord ──1 ReceiptConfirmation
DeliveryRecord ──0..1 ReceiptConfirmation
```

Discrepancy types:

```text
NONE
SHORTAGE
DAMAGE
QUALITY
WRONG_ITEM
OTHER
```

`accepted_quantity` must be non-negative.

The model exposes:

```text
has_discrepancy
```

which is true whenever `discrepancy_type != NONE`.

---

## 5. Receiver Domain

### `service_areas`

Geographic service areas used by receivers and volunteers.

Fields:

- `code` — unique slug
- `name` — unique
- `latitude`
- `longitude`
- `active`

Latitude is constrained to `-90..90`.

Longitude is constrained to `-180..180`.

---

### `receiver_profiles`

One-to-one receiver profile.

Relationships:

```text
User ──1 ReceiverProfile
ServiceArea ──< ReceiverProfile
```

Fields:

- `organization_name`
- `address`
- `service_area`
- `max_service_distance_km`
- `max_active_allocations`
- `operational`

---

### `receiver_preferences`

Food categories accepted by a receiver.

Relationships:

```text
User ──< ReceiverPreference
FoodCategory ──< ReceiverPreference
```

The `(receiver, category)` pair is unique.

---

### `receiver_requirements`

Quantified food requirements of receivers.

Relationships:

```text
User ──< ReceiverRequirement
FoodCategory ──< ReceiverRequirement
```

Fields:

- `unit`
- `quantity_needed`
- `quantity_reserved`
- `needed_until`
- `active`

Constraints ensure:

```text
quantity_needed > 0
quantity_reserved >= 0
quantity_reserved <= quantity_needed
```

The model exposes:

```text
remaining_quantity = quantity_needed - quantity_reserved
```

clamped to zero.

---

### `receiver_availability`

Weekly receiving availability.

Weekdays:

```text
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
```

The combination of receiver, weekday, start time, and end time is unique.

---

## 6. Volunteer Logistics

### `volunteer_profiles`

One-to-one volunteer profile.

Relationships:

```text
User ──1 VolunteerProfile
ServiceArea ──< VolunteerProfile
```

Availability status:

```text
AVAILABLE
UNAVAILABLE
BUSY
```

Fields include:

- `service_area`
- `availability_status`
- `max_service_distance_km`
- `max_active_tasks`
- `operational`
- `vehicle_description`

---

### `volunteer_capacities`

Transport capacity configured per volunteer and unit.

Units use `DonationRevision.Unit`.

The `(volunteer, unit)` combination is unique.

`maximum_quantity` must be greater than zero.

---

### `volunteer_availability`

Weekly volunteer availability.

The combination of volunteer, weekday, start time, and end time is unique.

---

### `volunteer_tasks`

Represents a logistics task associated with a donation.

Relationships:

```text
Donation ──1 VolunteerTask
DonationRequest ──1 VolunteerTask
User ──< VolunteerTask (assigned_volunteer)
ServiceArea ──< VolunteerTask (pickup_service_area)
ServiceArea ──< VolunteerTask (receiver_service_area)
```

Statuses:

```text
OPEN
ASSIGNED
ARRIVED_AT_DONOR
PICKED_UP
ARRIVED_AT_RECEIVER
DELIVERED
COMPLETED
CANCELLED
FAILED
```

`required_quantity` must be greater than zero.

---

### `volunteer_task_history`

Tracks volunteer task status events.

Fields:

- `task`
- `actor`
- `event_type`
- `from_status`
- `to_status`
- `reason`
- `created_at`

`actor` may be null.

---

### `volunteer_failure_reports`

Records volunteer task failures.

Stages:

```text
BEFORE_PICKUP
AFTER_PICKUP
```

Fields:

- `task`
- `volunteer`
- `stage`
- `reason`
- `reassign_requested`
- `created_at`

---

## 7. Verification

### `verification_submissions`

Tracks verification attempts for users.

Statuses:

```text
PENDING
APPROVED
REJECTED
```

Constraints:

- `(user, attempt)` is unique.
- Only one `PENDING` submission may exist for a user.
- `attempt > 0`.

---

### `verification_documents`

Documents attached to verification submissions.

Document types:

```text
IDENTITY
ORGANIZATION_REGISTRATION
ADDRESS_PROOF
OTHER
```

Files use private verification storage.

---

### `verification_history`

Tracks verification actions.

Actions:

```text
SUBMITTED
APPROVED
REJECTED
SUSPENDED
REOPENED
```

Records:

- user
- submission
- actor
- action
- from_status
- to_status
- reason
- created_at

---

## 8. Notifications & Operations

### `notifications`

User notification records.

Notification types include:

```text
REQUEST_SUBMITTED
REQUEST_WITHDRAWN
REQUEST_APPROVED
REQUEST_REJECTED
REQUEST_EXPIRED
ARRANGEMENT_CANCELLED
DONATION_CANCELLED
DONATION_EXPIRED
HANDOVER_CONFIRMED
DELIVERY_RECORDED
RECEIPT_CONFIRMED
RECEIPT_REJECTED
RECEIPT_REMINDER
PICKUP_REMINDER
PICKUP_OVERDUE
VOLUNTEER_TASK_ASSIGNED
VOLUNTEER_PICKUP
VOLUNTEER_DELIVERY
VOLUNTEER_TASK_FAILED
VOLUNTEER_TASK_REASSIGNED
ACCOUNT_SUSPENDED
```

`deduplication_key` is unique when supplied.

---

### `operational_issues`

Tracks operational problems requiring resolution.

Issue types:

```text
MISSED_PICKUP
VOLUNTEER_CANCELLATION
TRANSPORT_FAILURE
DELIVERY_REJECTED
RECEIPT_OVERDUE
ACCOUNT_SUSPENDED
```

Statuses:

```text
OPEN
RESOLVED
DISMISSED
```

Optional references can point to:

- donation
- donation request
- volunteer task
- affected user

There is an index on:

```text
(status, issue_type)
```

---

### `background_jobs`

Persistent background job records.

Current job type:

```text
SEND_NOTIFICATION
```

Statuses:

```text
PENDING
PROCESSING
SUCCEEDED
FAILED
```

The due-job index is:

```text
(status, run_after)
```

`max_attempts` must be greater than zero.

---

## 9. Recommendation / ML

### `recommendation_runs`

Represents an execution of the receiver recommendation process for a donation revision.

Algorithms:

```text
RULE_BASED_V1
RULE_BASED_V2
ML_COMPLETION_V1
```

Statuses:

```text
COMPLETED
FAILED
```

Tracks:

- donation
- revision
- requesting user
- algorithm
- model version
- weights
- considered count
- eligible count
- candidate count
- error message
- created timestamp

---

### `recommendation_evaluations`

Stores eligibility evaluation for receivers during a recommendation run.

Relationships:

```text
RecommendationRun ──< RecommendationEvaluation
User ──< RecommendationEvaluation
```

Stores:

- eligibility result
- rejection reasons
- eligibility checks
- feature snapshot
- baseline score

Baseline score, when present, must be `0..100`.

`(run, receiver)` is unique.

---

### `recommendation_candidates`

Stores ranked eligible receiver candidates.

Fields:

- `run`
- `receiver`
- `rank`
- `score`
- `approximate_distance_km`
- `remaining_capacity`
- `feature_snapshot`
- `explanations`

Constraints:

- `(run, receiver)` is unique.
- `(run, rank)` is unique.
- `score` must be `0..100`.

---

### `match_training_records`

Stores resolved donation-receiver outcomes used for model training.

Dataset sources:

```text
REAL
SYNTHETIC
PILOT
```

The model documentation explicitly states that only the saved recommendation-time feature snapshot is used as model input and outcome information is label metadata.

Important fields:

- `donation_request`
- `recommendation_evaluation`
- `dataset_source`
- `target_completed`
- `approved_at`
- `outcome_at`
- `failure_reason`
- `feature_snapshot`
- `baseline_version`
- `baseline_score`
- `recommendation_timestamp`
- `collected_at`

Constraint:

```text
outcome_at >= approved_at
```

---

## 10. Tables Referenced but Not Defined in the Supplied Source

The supplied code imports the following models, but their model definitions were not included:

```text
Complaint
AuditEvent
OutcomeCorrection
```

Therefore their fields, relationships, indexes, constraints, and database table names are intentionally not documented here.

They should be added after their actual Django model definitions are supplied.
