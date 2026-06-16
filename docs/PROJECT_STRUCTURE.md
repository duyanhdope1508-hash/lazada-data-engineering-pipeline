# Project Structure

This repository has been reorganized to follow a professional data engineering layout.

## Source And Pipeline

- `src/`: core Python pipeline modules.
- `src/main.py`: pipeline scheduler/orchestrator.
- `src/tiki_etl.py`: extraction from Lazada API and PostgreSQL loading.
- `src/kafka_producer/`: Kafka producer logic.
- `src/spark_consumer/`: Spark Structured Streaming logic.
- `src/metrics/`: metrics helpers.

## Data And Schemas

- `data/raw/`: checked-in raw/sample CSV/JSON inputs.
- `sql/postgres/`: PostgreSQL schema and seed scripts.
- `sql/cassandra/`: Cassandra schema scripts.

## Infrastructure

- `docker-compose.yml`: local infrastructure stack.
- `monitoring/`: Prometheus/Grafana dashboards, alert rules, and dashboard SQL.
- `config/`: config files for Hadoop, Kafka, Spark, PostgreSQL, and Kerberos.
- `nifi/`, `superset/`: local service mount points used by Docker Compose.

## Documentation

- `docs/reports/`: final/project PDF reports.
- `docs/requirements/`: school/regulation documents.
- `docs/templates/`: Word templates and outlines.
- `docs/images/project-screenshots/`: diagrams and screenshots used in the report.

## Generated Artifacts

- `runtime/`: logs, caches, Spark/Hadoop runtime folders, checkpoints, and egg metadata.
- `tools/`: local IDE/tool files such as DataGrip metadata.
