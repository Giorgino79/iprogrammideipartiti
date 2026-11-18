release: python manage.py migrate --noinput && python manage.py carica_esempio --solo-se-vuoto
web: gunicorn config.wsgi --log-file -
