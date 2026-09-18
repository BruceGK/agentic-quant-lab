FROM ghcr.io/astral-sh/uv:0.12.13@sha256:b485bd65cc2cf1c9a93b3554012c9c3778cf7b1b5fd3d3096ce9e1226c97e1e6 AS uv
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
COPY research/__init__.py research/engine.py research/
RUN uv sync --locked --no-dev --no-editable --no-cache --compile-bytecode

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
ARG RECORDER_GIT_SHA=""
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RECORDER_GIT_SHA="$RECORDER_GIT_SHA"
RUN groupadd --gid 10001 recorder \
    && useradd --uid 10001 --gid 10001 --no-create-home recorder \
    && mkdir /data \
    && chown 10001:10001 /data
COPY --from=build /opt/venv /opt/venv
USER 10001:10001
WORKDIR /data
ENTRYPOINT ["quant-recorder"]
CMD ["record"]
