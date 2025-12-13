# Quick Start Guide

## Prerequisites
1. Python 3.9+
2. Docker Desktop (or Docker + Docker Compose)
3. MongoDB Atlas account (free tier works)

## Setup Steps

### 1. Clone and Install
```bash
git clone <your-repo-url>
cd crypto-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure MongoDB
Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your MongoDB Atlas URI:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=crypto_pipeline
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### 3. Start Kafka
```bash
docker-compose up -d
```

Wait ~10 seconds for Kafka to be ready, then:
```bash
python scripts/setup_kafka.py
```

### 4. Run the Pipeline

**Terminal 1 - Producer:**
```bash
python src/ingestion/producer.py
```

You should see:
```
INFO:__main__:Connected to Kafka at localhost:9092
INFO:__main__:Starting producer, fetching data every 30s
INFO:__main__:Sent 50/50 validated records
```

**Terminal 2 - Consumer:**
```bash
python src/storage/consumer.py
```

You should see:
```
INFO:__main__:Connected to MongoDB: crypto_pipeline
INFO:__main__:Connected to Kafka topic: crypto-raw
INFO:__main__:Processed 50 messages
```

### 5. Verify Data in MongoDB

Connect to your MongoDB Atlas cluster and query:
```javascript
use crypto_pipeline

// Check raw data
db.market_data_raw.countDocuments()
db.market_data_raw.find({coin_id: "bitcoin"}).sort({timestamp: -1}).limit(5)

// View indexes
db.market_data_raw.getIndexes()
```

### 6. Run Daily Aggregation (Manual)

```bash
python src/aggregation.py
```

This aggregates yesterday's data. Check results:
```javascript
db.market_data_daily.find({coin_id: "bitcoin"}).sort({date: -1})
```

## Using Airflow (Optional)

Setup Airflow:
```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

Start Airflow:
```bash
airflow scheduler &
airflow webserver -p 8080
```

Access UI at http://localhost:8080 and trigger the `crypto_daily_aggregation` DAG.

## Troubleshooting

**"Failed to connect to Kafka"**
- Check Docker containers: `docker ps`
- Restart Kafka: `docker-compose restart kafka`
- Wait longer after starting (Kafka can take 15-20s to be ready)

**"Failed to connect to MongoDB"**
- Verify `.env` has correct MongoDB URI
- Check MongoDB Atlas network access (allow your IP)
- Test connection: `mongosh "your-connection-string"`

**"No data received from API"**
- CoinGecko might be rate limiting
- Check API status: https://status.coingecko.com/
- Increase `interval_seconds` in producer.py

**"Producer not sending messages"**
- Run setup script: `python scripts/setup_kafka.py`
- Check topic exists: `docker exec -it crypto-pipeline-kafka-1 kafka-topics --list --bootstrap-server localhost:9092`

## Stopping Everything

```bash
# Stop producer/consumer with Ctrl+C

# Stop Kafka
docker-compose down

# Clean up Python cache
make clean
```

## Making Changes

After code changes:
1. Stop producer/consumer (Ctrl+C)
2. Restart with `python src/ingestion/producer.py` and `python src/storage/consumer.py`
3. No need to restart Kafka unless changing configuration
