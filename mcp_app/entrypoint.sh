#!/bin/sh
echo "Waiting for database ($POSTGRES_HOST:$POSTGRES_PORT)..."

until python - <<PY
import os, sys, psycopg2, time
host=os.getenv('POSTGRES_HOST','db')
port=int(os.getenv('POSTGRES_PORT',5432))
user=os.getenv('POSTGRES_USER','mcp_user')
password=os.getenv('POSTGRES_PASSWORD','mcp_pass')
db=os.getenv('POSTGRES_DB','mcp_db')
try:
    conn=psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db, connect_timeout=2)
    conn.close()
    print("db ready")
except Exception as e:
    print("db not ready:", e)
    sys.exit(1)
PY
do
    echo "Database not ready, retrying in 1 sec..."
    sleep 1
done

# Run migrations and collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "$DJANGO_DEBUG" = "True" ] || [ "$DJANGO_DEBUG" = "true" ] || [ "$DJANGO_DEBUG" = "1" ]; then
  echo "Starting development server..."
  python manage.py runserver 0.0.0.0:8000
else
  echo "Starting Gunicorn..."
  exec gunicorn mcp_app.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
