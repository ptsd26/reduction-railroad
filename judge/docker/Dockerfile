
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Add the official isolate package repository.
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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
