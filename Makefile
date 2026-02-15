setup:
	python -m pip install -r requirements.txt

migrate:
	python manage.py migrate

seed:
	python manage.py seed_demo

run:
	python manage.py runserver

test:
	pytest
