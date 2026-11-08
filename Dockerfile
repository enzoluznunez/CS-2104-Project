# Seeking Pips container: Flask app served by gunicorn on port 5000.
FROM python:3.12-slim

# No .pyc files, and logs go straight to `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

# Install dependencies first so Docker can cache this layer between builds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY code/ code/
COPY data/ data/
COPY tests/ tests/
COPY pytest.ini .

# Run as a non-root user; instance/ holds the SQLite database.
RUN useradd --create-home app && mkdir instance && chown app instance
USER app

EXPOSE 5000
# --preload builds the database once, before the workers start. `exec` makes
# gunicorn the main process so `docker stop` shuts it down cleanly.
CMD exec gunicorn --chdir code --bind 0.0.0.0:$PORT --workers 2 --preload "app:create_app()"
