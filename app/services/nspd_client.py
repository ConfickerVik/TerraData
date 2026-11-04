import httpx
import logging
from typing import Optional, Dict, Any, List, Union

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

    # --- Универсальный метод для запросов к вкладкам ---

    async def _get_tab_data(self, tab_class: str, obj_id: int, registers_id: Optional[int], category_id: int, is_group: bool = False) -> Optional[Dict[str, Any]]:
        """
        Универсальный метод для получения данных из вкладок НСПД.
        Если registers_id передан, используется способ objdocId + registersId.
        Если registers_id отсутствует, используется способ categoryId + geomId.
        """
        url = f"{self.base_url}/v1/tab-group-data" if is_group else f"{self.base_url}/v1/tab-values-data"
        params = {"tabClass": tab_class}
        
        if registers_id:
            params.update({"objdocId": obj_id, "registersId": registers_id})
        else:
            params.update({"categoryId": category_id, "geomId": obj_id})
            
        return await self._make_request(url, params)

    # --- Методы для Зданий (Buildings) ---

    async def get_objects_list(self, obj_id: int, registers_id: Optional[int], category_id: int) -> Optional[Dict[str, Any]]:
        """Список помещений и машиномест, привязанных к объекту."""
        return await self._get_tab_data("objectsList", obj_id, registers_id, category_id, is_group=True)

    async def get_land_links(self, obj_id: int, registers_id: Optional[int], category_id: int) -> Optional[Dict[str, Any]]:
        """Связанные земельные участки."""
        return await self._get_tab_data("landLinks", obj_id, registers_id, category_id)

    async def get_build_parts(self, obj_id: int, registers_id: Optional[int], category_id: int) -> Optional[Dict[str, Any]]:
        """Части ОКС."""
        return await self._get_tab_data("buildParts", obj_id, registers_id, category_id)

    async def get_permission_types(self, obj_id: int, registers_id: Optional[int], category_id: int) -> Optional[Dict[str, Any]]:
        """Виды разрешенного использования."""
        return await self._get_tab_data("permissionType", obj_id, registers_id, category_id)

    # --- Методы для Земельных Участков (Land) ---

    async def get_land_objects_list(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Список объектов на земельном участке."""
        return await self._get_tab_data("objectsList", geom_id, None, self.CATEGORY_LAND, is_group=True)

    async def get_land_permission_types(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Виды разрешенного использования (ЗУ)."""
        return await self._get_tab_data("permissionType", geom_id, None, self.CATEGORY_LAND)

    async def get_land_parts(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Части земельного участка."""
        return await self._get_tab_data("landParts", geom_id, None, self.CATEGORY_LAND)

    async def get_land_composition(self, geom_id: int) -> Optional[Dict[str, Any]]:
        """Состав единого земельного участка (ЕЗП)."""
        return await self._get_tab_data("compositionLand", geom_id, None, self.CATEGORY_LAND)

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
