import json
import time
import logging
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError

from src.ingestion.api_client import CryptoAPIClient
from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoDataProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.producer: KafkaProducer | None = None
        self.api_client = CryptoAPIClient()

    def connect(self) -> None:
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                linger_ms=10,
                max_in_flight_requests_per_connection=1,
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error("Failed to connect to Kafka", exc_info=e)
            raise

    def send_message(self, data: dict) -> bool:
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False

        try:
            future = self.producer.send(self.topic, value=data)
            metadata = future.get(timeout=10)
            logger.debug(
                f"Message sent to {metadata.topic} "
                f"[partition={metadata.partition}, offset={metadata.offset}]"
            )
            return True
        except KafkaError as e:
            logger.error("Failed to send message to Kafka", exc_info=e)
            return False

    def run(self, interval_seconds: int = 30) -> None:
        self.connect()
        logger.info(
            f"Starting producer loop (interval={interval_seconds}s, topic={self.topic})"
        )

        try:
            while True:
                markets = self.api_client.fetch_markets(per_page=50)

                if not markets:
                    logger.warning("No market data received from API")
                    time.sleep(interval_seconds)
                    continue

                timestamp = datetime.utcnow().isoformat()
                sent_count = 0

                for market in markets:
                    if not self.api_client.validate_market_data(market):
                        continue

                    message = {
                        "timestamp": timestamp,
                        "coin_id": market["id"],
                        "symbol": market["symbol"],
                        "name": market.get("name"),
                        "current_price": market["current_price"],
                        "market_cap": market["market_cap"],
                        "total_volume": market["total_volume"],
                        "price_change_24h": market.get(
                            "price_change_percentage_24h"
                        ),
                        "circulating_supply": market.get("circulating_supply"),
                        "high_24h": market.get("high_24h"),
                        "low_24h": market.get("low_24h"),
                    }

                    if self.send_message(message):
                        sent_count += 1

                logger.info(f"Sent {sent_count}/{len(markets)} records to Kafka")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Producer interrupted by user")
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed")


if __name__ == "__main__":
    producer = CryptoDataProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC_RAW,
    )
    producer.run(interval_seconds=30)
