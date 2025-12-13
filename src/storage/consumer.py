import json
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW, MONGODB_URI, MONGODB_DATABASE, MONGODB_RAW_COLLECTION
from storage.mongo_client import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoDataConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, mongo_uri: str, mongo_db: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
        self.mongo_client = MongoDBClient(mongo_uri, mongo_db)
        
    def connect(self):
        if not self.mongo_client.connect():
            raise Exception("Failed to connect to MongoDB")
        
        self.mongo_client.setup_indexes(MONGODB_RAW_COLLECTION)
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='crypto-consumer-group'
            )
            logger.info(f"Connected to Kafka topic: {self.topic}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def run(self):
        self.connect()
        
        logger.info("Starting consumer")
        processed_count = 0
        
        try:
            for message in self.consumer:
                data = message.value
                
                if self.mongo_client.insert_raw_data(MONGODB_RAW_COLLECTION, data):
                    processed_count += 1
                    if processed_count % 50 == 0:
                        logger.info(f"Processed {processed_count} messages")
                        
        except KeyboardInterrupt:
            logger.info(f"Shutting down consumer. Total processed: {processed_count}")
        finally:
            if self.consumer:
                self.consumer.close()
            self.mongo_client.close()


if __name__ == '__main__':
    consumer = CryptoDataConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC_RAW,
        mongo_uri=MONGODB_URI,
        mongo_db=MONGODB_DATABASE
    )
    consumer.run()
