import asyncio
import logging
from typing import Dict, Any, Optional

from app.services.rosreestr_client import RosreestrClient
from app.services.nspd_client import NspdClient
from app.services.fias_client import FIASClient
from app.services.sudrf_client import SudrfClient

logger = logging.getLogger(__name__)


class ReportService:
    """
    Сервис агрегации данных для аналитического отчёта.

    Собирает данные из нескольких источников (Росреестр, НСПД, ФИАС, СУДРФ)
    и сводит их в единую нормализованную структуру отчёта.

    Росреестр — ядро отчёта (всегда собирается). Остальные источники
    опциональны и включаются флагами. При частичном сбое источника
    соответствующая секция получает значение None (в PDF отобразится
    как «данные недоступны»).
    """

    def __init__(
        self,
        rosreestr_client: Optional[RosreestrClient] = None,
        nspd_client: Optional[NspdClient] = None,
        fias_client: Optional[FIASClient] = None,
        sudrf_client: Optional[SudrfClient] = None,
    ):
        self.rosreestr = rosreestr_client or RosreestrClient()
        self.nspd = nspd_client or NspdClient()
        self.fias = fias_client or FIASClient()
        self.sudrf = sudrf_client or SudrfClient()

    async def gather_report(
        self,
        cad_num: str,
        include_nspd: bool = True,
        include_fias: bool = True,
        include_sudrf: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Собирает нормализованную структуру отчёта по кадастровому номеру.

        Возвращает None, если Росреестр (ядро) не вернул данные.
        """
        # --- Росреестр: ядро отчёта, всегда собирается ---
        rosreestr_raw = await self.rosreestr.get_full_info(cad_num)
        if not rosreestr_raw:
            logger.warning(f"Rosreestr returned no data for {cad_num}; report cannot be built")
            return None

        elements = rosreestr_raw.get("elements", [])
        obj = elements[0] if elements else {}

        # --- Опциональные источники (параллельно) ---
        nspd_task = self._collect_nspd(cad_num) if include_nspd else None
        fias_task = self._collect_fias(cad_num) if include_fias else None
        sudrf_task = self._collect_sudrf(cad_num, include_fias) if include_sudrf else None

        nspd_data = await nspd_task if nspd_task else None
        fias_data = await fias_task if fias_task else None
        sudrf_data = await sudrf_task if sudrf_task else None

        return self._build_report(cad_num, obj, nspd_data, fias_data, sudrf_data)

    async def _collect_nspd(self, cad_num: str) -> Optional[Dict[str, Any]]:
        """Собирает данные НСПД (база + геометрия). Ошибки -> None."""
        try:
            base_info = await self.nspd.get_property_cadastral_price(cad_num)
            if not base_info:
                return None

            geometry = None
            try:
                feature = base_info.get("data", {}).get("features", [{}])[0]
                raw_geom = feature.get("geometry")
                if raw_geom:
                    from app.services.coords_converter import CoordsConverter
                    geometry = CoordsConverter.convert_geometry(raw_geom)
            except (KeyError, IndexError):
                geometry = None

            return {
                "base_info": base_info,
                "geometry": geometry,
            }
        except Exception as e:
            logger.error(f"NSPD collection error for {cad_num}: {e}")
            return None

    async def _collect_fias(self, cad_num: str) -> Optional[Dict[str, Any]]:
        """Собирает данные ФИАС. Ошибки -> None."""
        try:
            data = await self.fias.search_fias_by_cadastral(cad_num)
            return data if data else None
        except Exception as e:
            logger.error(f"FIAS collection error for {cad_num}: {e}")
            return None

    async def _collect_sudrf(self, cad_num: str, include_fias: bool) -> Optional[Dict[str, Any]]:
        """
        Собирает данные СУДРФ (судебный участок).

        Логика определения суда: кадастровый номер -> ФИАС GUID дома -> СУДРФ.
        ФИАС-данные используются всегда (независимо от include_fias), так как
        они нужны для получения GUID.
        """
        try:
            fias_data = await self.fias.search_fias_by_cadastral(cad_num)
            if not fias_data:
                return None

            fias_guid = self._extract_house_guid(fias_data)

            if fias_guid:
                court = await self.sudrf.get_court_by_fias_id(fias_guid)
                if court:
                    return court

            # Fallback по адресу
            from app.services.address_cleaner import AddressCleaner
            try:
                full_name = fias_data.get("addresses", [{}])[0].get("full_name")
                cleaned = AddressCleaner.clean(full_name)
                fallback_guid = await self.sudrf.get_fias_id_by_address(cleaned) if cleaned else None
                if fallback_guid:
                    return await self.sudrf.get_court_by_fias_id(fallback_guid)
            except (KeyError, IndexError):
                pass

            return None
        except Exception as e:
            logger.error(f"SUDRF collection error for {cad_num}: {e}")
            return None

    @staticmethod
    def _extract_house_guid(fias_data: Dict[str, Any]) -> Optional[str]:
        """Извлекает GUID дома из иерархии адреса ФИАС."""
        try:
            hierarchy = fias_data.get("addresses", [{}])[0].get("hierarchy", [])
            for item in hierarchy:
                if item.get("object_type") == "house":
                    return item.get("object_guid")
        except (KeyError, IndexError):
            pass
        return None

    @staticmethod
    def _build_report(
        cad_num: str,
        obj: Dict[str, Any],
        nspd_data: Optional[Dict[str, Any]],
        fias_data: Optional[Dict[str, Any]],
        sudrf_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Собирает финальную нормализованную структуру отчёта."""
        address = obj.get("address", {}) or {}
        return {
            "general": {
                "cad_num": obj.get("cadNumber", cad_num),
                "obj_type": obj.get("objType"),
                "address": address.get("readableAddress"),
                "area": obj.get("area"),
                "area_unit": ReportService._extract_area_unit(obj),
                "floor": obj.get("floor"),
                "underFloor": obj.get("undergroundFloor"),
                "level_floor": obj.get("levelFloor"),
                "ownership_type": obj.get("ownershipType"),
                "oks_wall_material": obj.get("oksWallMaterial"),
                "oks_commisioning_year": obj.get("oksCommisioningYear"),
                "purpose": obj.get("purpose"),
                "cad_cost": obj.get("cadCost"),
                "cad_cost_date": obj.get("cadCostDeterminationDate"),
                "reg_date": obj.get("regDate"),
                "info_update_date" : obj.get("infoUpdateDate")
            },
            "spatial": nspd_data,
            "legal": {
                "rights": obj.get("rights", []),
                "encumbrances": obj.get("encumbrances", []),
            },
            "fias": fias_data,
            "court": sudrf_data,
        }


    @staticmethod
    def _extract_area_unit(obj: Dict[str, Any]) -> str:
        """Извлекает единицу измерения площади из mainCharacters."""
        try:
            chars = obj.get("mainCharacters", [])
            if chars:
                return chars[0].get("unitDescription", "кв.м")
        except (KeyError, IndexError):
            pass
        return "кв.м"
