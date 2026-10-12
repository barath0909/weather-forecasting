import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"WEATHER FORECASTING" in response.data

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}

def test_empty_city(client):
    response = client.get("/weather?city=")
    assert response.status_code == 200
    assert b"Please enter a city name" in response.data

@patch("requests.get")
def test_weather_success_mock(mock_get, client):
    # Current weather mock
    mock_curr = MagicMock()
    mock_curr.status_code = 200
    mock_curr.json.return_value = {
        "name": "Bengaluru",
        "sys": {"country": "IN", "sunrise": 1700000000, "sunset": 1700043200},
        "timezone": 19800,
        "coord": {"lat": 12.9716, "lon": 77.5946},
        "main": {"temp": 28.0, "feels_like": 29.0, "humidity": 60, "pressure": 1012},
        "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
        "wind": {"speed": 3.6, "deg": 90}
    }

    # Forecast mock
    mock_fore = MagicMock()
    mock_fore.status_code = 200
    mock_fore.json.return_value = {
        "list": [
            {
                "dt": 1700000000,
                "main": {"temp": 27.0, "humidity": 62},
                "weather": [{"main": "Clear", "icon": "01d"}]
            }
        ]
    }

    # AQI pollution mock
    mock_aqi = MagicMock()
    mock_aqi.status_code = 200
    mock_aqi.json.return_value = {
        "list": [
            {
                "main": {"aqi": 2},
                "components": {"pm2_5": 28.4, "pm10": 55.2}
            }
        ]
    }

    mock_get.side_effect = [mock_curr, mock_fore, mock_aqi]

    response = client.get("/weather?city=Bengaluru")
    assert response.status_code == 200
    assert b"Bengaluru" in response.data
    assert b"Air Quality Index" in response.data
    assert b"Day-by-Day Forecast Breakdown" in response.data