# SmartFood

> A food donation, receiver matching, volunteer logistics, verification, and completion-prediction platform.

SmartFood connects **donors**, **receivers**, and **volunteers** through a Django-based backend, a React frontend, and an experimental machine-learning pipeline for predicting whether an approved donation-receiver match will reach confirmed completion.

The repository is organized around the application's core domains:

```text
Donations → Requests → Fulfilment → Receipt
                         │
                         └── Volunteer Logistics

Donations → Recommendation Engine → Completion Prediction
```

> **ML note:** the current completion model is trained and evaluated on synthetic data. Its reported metrics demonstrate technical pipeline feasibility and are not real-world predictive validation.

---

## ✨ Core Features

### 👤 Accounts & Participant Roles

SmartFood defines four participant roles:

```text
DONOR
RECEIVER
VOLUNTEER
ADMIN
```

The custom Django `User` model uses email as the username field and supports participant verification states:

```text
PENDING
VERIFIED
REJECTED
SUSPENDED
```

The authentication API includes:

- registration
- login
- access-token refresh
- logout
- password reset
- contact verification
- current-profile access
- administrative user listing

---

### 🍱 Food Donation Management

The donation domain supports:

- food categories
- donation creation and listing
- versioned donation revisions
- donation images
- pickup information
- use-by information
- donation status history
- donation cancellation

Donation lifecycle states include:

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

Donation revisions use the following quantity units:

```text
KG
LITRE
PORTION
PACKAGE
```

---

### 🤝 Receiver Management

Receivers can maintain:

- receiver profiles
- service areas
- food preferences
- food requirements
- receiving availability
- donation discovery

Receiver requirements track both required and already-reserved quantities.

---

### 🚚 Volunteer Logistics

SmartFood supports volunteer-assisted fulfilment with:

- volunteer profiles
- service areas
- transport capacities
- weekly availability
- eligible-task discovery
- task assignment
- pickup
- delivery
- receipt confirmation
- assignment cancellation
- failure reporting
- task history

Volunteer task states include:

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

---

### 📦 Fulfilment & Receipt

A donation can progress through the physical fulfilment chain:

```text
Donation
   ↓
Approved Request
   ↓
Handover
   ↓
Delivery (when applicable)
   ↓
Receipt Confirmation
   ↓
Completed donation
```

Receipt confirmation supports discrepancy types such as:

```text
NONE
SHORTAGE
DAMAGE
QUALITY
WRONG_ITEM
OTHER
```

---

### ✅ Verification & Moderation

The moderation domain supports:

- verification submissions
- verification documents
- verification history
- verification approval/rejection
- private verification-document download
- participant suspension
- participant deactivation
- verification reopening
- audit-event access
- donation outcome correction
- complaints and complaint review

---

### 🔔 Notifications

The notification system covers events such as:

```text
REQUEST_SUBMITTED
REQUEST_APPROVED
REQUEST_REJECTED
REQUEST_EXPIRED
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

Notifications use optional unique deduplication keys.

---

### 🧠 Recommendation & ML

SmartFood stores recommendation execution and evaluation data through:

```text
RecommendationRun
RecommendationEvaluation
RecommendationCandidate
MatchTrainingRecord
```

Supported recommendation algorithms include:

```text
RULE_BASED_V1
RULE_BASED_V2
ML_COMPLETION_V1
```

The current completion model predicts:

```text
P(approved donation-receiver match reaches confirmed completion)
```

The model is applied only after hard eligibility rules have already determined that a receiver is eligible.

---

## 🏗️ System Architecture

```text
                          SmartFood
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        React Frontend   Django Backend     ML Pipeline
             │                │                │
             │                ├── Accounts     ├── Synthetic data
             │                ├── Donations    ├── Feature processing
             │                ├── Receivers     ├── Model training
             │                ├── Logistics    ├── Evaluation
             │                ├── Moderation   └── Saved model
             │                ├── Notifications
             │                ├── Analytics
             │                └── Recommendations
             │
             └──────────────────────┬──────────────
                                    ▼
                               Database
```

### Application flow

```text
React UI
   ↓
