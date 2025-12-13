# Real-Time Crypto Data Pipeline

A streaming data pipeline that ingests cryptocurrency market data, buffers it through Kafka, stores it in MongoDB, and runs daily aggregations via Airflow.

## Why this exists

This project demonstrates a realistic approach to building data pipelines for time-series data at moderate scale. It's designed to handle 100+ requests per minute while maintaining data quality and query performance.

The goal is not high-frequency trading data or millisecond latency—it's a pragmatic pipeline for tracking market trends with 30-second granularity.

## Why these tools

**MongoDB**: Chosen for flexible schema during development and native support for time-series access patterns. The raw collection uses compound indexes (`coin_id`, `timestamp`) to efficiently query price history for specific coins. Aggregated data lives in a separate collection to avoid mixing analytical queries with real-time writes.

**Kafka**: Decouples data ingestion from storage. If MongoDB is slow or down, the producer keeps running and Kafka buffers messages. The consumer can catch up when things recover. This separation also makes it easier to add new consumers later (e.g., for real-time alerts) without touching the producer.

**Airflow**: Runs the daily aggregation job at 1 AM UTC. It's overkill for a single task, but represents what you'd actually use in a production environment where you have multiple batch jobs with dependencies.

## Architecture

```
CoinGecko API → Producer (validation) → Kafka → Consumer → MongoDB (raw)
                                                              ↓
                                          Airflow DAG → Aggregation → MongoDB (daily)
```

Data flow:
1. Producer fetches from CoinGecko every 30 seconds
2. Validates required fields and filters bad data
3. Publishes to Kafka topic with 3 partitions
4. Consumer writes to `market_data_raw` collection
5. Airflow runs nightly to compute 24-hour stats and writes to `market_data_daily`

## Document design

**Raw documents** (market_data_raw):
```json
{
  "timestamp": "2025-01-15T14:30:00.000Z",
  "coin_id": "bitcoin",
  "symbol": "btc",
  "current_price": 43250.12,
  "market_cap": 846000000000,
  "total_volume": 28500000000,
  ...
}
```

**Aggregated documents** (market_data_daily):
```json
{
  "coin_id": "bitcoin",
  "date": "2025-01-15",
  "avg_price": 43180.45,
  "min_price": 42800.00,
  "max_price": 43600.00,
  "data_points": 2880
}
```

Tradeoff: We duplicate coin metadata (symbol, name) in every raw document rather than normalizing into a separate collection. This costs storage but makes queries faster since we don't need joins. At 50 coins × 2,880 records/day × 100 bytes = ~14MB/day, storage is cheap enough that query speed wins.

## Setup

**Prerequisites:**
- Python 3.9+
- Docker & Docker Compose
- MongoDB Atlas account (or local MongoDB)

**Installation:**

```bash
# Clone and install dependencies
git clone <repo>
cd crypto-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB Atlas URI

# Start Kafka locally
docker-compose up -d

# Create Kafka topic
python scripts/setup_kafka.py
```

**Running:**

```bash
# Terminal 1: Start producer
python src/ingestion/producer.py

# Terminal 2: Start consumer
python src/storage/consumer.py

# For Airflow (separate setup required):
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
airflow dags list
airflow dags trigger crypto_daily_aggregation
```

## What breaks first at scale

1. **CoinGecko rate limits**: Free tier is 50 calls/min. We're fetching 50 coins every 30s = 100 calls/min with pagination. Need to either reduce frequency, upgrade API tier, or add caching.

2. **Single Kafka partition per coin**: Consumer processes messages serially. With 3 partitions we get some parallelism, but we're not partitioning by coin_id, so related records could land on different partitions. This is fine for raw ingestion but would break if we needed ordered processing per coin.

3. **MongoDB document growth**: Raw collection grows indefinitely. At current rate (~14MB/day), we hit 5GB in a year. Need retention policy or move old data to cold storage (S3 + aggregated summaries).

4. **Aggregation memory**: Daily job loads all records for each coin into memory to calculate stats. Works fine for 2,880 records/coin/day, but breaks if we increase ingestion frequency to 1-second intervals (86,400 records/coin/day). Would need streaming aggregation or MongoDB's aggregation pipeline.

5. **Single producer**: No redundancy. If the producer crashes, we miss data until it restarts. Production would need multiple producers with leader election or at-least-once semantics.

## What I'd change for production

- Add retry logic with exponential backoff for API failures
- Implement dead letter queue for messages that fail validation
- Use MongoDB time-series collections (available in 5.0+) for better compression
- Add monitoring (Prometheus + Grafana) for lag, throughput, error rates
- Schema validation at Kafka level (Avro/Protobuf with Schema Registry)
- Separate Airflow environment with proper executor (Celery/Kubernetes, not Sequential)
- Add data quality checks in Airflow (Great Expectations or custom)
- TTL index on raw collection to auto-delete old data
- Proper secrets management (AWS Secrets Manager / Vault, not .env files)

## Assumptions

- Data freshness SLA is ~1 minute (producer runs every 30s, consumer is near-realtime)
- Historical data older than 1 year is not queried frequently
- CoinGecko API data is already reasonably clean (we validate but don't correct)
- Daily aggregations can run anytime between 1-2 AM UTC without strict timing requirements
- MongoDB Atlas M10 cluster (or equivalent) can handle 100 writes/min + aggregation queries
