FROM python:3.13-slim

ARG SERVICE_PATH
ARG WSGI_MODULE

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WSGI_MODULE=${WSGI_MODULE}

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_PATH}/requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt

COPY ${SERVICE_PATH}/ ./

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app

USER app
EXPOSE 8080

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn \"$WSGI_MODULE\" --bind \"0.0.0.0:${PORT:-8080}\" --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -"]
