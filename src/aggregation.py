from datetime import datetime, timedelta
from typing import List, Dict
import logging
from statistics import mean

from storage.mongo_client import MongoDBClient
from config import MONGODB_URI, MONGODB_DATABASE, MONGODB_RAW_COLLECTION, MONGODB_AGGREGATED_COLLECTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyAggregator:
    def __init__(self):
        self.mongo_client = MongoDBClient(MONGODB_URI, MONGODB_DATABASE)
        
    def calculate_24h_stats(self, data_points: List[Dict]) -> Dict:
        if not data_points:
            return None
        
        prices = [d['current_price'] for d in data_points if 'current_price' in d]
        volumes = [d['total_volume'] for d in data_points if 'total_volume' in d]
        market_caps = [d['market_cap'] for d in data_points if 'market_cap' in d]
        
        if not prices:
            return None
        
        return {
            'avg_price': mean(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_volume': mean(volumes) if volumes else None,
            'avg_market_cap': mean(market_caps) if market_caps else None,
            'data_points': len(data_points)
        }
    
    def aggregate_for_date(self, target_date: datetime):
        self.mongo_client.connect()
        self.mongo_client.setup_indexes(MONGODB_AGGREGATED_COLLECTION)
        
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        logger.info(f"Aggregating data for {start_time.date()}")
        
        collection = self.mongo_client.db[MONGODB_RAW_COLLECTION]
        distinct_coins = collection.distinct('coin_id', {
            'timestamp': {
                '$gte': start_time.isoformat(),
                '$lt': end_time.isoformat()
            }
        })
        
        aggregated_count = 0
        
        for coin_id in distinct_coins:
            raw_data = self.mongo_client.get_raw_data_for_date(
                MONGODB_RAW_COLLECTION,
                coin_id,
                start_time,
                end_time
            )
            
            stats = self.calculate_24h_stats(raw_data)
            
            if stats:
                last_record = raw_data[-1]
                
                aggregated_doc = {
                    'coin_id': coin_id,
                    'symbol': last_record.get('symbol'),
                    'name': last_record.get('name'),
                    'date': start_time.strftime('%Y-%m-%d'),
                    'avg_price': stats['avg_price'],
                    'min_price': stats['min_price'],
                    'max_price': stats['max_price'],
                    'avg_volume': stats['avg_volume'],
                    'avg_market_cap': stats['avg_market_cap'],
                    'data_points': stats['data_points'],
                    'last_price': last_record.get('current_price'),
                    'aggregated_at': datetime.utcnow().isoformat()
                }
                
                if self.mongo_client.insert_aggregated_data(MONGODB_AGGREGATED_COLLECTION, aggregated_doc):
                    aggregated_count += 1
        
        logger.info(f"Aggregated {aggregated_count} coins for {start_time.date()}")
        self.mongo_client.close()
        return aggregated_count


if __name__ == '__main__':
    aggregator = DailyAggregator()
    yesterday = datetime.utcnow() - timedelta(days=1)
    aggregator.aggregate_for_date(yesterday)