Django URL routing
   ↓
Application views
   ↓
Business/domain logic
   ↓
Django ORM
   ↓
Database
```

The machine-learning pipeline is separated into its own `ml/` directory and consumes point-in-time recommendation features.

---

# 📁 Repository Structure

The current repository is organized approximately as follows:

```text
SmartFood/
│
├── .github/
│
├── backend/
│   ├── manage.py
│   ├── config/
│   └── apps/
│       ├── accounts/
│       ├── donations/
│       ├── receivers/
│       ├── logistics/
│       ├── moderation/
│       ├── notifications/
│       ├── analytics/
│       └── recommendations/
│
├── docs/
│   ├── api/
│   │   ├── API_ARCHITECTURE.md
│   │   ├── API_DOCUMENTATION_NOTES.md
│   │   ├── API_ENDPOINT_REFERENCE.md
│   │   └── API_ROUTES_CURRENT.md
│   │
│   ├── database/
│   │   ├── DATABASE_DOCUMENTATION_CORRECTIONS.md
│   │   ├── DATABASE_SCHEMA_CURRENT.md
│   │   ├── ENUMS_AND_CONSTRAINTS.md
│   │   └── TABLES_AND_RELATIONSHIPS.md
│   │
│   ├── diagrams/
│   │   └── DATABASE_ER_DIAGRAM.md
│   │
│   ├── ml-training-dataset.md
│   └── ...
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── config/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── routes/
│   │   └── services/
│   ├── package.json
│   ├── vite.config.js
│   └── ...
│
├── ml/
│   ├── data/
│   │   ├── processed/
│   │   └── synthetic/
│   ├── evaluation/
│   ├── models/
│   ├── notebooks/
│   ├── training/
│   │   ├── generate_synthetic_data.py
│   │   └── train_model.py
│   ├── ml.md
│   └── requirements.txt
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
└── README.md
```

Additional development/cache folders may exist locally, such as `.ruff_cache` and frontend build/test output.

---

# 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| Database access | Django ORM |
| Backend routing | Django URL configuration |
| Frontend | React |
| Frontend tooling | Vite |
| ML | Python / scikit-learn |
| ML model | Logistic Regression (selected current model) |
| Alternative model | Random Forest |
| Model artifact | `joblib` |
| Data processing | pandas / NumPy |
| ML evaluation | scikit-learn metrics |
| Charts | Matplotlib |
| Authentication | Django account/authentication implementation |
| File handling | Django media/file storage |

---

# 🔌 API

## Base Prefix

The current project URL configuration mounts application APIs below:

```text
/api/
```

with domain-specific prefixes for some applications.

### Main API prefixes

```text
/api/
├── auth/
/api/profiles/
/api/admin/
/api/verifications/
/api/verification-documents/
/api/complaints/

/api/donations/

/api/receivers/

/api/logistics/

/api/notifications/

/api/analytics/

/api/recommendations/

/api/health/
```

---

## API Health Check

```text
GET /api/health/
```

The health check performs a database connectivity query.

Successful response:

```json
{
  "status": "healthy",
  "application": "SmartFood API",
  "database": "connected"
}
```

Database failure response:

```json
{
  "status": "unhealthy",
  "application": "SmartFood API",
  "database": "disconnected"
}
```

The failure response uses HTTP `503`.

---

## Authentication Endpoints

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
```

---

## Donation Endpoints

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

---

## Receiver Endpoints

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

---

## Logistics Endpoints

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

The supplied URL configuration intentionally places the volunteer-task catch-all route after the named task actions.

---

## Moderation Endpoints

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

---

## Notifications

```text
/api/notifications/
/api/notifications/mark-all-read/
/api/notifications/<uuid:notification_id>/read/
```

---

## Analytics

```text
/api/analytics/
```

---

## Recommendations

```text
/api/recommendations/donations/<uuid:donation_id>/
```

---

## Complete API Documentation

See:

