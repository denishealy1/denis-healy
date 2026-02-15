# European Era Mobility Portal (Malaga)

Django MVP for Erasmus mobility operations with EN/ES multilingual UI, RBAC, onboarding, placement, logistics, and certificate generation.

## Setup
1. Create venv and activate.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy env:
   - `cp .env.example .env`

## Postgres via Docker
- `docker-compose up -d`

## Environment variables
See `.env.example` for required values (`POSTGRES_*`, `DJANGO_SECRET_KEY`, etc.).

## Run migrations and seed
- `python manage.py migrate`
- `python manage.py seed_demo`

Demo users:
- `admin@example.com / AdminPass123!`
- `partner@example.com / PartnerPass123!`
- `student@example.com / StudentPass123!`

## Run app
- `python manage.py runserver`

## Tests
- `pytest`

## Translations
- Extract messages: `django-admin makemessages -l es`
- Update translations in `locale/es/LC_MESSAGES/django.po`
- Compile: `django-admin compilemessages`

## Storage notes
MVP stores uploads in local `/media`. For production, switch `DEFAULT_FILE_STORAGE` to S3 backend (`django-storages`) and configure bucket credentials.

## Payments extension point
No payment in MVP. Add a new `billing` app and payment provider webhooks later.

## WordPress/Hosting integration
Portal is standalone and ready to deploy at a subdomain (e.g., `portal.example.org`) and link from WordPress.
