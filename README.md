# 🌍 Real-Time Job Market Streaming Pipeline

> A production-grade real-time data engineering pipeline that ingests, processes, and analyzes Data Engineer job postings from 4 countries using Apache Kafka, Apache Spark Structured Streaming, PostgreSQL, and an interactive dark-mode Streamlit dashboard — fully containerized with Docker.

[![Pipeline](https://img.shields.io/badge/Pipeline-Active-brightgreen)](https://github.com/matheustrindad/realtime-job-market-streaming)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-7.4.0-black)](https://kafka.apache.org)
[![Spark](https://img.shields.io/badge/Apache_Spark-3.4-orange)](https://spark.apache.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Overview

This project is the **second chapter** of a data engineering portfolio trilogy, extending the [batch pipeline from Project 1](https://github.com/matheustrindad/global-job-market-pipeline) with real-time streaming capabilities.

While Project 1 collects and analyzes job data once per day, this pipeline processes job postings **as they arrive** — detecting salary anomalies in real time, routing invalid records to a Dead Letter Queue, and persisting results to a PostgreSQL database that feeds a live dashboard.

**Countries monitored:** 🇧🇷 Brazil · 🇺🇸 USA · 🇬🇧 United Kingdom · 🇨🇦 Canada

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│              Adzuna Jobs API (4 countries via REST)                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KAFKA PRODUCER (Python)                          │
│   Fetches jobs every 10 minutes · Publishes JSON events             │
│   Topic: job-events (3 partitions)                                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              APACHE KAFKA (Confluent 7.4.0)                         │
│   job-events ──────────────────────────► Spark Consumer             │
│   job-events-dlq ◄─────────────────────── Invalid records          │
│   Schema Registry for schema enforcement                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│          APACHE SPARK STRUCTURED STREAMING (PySpark 3.4)            │
│                                                                     │
│   1. Parse JSON events with enforced schema                         │
│   2. Fill nulls · Data quality validation                           │
│   3. Dynamic anomaly detection (salary > 3x batch average)          │
│   4. Valid records ──────────────────► PostgreSQL (job_events)      │
│   5. Invalid records (salary < 0) ──► Kafka DLQ topic               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                               │
│   Table: job_events (title, company, location, salary_min,          │
│           is_anomaly, country, job_url, timestamp)                   │
│   View: v_job_market_analysis (enriched analytical view)            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STREAMLIT DARK-MODE DASHBOARD                          │
│   KPIs · Salary trends · Anomaly alerts · Job table with links      │
│   Auto-refresh every 10–60 seconds (configurable)                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Streaming Broker | Apache Kafka (Confluent) | 7.4.0 |
| Stream Processing | Apache Spark Structured Streaming | 3.4.0 |
| Language | Python / PySpark | 3.11 |
| Database | PostgreSQL | 15 |
| Schema Management | Confluent Schema Registry | 7.4.0 |
| Dashboard | Streamlit + Plotly | Latest |
| Containerization | Docker + Docker Compose | Latest |
| Data Source | Adzuna Jobs API | REST v1 |

---

## 🔍 Engineering Highlights

### Dynamic Anomaly Detection
Instead of using a static threshold, the pipeline calculates the **average salary per micro-batch** and flags any record exceeding 3× that average as an anomaly. This self-adapts to different salary ranges across countries (BRL vs USD vs GBP).

```python
avg_row = batch_df.select(avg("salary_min")).first()
current_avg = avg_row[0] if avg_row and avg_row[0] is not None else 0

batch_df.withColumn("is_anomaly",
    when((col("salary_min") > (current_avg * 3)) & 
         (col("salary_min") > 1000), lit(True))
    .otherwise(lit(False))
)
```

### Dead Letter Queue (DLQ)
Records that fail validation (negative salary, null values) are **not discarded** — they are routed to a dedicated Kafka topic `job-events-dlq` for inspection and reprocessing. This is standard practice in production data platforms.

### Multi-Country Producer
The Kafka producer collects job postings from Brazil, USA, UK, and Canada in a single cycle, with built-in rate limiting between requests and full error handling per country.

### Stress Testing
A dedicated `stress_test.py` injects 50 synthetic job events including one salary anomaly ($95,000 against a ~$5,000 average) and one invalid record (negative salary) — proving the pipeline handles edge cases correctly.

---

## 🚀 How to Run

### Prerequisites
- Docker Desktop installed and running
- Python 3.11+
- Adzuna API credentials (free at [developer.adzuna.com](https://developer.adzuna.com))

### Step 1 — Clone and configure
```bash
git clone https://github.com/matheustrindad/realtime-job-market-streaming.git
cd realtime-job-market-streaming
cp .env.example .env
# Add your ADZUNA_APP_ID and ADZUNA_APP_KEY to .env
```

### Step 2 — Start all infrastructure
```bash
cd docker
docker-compose up -d
```

Wait ~20 seconds for all services to initialize.

### Step 3 — Create Kafka topics
```bash
docker exec kafka kafka-topics --create --topic job-events --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec kafka kafka-topics --create --topic job-events-dlq --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists
```

### Step 4 — Start the producer (Terminal 1)
```bash
cd ..
pip install -r requirements.txt
python src/producers/producer.py
```

### Step 5 — Start the Spark consumer (Terminal 2)
```bash
docker exec spark-master pkill -f consumer.py 2>/dev/null; \
docker exec spark-master rm -rf /tmp/spark-checkpoint-jobmarket; \
docker exec spark-master /opt/spark/bin/spark-submit \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0 \
  /opt/spark/work-dir/src/consumers/consumer.py
```

### Step 6 — Launch the dashboard (Terminal 3)
```bash
pip install streamlit plotly psycopg2-binary
streamlit run dashboard_streaming.py
```

Open **http://localhost:8501** in your browser.

---

## 🧪 Stress Test

To validate anomaly detection and DLQ routing with synthetic data:

```bash
python stress_test.py
```

This sends 50 events including:
- 48 normal jobs (salary $3,000–$7,000)
- 1 anomaly (salary $95,000 — will be flagged)
- 1 invalid record (salary -1 — will be sent to DLQ)

---

## 📊 Dashboard Features

- **KPI cards** — Total events, anomalies detected, average salary, unique companies
- **Market Trends** — Salary area chart over time (smooth Plotly)
- **Job Status** — Normal vs Anomaly vs No Data distribution
- **Salary Transparency** — Donut chart showing % of jobs with salary data
- **Top Companies** — Horizontal bar chart of most active hiring companies
- **Recent Postings** — Live table with clickable job links, salary, country, and timestamp
- **Search** — Filter jobs and companies in real time
- **Auto-refresh** — Configurable 5–60 second refresh interval

---

## 📁 Project Structure

```
realtime-job-market-streaming/
├── src/
│   ├── producers/
│   │   └── producer.py          # Kafka producer — multi-country API ingestion
│   └── consumers/
│       └── consumer.py          # Spark Structured Streaming consumer
├── docker/
│   └── docker-compose.yml       # Full stack: Kafka, Spark, PostgreSQL, Schema Registry
├── dashboard_streaming.py        # Dark-mode Streamlit dashboard
├── stress_test.py                # Synthetic load + anomaly injection test
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🗺️ Roadmap

- [ ] Migrate PostgreSQL to Supabase for cloud persistence
- [ ] Add Grafana dashboard as alternative to Streamlit
- [ ] Implement Avro serialization with Schema Registry enforcement
- [ ] Add windowed aggregations (5-minute salary averages)
- [ ] Extend to 6+ countries

---

## 🔗 Portfolio

This project is part of a data engineering trilogy:

| Project | Description | Stack |
|---------|-------------|-------|
| [Project 1 — Global Job Market Pipeline](https://github.com/matheustrindad/global-job-market-pipeline) | Daily batch pipeline with Medallion Architecture | Python, Pandas, PostgreSQL, GitHub Actions |
| **Project 2 — Real-Time Streaming** *(this repo)* | Real-time streaming with anomaly detection | Kafka, Spark, PostgreSQL, Streamlit |
| Project 3 — Job Market Platform *(coming soon)* | Airflow orchestration + Star Schema + FastAPI | Airflow, PySpark, FastAPI, Docker |

---

## 👤 Author

**Matheus Trindade Coimbra**
Data Engineer · Python · SQL · ETL · Apache Kafka · Apache Spark · Docker

[LinkedIn](https://linkedin.com/in/matheus-coimbra-a83010218) · [GitHub](https://github.com/matheustrindad) · [Project 1](https://github.com/matheustrindad/global-job-market-pipeline)