- [`docs/api/API_ROUTES_CURRENT.md`](docs/api/API_ROUTES_CURRENT.md)
- [`docs/api/API_ENDPOINT_REFERENCE.md`](docs/api/API_ENDPOINT_REFERENCE.md)
- [`docs/api/API_ARCHITECTURE.md`](docs/api/API_ARCHITECTURE.md)
- [`docs/api/API_DOCUMENTATION_NOTES.md`](docs/api/API_DOCUMENTATION_NOTES.md)

The route documentation intentionally distinguishes URL-level facts from details that require the actual view and serializer implementations.

---

# 🗄️ Database

SmartFood's Django models define a relational domain covering:

```text
Accounts
Food categories
Donations
Donation revisions
Donation requests
Donation images
Donation status history
Handover
Delivery
Receipt confirmation
Receivers
Service areas
Receiver preferences
Receiver requirements
Receiver availability
Volunteers
Volunteer capacity
Volunteer availability
Volunteer tasks
Volunteer task history
Volunteer failure reports
Verification
Notifications
Operational issues
Background jobs
Recommendations
ML training records
```

The supplied model definitions use UUID primary keys for these business entities.

Important integrity rules include:

```text
One current donation revision per donation
One approved request per donation
One active request per receiver/donation
Positive donation quantities
Valid pickup time windows
Positive handover/delivery quantities
Receiver requirement quantity limits
Unique receiver preferences
Unique volunteer capacity per unit
Unique recommendation candidates/ranks
Chronological training outcomes
```

### Database Documentation

- [`docs/database/DATABASE_SCHEMA_CURRENT.md`](docs/database/DATABASE_SCHEMA_CURRENT.md)
- [`docs/database/TABLES_AND_RELATIONSHIPS.md`](docs/database/TABLES_AND_RELATIONSHIPS.md)
- [`docs/database/ENUMS_AND_CONSTRAINTS.md`](docs/database/ENUMS_AND_CONSTRAINTS.md)
- [`docs/database/DATABASE_DOCUMENTATION_CORRECTIONS.md`](docs/database/DATABASE_DOCUMENTATION_CORRECTIONS.md)
- [`docs/diagrams/DATABASE_ER_DIAGRAM.md`](docs/diagrams/DATABASE_ER_DIAGRAM.md)

---

# 🖥️ Frontend

The frontend is a React application using Vite-based project tooling.

The supplied project structure contains:

```text
frontend/
└── src/
    ├── api/
    ├── assets/
    ├── auth/
    ├── components/
    ├── config/
    ├── features/
    ├── hooks/
    ├── lib/
    ├── pages/
    ├── routes/
    └── services/
```

## Frontend responsibilities

The visible page structure is organized around:

```text
Admin
Auth
Donor
Receiver
Shared
Volunteer
```

Examples visible in the project include:

```text
Admin
├── AdminComplaintsPage
└── AdminPages

Auth
└── LoginPage

Donor
├── CreateDonationPage
├── DonationRequestsPage
├── DonorPage
└── ReceiverRecommendationsPage

Receiver
├── BrowseDonationsPage
└── ReceiverPages

Shared
├── AnalyticsPage
├── ComplaintsPage
├── DirectFulfillmentPage
├── ProfilePage
└── SharedPages

Volunteer
├── DashboardPage
├── FeatureVolunteerPage
├── LoginPage
├── NotFoundPage
└── UnauthorizedPage
```

The repository also contains shared API/error utilities under `src/lib/` and API-related code under `src/api/`.

---

# 🤖 Machine Learning

## Objective

The current ML system predicts whether an **approved donation-receiver match** will reach confirmed completion.

```text
Eligible receiver
       ↓
Approved match
       ↓
Point-in-time recommendation features
       ↓
Completion prediction model
       ↓
Predicted probability
```

Eligibility remains controlled by the application's business rules.

---

## Current ML Dataset

Current active training source:

```text
SYNTHETIC
```

Synthetic dataset:

```text
ml/data/synthetic/smartfood_synthetic_matches.csv
```

Dataset version:

```text
synthetic-1.0
```

Rows:

```text
3000
```

Distribution:

```text
Completed     2108
Not completed  892
```

---

## Input Features

### Numeric

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

### Categorical

```text
category_name
unit
```

---

