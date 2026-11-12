import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NspdClient:
    def __init__(self):
        self.base_url = "https://nspd.gov.ru/api/geoportal"
        # Категории объектов
        self.CATEGORY_BUILDINGS = 36369  # Здания/ОКС
        self.CATEGORY_PREMISES = 37163  # Помещения/Квартиры
        self.CATEGORY_LAND = 36368  # Земельные участки

    async def get_property_cadastral_price(self, cad_num: str) -> dict[str, Any] | None:
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

    def get_category_id(self, data: dict[str, Any]) -> int | None:
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

    async def collect_details(self, base_info: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Собирает категорийные вкладки (tab) объекта по базовой карточке НСПД.

        Набор вкладок зависит от категории объекта (Здание/ЗУ). Для помещений
        и неизвестных категорий возвращает None. Ключи ответа могут отличаться
        даже внутри одной категории, поэтому все обращения защищены .get().
        """
        if not base_info:
            return None

        try:
            feature = base_info["data"]["features"][0]
        except (KeyError, IndexError, TypeError):
            return None

        category_id = self.get_category_id(base_info)
        obj_id = feature.get("id")
        options = (feature.get("properties") or {}).get("options") or {}
        registers_id = options.get("registersId")

        if category_id == self.CATEGORY_BUILDINGS:
            results = await asyncio.gather(
                self.get_objects_list(obj_id, registers_id, category_id),
                self.get_land_links(obj_id, registers_id, category_id),
                self.get_build_parts(obj_id, registers_id, category_id),
                self.get_permission_types(obj_id, registers_id, category_id),
            )
            return {
                "objects_list": results[0],
                "land_links": results[1],
                "build_parts": results[2],
                "permission_types": results[3],
            }

        if category_id == self.CATEGORY_LAND:
            results = await asyncio.gather(
                self.get_land_objects_list(obj_id),
                self.get_land_permission_types(obj_id),
                self.get_land_parts(obj_id),
                self.get_land_composition(obj_id),
            )
            return {
                "objects_list": results[0],
                "permission_types": results[1],
                "land_parts": results[2],
                "composition_land": results[3],
            }

        return None

    # --- Универсальный метод для запросов к вкладкам ---

    async def _get_tab_data(
        self,
        tab_class: str,
        obj_id: int,
        registers_id: int | None,
        category_id: int,
        is_group: bool = False,
    ) -> dict[str, Any] | None:
        """
        Универсальный метод для получения данных из вкладок НСПД.
        Если registers_id передан, используется способ objdocId + registersId.
        Если registers_id отсутствует, используется способ categoryId + geomId.
        """
        url = (
            f"{self.base_url}/v1/tab-group-data"
            if is_group
            else f"{self.base_url}/v1/tab-values-data"
        )
        params = {"tabClass": tab_class}

        if registers_id:
            params.update({"objdocId": obj_id, "registersId": registers_id})
        else:
            params.update({"categoryId": category_id, "geomId": obj_id})

        return await self._make_request(url, params)

    # --- Методы для Зданий (Buildings) ---

    async def get_objects_list(
        self, obj_id: int, registers_id: int | None, category_id: int
    ) -> dict[str, Any] | None:
        """Список помещений и машиномест, привязанных к объекту."""
        return await self._get_tab_data(
            "objectsList", obj_id, registers_id, category_id, is_group=True
        )

    async def get_land_links(
        self, obj_id: int, registers_id: int | None, category_id: int
    ) -> dict[str, Any] | None:
        """Связанные земельные участки."""
        return await self._get_tab_data("landLinks", obj_id, registers_id, category_id)

    async def get_build_parts(
        self, obj_id: int, registers_id: int | None, category_id: int
    ) -> dict[str, Any] | None:
        """Части ОКС."""
        return await self._get_tab_data("buildParts", obj_id, registers_id, category_id)

    async def get_permission_types(
        self, obj_id: int, registers_id: int | None, category_id: int
    ) -> dict[str, Any] | None:
        """Виды разрешенного использования."""
        return await self._get_tab_data("permissionType", obj_id, registers_id, category_id)

    # --- Методы для Земельных Участков (Land) ---

    async def get_land_objects_list(self, geom_id: int) -> dict[str, Any] | None:
        """Список объектов на земельном участке."""
        return await self._get_tab_data(
            "objectsList", geom_id, None, self.CATEGORY_LAND, is_group=True
        )

    async def get_land_permission_types(self, geom_id: int) -> dict[str, Any] | None:
        """Виды разрешенного использования (ЗУ)."""
        return await self._get_tab_data("permissionType", geom_id, None, self.CATEGORY_LAND)

    async def get_land_parts(self, geom_id: int) -> dict[str, Any] | None:
        """Части земельного участка."""
        return await self._get_tab_data("landParts", geom_id, None, self.CATEGORY_LAND)

    async def get_land_composition(self, geom_id: int) -> dict[str, Any] | None:
        """Состав единого земельного участка (ЕЗП)."""
        return await self._get_tab_data("compositionLand", geom_id, None, self.CATEGORY_LAND)

    async def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Вспомогательный метод для выполнения GET запросов к НСПД."""
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                if response.status_code == 200:
                    return response.json()
                logger.warning(
                    f"NSPD API returned status {response.status_code} for params {params}"
                )
                return None
            except Exception as e:
                logger.error(f"NSPD API request error: {e}")
                return None
