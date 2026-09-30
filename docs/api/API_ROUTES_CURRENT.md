# SmartFood API Routes — Current

## Purpose

This document records the current SmartFood API URL structure from the supplied Django `urls.py` files.

The project uses Django URL routing with application-level URL modules included from the root project URL configuration.

> **Source of truth:** the URL configuration supplied for this documentation task.
>
> **Scope:** paths, prefixes, namespaces, route names, path parameters, and referenced view classes.
>
> HTTP methods, serializers, request bodies, response schemas, authentication permissions, and validation behavior are not inferred because the corresponding view definitions were not supplied.

---

## 1. Root Project URL Configuration

The supplied project URL configuration defines these top-level routes:

| Prefix / Path | Included configuration |
|---|---|
| `admin/` | Django admin site |
| `api/health/` | `config.views.health_check` |
| `api/` | `apps.accounts.urls` |
| `api/donations/` | `apps.donations.urls` |
| `api/` | `apps.moderation.urls` |
| `api/receivers/` | `apps.receivers.urls` |
| `api/logistics/` | `apps.logistics.urls` |
| `api/notifications/` | `apps.notifications.urls` |
| `api/analytics/` | `apps.analytics.urls` |
| `api/recommendations/` | `apps.recommendations.urls` |

When `DEBUG` is enabled, Django also serves configured media files using:

```text
settings.MEDIA_URL
settings.MEDIA_ROOT
```

---

# 2. Health API

## `GET /api/health/`

View:

```text
config.views.health_check
```

The supplied implementation executes:

```sql
SELECT 1
```

against the configured database connection.

### Healthy response

The supplied code returns HTTP `200` with:

```json
{
  "status": "healthy",
  "application": "SmartFood API",
  "database": "connected"
}
```

### Unhealthy response

When the database check raises an exception, the supplied code returns HTTP `503` with:

```json
{
  "status": "unhealthy",
  "application": "SmartFood API",
  "database": "disconnected"
}
```

---

# 3. Accounts API

Included at:

```text
/api/
```

Namespace:

```text
accounts
```

## Authentication and profile routes

| Full path | View | Route name |
|---|---|---|
| `POST? /api/auth/csrf/` | `CsrfTokenView` | `csrf` |
| `POST? /api/auth/register/` | `RegistrationView` | `register` |
| `POST? /api/auth/login/` | `LoginView` | `login` |
| `POST? /api/auth/refresh/` | `RefreshAccessTokenView` | `refresh` |
| `POST? /api/auth/logout/` | `LogoutView` | `logout` |
| `POST? /api/auth/password-reset/` | `PasswordResetRequestView` | `password-reset` |
| `POST? /api/auth/password-reset/confirm/` | `PasswordResetConfirmView` | `password-reset-confirm` |
| `POST? /api/auth/contact-verification/confirm/` | `ContactVerificationConfirmView` | `contact-verification-confirm` |
| `POST? /api/auth/contact-verification/resend/` | `ContactVerificationResendView` | `contact-verification-resend` |
| `GET/POST? /api/profiles/me/` | `MyProfileView` | `my-profile` |
| `GET? /api/admin/users/` | `AdminUserListView` | `admin-user-list` |

> The `?` notation above intentionally indicates that the HTTP method was not supplied by the URL configuration itself. Consult each view class for the authoritative method list.

---

# 4. Donations API

Included at:

```text
/api/donations/
```

Namespace:

```text
donations
```

## Food categories

```text
/api/donations/food-categories/
```

View:

```text
FoodCategoryListView
```

Route name:

```text
food-category-list
```

## Donation collection

```text
/api/donations/
```

View:

```text
DonationListCreateView
```

Route name:

```text
list-create
```

## Donation requests

```text
/api/donations/requests/
```

View:

```text
DonationRequestListView
```

Route name:

```text
request-list
```

### Withdraw request

```text
/api/donations/requests/<uuid:request_id>/withdraw/
```

View:

```text
DonationRequestWithdrawView
```

Route name:

```text
request-withdraw
```

### Approve request

```text
/api/donations/requests/<uuid:request_id>/approve/
```

View:

```text
DonationRequestApproveView
```

Route name:

```text
request-approve
```

### Reject request

```text
/api/donations/requests/<uuid:request_id>/reject/
```

View:

```text
DonationRequestRejectView
```

Route name:

```text
request-reject
```

### Cancel arrangement

```text
/api/donations/requests/<uuid:request_id>/cancel-arrangement/
```

View:

```text
DonationArrangementCancelView
```

Route name:

```text
arrangement-cancel
```

## Donation detail

```text
/api/donations/<uuid:donation_id>/
```

View:

```text
DonationDetailView
```

Route name:

```text
detail
```

## Donation revision

```text
/api/donations/<uuid:donation_id>/revisions/
```

View:

```text
DonationRevisionCreateView
```

Route name:

```text
revision-create
```

## Donation images

