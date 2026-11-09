from fastapi import APIRouter, HTTPException, Query
from app.services.fias_client import FIASClient
from app.services.sudrf_client import SudrfClient
from app.services.address_cleaner import AddressCleaner
from typing import Optional, Dict, Any

router = APIRouter(prefix="/sudrf", tags=["SUDRF Data"])

fias_client = FIASClient()
sudrf_client = SudrfClient()

async def _resolve_court_info(fias_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Вспомогательная функция для извлечения судебного участка из данных ФИАС.
    Реализует основную логику (по GUID дома) и fallback-логику (по адресу через Sudrf).
    """
    if not fias_data:
        return None

    # 1. Попытка извлечь GUID дома из иерархии ФИАС
    fias_guid = None
    try:
        hierarchy = fias_data["addresses"][0]["hierarchy"]
        for item in hierarchy:
            if item["object_type"] == "house":
                fias_guid = item["object_guid"]
                break
    except (KeyError, IndexError):
        pass

    # 2. Попытка получить суд по GUID
    if fias_guid:
        court_info = await sudrf_client.get_court_by_fias_id(fias_guid)
        if court_info:
            return court_info

    # 3. Fallback: если GUID не найден или суд по GUID не определился,
    # пробуем найти fias_id через текстовый адрес в Sudrf
    try:
        address_for_fallback = fias_data["addresses"][0]["full_name"]
        cleaned_adr = AddressCleaner.clean(address_for_fallback)
        fallback_guid = await sudrf_client.get_fias_id_by_address(cleaned_adr)
        if fallback_guid:
            return await sudrf_client.get_court_by_fias_id(fallback_guid)
    except (KeyError, IndexError):
        pass

    return None

async def _check_resolve(fias_data: Optional[Dict[str, Any]] ) -> Optional[Dict[str, Any]]:
    # Извлекаем судебный участок
    court_info = await _resolve_court_info(fias_data)

    fias_ok = bool(fias_data and fias_data.get("addresses"))
    court_ok = court_info is not None

    if not fias_ok and not court_ok:
        raise HTTPException(status_code=404,
                            detail="Сведения в ФИАС по данному кадастровому номеру не найдены и fallback-поиск не дал результата")

    return {
        "court_info": court_info
    }

@router.get("/by-cadastral")
async def get_court_by_cadastral(
    cad_num: str,
    address_type: int = Query(1, description="1 - административное деление, 2 - муниципальное")
):
    """
    Полный цикл: Кадастр -> ФИАС GUID -> Sudrf Суд.
    """
    fias_data = await fias_client.search_fias_by_cadastral(cad_num, address_type)
    court_info = await _check_resolve(fias_data)

    return court_info

@router.get("/by-address")
async def get_fias_by_cadastral(
        address: str,
        address_type: int = Query(1, description="1 - административное деление, 2 - муниципальное")
):
    """
    Полный цикл: Адрес -> ФИАС GUID -> Sudrf -> Суд.
    """
    object_id = await fias_client.search_fias_by_address(address, address_type)

    if object_id:
        fias_data = await fias_client.get_info_by_object_id(object_id["object_id"])
        court_info = await _check_resolve(fias_data)

        return court_info

    return None

@router.get("/by-object-id")
async def get_fias_by_object_id(
    object_id: str,
    address_type: int = Query(1, description="1 - административное деление, 2 - муниципальное")
):
    """
    Полный цикл: ObjectID -> ФИАС данные -> Sudrf -> Суд.
    """
    fias_data = await fias_client.search_fias_by_address_id(object_id, address_type)
    court_info = await _resolve_court_info(fias_data)

    if not fias_data and not court_info:
        raise HTTPException(status_code=404, detail="Сведения по ObjectID не найдены и fallback-поиск не дал результата")

    return {
        "fias_data": fias_data,
        "court_info": court_info
    }
