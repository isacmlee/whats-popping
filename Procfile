web: gunicorn main:app
worker: celery worker -A tasks.app -l INFO
