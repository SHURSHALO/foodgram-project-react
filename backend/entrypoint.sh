#!/bin/bash

docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend sh -c "cp -r /app/collected_static/. /backend_static/static/"
docker compose exec backend python import_ingredients.py
docker compose exec backend python import_tags.py
docker compose exec backend python manage.py createsuperuser