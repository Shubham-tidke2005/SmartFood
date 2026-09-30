# SmartFood API Documentation Notes

## Source Scope

The current API documentation was generated from the Django URL configurations supplied for the project.

The route configuration identifies URL paths, namespaces, route names, path converters, and referenced view classes.

It does not by itself establish the full API contract.

---

## Details Still Requiring View/Serializer Source

The following should be documented after the corresponding source is supplied:

### HTTP methods

URL declarations using class-based views do not reveal the complete method implementation.

The exact method set should be taken from each view class.

### Authentication and permissions

The route definitions do not show:

- authentication classes
- permission classes
- role restrictions
- object-level authorization
- anonymous/public access

These should be taken from the view and permission code.

### Request schemas

The URL definitions do not show serializer/input structures.

Document request fields from the corresponding serializers or request parsing code.

### Response schemas

Document response bodies from the actual views/serializers.

### Error responses

Document exact error status codes and response structures from implementation and tests.

---

## Important Routing Details

### Root prefix

The supplied root configuration uses:

```text
/api/
```

for accounts and moderation.

Other applications have dedicated prefixes:

```text
/api/donations/
/api/receivers/
/api/logistics/
/api/notifications/
/api/analytics/
/api/recommendations/
```

### Django admin

The standard Django admin site is mounted at:

```text
/admin/
```

### Health check

The application health endpoint is:

```text
/api/health/
```

It performs a database connectivity query.

### Debug media serving

When `settings.DEBUG` is true, the project appends Django's static media-serving URL patterns using:

```text
settings.MEDIA_URL
settings.MEDIA_ROOT
```

This is development/debug routing, not a production API contract.

---

## Route Naming

The supplied application modules declare:

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

Django route names should be maintained when adding documentation examples or reverse URL lookups.

---

## Catch-All Volunteer Route

The volunteer URL module contains:

```text
volunteer/tasks/<uuid:task_id>/<str:action>/
```

and explicitly comments:

```text
Keep the catch-all status transition after every named task action.
```

This ordering is part of the supplied routing design and should not be changed casually.

---

## Documentation Corrections

### Do not document implied HTTP methods

Names such as:

```text
ListCreateView
ApproveView
ConfirmView
```

suggest intended behavior, but this file does not convert those names into unverified method claims.

### Do not invent request/response examples

Request JSON, response JSON, status codes, pagination, filtering, and validation should be added only from the corresponding source code.

### Do not invent role permissions

The presence of an `/admin/` URL does not, by itself, document the permission implementation.

The moderation and account administration endpoints should be paired with their permission/authentication source before publishing a complete security/API contract.

---

## Missing Source for Complete API Documentation

For a full API reference, additionally inspect:

```text
views.py
admin_views.py
request_views.py
volunteer_views.py
audit_views.py
complaint_views.py
serializers.py
permissions.py
authentication code
services/
tests/
```

The URL files supplied here are sufficient for route inventory, but not for a complete request/response API specification.
