.PHONY: help setup kafka-up kafka-down producer consumer clean

help:
	@echo "Available commands:"
	@echo "  make setup       - Install Python dependencies"
	@echo "  make kafka-up    - Start Kafka and Zookeeper"
	@echo "  make kafka-down  - Stop Kafka and Zookeeper"
	@echo "  make producer    - Run the data producer"
	@echo "  make consumer    - Run the data consumer"
	@echo "  make clean       - Remove Python cache files"

setup:
	pip install -r requirements.txt

kafka-up:
	docker-compose up -d
	@echo "Waiting for Kafka to be ready..."
	@sleep 10
	python scripts/setup_kafka.py

kafka-down:
	docker-compose down

producer:
	python src/ingestion/producer.py

consumer:
	python src/storage/consumer.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
