
FROM python:3.14-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install Isolate and the C++ compiler.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl g++ binutils \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://www.ucw.cz/isolate/debian/signing-key.asc \
       -o /etc/apt/keyrings/isolate.asc \
    && printf '%s\n' \
       'deb [arch=amd64 signed-by=/etc/apt/keyrings/isolate.asc] http://www.ucw.cz/isolate/debian/ bookworm-isolate main' \
       > /etc/apt/sources.list.d/isolate.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends isolate \
    && rm -rf /var/lib/apt/lists/*

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the Python project and install its dependencies.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "--no-sync", "judge"]
