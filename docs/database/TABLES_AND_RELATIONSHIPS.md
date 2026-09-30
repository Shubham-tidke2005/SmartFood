# SmartFood Tables & Relationships

> Derived from the supplied Django model definitions.

## Entity Relationship Overview

```text
                         ┌─────────────────┐
                         │  accounts_user  │
                         │     User        │
                         └───────┬─────────┘
                                 │
              ┌──────────────────┼─────────────────────┐
              │                  │                     │
              ▼                  ▼                     ▼
       ReceiverProfile    VolunteerProfile      VerificationSubmission
              │                  │                     │
              ▼                  ▼                     ▼
        ServiceArea       VolunteerCapacity    VerificationDocument
              │                  │
              │                  ▼
              │           VolunteerAvailability
              │
              ▼
       ReceiverPreference
              │
              ▼
       ReceiverRequirement
              │
              ▼
       ReceiverAvailability


FoodCategory
     │
     └───────────────┐
                     ▼
              DonationRevision
                     │
                     ▼
                  Donation
                 /   |    \
                /    |     \
               ▼     ▼      ▼
       DonationRequest  StatusHistory  RecommendationRun
              │                         │
              │                         ├── Evaluations
              │                         └── Candidates
              │
       ┌──────┼──────────────┐
       ▼      ▼              ▼
   Handover Delivery     VolunteerTask
       │      │              │
       └──────┴──────┐       ├── TaskHistory
                     │       └── FailureReports
                     ▼
             ReceiptConfirmation

RecommendationEvaluation
           │
           ▼
     MatchTrainingRecord
```

---

## Relationship Matrix

| Parent | Child | Cardinality | Child field |
|---|---|---:|---|
| User | Donation | 1:N | `donor` |
| User | DonationRevision | 1:N | `proposed_by` |
| FoodCategory | DonationRevision | 1:N | `category` |
| Donation | DonationRevision | 1:N | `donation` |
| Donation | DonationRequest | 1:N | `donation` |
| User | DonationRequest | 1:N | `receiver` |
| DonationRevision | DonationRequest | 1:N | `requested_revision` |
| DonationRevision | DonationImage | 1:N | `revision` |
| Donation | DonationStatusHistory | 1:N | `donation` |
| User | DonationStatusHistory | 1:N | `actor` |
| Donation | HandoverRecord | 1:1 | `donation` |
| DonationRequest | HandoverRecord | 1:1 | `donation_request` |
| DonationRevision | HandoverRecord | 1:N | `revision` |
| User | HandoverRecord | 1:N | `confirmed_by` |
| Donation | DeliveryRecord | 1:1 | `donation` |
| DonationRequest | DeliveryRecord | 1:1 | `donation_request` |
| HandoverRecord | DeliveryRecord | 1:1 | `handover` |
| User | DeliveryRecord | 1:N | `delivered_by` |
| Donation | ReceiptConfirmation | 1:1 | `donation` |
| DonationRequest | ReceiptConfirmation | 1:1 | `donation_request` |
| HandoverRecord | ReceiptConfirmation | 1:1 | `handover` |
| DeliveryRecord | ReceiptConfirmation | 0..1:1 | `delivery` |
| User | ReceiptConfirmation | 1:N | `confirmed_by` |
| ServiceArea | ReceiverProfile | 1:N | `service_area` |
| User | ReceiverProfile | 1:1 | `user` |
| User | ReceiverPreference | 1:N | `receiver` |
| FoodCategory | ReceiverPreference | 1:N | `category` |
| User | ReceiverRequirement | 1:N | `receiver` |
| FoodCategory | ReceiverRequirement | 1:N | `category` |
| User | ReceiverAvailability | 1:N | `receiver` |
| User | VolunteerProfile | 1:1 | `user` |
| ServiceArea | VolunteerProfile | 1:N | `service_area` |
| User | VolunteerCapacity | 1:N | `volunteer` |
| User | VolunteerAvailability | 1:N | `volunteer` |
| Donation | VolunteerTask | 1:1 | `donation` |
| DonationRequest | VolunteerTask | 1:1 | `donation_request` |
| User | VolunteerTask | 0..N | `assigned_volunteer` |
| ServiceArea | VolunteerTask | 0..N | `pickup_service_area` |
| ServiceArea | VolunteerTask | 1:N | `receiver_service_area` |
| VolunteerTask | VolunteerTaskHistory | 1:N | `task` |
| User | VolunteerTaskHistory | 0..N | `actor` |
| VolunteerTask | VolunteerFailureReport | 1:N | `task` |
| User | VolunteerFailureReport | 1:N | `volunteer` |
| User | VerificationSubmission | 1:N | `user` |
| User | VerificationSubmission | 0..N | `reviewer` |
| VerificationSubmission | VerificationDocument | 1:N | `submission` |
| User | VerificationHistory | 1:N | `user` |
| VerificationSubmission | VerificationHistory | 0..N | `submission` |
| User | VerificationHistory | 1:N | `actor` |
| User | Notification | 1:N | `recipient` |
| Donation | OperationalIssue | 0..N | `donation` |
| DonationRequest | OperationalIssue | 0..N | `donation_request` |
| VolunteerTask | OperationalIssue | 0..N | `volunteer_task` |
| User | OperationalIssue | 0..N | `affected_user` |
| Donation | RecommendationRun | 1:N | `donation` |
| DonationRevision | RecommendationRun | 1:N | `revision` |
| User | RecommendationRun | 1:N | `requested_by` |
| RecommendationRun | RecommendationEvaluation | 1:N | `run` |
| User | RecommendationEvaluation | 1:N | `receiver` |
| RecommendationRun | RecommendationCandidate | 1:N | `run` |
| User | RecommendationCandidate | 1:N | `receiver` |
| DonationRequest | MatchTrainingRecord | 1:1 | `donation_request` |
| RecommendationEvaluation | MatchTrainingRecord | 1:N | `recommendation_evaluation` |

---

## Important One-to-One Relationships

The following are explicitly represented with `OneToOneField`:

```text
User ──1 ReceiverProfile
User ──1 VolunteerProfile

Donation ──1 HandoverRecord
DonationRequest ──1 HandoverRecord

Donation ──1 DeliveryRecord
DonationRequest ──1 DeliveryRecord
HandoverRecord ──1 DeliveryRecord

Donation ──1 ReceiptConfirmation
DonationRequest ──1 ReceiptConfirmation
HandoverRecord ──1 ReceiptConfirmation
DeliveryRecord ──0..1 ReceiptConfirmation

Donation ──1 VolunteerTask
DonationRequest ──1 VolunteerTask

DonationRequest ──1 MatchTrainingRecord
```

---

## Lifecycle Relationship

The main donation lifecycle represented by the schema is:

```text
Donation
   │
   ├── current DonationRevision
   │
   ├── DonationRequest
   │       │
   │       └── approved request
   │
   ├── HandoverRecord
   │
   ├── DeliveryRecord (when delivery occurs)
   │
   ├── ReceiptConfirmation
   │
   └── DonationStatusHistory
```

Volunteer-assisted delivery additionally introduces:

```text
Donation
   │
   └── VolunteerTask
           │
           ├── VolunteerTaskHistory
           └── VolunteerFailureReport
```

---

## Recommendation Relationship

```text
Donation
   │
   └── RecommendationRun
          │
          ├── RecommendationEvaluation
          │       │
          │       └── MatchTrainingRecord
          │
          └── RecommendationCandidate
```

The recommendation run stores the algorithm/model version and execution-level counts.

The evaluation stores eligibility and feature snapshots.

The candidate stores ranked results and explanations.

The training record stores the later resolved outcome.
