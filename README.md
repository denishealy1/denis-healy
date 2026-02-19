# European Era Mobility Portal (Malaga)

Django MVP for managing Erasmus mobility end-to-end.

## Stack
- Django + PostgreSQL
- Bootstrap 5 templates
- Local media uploads (`/media`)
- pytest + pytest-django
- Docker Compose for PostgreSQL

## Setup
1. Copy env:
   ```bash
   cp .env.example .env
   ```
2. Create venv and install dependencies:
   ```bash
   make setup
   ```
3. Start PostgreSQL:
   ```bash
   docker compose up -d
   ```
4. Run migrations:
   ```bash
   make migrate
   ```
5. Seed demo data:
   ```bash
   make seed
   ```
6. Run server:
   ```bash
   make run
   ```



## Windows + Docker Desktop (one command)
Open **PowerShell** in the repo root and run:
```powershell
./scripts/setup_windows.ps1
```
This script will:
- create `.venv`
- install Python dependencies
- start PostgreSQL (`docker compose up -d`)
- run migrations
- seed demo data
- start Django at `http://localhost:8000/`

If script execution is blocked, run once in PowerShell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## App links (local)
After `make run`, open:
- Main entry: `http://localhost:8000/`
- Login page: `http://localhost:8000/accounts/login/`
- Admin dashboard (after admin login): `http://localhost:8000/admin-portal/`
- Partner dashboard (after partner login): `http://localhost:8000/partner/`
- Student dashboard (after student login): `http://localhost:8000/student/`

Spanish URLs also work with `/es/` prefix, for example `http://localhost:8000/es/accounts/login/`.

## Demo users
- `admin@example.com` / `AdminPass123!`
- `partner@example.com` / `PartnerPass123!`
- `student@example.com` / `StudentPass123!`

## Environment variables
See `.env.example`.

## Tests
```bash
make test
```

## i18n (EN/ES)
- Update messages:
  ```bash
  django-admin makemessages -l es
  ```
- Compile translations:
  ```bash
  django-admin compilemessages
  ```

## Storage
Files are stored locally in `media/` for MVP. To swap to S3 later, configure Django storage backend (e.g., `django-storages` + boto3), set `DEFAULT_FILE_STORAGE`, and provide bucket credentials.

## Notes
- Invite sending is stubbed: links are shown in UI and logged in server logs.
- Payment integration intentionally omitted; extension points are in place via service-style views.
