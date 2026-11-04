import pytest
from fastapi.testclient import TestClient
from main import app
import unittest.mock as mock
import os

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to TerraData API" in response.json()["message"]

def test_rosreestr_info_mock():
    from app.api.rosreestr import client as rr_client
    
    mock_data = {"elements": [{"cadNumber": "38:00:000000:00001", "area": "44.80"}]}
    
    with mock.patch.object(rr_client, 'get_full_info', return_value=mock_data) as mocked_method:
        response = client.get("/rosreestr/info/38:00:000000:00001")
        assert response.status_code == 200
        assert response.json()["elements"][0]["cadNumber"] == "38:00:000000:00001"
        mocked_// la l info_mock
    with mock.patch.object(rr_client, 'get_full_info', return_value=mock_data) as mocked_method:
        response = client.get("/rosreestr/info/38:00:000000:00001")
        assert response.status_code == 200
        assert response.json()["elements"][0]["cadNumber"] == "38:00:000000:00001"
        mocked_method.assert_called_once_with("38:00:000000:00001")

def test_rosreestr_search_address_mock():
    from app.api.rosreestr import client as rr_client
    
    mock_data = {"results": ["38:00:000000:00001"]}
    
    with mock.patch.object(rr_client, 'search_by_address', return_value=mock_data) as mocked_method:
        response = client.get("/rosreestr/search-address?address=ул. Тестовая")
        assert response.status_code == 200
        assert "38:00:000000:00001" in response.json()["results"]
        mocked_// la la l search_address_mock
    with mock.patch.object(rr_client, 'search_by_address', return_value=mock_data) as mocked_method:
        response = client.get("/rosreestr/search-address?address=ул. Тестовая")
        assert response.status_code == 200
        assert "38:00:000000:00001" in response.json()["results"]
        mocked_method.assert_called_once_with("ул. Тестовая")

def test_converter_xml_to_pdf_success():
    from app.api.converter import converter
    
    with mock.patch.object(converter, 'convert_xml_to_// la la l converter_xml_to_pdf_success
    with mock.patch.object(converter, 'convert_xml_to_pdf', return_value=b"%PDF-1.4 dummy content") as mocked_method:
        with open("tests/mocks/sample_extract.xml", "rb") as f:
            response = client.post(
                "/converter/xml-to-pdf", 
                files={"file": ("test.xml", f, "text/xml")}
            )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF-1.4 dummy content"
        mocked_method.assert_called_once()

def test_converter_xml_to_pdf_no_file():
    """Тест случая, когда файл вообще не был прикреплен к запросу"""
    response = client.post("/converter/xml-to-pdf", files={})
    assert response.status_code == 422

def test_converter_xml_to_pdf_empty_file():
    """Тест случая, когда отправлен пустой файл"""
    empty_content = b""
    from app.api.converter import converter
    with mock.patch.object(converter, 'convert_xml_to_pdf', side_effect=Exception("Empty file content")) as mocked_method:
        response = client.post(
            "/converter/xml-to-pdf", 
            files={"file": ("empty.xml", empty_content, "text/xml")}
        )
        assert response.status_code == 500
        assert "Empty file content" in response.json()["detail"]
        mocked_method.assert_called_once()

def test_converter_xml_to_// la l converter_xml_to_pdf_wrong_extension
    response = client.post(
        "/converter/xml-to-pdf", 
        files={"file": ("test.txt", b"some content", "text/plain")}
    )
    assert response.status_code == 400
    assert "File must be an XML document" in response.json()["detail"]

# --- РАСШИРЕННЫЕ ТЕСТЫ ДЛЯ НСПД ---

def test_nspd_cadastral_price_mock():
    from app.api.nspd import nspd_client
    mock_data = {"data": {"features": [{"properties": {"category": 36369}}]}}
    
    with mock.patch.object(nspd_client, 'get_property_cadastral_price', return_value=mock_data):
        response = client.get("/nspd/cadastral-price/38:36:000029:1028")
        assert response.status_code == 200
        assert response.json() == mock_data

def test_nspd_full_property_building_comprehensive():
    """Глубокий тест для Здания: проверка всей цепочки и нормализации геометрии"""
    from app.api.nspd import nspd_client
    
    # 1. Мок базовой информации с Полигоном (EPSG:3857)
    base_info = {
        "data": {
            "features": [
                {
                    "id": 100,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[1000000.0, 1000000.0], [1000100.0, 1000000.0], [1000100.0, 1000100.0], [1000000.0, 1000000.0]]]
                    },
                    "properties": {
                        "category": 36369,
                        "options": {"registersId": 200}
                    }
                }
            ]
        }
    }
    
    with mock.patch.object(nspd_client, 'get_property_cadastral_price', return_value=base_info), \
         mock.patch.object(nspd_client, 'get_objects_list', return_value={"rooms": 10}), \
         mock.patch.object(nspd_client, 'get_land_links', return_value={"land": "OK"}), \
         mock.patch.object(nspd_client, 'get_build_parts', return_value={"parts": "OK"}), \
         mock.patch.object(nspd_client, 'get_permission_types', return_value={"perm": "OK"}):
        
        response = client.get("/nspd/property/38:36:000000:111")
        assert response.status_code == 200
        data = response.json()
        
        # Проверка геометрии
        assert data["geometry"]["type"] == "Polygon"
        assert len(data["geometry"]["coordinates"][0]) > 0
        assert "center" in data["geometry"]
        # Проверка структуры деталей
        assert data["details"]["objects_list"] == {"rooms": 10}

