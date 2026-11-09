import httpx
import json
import logging
from typing import List, Dict, Optional, Any
from app.services.address_cleaner import AddressCleaner

logger = logging.getLogger(__name__)

class FIASClient:
    def __init__(self, timeout=30.0):
        self.timeout = timeout
        self.base_url_public = "https://fias-public-service.nalog.ru/api/spas/v2.0"
        self.base_url_nalog = "https://fias.nalog.ru"

    async def get_master_token(self) -> Optional[str]:
        """Получение мастер токена для доступа к API ФИАС."""
        url = f"{self.base_url_nalog}/Home/GetSpasSettings?url=https%3A%2F%2Ffias.nalog.ru%2F"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.get(url)
            if response.status_code == 200:
                content = json.loads(response.text)
                return content.get('Token')
        except Exception as e:
            logger.error(f"Error getting master token: {e}")
        return None

    async def get_object_id_by_cadastral_number(self, cadastral_number: str) -> Optional[str]:
        """Получение уникального ObjectID по кадастровому номеру."""
        url = f"{self.base_url_nalog}/ExtendedSearch/GetObjectsByCadastralNumber"
        form = {"cadastralNumber": cadastral_number}
        token = await self.get_master_token()
        if not token:
            return None

        try:
            headers = {"master-token": token}
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.post(url, data=form, headers=headers)
            if response.status_code == 200:
                object_ids = json.loads(response.text).get("ObjectIds", [])
                return object_ids[0] if object_ids else None
        except Exception as e:
            logger.error(f"Error getting object ID by cadastral: {e}")
        return None

    async def get_address_hints(self, address: str) -> List[Dict[str, Any]]:
        """
        Получение списка всех подходящих вариантов адресов (подсказок).
        Возвращает список словарей с object_id и текстовым представлением.
        """
        # Очищаем адрес перед запросом в ФИАС
        cleaned_address = AddressCleaner.clean(address)
        if not cleaned_address:
            return []

        url = f"{self.base_url_public}/GetAddressHint"
        payload = {"searchString": cleaned_address, "addressType": 2, "searchNonActive": False}
        token = await self.get_master_token()
        if not token:
            return []

        try:
            headers = {"master-token": token}
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                content = json.loads(response.text)
                hints = content.get("hints", [])
                return [
                    {
                        "object_id": h.get("object_id"),
                        "value": h.get("full_name"),
                        "path": h.get("path")
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
        token = await self.get_master_token()
        if not token:
            return None

        try:
            headers = {"master-token": token}
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.get(url, headers=headers)
            if response.status_code != 200:
                return None
            data = json.loads(response.text)
        except Exception as e:
            logger.error(f"Error getting info by object ID: {e}")
            return None

        # Дополнительная информация по объекту недвижимости.
        details = await self.get_object_details(object_id)
        if details:
            data["object_details"] = details

        return data

    async def get_object_details(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение дополнительной информации об объекте недвижимости по ObjectID
        (реестровый номер, даты начала/обновления, федеральный округ и т.д.).
        """
        url = f"{self.base_url_nalog}/Search/ObjectDetails?objectId={object_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as session:
                response = await session.get(url)
            if response.status_code == 200:
                return json.loads(response.text)
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
