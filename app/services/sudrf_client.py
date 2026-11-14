import json
import logging
from typing import Any

import httpx

from app.services.types.court_types import COURT_TYPE_ORDER

logger = logging.getLogger(__name__)


class SudrfClient:
    """
    Сервис для взаимодействия с API sudrf.ru для получения данных о судебных участках.
    """

    def __init__(self, timeout=30.0):
        self.timeout = timeout
        self.base_url = "https://sudrf.ru/api.php"
        self.suggest_url = "https://sudrf.ru/suggestions/api/4_1/rs/suggest/address"

    async def get_courts_by_fias(self, fias_id: str) -> list[dict[str, Any]] | None:
        """
        Получение списка судов по FIAS ID (GUID) напрямую из API sudrf.ru.
        Метод: getCourtListByFiasCode.

        Возвращает отсортированный список всех судов (мировой участок, районный,
        областной, апелляционный, кассационный, военные) с их типом и реквизитами.
        """
        url = f"{self.base_url}?opt=court_list&action=getCourtListByFiasCode&fiasId={fias_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.get(url)

            if response.status_code != 200:
                return None

            content = json.loads(response.text)
            courts_list = content.get("list", [])
            if not courts_list:
                return None

            # Собираем все суды: плоские записи списка + вложенные
            # вышестоящие суды (KJ, AJ, OS, AV, KV, OV). Дедуплицируем по VNKOD.
            collected: dict[str, dict[str, Any]] = {}
            for entry in courts_list:
                if not isinstance(entry, dict):
                    continue
                if entry.get("VNKOD"):
                    collected[entry["VNKOD"]] = entry
                for value in entry.values():
                    if isinstance(value, dict) and value.get("VNKOD"):
                        collected.setdefault(value["VNKOD"], value)

            if not collected:
                return None

            # Тип суда закодирован в VNKOD (позиции 2-3): MS, RS, OS, AJ, KJ, ...
            courts = []
            for vncod, entry in collected.items():
                courts.append(
                    {
                        "type": vncod[2:4] if len(vncod) >= 4 else vncod,
                        "vncod": vncod,
                        "name": entry.get("ZNACHATR", ""),
                        "address": entry.get("ADDRESS", ""),
                        "url": entry.get("PRIM", ""),
                    }
                )

            # Порядок вывода: мировой участок -> районный -> областной ->
            # апелляционный -> кассационный -> военные суды.
            courts.sort(
                key=lambda c: (
                    COURT_TYPE_ORDER.index(c["type"])
                    if c["type"] in COURT_TYPE_ORDER
                    else len(COURT_TYPE_ORDER)
                )
            )

            return courts
        except Exception as e:
            logger.error(f"Error getting courts by fias_id {fias_id}: {e}")
        return None

    async def get_court_by_fias_id(
        self, fias_id: str, region_code: str | None = None
    ) -> dict[str, Any] | None:
        """
        Получение основного судебного участка по FIAS ID (GUID).
        Метод: getCourtListByFiasCode.

        Основной суд по умолчанию — судебный участок (MS), иначе первый из списка.
        """
        courts = await self.get_courts_by_fias(fias_id)
        if not courts:
            return None

        # Основной суд по умолчанию — судебный участок (MS), иначе первый.
        main_court = next((c for c in courts if c["type"] == "MS"), courts[0])

        return {
            "court_name": main_court["name"],
            "vncod": main_court["vncod"],
            "courts": courts,
        }

    async def get_fias_id_by_address(self, address: str) -> str | None:
        """
        Поиск fias_id через внутренний сервис подсказок sudrf.ru.
        Используется как fallback-метод, если основной поиск ФИАС не дал результата.
        """
        payload = {
            "query": address,
            "from_bound": {"value": "region"},
            "to_bound": {"value": "house"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.post(self.suggest_url, json=payload)

            if response.status_code == 200:
                content = json.loads(response.text)
                suggestions = content.get("suggestions", [])
                if suggestions:
                    # Извлекаем fias_id из первого совпадения
                    # В sudrf структуре fias_id обычно лежит в data -> fias_id
                    return suggestions[0].get("data", {}).get("fias_id")
        except Exception as e:
            logger.error(f"Error getting fias_id from sudrf suggest by address '{address}': {e}")
        return None
