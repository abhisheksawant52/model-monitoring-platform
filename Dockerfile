# syntax=docker/dockerfile:1

# ---- Builder stage -----------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

# Build a wheel and install it into an isolated prefix.
RUN python -m pip install --upgrade pip build \
    && python -m build --wheel --outdir /wheels \
    && pip install --prefix=/install /wheels/*.whl

# ---- Runtime stage -----------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MM_HOST=0.0.0.0 \
    MM_PORT=8000

# Create a non-root user.
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /install /usr/local

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["model-monitoring"]
