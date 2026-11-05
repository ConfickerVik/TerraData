import pytest
from unittest.mock import MagicMock, patch
from app.services.address_cleaner import AddressCleaner
from app.services.fias_client import FIASClient
from app.services.sudrf_client import SudrfClient
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# --- Тесты AddressCleaner ---
def test_address_cleaner_basic():
    assert AddressCleaner.clean("г. Иркутск, ул. Ленина, д. 10, кв. 5") == "г. Иркутск, ул. Ленина, д. 10"
    assert AddressCleaner.clean("Иркутская обл, г. Иркутск, ул. Мира, д. 1, пом. 2") == "Иркутская обл, г. Иркутск, ул. Мира, д. 1"
    assert AddressCleaner.clean(None) is None
    assert AddressCleaner.clean("   ") == ""

def test_address_cleaner_complex():
    addr = "г. Иркутск, ул. Помяловского, д. 22, квартира 15, муниципальный район"
    cleaned = AddressCleaner.clean(addr)
    assert "квартира" not in cleaned
    assert "муниципальный район" not in cleaned
    assert "д. 22" in cleaned

# --- Тесты FIASClient ---
@patch('httpx.Client.get')
def test_fias_get_token_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '{"Token": "test_token"}'
    fias = FIASClient()
    assert fias.get_master_token() == "test_token"

@patch('httpx.Client.get')
def test_fias_get_token_fail(mock_get):
    mock_get.return_value.status_code = 500
    fias = FIASClient()
    assert fias.get_master_token() is None

# --- Тесты SudrfClient ---
@patch('httpx.Client.get')
def test_sudrf_get_court_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '{"list": [{"VNKOD": "12MS0000", "ZNACHATR": "Судебный участок №1"}]}'
    sudrf = SudrfClient()
    res = sudrf.get_court_by_fias_id("some_guid")
    assert res["court_name"] == "Судебный участок №1"

@patch('httpx.Client.post')
def test_sudrf_get_fias_id_by_address_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = '{"suggestions": [{"data": {"fias_id": "guid_123"}}]}'
    sudrf = SudrfClient()
    assert sudrf.get_fias_id_by_address("some address") == "guid_123"

# --- Интеграционные тесты API ---

@patch('app.api.sudrf.fias_client.search_fias_by_cadastral')
@patch('app.api.sudrf.sudrf_client.get_court_by_fias_id')
def test_api_by_cadastral_full_success(mock_sudrf, mock_fias):
    mock_fias.return_value = {
        "addresses": [{
            "full_name": "г. Иркутск, ул. Тест, д. 1",
            "hierarchy": [{"object_type": "house", "object_guid": "guid_house"}]
        }]
    }
    mock_sudrf.return_value = {"court_name": "Судебный участок №10"}
    response = client.get("/sudrf/by-cadastral?cad_num=123:45:6789")
    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №10"

@patch('app.api.sudrf.fias_client.search_fias_by_cadastral')
@patch('app.api.sudrf.sudrf_client.get_court_by_fias_id')
@patch('app.api.sudrf.sudrf_client.get_fias_id_by_address')
def test_api_by_cadastral_fallback_success(mock_fallback_id, mock_sudrf, mock_fias):
    mock_fias.return_value = {
        "addresses": [{
            "full_name": "г. Иркутск, ул. Тест, д. 1",
            "hierarchy": [] 
        }]
    }
    mock_fallback_id.return_value = "fallback_guid"
    mock_sudrf.return_value = {"court_name": "Судебный участок №20"}
    response = client.get("/sudrf/by-cadastral?cad_num=123:45:6789")
    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №20"

@patch('app.api.fias.fias_client.search_fias_by_cadastral')
def test_api_by_cadastral_not_found(mock_fias):
    mock_fias.return_value = None
    response = client.get("/fias/by-cadastral/000:00:0000")
    assert response.status_code == 404
    assert "не найдены" in response.json()["detail"]

@patch('app.api.fias.fias_client.search_fias_by_address_id')
@patch('app.api.sudrf.sudrf_client.get_court_by_fias_id')
def test_api_by_object_id_success(mock_sudrf, mock_fias):
    mock_fias.return_value = {
        "addresses": [{
            "full_name": "г. Иркутск, ул. Тест, д. 1",
            "hierarchy": [{"object_type": "house", "object_guid": "guid_house"}]
        }]
    }
    mock_sudrf.return_value = {"court_name": "Судебный участок №30"}
    response = client.get("/sudrf/by-object-id?object_id=67352892")
    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №30"

def test_api_search_address_empty():
    response = client.get("/fias/search-address?address=")
    assert response.status_code == 400

# --- Мок-тесты для проверки логики переходов ---

class MockFIASClient:
    def __init__(self):
        self.search_fias_by_cadastral = MagicMock()
        self.search_fias_by_address_id = MagicMock()
        self.get_address_hints = MagicMock()
        self.get_object_id_by_cadastral_number = MagicMock()

class MockSudrfClient:
    def __init__(self):
        self.get_court_by_fias_id = MagicMock()
        self.get_fias_id_by_address = MagicMock()

@pytest.fixture
def mock_services():
    fias_mock = MockFIASClient()
    sudrf_mock = MockSudrfClient()

    with patch('app.api.sudrf.fias_client', fias_mock), \
         patch('app.api.sudrf.sudrf_client', sudrf_mock):
        yield fias_mock, sudrf_mock

def test_complete_fallback_chain(mock_services):
    fias_mock, sudrf_mock = mock_services
    fias_mock.search_fias_by_cadastral.return_value = {
        "addresses": [{
            "full_name": "г. Иркутск, ул. Тестовая, д. 1",
            "hierarchy": [{"object_type": "city", "object_guid": "city_123"}] 
        }]
    }
    sudrf_mock.get_fias_id_by_address.return_value = "fallback_guid_456"
    sudrf_mock.get_court_by_fias_id.return_value = {"court_name": "Суд-Фоллбек"}

    response = client.get("/sudrf/by-cadastral?cad_num=1:2:3")
    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Суд-Фоллбек"
    sudrf_mock.get_court_by_fias_id.assert_called_with("fallback_guid_456")

def test_fias_success_no_fallback_needed(mock_services):
    fias_mock, sudrf_mock = mock_services
    fias_mock.search_fias_by_cadastral.return_value = {
        "addresses": [{
            "full_name": "г. Иркутск, ул. Тестовая, д. 1",
            "hierarchy": [{"object_type": "house", "object_guid": "direct_guid"}]
        }]
    }
    sudrf_mock.get_court_by_fias_id.return_value = {"court_name": "Прямой Суд"}

    response = client.get("/sudrf/by-cadastral?cad_num=1:2:3")
    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Прямой Суд"
    sudrf_mock.get_fias_id_by_address.assert_not_called()

def test_total_failure_scenario(mock_services):
    fias_mock, sudrf_mock = mock_services
    fias_mock.search_fias_by_cadastral.return_value = {
        "addresses": []
    }
    sudrf_mock.get_fias_id_by_address.return_value = None
    response = client.get("/sudrf/by-cadastral?cad_num=1:2:3")
    assert response.status_code == 404
    assert "fallback-поиск не дал результата" in response.json()["detail"]

def test_fias_data_corruption(mock_services):
    fias_mock, sudrf_mock = mock_services
    fias_mock.search_fias_by_cadastral.return_value = {"addresses": []}
    response = client.get("/sudrf/by-cadastral?cad_num=1:2:3")
    assert response.status_code == 404
