# FastAPI Backend

This backend currently implements the platform foundation and the first labour module:

- FastAPI application bootstrap
- SQLAlchemy session management
- SQLite connection
- Alembic scaffolding
- JWT authentication
- User registration and login
- User management for organization admins
- Worker management
- Attendance management
- Payroll management
- Reporting and exports

## Folder Structure

```text
backend/
+-- alembic/
|   +-- env.py
|   +-- script.py.mako
|   `-- versions/
+-- src/
|   +-- api/
|   |   +-- routes/
|   |   +-- deps.py
|   |   `-- router.py
|   +-- core/
|   |   +-- config.py
|   |   `-- security.py
|   +-- database/
|   |   +-- base.py
|   |   +-- models.py
|   |   `-- __init__.py
|   +-- db/
|   |   `-- session.py
|   +-- schemas/
|   |   +-- auth.py
|   |   +-- user.py
|   |   `-- __init__.py
|   +-- services/
|   |   +-- auth.py
|   |   +-- users.py
|   |   `-- __init__.py
|   +-- main.py
|   `-- __init__.py
+-- .env.example
+-- alembic.ini
`-- requirements.txt
```

## Run

Install dependencies and run from the `backend` directory:

```bash
uvicorn src.main:app --reload
```

## Alembic

Generate a migration:

```bash
alembic revision --autogenerate -m "init"
```

Apply migrations:

```bash
alembic upgrade head
```

## Development seed data

The development-only seed script resets only the organization with code `demo` and creates deterministic sample data:

- Demo Construction Company
- Admin and supervisor users
- 3 construction sites
- 75 workers across Mason, Helper, Carpenter, Electrician, and Plumber categories
- Attendance for the last 30 days
- Current-month payroll, advances, partial and pending payments
- Labour, material, and site expenses

Run it from the `backend` directory:

```bash
python scripts/seed_dev_data.py
```

It is repeatable and intended for the local development SQLite database only. The demo credentials are:

```text
Admin:      admin@example.com / password123
Supervisor: supervisor@example.com / password123
Organization code: demo
```
