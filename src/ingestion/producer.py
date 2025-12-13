import json
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

from api_client import CryptoAPIClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoDataProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        self.producer = None
        self.bootstrap_servers = bootstrap_servers
        self.api_client = CryptoAPIClient()
        
    def connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def send_message(self, data: dict) -> bool:
        if not self.producer:
            logger.error("Producer not connected")
            return False
            
        try:
            future = self.producer.send(self.topic, value=data)
            record_metadata = future.get(timeout=10)
            logger.debug(f"Sent to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def run(self, interval_seconds: int = 30):
        self.connect()
        
        logger.info(f"Starting producer, fetching data every {interval_seconds}s")
        
        try:
            while True:
                markets = self.api_client.fetch_markets(per_page=50)
                
                if not markets:
                    logger.warning("No data received from API")
                    time.sleep(interval_seconds)
                    continue
                
                timestamp = datetime.utcnow().isoformat()
                valid_count = 0
                
                for market in markets:
                    if self.api_client.validate_market_data(market):
                        message = {
                            'timestamp': timestamp,
                            'coin_id': market['id'],
                            'symbol': market['symbol'],
                            'name': market.get('name'),
                            'current_price': market['current_price'],
                            'market_cap': market['market_cap'],
                            'total_volume': market['total_volume'],
                            'price_change_24h': market.get('price_change_percentage_24h'),
                            'circulating_supply': market.get('circulating_supply'),
                            'high_24h': market.get('high_24h'),
                            'low_24h': market.get('low_24h')
                        }
                        
                        if self.send_message(message):
                            valid_count += 1
                
                logger.info(f"Sent {valid_count}/{len(markets)} validated records")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Shutting down producer")
        finally:
            if self.producer:
                self.producer.close()


if __name__ == '__main__':
    producer = CryptoDataProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC_RAW
    )
    producer.run(interval_seconds=30)