## Leakage Prevention

The model explicitly excludes outcome and identity fields such as:

```text
target_completed
failure_reason
approved_at
outcome_at
baseline_score
donation_id
donation_request_id
receiver_id
recommendation_timestamp
```

Only recommendation-time feature snapshots are intended to become model inputs.

---

## Data Split

The supplied training implementation uses:

```text
70% Train
15% Validation
15% Test
```

with chronological ordering grouped by:

```text
donation_id
```

Current split:

| Split | Rows | Completed | Not completed |
|---|---:|---:|---:|
| Train | 2100 | 1481 | 619 |
| Validation | 450 | 317 | 133 |
| Test | 450 | 310 | 140 |

---

## Models

Current candidate models:

```text
Logistic Regression
Random Forest
```

The current selected artifact is:

```text
logistic_regression
```

Model version:

```text
completion-model-1.0
```

Selection rule:

```text
Lowest validation Brier score,
then highest validation F1
```

---

## Current Test Metrics

### Logistic Regression

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

### Rule-based baseline

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

These values are from the supplied synthetic-data evaluation artifacts.

---

## ML Artifacts

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
├── notebooks/
│
├── training/
│   ├── generate_synthetic_data.py
│   └── train_model.py
│
├── ml.md
└── requirements.txt
```

Detailed ML documentation:

[`ml/ml.md`](ml/ml.md)

---

# 🔄 Major Application Workflows

## 1. Donation → Receiver Request

```text
Donor
  ↓
Create donation
  ↓
Donation available
  ↓
Receiver discovers donation
  ↓
Receiver submits request
  ↓
Donor reviews request
  ↓
Approve / reject / withdraw / cancel arrangement
```

---

## 2. Direct Fulfilment

```text
Approved request
      ↓
Handover confirmation
      ↓
Delivery record (when applicable)
      ↓
Receipt confirmation
      ↓
Donation completion
```

---

## 3. Volunteer Fulfilment

```text
Approved request
      ↓
Volunteer task
      ↓
Task eligible
      ↓
Volunteer accepts
      ↓
Arrives at donor
      ↓
Pickup
      ↓
Arrives at receiver
      ↓
Delivery
      ↓
Receipt confirmation
      ↓
Task completion
```

Failure/cancellation routes are available throughout the task workflow.

---

## 4. Recommendation + ML

```text
Donation
   ↓
Eligibility rules
   ↓
Recommendation run
   ↓
Receiver evaluation
   ↓
Ranked candidates
   ↓
Approved match
   ↓
Completion probability
   ↓
Resolved outcome
   ↓
Training record
```

The training record keeps recommendation-time features separate from later outcome information.

---

# 🔐 Security & Data Integrity

The architecture contains several safeguards through Django models and application boundaries.

### Authentication

Participant accounts use a custom Django `User` model with email as the login identifier.

### Verification

Participants have explicit verification states and the moderation application provides verification review workflows.

### File handling

Donation images and verification documents are stored through Django file fields. Verification documents use a private verification storage implementation in the supplied model source.

### Database integrity

Django `UniqueConstraint` and `CheckConstraint` definitions enforce important business rules at the data layer.

### Auditability

The moderation API includes audit-event access, and donation/verification/volunteer status histories provide historical lifecycle records.

---

# 🧪 Testing

The repository contains a dedicated:

```text
tests/
```

directory.

Testing should cover at least:

```text
Authentication
Authorization
Donation lifecycle
Request lifecycle
Handover/delivery/receipt
Volunteer tasks
Verification
Notifications
Recommendations
ML data validation
ML training/evaluation
```

For the ML pipeline, the training code already validates:

- required columns
- target classes
- minimum record count
- donation IDs
- recommendation timestamps
- forbidden model inputs
- chronological transaction separation

---

# ⚙️ Local Development

## Backend

The backend is a Django project under:

```text
backend/
```

Start from the backend directory and use the project's configured Python environment and dependencies.

Typical Django development command:

```bash
cd backend
python manage.py runserver
```

The authoritative command should follow the project's current environment/dependency setup.

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend uses Vite tooling.

---

## ML

Install the ML dependencies:

```bash
cd ml
pip install -r requirements.txt
```

Generate synthetic training data using the project's generator:

```bash
python training/generate_synthetic_data.py
```

Train and evaluate the current models:

```bash
python training/train_model.py
```

The training script can also accept:

```text
--dataset
--model-directory
--evaluation-directory
```

---

# 🌍 Environment Configuration

Project environment templates are present at the repository root:

```text
.env
.env.example
```

Secrets and environment-specific values should remain outside source control.

The exact environment variables should be taken from the current backend/frontend configuration rather than duplicated here when they change.

---

# 📚 Documentation Map

```text
docs/
├── api/
│   ├── API_ARCHITECTURE.md
│   ├── API_DOCUMENTATION_NOTES.md
│   ├── API_ENDPOINT_REFERENCE.md
│   └── API_ROUTES_CURRENT.md
│
├── database/
│   ├── DATABASE_DOCUMENTATION_CORRECTIONS.md
│   ├── DATABASE_SCHEMA_CURRENT.md
│   ├── ENUMS_AND_CONSTRAINTS.md
│   └── TABLES_AND_RELATIONSHIPS.md
│
├── diagrams/
│   └── DATABASE_ER_DIAGRAM.md
│
└── ml-training-dataset.md
```

---

# 📌 Current Project Structure

```text
SmartFood/
│
├── .github/
├── backend/
├── docs/
├── frontend/
├── ml/
├── tests/
│
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚠️ Current Limitations

### ML

The current completion model is trained on synthetic data.

Therefore:

```text
Synthetic evaluation
≠
Real-world validation
```

The model should be documented and presented as an experimental predictive prototype until evaluated on appropriate real transaction data.

### API documentation

The current `docs/api/` files are based on the supplied URL configurations. Exact serializer fields, HTTP methods, permissions, and response schemas should be documented from the corresponding view/serializer implementations.

### External model definitions

The supplied database source references models such as:

```text
Complaint
AuditEvent
OutcomeCorrection
```

without providing their complete model definitions. Their full database schema should therefore be taken from the actual source before extending database documentation.

---

# 🗺️ Development Roadmap

The project documentation can continue to evolve in these areas:

```text
Database
   ↓
ER diagrams
   ↓
Complete API contract
   ↓
Frontend route documentation
   ↓
Workflow diagrams
   ↓
Testing documentation
   ↓
Security review
   ↓
ML/data validation
   ↓
Production deployment
```

For the ML component specifically:

```text
Synthetic data
      ↓
Real resolved transactions
      ↓
Validated point-in-time features
      ↓
Leakage checks
      ↓
Chronological evaluation
      ↓
Calibration/monitoring
      ↓
Versioned production model
```

---

# 📄 License

Add the project's final license information here.

---

# 👥 Contributors

Add the project contributors/maintainers here.

---

## SmartFood at a Glance

```text
                ┌───────────────────┐
                │       DONOR       │
                └─────────┬─────────┘
                          │
                          ▼
                    ┌───────────┐
                    │ Donation  │
                    └─────┬─────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Recommendation│
                  └───────┬───────┘
                          │
                          ▼
                ┌───────────────────┐
                │     RECEIVER      │
                └─────────┬─────────┘
                          │
                          ▼
                    ┌───────────┐
                    │  Request  │
                    └─────┬─────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
     Direct Fulfilment          Volunteer Task
             │                         │
             └────────────┬────────────┘
                          ▼
                      Handover
                          │
                          ▼
                       Delivery
                          │
                          ▼
                  Receipt Confirmation
                          │
                          ▼
                      COMPLETED
                          │
                          ▼
                Match Training Record
```

---

## Documentation Status

The repository currently includes documentation for:

```text
✓ Database schema
✓ Tables and relationships
✓ Enums and constraints
✓ Database ER diagram
✓ API route inventory
✓ API endpoint reference
✓ API architecture
✓ API documentation notes
✓ ML pipeline and evaluation
✓ ML training dataset documentation
```

The root `README.md` is intended to provide the high-level entry point to these project areas.