```text
/api/donations/<uuid:donation_id>/images/
```

View:

```text
DonationImageUploadView
```

Route name:

```text
image-upload
```

## Cancel donation

```text
/api/donations/<uuid:donation_id>/cancel/
```

View:

```text
DonationCancelView
```

Route name:

```text
cancel
```

## Donation history

```text
/api/donations/<uuid:donation_id>/history/
```

View:

```text
DonationHistoryView
```

Route name:

```text
history
```

## Create donation request for a donation

```text
/api/donations/<uuid:donation_id>/requests/
```

View:

```text
DonationRequestCreateView
```

Route name:

```text
request-create
```

---

# 5. Moderation API

Included at:

```text
/api/
```

Namespace:

```text
moderation
```

## Verification

| Full path | View | Route name |
|---|---|---|
| `/api/verifications/` | `VerificationListCreateView` | `verification-list-create` |
| `/api/verifications/history/` | `VerificationHistoryView` | `verification-history` |
| `/api/verifications/<uuid:submission_id>/` | `VerificationDetailView` | `verification-detail` |
| `/api/verifications/<uuid:submission_id>/approve/` | `ApproveVerificationView` | `verification-approve` |
| `/api/verifications/<uuid:submission_id>/reject/` | `RejectVerificationView` | `verification-reject` |
| `/api/verification-documents/<uuid:document_id>/download/` | `VerificationDocumentDownloadView` | `document-download` |

## Participant administration

```text
/api/admin/users/<uuid:user_id>/suspend/
```

View:

```text
SuspendParticipantView
```

Route name:

```text
participant-suspend
```

```text
/api/admin/users/<uuid:user_id>/deactivate/
```

View:

```text
ParticipantDeactivateView
```

Route name:

```text
participant-deactivate
```

```text
/api/admin/users/<uuid:user_id>/reopen-verification/
```

View:

```text
ReopenParticipantVerificationView
```

Route name:

```text
participant-reopen
```

## Audit

```text
/api/admin/audit-events/
```

View:

```text
AuditEventListView
```

Route name:

```text
audit-event-list
```

## Donation outcome correction

```text
/api/admin/donations/<uuid:donation_id>/correct-outcome/
```

View:

```text
DonationOutcomeCorrectionView
```

Route name:

```text
donation-outcome-correction
```

## Complaints

```text
/api/complaints/
```

View:

```text
ComplaintListCreateView
```

Route name:

```text
complaint-list-create
```

```text
/api/complaints/<uuid:complaint_id>/
```

View:

```text
ComplaintDetailView
```

Route name:

```text
complaint-detail
```

```text
/api/complaints/<uuid:complaint_id>/review/
```

View:

```text
ComplaintAdminUpdateView
```

Route name:

```text
complaint-review
```

---

# 6. Receiver API

Included at:

```text
/api/receivers/
```

Namespace:

```text
receivers
```

| Full path | View | Route name |
|---|---|---|
| `/api/receivers/service-areas/` | `ServiceAreaListView` | `service-area-list` |
| `/api/receivers/profile/` | `ReceiverProfileView` | `profile` |
| `/api/receivers/preferences/` | `ReceiverPreferenceListCreateView` | `preference-list-create` |
| `/api/receivers/preferences/<uuid:preference_id>/` | `ReceiverPreferenceDetailView` | `preference-detail` |
| `/api/receivers/requirements/` | `ReceiverRequirementListCreateView` | `requirement-list-create` |
| `/api/receivers/requirements/<uuid:requirement_id>/` | `ReceiverRequirementDetailView` | `requirement-detail` |
| `/api/receivers/availability/` | `ReceiverAvailabilityListCreateView` | `availability-list-create` |
| `/api/receivers/availability/<uuid:availability_id>/` | `ReceiverAvailabilityDetailView` | `availability-detail` |
| `/api/receivers/discover-donations/` | `ReceiverDonationDiscoveryView` | `discover-donations` |

---

# 7. Logistics API

Included at:

```text
/api/logistics/
```

Namespace:

```text
logistics
```

## Direct fulfilment

```text
/api/logistics/donations/<uuid:donation_id>/
```

View:

```text
DirectFulfilmentDetailView
```

Route name:

```text
direct-fulfilment-detail
```

### Handover

```text
/api/logistics/donations/<uuid:donation_id>/handover/
```

View:

```text
HandoverConfirmView
```

Route name:

```text
handover-confirm
```

### Delivery record

```text
/api/logistics/donations/<uuid:donation_id>/delivery/
```

View:

```text
DirectDeliveryRecordView
```

Route name:

```text
delivery-record
```

### Receipt confirmation

```text
/api/logistics/donations/<uuid:donation_id>/receipt/
```

View:

```text
ReceiptConfirmView
```

Route name:

```text
receipt-confirm
```

---

## Volunteer profile and configuration

```text
/api/logistics/volunteer/profile/
```

View:

```text
VolunteerProfileView
```

Route name:

