# SmartFood API Architecture

## 1. URL Routing Architecture

The supplied project uses a central Django URL configuration that delegates groups of routes to application-specific URL modules.

```text
                    SmartFood Django Project
                              │
                              ▼
                       Root urlpatterns
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
     /api/health/          /api/                 /api/donations/
          │                   │                    │
          ▼                   ├── accounts         ▼
      health_check            └── moderation     donations
                              │
                              ├── /api/receivers/
                              ├── /api/logistics/
                              ├── /api/notifications/
                              ├── /api/analytics/
                              └── /api/recommendations/
```

---

## 2. Application API Modules

### Accounts

Responsibilities represented by route names and views:

```text
Authentication
Session/token operations
Password reset
Contact verification
Current profile
Administrative user listing
```

### Donations

Responsibilities:

```text
Food categories
Donation creation/listing/detail
Donation revisions
Donation images
Donation lifecycle actions
Donation history
Donation requests
```

### Receivers

Responsibilities:

```text
Service areas
Receiver profile
Food preferences
Food requirements
Receiving availability
Donation discovery
```

### Logistics

Responsibilities:

```text
Direct fulfilment
Handover
Delivery
Receipt confirmation
Volunteer profile
Volunteer capacities
Volunteer availability
Volunteer task discovery
Volunteer task lifecycle
Volunteer failure reporting
```

### Moderation

Responsibilities:

```text
Verification
Verification history
Verification decisions
Verification document download
Participant suspension/deactivation
Verification reopening
Audit events
Donation outcome correction
Complaints
Complaint review
```

### Notifications

Responsibilities:

```text
Notification listing
Mark all read
Mark one notification read
```

### Analytics

Responsibilities:

```text
Analytics
```

### Recommendations

Responsibilities:

```text
Donation-specific recommendations
```

---

## 3. Fulfilment API Flow

The route structure supports a donation fulfilment flow:

```text
Donation
   │
   ▼
Donation Request
   │
   ├───────────────┐
   │               │
   ▼               ▼
Direct fulfilment  Volunteer fulfilment
   │               │
   ▼               ▼
Handover       Volunteer Task
   │               │
   ▼               ├── Accept
Delivery           ├── Pickup
   │               ├── Delivery
   ▼               ├── Confirm Receipt
Receipt            └── Failure / Cancellation
```

This represents route organization only; exact business-state transitions should be verified from the corresponding view/service implementations.

---

## 4. Recommendation API Flow

The supplied route exposes recommendation generation for a donation:

```text
/api/recommendations/
        │
        ▼
/donations/<donation_id>/
        │
        ▼
DonationRecommendationView
```

The corresponding database models record recommendation runs, evaluations, candidates, and training outcomes.

---

## 5. Verification API Flow

```text
/api/verifications/
        │
        ├── list/create
        ├── history
        ├── detail
        ├── approve
        └── reject

/api/verification-documents/
        │
        └── download
```

Administrative participant actions are exposed under:

```text
/api/admin/users/
```

Audit and donation-outcome administration are also under the moderation URL module.

---

## 6. Volunteer Task Routing

The volunteer task routes contain explicit named actions:

```text
tasks/<task_id>/accept/
tasks/<task_id>/pickup/
tasks/<task_id>/delivery/
tasks/<task_id>/confirm-receipt/
tasks/<task_id>/cancel-assignment/
tasks/<task_id>/report-failure/
```

A generic route follows these named routes:

```text
tasks/<task_id>/<action>/
```

The supplied comment states that the catch-all status route is intentionally placed after the named task-action routes.

This ordering should be retained when editing the URL configuration.

