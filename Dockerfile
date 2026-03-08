FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs

RUN pip install --upgrade pip \
    && pip install -e .

EXPOSE 8000

CMD ["python", "-m", "scripts.serve", "--host", "0.0.0.0", "--port", "8000"]

