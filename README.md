# Foundational Components for a Data Ingestion Pipeline

This repository provides a set of core, reusable components for building a real-time data ingestion pipeline. It demonstrates professional data engineering practices by prioritizing modularity, testability, and correct implementation over a fully-integrated but brittle system.

The project uses Python, Kafka, and Docker to construct a reliable foundation for capturing and buffering event data, with a dedicated client for data storage.

## What Runs Today

The following components are implemented, tested, and runnable:

*   **Kafka Cluster:** A local Kafka and Zookeeper cluster managed via `docker-compose`.
*   **Data Producer:** A standalone Python application (`src/ingestion/producer.py`) that fetches real-time cryptocurrency data from a public API and publishes it as messages to a Kafka topic named `crypto-raw`.
*   **Message Verification:** The successful production and buffering of messages in Kafka can be verified using the standard `kafka-console-consumer` tool.
*   **Unit-Tested Database Client:** A Python class (`src/storage/mongo_client.py`) for connecting to and writing data into MongoDB. Its logic is fully verified with a suite of `pytest` unit tests using `unittest.mock`. **Note:** This client is not yet wired into a Kafka consumer. MongoDB itself is not run via Docker in this repository; database logic is validated using isolated unit tests with mocks.

## Key Component: Testable Database Client

A core focus of this project is the design of a robust and testable database client. While MongoDB is used for this implementation, the design principles are applicable to any database system.

### Data Modeling
The client is designed to handle two distinct data models, a common pattern in data pipelines:
1.  **Raw Events:** A flexible schema to store immutable, timestamped JSON data exactly as it arrives from the source.
2.  **Aggregated Summaries:** A structured schema for aggregated, analytical data, such as daily summaries. This model uses a unique key (`coin_id`, `date`) to ensure data integrity.

### Write Strategy
The client employs different write strategies tailored to each data model:
*   **Simple Inserts:** Raw events are written using `insert_one()`, as each is a unique, immutable fact.
*   **Idempotent Upserts:** Aggregated data is written using `replace_one()` with `upsert=True`. This allows aggregation jobs to be re-run safely, as the operation will either create a new daily summary or overwrite an existing one, preventing duplicate data.

### Indexing
The client includes logic to create indexes that are critical for performance in a time-series use case. For the raw data collection, a compound index on `(coin_id, timestamp)` is used to enable efficient lookups of a specific coin's data within a date range—a common query pattern for aggregation tasks.

### Testability
The client is developed with testability as a primary concern. The business logic is decoupled from the `pymongo` driver, allowing for comprehensive unit tests that run in memory without a live database connection. This guarantees the client's behavior is correct and makes it easy to maintain and extend.

## Planned Components

The existing components provide a solid foundation for the following planned extensions:

1.  **Kafka Consumer Service:** A service that consumes messages from the `crypto-raw` topic and uses the `MongoDBClient` to persist them to the database.
2.  **Batch Aggregation Job:** An orchestration tool like Airflow will be used to trigger a daily job. This job will use the `MongoDBClient` to read raw data and write to the daily summary collection. The initial DAG (`airflow/dags/daily_aggregation.py`) is included as a placeholder.
3.  **Integration & End-to-End Tests:** A suite of tests to verify the complete data flow between all services.

## Setup & Usage

Follow these steps to set up the environment and run the tests.

**Prerequisites:**
*   Python 3.9+
*   Docker & Docker Compose

**Instructions:**
```bash
# 1. Clone the repository and navigate into the directory
git clone <your-repo-url>
cd crypto-pipeline

# 2. Install Python dependencies
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
pip install -r requirements.txt

# 3. Start Kafka and Zookeeper
docker-compose up -d

# 4. Run the unit tests to verify the database client logic
pytest
```

To see the producer in action, you can run it as a standalone script. It will begin fetching data and publishing it to the `crypto-raw` Kafka topic.

```bash
# Optional: Run the producer
python -m src.ingestion.producer
```

## Screenshots

The following screenshots document the key components of the project in action.

**Docker Services**
*Shows the Kafka and Zookeeper containers running.*
![Docker Processes](screenshots/docker_ps.png)

**Kafka Producer Logs**
*Shows the producer successfully fetching data and publishing messages to the Kafka topic.*
![Producer Logs](screenshots/producer_logs.png)

**Kafka Topic Consumer**
*Shows a command-line consumer reading messages from the `crypto-raw` topic.*
![Kafka Consumer](screenshots/kafka_consumer.png)

**Pytest Results**
*Shows the successful execution of the unit tests for the MongoDB client.*
![Pytest Results](screenshots/pytest.png)

**Git History**
*A clean, atomic commit history demonstrating a structured development process.*
![Git Log](screenshots/git_log.png)