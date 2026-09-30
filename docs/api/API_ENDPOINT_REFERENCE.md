# SmartFood API Endpoint Reference

## Endpoint Catalog

### Accounts

```text
/api/auth/csrf/
/api/auth/register/
/api/auth/login/
/api/auth/refresh/
/api/auth/logout/
/api/auth/password-reset/
/api/auth/password-reset/confirm/
/api/auth/contact-verification/confirm/
/api/auth/contact-verification/resend/
/api/profiles/me/
/api/admin/users/
```

### Donations

```text
/api/donations/food-categories/
/api/donations/
/api/donations/requests/
/api/donations/requests/<uuid:request_id>/withdraw/
/api/donations/requests/<uuid:request_id>/approve/
/api/donations/requests/<uuid:request_id>/reject/
/api/donations/requests/<uuid:request_id>/cancel-arrangement/
/api/donations/<uuid:donation_id>/
/api/donations/<uuid:donation_id>/revisions/
/api/donations/<uuid:donation_id>/images/
/api/donations/<uuid:donation_id>/cancel/
/api/donations/<uuid:donation_id>/history/
/api/donations/<uuid:donation_id>/requests/
```

### Moderation

```text
/api/verifications/
/api/verifications/history/
/api/verifications/<uuid:submission_id>/
/api/verifications/<uuid:submission_id>/approve/
/api/verifications/<uuid:submission_id>/reject/
/api/verification-documents/<uuid:document_id>/download/
/api/admin/users/<uuid:user_id>/suspend/
/api/admin/users/<uuid:user_id>/deactivate/
/api/admin/users/<uuid:user_id>/reopen-verification/
/api/admin/audit-events/
/api/admin/donations/<uuid:donation_id>/correct-outcome/
/api/complaints/
/api/complaints/<uuid:complaint_id>/
/api/complaints/<uuid:complaint_id>/review/
```

### Receivers

```text
/api/receivers/service-areas/
/api/receivers/profile/
/api/receivers/preferences/
/api/receivers/preferences/<uuid:preference_id>/
/api/receivers/requirements/
/api/receivers/requirements/<uuid:requirement_id>/
/api/receivers/availability/
/api/receivers/availability/<uuid:availability_id>/
/api/receivers/discover-donations/
```

### Logistics

```text
/api/logistics/donations/<uuid:donation_id>/
/api/logistics/donations/<uuid:donation_id>/handover/
/api/logistics/donations/<uuid:donation_id>/delivery/
/api/logistics/donations/<uuid:donation_id>/receipt/
/api/logistics/volunteer/profile/
/api/logistics/volunteer/capacities/
/api/logistics/volunteer/availability/
/api/logistics/volunteer/tasks/eligible/
/api/logistics/volunteer/tasks/mine/
/api/logistics/volunteer/tasks/<uuid:task_id>/accept/
/api/logistics/volunteer/tasks/<uuid:task_id>/pickup/
/api/logistics/volunteer/tasks/<uuid:task_id>/delivery/
/api/logistics/volunteer/tasks/<uuid:task_id>/confirm-receipt/
/api/logistics/volunteer/tasks/<uuid:task_id>/cancel-assignment/
/api/logistics/volunteer/tasks/<uuid:task_id>/report-failure/
/api/logistics/volunteer/tasks/<uuid:task_id>/<str:action>/
```

### Notifications

```text
/api/notifications/
/api/notifications/mark-all-read/
/api/notifications/<uuid:notification_id>/read/
```

### Analytics

```text
/api/analytics/
```

### Recommendations

```text
/api/recommendations/donations/<uuid:donation_id>/
```

### Health

```text
/api/health/
```

---

## Route Naming Convention

Each application URL module defines a Django `app_name` and assigns a route `name` to each URL.

Examples:

```text
accounts:login
donations:list-create
donations:request-approve
logistics:task-accept
notifications:mark-read
recommendations:donation-recommendations
```

These names are based on the supplied `app_name` and `name` declarations.

