from fastapi import APIRouter, HTTPException, Query

from app.services.fias_client import FIASClient

router = APIRouter(prefix="/fias", tags=["FIAS Data"])

fias_client = FIASClient()


@router.get("/by-cadastral")
async def get_fias_by_cadastral(
    cad_num: str,
    address_type: int = Query(1, description="1 - административное деление, 2 - муниципальное"),
):
    """
    Получение сведений ФИАС по кадастровому номеру объекта.
    """
    data = await fias_client.search_fias_by_cadastral(cad_num, address_type)
    if not data:
        raise HTTPException(
            status_code=404, detail="Сведения в ФИАС по данному кадастровому номеру не найдены"
        )
    return data


@router.get("/search-address")
async def search_fias_address(
    address: str,
):
    """
    Поиск подходящих вариантов адреса в ФИАС (с предварительной очисткой).
    Возвращает список кандидатов с их ID и текстовым представлением.
    """
    if not address:
        raise HTTPException(status_code=400, detail="Адрес не может быть пустым")

    hints = await fias_client.get_address_hints(address)
    if not hints:
        raise HTTPException(status_code=404, detail="Подходящие адреса в ФИАС не найдены")
    return hints


@router.get("/by-object-id")
async def get_fias_by_object_id(
    object_id: str,
    address_type: int = Query(1, description="1 - административное деление, 2 - муниципальное"),
):
    """
    Получение детальной информации о ФИАС объекте по его ObjectID.
    """
    data = await fias_client.search_fias_by_address_id(object_id, address_type)
    if not data:
        raise HTTPException(
            status_code=404, detail="Сведения по данному ObjectID в ФИАС не найдены"
        )
    return data


@router.get("/object-id-by-cadastral")
async def get_fias_object_id(cad_num: str):
    """
    Получение только внутреннего ObjectID ФИАС по кадастровому номеру.
    """
    object_id = await fias_client.get_object_id_by_cadastral_number(cad_num)
    if not object_id:
        raise HTTPException(
            status_code=404, detail="ObjectID для данного кадастрового номера не найден"
        )
    return {"object_id": object_id}
