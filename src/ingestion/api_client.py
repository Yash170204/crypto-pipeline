import time
import requests
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoAPIClient:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, rate_limit_delay: float = 0.6):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def fetch_markets(self, vs_currency: str = 'usd', per_page: int = 50) -> Optional[List[Dict]]:
        self._rate_limit()
        
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            'vs_currency': vs_currency,
            'order': 'market_cap_desc',
            'per_page': per_page,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return None
                
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            return None
    
    def validate_market_data(self, data: Dict) -> bool:
        required_fields = ['id', 'symbol', 'current_price', 'market_cap', 'total_volume']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
            if data[field] is None:
                logger.warning(f"Null value for required field: {field}")
                return False
        
        if not isinstance(data.get('current_price'), (int, float)):
            return False
        if data['current_price'] <= 0:
            return False
            
        return True