```text
volunteer-profile
```

```text
/api/logistics/volunteer/capacities/
```

View:

```text
VolunteerCapacityListCreateView
```

Route name:

```text
volunteer-capacities
```

```text
/api/logistics/volunteer/availability/
```

View:

```text
VolunteerAvailabilityListCreateView
```

Route name:

```text
volunteer-availability
```

---

## Volunteer tasks

### Eligible tasks

```text
/api/logistics/volunteer/tasks/eligible/
```

View:

```text
EligibleVolunteerTaskListView
```

Route name:

```text
eligible-tasks
```

### My tasks

```text
/api/logistics/volunteer/tasks/mine/
```

View:

```text
MyVolunteerTaskListView
```

Route name:

```text
my-tasks
```

### Accept

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/accept/
```

View:

```text
VolunteerTaskAcceptView
```

Route name:

```text
task-accept
```

### Pickup

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/pickup/
```

View:

```text
VolunteerPickupView
```

Route name:

```text
task-pickup
```

### Delivery

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/delivery/
```

View:

```text
VolunteerDeliveryView
```

Route name:

```text
task-delivery
```

### Confirm receipt

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/confirm-receipt/
```

View:

```text
VolunteerReceiptConfirmView
```

Route name:

```text
task-receipt
```

### Cancel assignment

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/cancel-assignment/
```

View:

```text
VolunteerCancelAssignmentView
```

Route name:

```text
assignment-cancel
```

### Report failure

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/report-failure/
```

View:

```text
VolunteerFailureReportView
```

Route name:

```text
task-failure
```

### Generic status transition

```text
/api/logistics/volunteer/tasks/<uuid:task_id>/<str:action>/
```

View:

```text
VolunteerTaskStatusView
```

Route name:

```text
task-status
```

The supplied URL configuration explicitly places this catch-all status route **after** the named task-action routes.

---

# 8. Notifications API

Included at:

```text
/api/notifications/
```

Namespace:

```text
notifications
```

| Full path | View | Route name |
|---|---|---|
| `/api/notifications/` | `NotificationListView` | `list` |
| `/api/notifications/mark-all-read/` | `NotificationMarkAllReadView` | `mark-all-read` |
| `/api/notifications/<uuid:notification_id>/read/` | `NotificationMarkReadView` | `mark-read` |

---

# 9. Analytics API

Included at:

```text
/api/analytics/
```

Namespace:

```text
analytics
```

## Analytics

```text
/api/analytics/
```

View:

```text
AnalyticsView
```

Route name:

```text
analytics
```

---

# 10. Recommendations API

Included at:

```text
/api/recommendations/
```

Namespace:

```text
recommendations
```

## Donation recommendations

```text
/api/recommendations/donations/<uuid:donation_id>/
```

View:

```text
DonationRecommendationView
```

Route name:

```text
donation-recommendations
```

---

# 11. API Route Inventory

The supplied URL configurations expose these application route groups:

```text
/api/
├── auth/
├── profiles/
├── admin/
├── verifications/
├── verification-documents/
└── complaints/

/api/donations/
├── food-categories/
├── requests/
└── <donation_id>/

/api/receivers/
├── service-areas/
├── profile/
├── preferences/
├── requirements/
├── availability/
└── discover-donations/

/api/logistics/
├── donations/
└── volunteer/

/api/notifications/
├──
├── mark-all-read/
└── <notification_id>/read/

/api/analytics/
└──

/api/recommendations/
└── donations/

/api/health/
```

---

# 12. Path Parameter Types

The supplied routes use these path parameters:

| Parameter | Django converter | Meaning |
|---|---|---|
| `request_id` | `uuid` | Donation request identifier |
| `donation_id` | `uuid` | Donation identifier |
| `submission_id` | `uuid` | Verification submission identifier |
| `document_id` | `uuid` | Verification document identifier |
| `user_id` | `uuid` | User identifier |
| `complaint_id` | `uuid` | Complaint identifier |
| `preference_id` | `uuid` | Receiver preference identifier |
| `requirement_id` | `uuid` | Receiver requirement identifier |
| `availability_id` | `uuid` | Receiver availability identifier |
| `task_id` | `uuid` | Volunteer task identifier |
| `notification_id` | `uuid` | Notification identifier |
| `action` | `str` | Generic volunteer task action |

---

# 13. URL Namespaces

The supplied application URL modules declare:

```text
accounts
analytics
donations
logistics
moderation
notifications
receivers
recommendations
```

These namespaces are useful when reversing or referring to routes using Django URL names.

---

# 14. Route Documentation Boundary

This file intentionally does not claim:

- exact HTTP methods for each view
- authentication requirements
- role/permission rules
- serializer names
- request body fields
- query parameters
- response JSON schemas
- status codes beyond the explicitly supplied health-check implementation
- pagination behavior
- throttling/rate limiting
- filtering/sorting semantics

Those details require the relevant view classes, serializers, permissions, and service code.

