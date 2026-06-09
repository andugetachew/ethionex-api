#!/bin/sh

echo "Waiting for database to be ready..."

# Wait for PostgreSQL to be ready
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Database is ready!"

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache tables (if using database cache)
python manage.py createcachetable || true

echo "Starting application..."

exec "$@"