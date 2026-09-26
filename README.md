# SmartFood

SmartFood is an AI-assisted food redistribution platform that connects
food donors, receivers and volunteers.

## Technology Stack

- Frontend: React.js, JavaScript and Tailwind CSS
- Backend: Django and Django REST Framework
- Database: PostgreSQL
- AI/ML: Python and scikit-learn

## Requirements

Install:

- Python 3.12
- Node.js
- PostgreSQL
- Git

## Backend Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update the PostgreSQL values in `backend/.env`.

The Django project will be generated in Step 8.

## Frontend Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Basic Checks

```powershell
ruff check backend ml
black --check backend ml

npm --prefix frontend run lint
npm --prefix frontend run build
```

## Important Security Rules

Do not commit:

- `.env` files
- Database passwords
- Django secret keys
- Uploaded verification documents
- Private user information
- Real datasets
- Trained model files containing private data.

## Branches

- `main`: stable project
- `develop`: combined development work
- `feature/*`: individual features
- `fix/*`: bug fixes