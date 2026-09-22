# Cloud Run image for the Dash application.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/web_app

WORKDIR /app/web_app

COPY web_app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# The app imports its local assets, case-study data, and GeoRepo cache at
# startup. Credentials and .env files are excluded by .dockerignore and must
# be supplied through Cloud Run secrets/environment configuration.
COPY web_app/ ./
COPY schema/ /app/schema/
COPY case_studies/ /app/case_studies/
RUN mkdir -p credentials

# Cloud Run provides PORT. One worker keeps the Earth Engine/Dash caches within
# one process; Cloud Run can scale out to additional instances as needed.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 300 app:server"]
