import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.services.address_cleaner import AddressCleaner

logger = logging.getLogger(__name__)

# Заголовки, имитирующие браузерный запрос: на fias.nalog.ru стоит анти-бот,
# и дефолтный User-Agent python-httpx быстрее попадает под rate-limit.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://fias.nalog.ru/",
    "Accept": "application/json, text/plain, */*",
}


class FIASClient:
    def __init__(self, timeout=60.0):
        self.timeout = timeout
        self.base_url_public = "https://fias-public-service.nalog.ru/api/spas/v2.0"
        self.base_url_nalog = "https://fias.nalog.ru"

        # Кэш master-токена: запрашиваем его один раз и переиспользуем,
        # чтобы не упираться в rate-limit / временные баны по IP.
        self._token: str | None = None
        self._token_ts = 0.0
        self._token_ttl = 25 * 60  # секунд (токен ФИАС живёт ~30 минут)
        self._token_lock = asyncio.Lock()

    async def get_master_token(self, force: bool = False) -> str | None:
        """
        Получение master-токена для доступа к API ФИАС.

        Токен кэшируется на `_token_ttl` секунд; при неудаче выполняется до
        3 попыток с экспоненциальной задержкой. Блокировка гарантирует, что
        при параллельных запросах токен запрашивается только один раз.
        """
        async with self._token_lock:
            if not force and self._token and (time.monotonic() - self._token_ts) < self._token_ttl:
                return self._token

            url = f"{self.base_url_nalog}/Home/GetSpasSettings?url=https%3A%2F%2Ffias.nalog.ru%2F"

            for attempt in range(3):
                try:
                    async with httpx.AsyncClient(
                        timeout=self.timeout, headers=_BROWSER_HEADERS
                    ) as session:
                        response = await session.get(url)

                    if response.status_code == 200:
                        token = response.json().get("Token")
                        if token:
                            self._token = token
                            self._token_ts = time.monotonic()
                            return token
                        logger.warning(
                            "GetSpasSettings вернул 200, но без Token: %.200s", response.text
                        )
                    else:
                        logger.warning(
                            "GetSpasSettings attempt=%d status=%s body=%.200s",
                            attempt + 1,
                            response.status_code,
                            response.text,
                        )
                except Exception as e:
                    logger.warning("GetSpasSettings attempt=%d error: %s", attempt + 1, e)

                if attempt < 2:
                    await asyncio.sleep(2**attempt)  # 1с, 2с

            return None

    async def _authorized_headers(self, force: bool = False) -> dict[str, str] | None:
        token = await self.get_master_token(force=force)
        if not token:
            return None
        return {"master-token": token}

    async def _request_with_token(
        self,
        request: Callable[[dict[str, str]], Awaitable[httpx.Response]],
    ) -> httpx.Response | None:
        """
        Выполняет авторизованный запрос. При 401/403 один раз принудительно
        обновляет master-токен и повторяет. Возвращает None, если токен
        получить не удалось.
        """
        headers = await self._authorized_headers()
        if headers is None:
            return None

        response = await request(headers)
        if response.status_code in (401, 403):
            logger.warning(
                "API ФИАС отклонил master-token (status=%s), обновляю токен один раз",
                response.status_code,
            )
            headers = await self._authorized_headers(force=True)
            if headers is None:
                return response
            response = await request(headers)

        return response

    async def get_object_id_by_cadastral_number(self, cadastral_number: str) -> str | None:
        """Получение уникального ObjectID по кадастровому номеру."""
        url = f"{self.base_url_nalog}/ExtendedSearch/GetObjectsByCadastralNumber"
        form = {"cadastralNumber": cadastral_number}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:

                async def do(headers: dict[str, str]) -> httpx.Response:
                    return await session.post(url, data=form, headers=headers)

                response = await self._request_with_token(do)

            if not response or response.status_code != 200:
                logger.warning(
                    "GetObjectsByCadastralNumber status=%s",
                    response.status_code if response else "no-token",
                )
                return None

            object_ids = response.json().get("ObjectIds", [])
            return object_ids[0] if object_ids else None
        except Exception as e:
            logger.error(f"Error getting object ID by cadastral: {e}")
            return None

    async def get_address_hints(self, address: str) -> list[dict[str, Any]]:
        """
        Получение списка всех подходящих вариантов адресов (подсказок).
        Возвращает список словарей с object_id и текстовым представлением.
        """
        cleaned_address = AddressCleaner.clean(address)
        if not cleaned_address:
            return []

        url = f"{self.base_url_public}/GetAddressHint"
        payload = {"searchString": cleaned_address, "addressType": 2, "searchNonActive": False}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:

                async def do(headers: dict[str, str]) -> httpx.Response:
                    return await session.post(url, json=payload, headers=headers)

                response = await self._request_with_token(do)

            if not response or response.status_code != 200:
                logger.warning(
                    "GetAddressHint status=%s",
                    response.status_code if response else "no-token",
                )
                return []

            hints = response.json().get("hints", [])
            return [
                {
                    "object_id": h.get("object_id"),
                    "value": h.get("full_name"),
                    "path": h.get("path"),
                }
                for h in hints
            ]
        except Exception as e:
            logger.error(f"Error getting address hints: {e}")
            return []

    async def get_info_by_object_id(self, object_id: str, address_type: int = 1):
        """
        Получение детальной информации об объекте по его ObjectID.
        address_type: 1 - административное деление, 2 - муниципальное.

        В результат дополнительно добавляется ключ `object_details`
        (сведения из /Search/ObjectDetails: ReesterNumber, StartDate,
        UpdateDate и т.д.).
        """
        url = f"{self.base_url_public}/GetAddressItemById?object_id={object_id}&address_type={address_type}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:

                async def do(headers: dict[str, str]) -> httpx.Response:
                    return await session.get(url, headers=headers)

                response = await self._request_with_token(do)

            if not response or response.status_code != 200:
                logger.warning(
                    "GetAddressItemById status=%s",
                    response.status_code if response else "no-token",
                )
                return None

            data = response.json()
        except Exception as e:
            logger.error(f"Error getting info by object ID: {e}")
            return None

        # Дополнительная информация по объекту недвижимости.
        details = await self.get_object_details(object_id)
        if details:
            data["object_details"] = details

        return data

    async def get_object_details(self, object_id: str) -> dict[str, Any] | None:
        """
        Получение дополнительной информации об объекте недвижимости по ObjectID
        (реестровый номер, даты начала/обновления, федеральный округ и т.д.).
        """
        url = f"{self.base_url_nalog}/Search/ObjectDetails?objectId={object_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.get(url)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "ObjectDetails status=%s body=%.200s", response.status_code, response.text
            )
        except Exception as e:
            logger.error(f"Error getting object details: {e}")
        return None

    async def search_fias_by_cadastral(self, cadastral_number: str, address_type: int = 1):
        """Интегрированный поиск информации ФИАС по кадастровому номеру."""
        object_id = await self.get_object_id_by_cadastral_number(cadastral_number)
        if object_id:
            return await self.get_info_by_object_id(object_id, address_type)
        return None

    async def search_fias_by_address_id(self, object_id: str, address_type: int = 1):
        """Поиск детальной информации по конкретному ID, полученному из подсказок."""
        return await self.get_info_by_object_id(object_id, address_type)

    async def search_fias_by_address(self, address: str, address_type: int = 1):
        clean_address = AddressCleaner.clean(address)
        if clean_address:
            hints = await self.get_address_hints(clean_address)
            return hints[0] if hints else None
