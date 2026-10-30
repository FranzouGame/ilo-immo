FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml .
COPY app ./app
RUN pip install -e ".[dev]"
COPY alembic.ini .
COPY alembic ./alembic
COPY tests ./tests
