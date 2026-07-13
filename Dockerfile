ARG PYTHON_BASE=python:3.12-slim@sha256:5072b08ad74609c5329ab4085a96dfa873de565fb4751a4cfcd7dcc427661df0
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823

FROM ${UV_IMAGE} AS uv-bin

FROM ${PYTHON_BASE} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=uv-bin /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --frozen --no-dev --extra mineru

FROM ${PYTHON_BASE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEWSDOM_MINERU_BIN=mineru \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --home-dir /home/newsdom --shell /usr/sbin/nologin newsdom

COPY --from=builder --chown=newsdom:newsdom /app /app

USER newsdom

EXPOSE 8000

CMD ["uvicorn", "newsdom_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
