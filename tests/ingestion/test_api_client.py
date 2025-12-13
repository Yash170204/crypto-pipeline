import pytest
from unittest.mock import patch, Mock

from src.ingestion.api_client import CryptoAPIClient


@pytest.fixture
def api_client():
    return CryptoAPIClient(rate_limit_delay=0)


def test_fetch_markets_success(api_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "bitcoin", "symbol": "btc"},
        {"id": "ethereum", "symbol": "eth"},
    ]

    with patch("src.ingestion.api_client.requests.get", return_value=mock_response):
        result = api_client.fetch_markets()

    assert result is not None
    assert isinstance(result, list)
    assert result[0]["id"] == "bitcoin"


def test_fetch_markets_api_failure(api_client, caplog):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {}

    with patch("src.ingestion.api_client.requests.get", return_value=mock_response):
        result = api_client.fetch_markets()

    assert result is None
    assert "Unexpected response format" in caplog.text
