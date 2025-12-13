from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self, uri: str, database: str):
        self.uri = uri
        self.database_name = database
        self.client = None
        self.db = None
        
    def connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def setup_indexes(self, collection_name: str):
        collection = self.db[collection_name]
        
        if collection_name == 'market_data_raw':
            collection.create_index([
                ('coin_id', ASCENDING),
                ('timestamp', DESCENDING)
            ], name='coin_time_idx')
            
            collection.create_index([
                ('timestamp', DESCENDING)
            ], name='time_idx')
            
            logger.info(f"Indexes created for {collection_name}")
            
        elif collection_name == 'market_data_daily':
            collection.create_index([
                ('coin_id', ASCENDING),
                ('date', DESCENDING)
            ], name='coin_date_idx', unique=True)
            
            collection.create_index([
                ('date', DESCENDING)
            ], name='date_idx')
            
            logger.info(f"Indexes created for {collection_name}")
    
    def insert_raw_data(self, collection_name: str, data: dict) -> bool:
        try:
            collection = self.db[collection_name]
            collection.insert_one(data)
            return True
        except Exception as e:
            logger.error(f"Failed to insert data: {e}")
            return False
    
    def insert_aggregated_data(self, collection_name: str, data: dict) -> bool:
        try:
            collection = self.db[collection_name]
            result = collection.replace_one(
                {'coin_id': data['coin_id'], 'date': data['date']},
                data,
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to upsert aggregated data: {e}")
            return False
    
    def get_raw_data_for_date(self, collection_name: str, coin_id: str, start_time: datetime, end_time: datetime):
        collection = self.db[collection_name]
        query = {
            'coin_id': coin_id,
            'timestamp': {
                '$gte': start_time.isoformat(),
                '$lt': end_time.isoformat()
            }
        }
        return list(collection.find(query).sort('timestamp', ASCENDING))
    
    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
