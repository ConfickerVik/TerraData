import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class NspdClient:
    def __init__(self):
        self.base_url = "https://nspd.gov.ru/api/geoportal"
        # Категории объектов
        self.CATEGORY_BUILDINGS = 36369  # Здания/ОКС
        self.CATEGORY_PREMISES = 37163   # Помещения/Квартиры
        self.CATEGORY_LAND = 36368       # Земельные участки

    async def get_property_cadastral_price(self, cad_num: str) -> Optional[Dict[str, Any]]:
        """
        Запрос данных по объекту недвижимости (кадастровая стоимость и общие сведения).
        Работает для всех категорий объектов.
        """
        url = f"{self.base_url}/v2/search/cadastralPrice"
        params = {"query": cad_num}
        
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                if response.status_code == 200:
                    return response.json()
                
                logger.warning(f"NSPD API returned status {response.status_code} for {cad_num}")
                return None
            except Exception as e:
                logger.error(f"NSPD API request error: {e}")
                return None

    def get_category_id(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Извлекает categoryId объекта из ответа API НСПД.
        """
        try:
            features = data.get("data", {}).get("features", [])
            if features:
                return features[0]["properties"]["category"]
        except (KeyError, IndexError):
            pass
        return None

    # --- Методы для Зданий (Buildings) ---

    async def get_objects_list(self, objdoc_id: int, registers_id: int) -> Optional[Dict[str, Any]]:
        """Список помещений и машиномест, привязанных к объекту (Здания)."""
        url = f"{self.base_url}/v1/tab-group-data"
        params = {"tabClass": "objectsList", "objdocId": objdoc_id, "registersId": registers_id}
        return await self._make_request(url, params)

    async def get_land_links(self, objdoc_id: int, registers_id: int) -> Optional[Dict[str, Any]]:
        """Связанные земельные участки (Здания)."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "landLinks", "objdocId": objdoc_id, "registersId": registers_id}
        return await self._make_request(url, params)

    async def get_build_parts(self, objdoc_id: int, registers_id: int) -> Optional[Dict[str, Any]]:
        """Части ОКС (Здания)."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "buildParts", "objdocId": objdoc_id, "registersId": registers_id}
        return await self._make_request(url, params)

    async def get_permission_types(self, objdoc_id: int, registers_id: int) -> Optional[Dict[str, Any]]:
        """Виды разрешенного использования (Здания)."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "permissionType", "objdocId": objdoc_id, "registersId": registers_id}
        return await self._make_request(url, params)

    # --- Методы для Земельных Участков (Land) ---

    async def get_land_objects_list(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Список объектов на земельном участке."""
        url = f"{self.base_url}/v1/tab-group-data"
        params = {"tabClass": "objectsList", "categoryId": self.CATEGORY_LAND, "geomId": geom_id}
        return await self._make_request(url, params)

    async def get_land_permission_types(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Виды разрешенного использования (ЗУ)."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "permissionType", "categoryId": self.CATEGORY_LAND, "geomId": geom_id}
        return await self._make_request(url, params)

    async def get_land_parts(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Части земельного участка."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "landParts", "categoryId": self.CATEGORY_LAND, "geomId": geom_id}
        return await self._make_request(url, params)

    async def get_land_composition(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Состав единого земельного участка (ЕЗП)."""
        url = f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": "compositionLand", "categoryId": self.CATEGORY_LAND, "geomId": geom_id}
        return await self._make_request(url, params)

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Вспомогательный метод для выполнения GET запросов к НСПД."""
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"NSPD API returned status {response.status_code} for params {params}")
                return None
            except Exception as e:
                logger.error(f"NSPD API request error: {e}")
                return None
