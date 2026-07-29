#!/bin/sh

set -e

echo "Waiting for PostgreSQL on $DB_HOST:$DB_PORT..."

while ! python -c "import socket; s=socket.socket(); s.connect(('$DB_HOST', $DB_PORT)); s.close()" 2>/dev/null; do
    echo "PostgreSQL not ready - waiting..."
    sleep 1
done

echo "PostgreSQL ready - continuing..."

python manage.py collectstatic --noinput
python manage.py migrate

python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")
EOF

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120