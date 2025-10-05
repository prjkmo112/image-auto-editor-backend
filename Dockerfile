FROM python:3.12-slim AS base

WORKDIR /iae

RUN pip install uv

COPY pyproject.toml ./
COPY uv.lock ./

FROM base AS builder

RUN uv sync --frozen --no-dev

FROM base AS runtime

RUN useradd -m -u 10001 appuser

ENV VIRTUAL_ENV=/iae/.venv
ENV PATH=/iae/.venv/bin:$PATH

ENV CORS_ALLOW_ORIGINS=http://localhost:5432
ENV DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/image_auto_editor
ENV SAVED_IMG_DIR=./images

COPY --from=builder /iae/.venv /iae/.venv

COPY app /iae/app
COPY alembic /iae/alembic
COPY alembic.ini /iae/alembic.ini

RUN chmod -R 755 /iae
RUN chown -R appuser:appuser /iae

USER appuser

RUN mkdir "/iae/logs"

EXPOSE 8000

ENTRYPOINT ["/iae/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]