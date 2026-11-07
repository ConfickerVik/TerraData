from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# =============================================================================
# МОДУЛЬ: main / корневой эндпоинт
# =============================================================================


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "Welcome to TerraData API" in body["message"]
    assert body["endpoints"] == {
        "rosreestr": "/rosreestr",
        "converter": "/converter",
        "nspd": "/nspd",
        "fias": "/fias",
        "sudrf": "/sudrf",
    }


# =============================================================================
# МОДУЛЬ: app.services.coords_converter (CoordsConverter)
# =============================================================================

from app.services.coords_converter import CoordsConverter


def test_normalize_coordinates_origin():
    """Точка (0, 0) в Веб-Меркаторе соответствует (0°, 0°)."""
    lat, lon = CoordsConverter.normalize_coordinates(0.0, 0.0)
    assert lat == pytest.approx(0.0)
    assert lon == pytest.approx(0.0)


def test_normalize_coordinates_max_extent():
    """Граница проекции по X должна давать долготу около 180°."""
    lat, lon = CoordsConverter.normalize_coordinates(CoordsConverter.MAX_EXTENT, 0.0)
    assert lon == pytest.approx(180.0, abs=0.01)
    assert lat == pytest.approx(0.0)


def test_get_center_point():
    """Для Point (список [x, y]) центр совпадает с нормализованной точкой."""
    center = CoordsConverter.get_center([0.0, 0.0])
    assert center == pytest.approx((0.0, 0.0))


def test_get_center_polygon():
    """Для Polygon центр — среднее арифметическое точек контура."""
    points = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]
    center = CoordsConverter.get_center(points)
    assert center == pytest.approx(CoordsConverter.normalize_coordinates(50.0, 50.0))


def test_convert_geometry_point():
    result = CoordsConverter.convert_geometry(
        {"type": "Point", "coordinates": [0.0, 0.0]}
    )
    assert result["type"] == "Point"
    # GeoJSON стандарт: [lon, lat]
    assert result["coordinates"] == [0.0, 0.0]
    assert result["center"] == [0.0, 0.0]


def test_convert_geometry_polygon_structure():
    """Проверка структуры Polygon: тип, наличие контура и центра."""
    polygon = [
        [[1000000.0, 1000000.0], [1000100.0, 1000000.0],
         [1000100.0, 1000100.0], [1000000.0, 1000000.0]]
    ]
    result = CoordsConverter.convert_geometry(
        {"type": "Polygon", "coordinates": polygon}
    )
    assert result["type"] == "Polygon"
    assert len(result["coordinates"]) == 1
    assert len(result["coordinates"][0]) == 4
    assert "center" in result


def test_convert_geometry_unknown():
    result = CoordsConverter.convert_geometry({"type": "LineString", "coordinates": []})
    assert result["type"] == "Unknown"
    assert result["coordinates"] == []
    assert result["center"] == [0.0, 0.0]


# =============================================================================
# МОДУЛЬ: app.services.pdf_service (PDFService)
# =============================================================================

from app.services.pdf_service import PDFService, format_timestamp


def test_format_timestamp_none():
    assert format_timestamp(None) == "н/д"


def test_format_timestamp_zero():
    # 0 — falsy, трактуется как «нет данных»
    assert format_timestamp(0) == "н/д"


def test_format_timestamp_valid():
    # Ненулевой таймстамп в миллисекундах -> дата в формате ДД.ММ.ГГГГ
    result = format_timestamp(1609459200000)  # 01.01.2021 00:00:00 UTC
    assert len(result) == 10
    assert result[2] == "." and result[5] == "."


def test_format_timestamp_invalid():
    assert format_timestamp("not-a-number") == "not-a-number"


def test_pdf_service_empty_elements(tmp_path):
    output = tmp_path / "report.txt"
    assert PDFService().generate_report({"elements": []}, str(output)) is False
    assert not output.exists()


def test_pdf_service_generates_report(tmp_path):
    output = tmp_path / "report.txt"
    data = {
        "elements": [
            {
                "cadNumber": "38:00:000000:00001",
                "address": {"readableAddress": "г. Иркутск, ул. Тестовая, д. 1"},
                "area": "44.80",
                "mainCharacters": [{"unitDescription": "кв.м"}],
                "levelFloor": "1",
                "cadCost": "1234567.89",
                "cadCostDeterminationDate": None,
                "rights": [],
                "encumbrances": [],
            }
        ]
    }
    assert PDFService().generate_report(data, str(output)) is True
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "ОТЧЕТ ОБ ОБЪЕКТЕ НЕДВИЖИМОСТИ" in content
    assert "38:00:000000:00001" in content
    assert "г. Иркутск, ул. Тестовая, д. 1" in content