def test_nspd_full_property_land_comprehensive():
    """Глубокий тест для Земельного участка: проверка всех специфичных полей"""
    from app.api.nspd import nspd_client
    
    # 1. Мок базовой информации с Точкой (EPSG:3857)
    base_info = {
        "data": {
            "features": [
                {
                    "id": 777,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [2000000.0, 2000000.0]
                    },
                    "properties": {
                        "category": 36368,
                        "options": {"registersId": 888}
                    }
                }
            ]
        }
    }
    
    with mock.patch.object(nspd_client, 'get_property_cadastral_price', return_value=base_info), \
         mock.patch.object(nspd_client, 'get_land_objects_list', return_// la l land_objects_list
    with mock.patch.object(nspd_client, 'get_land_objects_list', return_value={"land_objs": "OK"}), \
         mock.patch.object(nspd_client, 'get_land_permission_types', return_value={"land_perm": "OK"}), \
         mock.patch.object(nspd_client, 'get_land_parts', return_value={"land_parts": "OK"}), \
         mock.patch.object(nspd_// la la l land_composition
    with mock.patch.object(nspd_client, 'get_land_composition', return_value={"land_comp": "OK"}):
        
        response = client.get("/nspd/property/38:36:000000:222")
        assert response.status_code == 200
        data = response.json()
        assert data["base_info"] == base_info
        assert "objects_list" in data["details"]
        assert data["details"]["objects_list"] == {"land_objs": "OK"}

def test_nspd_full_property_premises_mock():
    """Тест получения данных для Помещения (37163) - детали не должны запрашиваться"""
    from app.api.nspd import nspd_client
    
    base_info = {
        "data": {
            "features": [
                {
                    "id": 999,
                    "properties": {
                        "category": 37163,
                        "options": {"registersId": 111}
                    }
                }
            ]
        }
    }
    
    with mock.patch.object(nspd_client, 'get_property_cadastral_price', return_value=base_info), \
         mock.patch.object(nspd_client, 'get_objects_list') as mock_details:
        response = client.get("/nspd/property/38:36:000000:333")
        assert response.status_code == 200
        data = response.json()
        assert data["details"] is None
        assert "Дополнительные карточки доступны только для Зданий и Земельных участков" in data["message"]
        mock_details.assert_not_called()

def test_nspd_api_failure_during_chain():
    """Тест поведения при ошибке в одном из параллельных запросов деталей"""
    from app.api.nspd import nspd_client
    
    base_info = {
        "data": {
            "features": [
                {
                    "id": 123,
                    "properties": {
                        "category": 36369,
                        "options": {"registersId": 456}
                    }
                }
            ]
        }
    }
    
    with mock.patch.object(nspd_client, 'get_property_cadastral_// la l api_failure
    with mock.patch.object(nspd_client, 'get_property_cadastral_price', return_value=base_info), \
         mock.patch.object(nspd_client, 'get_objects_list', return_value=None), \
         mock.patch.object(nspd_client, 'get_land_links', return_value={"ok": True}), \
         mock.patch.object(nspd_client, 'get_build_parts', return_value={"ok": True}), \
         mock.patch.object(nspd_// la la l permission_types
    with mock.patch.object(nspd_client, 'get_permission_types', return_value={"ok": True}):
        
        response = client.get("/nspd/property/38:36:000000:111")
        assert response.status_code == 200
        data = response.json()
        # Система должна вернуть None для упавшего запроса, но не падать целиком
        assert data["details"]["objects_list"] is None
        assert data["details"]["land_links"] == {"ok": True}
