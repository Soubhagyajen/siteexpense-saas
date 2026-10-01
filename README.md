# SiteExpense SaaS

MVP for construction and MEP site expense control.

## Workflow
Founder creates an advance -> Manager/Engineer records expenses -> expenses are submitted -> Founder reviews -> monthly reconciliation.

## Stack
- Django
- SQLite for MVP
- Django Templates
- Tailwind CDN

## Run
```
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

Open http://127.0.0.1:8000/

Create the first admin user with:
```
python manage.py createsuperuser
```

Then create Users, Profiles, and Projects from /admin/.

## Core rule
Advance Received - Approved Expenses = Remaining Advance.