# =============================================================================
# МОДУЛЬ: app.services.rosreestr_client (RosreestrClient)
# =============================================================================

from app.services.rosreestr_client import RosreestrClient


@pytest.fixture
def rosreestr_client():
    # Передаём поддельный pdf_converter, чтобы не грузить модель
    return RosreestrClient(pdf_converter=MagicMock())


def test_normalize_cadastral_short(rosreestr_client):
    """Кадастровый номер с менее чем 4 частями не изменяется."""
    assert rosreestr_client._normalize_cadastral_number("38:00:000000") == "38:00:000000"


def test_normalize_cadastral_two_digit_region_unchanged(rosreestr_client):
    """Первая часть из 2 символов (типичный регион) -> номер не изменяется."""
    assert rosreestr_client._normalize_cadastral_number("38:00:000000:00001") == "38:00:000000:00001"


def test_normalize_cadastral_long_first_part_strips_zeros(rosreestr_client):
    """Первая часть длиннее 2 символов -> ведущие нули последней части удаляются."""
    assert rosreestr_client._normalize_cadastral_number("138:00:000000:00001") == "138:00:000000:1"


def test_normalize_cadastral_long_first_part_all_zeros(rosreestr_client):
    """Первая часть длиннее 2 символов и последняя часть из нулей -> остаётся '0'."""
    assert rosreestr_client._normalize_cadastral_number("138:00:000000:00000") == "138:00:000000:0"


# =============================================================================
# МОДУЛЬ: app.services.address_cleaner (AddressCleaner)
# =============================================================================

from app.services.address_cleaner import AddressCleaner


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


def test_address_cleaner_removes_literal():
    """Литера (лит.) удаляется из адреса."""
    cleaned = AddressCleaner.clean("г. Иркутск, ул. Ленина, д. 10, лит. А")
    assert "лит" not in cleaned.lower()


def test_address_cleaner_removes_building_marker():
    """Служебная пометка 'строение' исключается."""
    cleaned = AddressCleaner.clean("г. Иркутск, ул. Ленина, д. 10, строение 2")
    assert "строение" not in cleaned.lower()


# =============================================================================
# МОДУЛЬ: app.services.fias_client (FIASClient)
# =============================================================================

from app.services.fias_client import FIASClient


@patch("httpx.Client.get")
def test_fias_get_token_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '{"Token": "test_token"}'
    fias = FIASClient()
    assert fias.get_master_token() == "test_token"


@patch("httpx.Client.get")
def test_fias_get_token_fail(mock_get):
    mock_get.return_value.status_code = 500
    fias = FIASClient()
    assert fias.get_master_token() is None


@patch.object(FIASClient, "get_master_token", return_value=None)
def test_fias_get_address_hints_empty_without_token(mock_token):
    """Без мастер-токена подсказки не запрашиваются."""
    fias = FIASClient()
    assert fias.get_address_hints("г. Иркутск") == []


# =============================================================================
# МОДУЛЬ: app.services.sudrf_client (SudrfClient)
# =============================================================================

from app.services.sudrf_client import SudrfClient


@patch("httpx.Client.get")
def test_sudrf_get_court_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '{"list": [{"VNKOD": "12MS0000", "ZNACHATR": "Судебный участок №1"}]}'
    sudrf = SudrfClient()
    res = sudrf.get_court_by_fias_id("some_guid")
    assert res["court_name"] == "Судебный участок №1"


