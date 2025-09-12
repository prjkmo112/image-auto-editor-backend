FROM python:3.12-slim AS base

RUN alembic upgrade head

RUN useradd -m -u 10001 appuser

WORKDIR /iae

COPY app /iae/app
COPY alembic /iae/alembic
COPY alembic.ini /app/alembic.ini

# entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

#HEALTHCHECK

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]