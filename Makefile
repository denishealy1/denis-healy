setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
migrate:
	python manage.py makemigrations && python manage.py migrate
seed:
	python manage.py seed_demo
run:
	python manage.py runserver
test:
	pytest
