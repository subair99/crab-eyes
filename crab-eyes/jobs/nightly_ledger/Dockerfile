# Nebius Serverless Job image: runs once, updates the ledger, exits.
# Build from the repo root: docker build -f jobs/nightly_ledger/Dockerfile -t crab-eyes-ledger .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY jobs ./jobs
COPY routing.yaml ./
CMD ["uv", "run", "--no-dev", "python", "-m", "jobs.nightly_ledger.run"]
