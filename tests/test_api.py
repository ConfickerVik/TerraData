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
        mocked_method.assert_called_once_with("38:00:000000:00001")

def test_rosreestr_search_address_mock():
    from app.api.rosreestr import client as rr_client
    
    mock_data = {"results": ["38:00:000000:00001"]}
    
    with mock.patch.object(rr_client, 'search_by_address', return_value=mock_data) as mocked_method:
        response = client.get("/rosreestr/search-address?address=ул. Тестовая")
        assert response.status_code == 200
        assert "38:00:000000:00001" in response.json()["results"]
        mocked_method.assert_called_once_with("ул. Тестовая")

def test_converter_xml_to_pdf_success():
    from app.api.converter import converter
    
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
    
    # FastAPI возвращает 422 Unprocessable Entity, если обязательный UploadFile отсутствует
    assert response.status_code == 422

def test_converter_xml_to_pdf_empty_file():
    """Тест случая, когда отправлен пустой файл"""
    # Создаем пустой файл в памяти
    empty_content = b""
    
    # Мокаем конвертер, так как он может упасть на пустом контенте
    from app.api.converter import converter
    with mock.patch.object(converter, 'convert_xml_to_pdf', side_effect=Exception("Empty file content")) as mocked_method:
        response = client.post(
            "/converter/xml-to-pdf", 
            files={"file": ("empty.xml", empty_content, "text/xml")}
        )
        
        # Ожидаем 500 ошибку, так как в app/api/converter.py блок try-except ловит всё и возвращает 500
        assert response.status_code == 500
        assert "Empty file content" in response.json()["detail"]
        mocked_method.assert_called_once()

def test_converter_xml_to_pdf_wrong_extension():
    """Тест случая, когда загружен файл с неправильным расширением"""
    response = client.post(
        "/converter/xml-to-pdf", 
        files={"file": ("test.txt", b"some content", "text/plain")}
    )
    assert response.status_code == 400
    assert "File must be an XML document" in response.json()["detail"]
