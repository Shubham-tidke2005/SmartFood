# SmartFood Enums & Database Constraints

> Derived from the supplied Django model definitions.

## 1. User Enums

### User.Role

```text
DONOR
RECEIVER
VOLUNTEER
ADMIN
```

### User.VerificationStatus

```text
PENDING
VERIFIED
REJECTED
SUSPENDED
```

---

## 2. Donation Enums

### Donation.Status

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

### DonationRevision.Unit

```text
KG
LITRE
PORTION
PACKAGE
```

### DonationRequest.Status

```text
PENDING
APPROVED
REJECTED
WITHDRAWN
EXPIRED
CANCELLED
```

### DonationRequest.TransportMode

```text
RECEIVER_COLLECTION
DONOR_DELIVERY
VOLUNTEER_DELIVERY
```

---

## 3. Receipt Enums

### ReceiptConfirmation.DiscrepancyType

```text
NONE
SHORTAGE
DAMAGE
QUALITY
WRONG_ITEM
OTHER
```

---

## 4. Volunteer Enums

### VolunteerProfile.AvailabilityStatus

```text
AVAILABLE
UNAVAILABLE
BUSY
```

### VolunteerAvailability.Weekday

```text
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
```

### VolunteerTask.Status

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

### VolunteerFailureReport.Stage

```text
BEFORE_PICKUP
AFTER_PICKUP
```

---

## 5. Receiver Enums

### ReceiverAvailability.Weekday

```text
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
```

---

## 6. Verification Enums

### VerificationSubmission.Status

```text
PENDING
APPROVED
REJECTED
```

### VerificationDocument.DocumentType

```text
IDENTITY
ORGANIZATION_REGISTRATION
ADDRESS_PROOF
OTHER
```

### VerificationHistory.Action

```text
SUBMITTED
APPROVED
REJECTED
SUSPENDED
REOPENED
```

---

## 7. Notification Enums

### Notification.Type

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

---

## 8. Operational Enums

### OperationalIssue.IssueType

```text
MISSED_PICKUP
VOLUNTEER_CANCELLATION
TRANSPORT_FAILURE
DELIVERY_REJECTED
RECEIPT_OVERDUE
ACCOUNT_SUSPENDED
```

### OperationalIssue.Status

```text
OPEN
RESOLVED
DISMISSED
```

### BackgroundJob.JobType

```text
SEND_NOTIFICATION
```

### BackgroundJob.Status

```text
PENDING
PROCESSING
SUCCEEDED
FAILED
```

---

## 9. Recommendation / ML Enums

### RecommendationRun.Status

```text
COMPLETED
FAILED
```

### RecommendationRun.Algorithm

```text
RULE_BASED_V1
RULE_BASED_V2
ML_COMPLETION_V1
```

### MatchTrainingRecord.DatasetSource

```text
REAL
SYNTHETIC
PILOT
```

---

# Database Constraints

## Donation Revision

### Unique revision number

```text
(donation, number) UNIQUE
```

### One current revision

Only one revision can have:

```text
is_current = TRUE
```

per donation.

### Positive quantity

```text
quantity > 0
```

### Valid pickup window

```text
pickup_deadline > pickup_starts_at
```

---

## Donation Requests

### One active request per receiver and donation

For statuses:

```text
PENDING
APPROVED
```

the pair is unique:

```text
(donation, receiver)
```

### One approved request per donation

Only one request for a donation may have:

```text
status = APPROVED
```

---

## Donation Images

Image position is unique within a revision:

```text
(revision, position) UNIQUE
```

---

## Handover

```text
actual_quantity > 0
```

---

## Delivery

```text
actual_quantity > 0
```

---

## Receipt Confirmation

```text
accepted_quantity >= 0
```

---

## Volunteer Profile

```text
max_service_distance_km > 0
max_active_tasks > 0
```

---

## Volunteer Capacity

```text
(volunteer, unit) UNIQUE
maximum_quantity > 0
```

---

## Volunteer Availability

```text
(volunteer, weekday, starts_at, ends_at) UNIQUE
```

---

## Volunteer Task

```text
required_quantity > 0
```

---

## Receiver Preference

```text
(receiver, category) UNIQUE
```

---

## Receiver Requirement

```text
(receiver, category, unit) UNIQUE

quantity_needed > 0
quantity_reserved >= 0
quantity_reserved <= quantity_needed
```

---

## Receiver Availability

```text
(receiver, weekday, starts_at, ends_at) UNIQUE
```

---

## Service Area

```text
code UNIQUE
name UNIQUE
latitude ∈ [-90, 90]
longitude ∈ [-180, 180]
```

---

## Verification Submission

```text
(user, attempt) UNIQUE
```

Only one pending submission per user:

```text
user UNIQUE WHERE status = PENDING
```

And:

```text
attempt > 0
```

---

## Notification

```text
deduplication_key UNIQUE
```

The field is nullable, so multiple null values remain possible under normal database unique-null behavior.

---

## Operational Issue

```text
deduplication_key UNIQUE
```

Index:

```text
(status, issue_type)
```

---

## Background Job

```text
deduplication_key UNIQUE
max_attempts > 0
```

Index:

```text
(status, run_after)
```

---

## Recommendation Evaluation

```text
(run, receiver) UNIQUE
```

Baseline score, when supplied:

```text
0 <= baseline_score <= 100
```

Index:

```text
(run, eligible)
```

---

## Recommendation Candidate

```text
(run, receiver) UNIQUE
(run, rank) UNIQUE
0 <= score <= 100
```

Index:

```text
(run, rank)
```

---

## Match Training Record

Outcome must not precede approval:

```text
outcome_at >= approved_at
```

Baseline score, when supplied:

```text
0 <= baseline_score <= 100
```

Indexes:

```text
(dataset_source, target_completed)
(approved_at)
```

---

# Delete Behavior

The supplied models predominantly use:

```text
on_delete = PROTECT
```

for core business records.

This means referenced records are protected from deletion when dependent records exist.

Some recommendation relationships use:

```text
on_delete = CASCADE
```

Specifically:

```text
RecommendationRun → RecommendationEvaluation
RecommendationRun → RecommendationCandidate
```

Thus deleting a recommendation run cascades to its evaluations and candidates.

