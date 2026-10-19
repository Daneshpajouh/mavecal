# Runtime for the workflow and tests. Base image pinned by digest (python:3.13-slim,
# pulled 2026-10-19); Python packages pinned in pyproject.toml.
FROM python@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/mave-clinvar-calibration
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[dev]"

COPY . .
RUN useradd --create-home analyst && chown -R analyst /opt/mave-clinvar-calibration
USER analyst

# Mount the data directory and pass -e MAVECAL_DATA_DIR=/data (see README).
ENTRYPOINT ["snakemake"]
CMD ["--profile", "profiles/local"]
