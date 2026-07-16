FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir .

COPY profiles.yml .
COPY dbt_project.yml .
COPY analyses analyses
COPY macros macros
COPY models models
COPY seeds seeds
COPY snapshots snapshots
COPY tests tests

CMD ["sh", "-c", "dbt seed && dbt run && dbt test && dbt docs generate && dbt docs serve --host 0.0.0.0"]
