$ErrorActionPreference = 'Stop'

Write-Host '== European Era Mobility Portal Windows setup ==' -ForegroundColor Cyan

if (!(Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example'
}

if (!(Test-Path '.venv')) {
    py -3 -m venv .venv
    Write-Host 'Created virtual environment at .venv'
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

docker compose up -d

python manage.py migrate
python manage.py seed_demo

Write-Host 'Starting Django dev server at http://localhost:8000/' -ForegroundColor Green
python manage.py runserver
