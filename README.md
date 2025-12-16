# EPA---Team-Rota-Management-System
This project will develop a web-based application to streamline team availability and rota management, replacing inefficient spreadsheet-based processes. The system will store staff availability in a central database, provide a user-friendly calendar view, and allow team members to update their schedules.

## Getting started

1. Create and activate a virtual environment with Python 3.10 or later.
2. Install dependencies: `pip install -r requirements.txt`.
3. Apply migrations and create a superuser:
   - `python manage.py migrate`
   - `python manage.py createsuperuser`
4. Run the development server: `python manage.py runserver`.

The project uses SQLite by default (configured in `teamrota/settings.py`), so no additional database setup is required for local development.
