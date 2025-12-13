import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'crypto_pipeline')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

KAFKA_TOPIC_RAW = 'crypto-raw'
MONGODB_RAW_COLLECTION = 'market_data_raw'
MONGODB_AGGREGATED_COLLECTION = 'market_data_daily'
