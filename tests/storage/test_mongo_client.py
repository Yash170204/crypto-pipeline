from unittest.mock import MagicMock, patch
from src.storage.mongo_client import MongoDBClient


@patch("src.storage.mongo_client.MongoClient")
def test_insert_raw_data_calls_insert_one(mock_mongo_client):
    mock_collection = MagicMock()

    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db

    mock_mongo_client.return_value = mock_client

    mongo_client = MongoDBClient("mongodb://localhost:27017", "test_db")

    data = {
        "coin_id": "bitcoin",
        "price": 50000,
        "timestamp": "2024-12-13"
    }

    result = mongo_client.insert_raw_data("market_data_raw", data)

    mock_collection.insert_one.assert_called_once_with(data)
    assert result is True


@patch("src.storage.mongo_client.MongoClient")
def test_insert_aggregated_data_calls_replace_one(mock_mongo_client):
    mock_collection = MagicMock()

    mock_result = MagicMock()
    mock_result.acknowledged = True
    mock_collection.replace_one.return_value = mock_result

    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db

    mock_mongo_client.return_value = mock_client

    mongo_client = MongoDBClient("mongodb://localhost:27017", "test_db")

    aggregated_data = {
        "coin_id": "bitcoin",
        "avg_price": 51000,
        "date": "2024-12-13"
    }

    result = mongo_client.insert_aggregated_data(
        "market_data_daily",
        aggregated_data
    )

    mock_collection.replace_one.assert_called_once_with(
        {"coin_id": "bitcoin", "date": "2024-12-13"},
        aggregated_data,
        upsert=True
    )
    assert result is True