@patch("httpx.Client.get")
def test_sudrf_get_court_empty_list(mock_get):
    """Пустой список судов -> None."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '{"list": []}'
    sudrf = SudrfClient()
    assert sudrf.get_court_by_fias_id("some_guid") is None


@patch("httpx.Client.post")
def test_sudrf_get_fias_id_by_address_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = '{"suggestions": [{"data": {"fias_id": "guid_123"}}]}'
    sudrf = SudrfClient()
    assert sudrf.get_fias_id_by_address("some address") == "guid_123"


# =============================================================================
# МОДУЛЬ: app.services.nspd_client (NspdClient)
# =============================================================================

from app.services.nspd_client import NspdClient


def test_nspd_get_category_id():
    data = {"data": {"features": [{"properties": {"category": 36369}}]}}
    assert NspdClient().get_category_id(data) == 36369


# =============================================================================
# МОДУЛЬ: app.api.rosreestr (Росреестр)
# =============================================================================

from app.api.rosreestr import client as rr_client


@patch.object(rr_client, "get_full_info", return_value={"elements": [{"cadNumber": "38:00:000000:00001", "area": "44.80"}]})
def test_rosreestr_info_mock(mocked_method):
    response = client.get("/rosreestr/info/38:00:000000:00001")
    assert response.status_code == 200
    assert response.json()["elements"][0]["cadNumber"] == "38:00:000000:00001"
    mocked_method.assert_called_once_with("38:00:000000:00001")


@patch.object(rr_client, "get_full_info", return_value=None)
def test_rosreestr_info_not_found(mocked_method):
    response = client.get("/rosreestr/info/00:00:000000:00000")
    assert response.status_code == 404
    mocked_method.assert_called_once()


@patch.object(rr_client, "search_by_address", return_value={"results": ["38:00:000000:00001"]})
def test_rosreestr_search_address_mock(mocked_method):
    response = client.get("/rosreestr/search-address?address=ул. Тестовая")
    assert response.status_code == 200
    assert "38:00:000000:00001" in response.json()["results"]
    mocked_method.assert_called_once_with("ул. Тестовая")


@patch.object(rr_client, "search_by_address", return_value=None)
def test_rosreestr_search_address_not_found(mocked_method):
    response = client.get("/rosreestr/search-address?address=нет такого адреса")
    assert response.status_code == 404


# =============================================================================
# МОДУЛЬ: app.api.converter (Конвертер XML -> PDF)
# =============================================================================

from app.api.converter import converter


@patch.object(converter, "convert_xml_to_pdf", return_value=b"%PDF-1.4 dummy content")
def test_converter_xml_to_pdf_success(mocked_method):
    with open("tests/mocks/sample_extract.xml", "rb") as f:
        response = client.post(
            "/converter/xml-to-pdf",
            files={"file": ("test.xml", f, "text/xml")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 dummy content"
    mocked_method.assert_called_once()


def test_converter_xml_to_pdf_no_file():
    """Тест случая, когда файл вообще не был прикреплен к запросу"""
    response = client.post("/converter/xml-to-pdf", files={})
    assert response.status_code == 422


@patch.object(converter, "convert_xml_to_pdf", side_effect=Exception("Empty file content"))
def test_converter_xml_to_pdf_empty_file(mocked_method):
    """Тест случая, когда отправлен пустой файл"""
    empty_content = b""
    response = client.post(
        "/converter/xml-to-pdf",
        files={"file": ("empty.xml", empty_content, "text/xml")},
    )
    assert response.status_code == 500
    assert "Empty file content" in response.json()["detail"]
    mocked_method.assert_called_once()


def test_converter_xml_to_pdf_wrong_extension():
    """Тест случая, когда загружен файл с неправильным расширением"""
    response = client.post(
        "/converter/xml-to-pdf",
        files={"file": ("test.txt", b"some content", "text/plain")},
    )
    assert response.status_code == 400
    assert "File must be an XML document" in response.json()["detail"]


# =============================================================================
# МОДУЛЬ: app.api.nspd (НСПД)
# =============================================================================

from app.api.nspd import nspd_client


@patch.object(nspd_client, "get_property_cadastral_price", return_value={"data": {"features": [{"properties": {"category": 36369}}]}})
def test_nspd_cadastral_price_mock(mocked_method):
    response = client.get("/nspd/cadastral-price/38:00:000000:00001")
    assert response.status_code == 200
    assert response.json() == {"data": {"features": [{"properties": {"category": 36369}}]}}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=None)
def test_nspd_cadastral_price_not_found(mocked_method):
    response = client.get("/nspd/cadastral-price/00:00:000000:00000")
    assert response.status_code == 404


BASE_INFO_BUILDING = {
    "data": {
        "features": [
            {
                "id": 100,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[1000000.0, 1000000.0], [1000100.0, 1000000.0], [1000100.0, 1000100.0], [1000000.0, 1000000.0]]],
                },
                "properties": {
                    "category": 36369,
                    "options": {"registersId": 200},
                },
            }
        ]
    }
}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=BASE_INFO_BUILDING)
@patch.object(nspd_client, "get_objects_list", return_value={"rooms": 10})
@patch.object(nspd_client, "get_land_links", return_value={"land": "OK"})
@patch.object(nspd_client, "get_build_parts", return_value={"parts": "OK"})
@patch.object(nspd_client, "get_permission_types", return_value={"perm": "OK"})
def test_nspd_full_property_building_comprehensive(*_):
    """Глубокий тест для Здания: проверка всей цепочки и нормализации геометрии"""
    response = client.get("/nspd/property/38:36:000000:111")
    assert response.status_code == 200
    data = response.json()

    assert data["geometry"]["type"] == "Polygon"
    assert len(data["geometry"]["coordinates"][0]) > 0
    assert "center" in data["geometry"]
    assert data["details"]["objects_list"] == {"rooms": 10}


BASE_INFO_LAND = {
    "data": {
        "features": [
            {
                "id": 777,
                "geometry": {
                    "type": "Point",
                    "coordinates": [2000000.0, 2000000.0],
                },
                "properties": {
                    "category": 36368,
                    "options": {"registersId": 888},
                },
            }
        ]
    }
}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=BASE_INFO_LAND)
@patch.object(nspd_client, "get_land_objects_list", return_value={"land_objs": "OK"})
@patch.object(nspd_client, "get_land_permission_types", return_value={"land_perm": "OK"})
@patch.object(nspd_client, "get_land_parts", return_value={"land_parts": "OK"})
@patch.object(nspd_client, "get_land_composition", return_value={"land_comp": "OK"})
def test_nspd_full_property_land_comprehensive(*_):
    """Глубокий тест для Земельного участка: проверка всех специфичных полей"""
    response = client.get("/nspd/property/38:36:000000:222")
    assert response.status_code == 200
    data = response.json()
    assert data["base_info"] == BASE_INFO_LAND
    assert "objects_list" in data["details"]
    assert data["details"]["objects_list"] == {"land_objs": "OK"}


BASE_INFO_PREMISES = {
    "data": {
        "features": [
            {
                "id": 999,
                "properties": {
                    "category": 37163,
                    "options": {"registersId": 111},
                },
            }
        ]
    }
}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=BASE_INFO_PREMISES)
@patch.object(nspd_client, "get_objects_list")
def test_nspd_full_property_premises_mock(mock_details, *_):
    """Тест получения данных для Помещения (37163) - детали не должны запрашиваться"""
    response = client.get("/nspd/property/38:36:000000:333")
    assert response.status_code == 200
    data = response.json()
    assert data["details"] is None
    assert "Детальные карточки доступны только для Зданий и Земельных участков" in data["message"]
    mock_details.assert_not_called()


BASE_INFO_CHAIN = {
    "data": {
        "features": [
            {
                "id": 123,
                "properties": {
                    "category": 36369,
                    "options": {"registersId": 456},
                },
            }
        ]
    }
}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=BASE_INFO_CHAIN)
@patch.object(nspd_client, "get_objects_list", return_value=None)
@patch.object(nspd_client, "get_land_links", return_value={"ok": True})
@patch.object(nspd_client, "get_build_parts", return_value={"ok": True})
@patch.object(nspd_client, "get_permission_types", return_value={"ok": True})
def test_nspd_api_failure_during_chain(*_):
    """Тест поведения при ошибке в одном из параллельных запросов деталей"""
    response = client.get("/nspd/property/38:36:000000:111")
    assert response.status_code == 200
    data = response.json()
    assert data["details"]["objects_list"] is None
    assert data["details"]["land_links"] == {"ok": True}


@patch.object(nspd_client, "get_property_cadastral_price", return_value=None)
def test_nspd_full_property_not_found(mocked_method):
    response = client.get("/nspd/property/00:00:000000:00000")
    assert response.status_code == 404


# =============================================================================
# МОДУЛЬ: app.api.fias (ФИАС)
# =============================================================================

from app.api.fias import fias_client as api_fias_client


@patch.object(api_fias_client, "search_fias_by_cadastral", return_value=None)
def test_fias_by_cadastral_not_found(mocked_method):
    response = client.get("/fias/by-cadastral/000:00:0000")
    assert response.status_code == 404
    assert "не найдены" in response.json()["detail"]


@patch.object(api_fias_client, "get_address_hints", return_value=[])
def test_fias_search_address_not_found(mocked_method):
    response = client.get("/fias/search-address?address=нет такого адреса")
    assert response.status_code == 404


def test_fias_search_address_empty():
    """Пустой адрес отклоняется до обращения к ФИАС."""
    response = client.get("/fias/search-address?address=")
    assert response.status_code == 400


@patch.object(api_fias_client, "search_fias_by_address_id", return_value=None)
def test_fias_by_object_id_not_found(mocked_method):
    response = client.get("/fias/by-object-id/000000")
    assert response.status_code == 404


@patch.object(api_fias_client, "get_object_id_by_cadastral_number", return_value=None)
def test_fias_object_id_not_found(mocked_method):
    response = client.get("/fias/object-id/000:00:0000")
    assert response.status_code == 404


# =============================================================================
# МОДУЛЬ: app.api.sudrf (СУДРФ)
# =============================================================================


@patch("app.api.sudrf.fias_client.search_fias_by_cadastral")
@patch("app.api.sudrf.sudrf_client.get_court_by_fias_id")
@patch("app.api.sudrf.sudrf_client.get_fias_id_by_address")
def test_api_by_cadastral_full_success(mock_fias_id_by_address, mock_get_court, mock_fias):
    """Успешный путь: GUID дома найден, суд определяется напрямую, fallback не нужен."""
    mock_fias.return_value = {
        "addresses": [
            {
                "full_name": "г. Иркутск, ул. Тест, д. 1",
                "hierarchy": [{"object_type": "house", "object_guid": "guid_house"}],
            }
        ]
    }
    mock_get_court.return_value = {"court_name": "Судебный участок №10"}

    response = client.get("/sudrf/by-cadastral?cad_num=123:45:6789")

    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №10"
    mock_get_court.assert_called_once_with("guid_house")
    mock_fias_id_by_address.assert_not_called()


@patch("app.api.sudrf.fias_client.search_fias_by_cadastral")
@patch("app.api.sudrf.sudrf_client.get_court_by_fias_id")
@patch("app.api.sudrf.sudrf_client.get_fias_id_by_address")
def test_api_by_cadastral_fallback_success(mock_fias_id_by_address, mock_get_court, mock_fias):
    """Fallback-путь: GUID дома не найден, суд ищется по адресу через СУДРФ."""
    mock_fias.return_value = {
        "addresses": [
            {
                "full_name": "г. Иркутск, ул. Тест, д. 1",
                "hierarchy": [],
            }
        ]
    }
    mock_fias_id_by_address.return_value = "fallback_guid"
    mock_get_court.return_value = {"court_name": "Судебный участок №20"}

    response = client.get("/sudrf/by-cadastral?cad_num=123:45:6789")

    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №20"
    mock_get_court.assert_called_with("fallback_guid")


@patch("app.api.sudrf.fias_client.search_fias_by_cadastral")
@patch("app.api.sudrf.sudrf_client.get_fias_id_by_address")
def test_api_by_cadastral_not_found(mock_fias_id_by_address, mock_fias):
    """Нет ни ФИАС-данных, ни fallback-результата -> 404."""
    mock_fias.return_value = {"addresses": []}
    mock_fias_id_by_address.return_value = None

    response = client.get("/sudrf/by-cadastral?cad_num=1:2:3")

    assert response.status_code == 404
    assert "fallback-поиск не дал результата" in response.json()["detail"]


@patch("app.api.fias.fias_client.search_fias_by_address_id")
@patch("app.api.sudrf.sudrf_client.get_court_by_fias_id")
def test_api_by_object_id_success(mock_get_court, mock_fias):
    mock_fias.return_value = {
        "addresses": [
            {
                "full_name": "г. Иркутск, ул. Тест, д. 1",
                "hierarchy": [{"object_type": "house", "object_guid": "guid_house"}],
            }
        ]
    }
    mock_get_court.return_value = {"court_name": "Судебный участок №30"}

    response = client.get("/sudrf/by-object-id?object_id=67352892")

    assert response.status_code == 200
    assert response.json()["court_info"]["court_name"] == "Судебный участок №30"
