from fastapi import APIRouter, HTTPException

from app.services.coords_converter import CoordsConverter
from app.services.nspd_client import NspdClient

router = APIRouter(prefix="/nspd", tags=["NSPD Data"])

nspd_client = NspdClient()


@router.get("/cadastral-price")
async def get_cadastral_price(cad_num: str):
    """
    Запрос только кадастровой стоимости и базовых сведений об объекте.
    Вынесен в отдельный эндпоинт для дальнейшего уточнения параметров.
    """
    data = await nspd_client.get_property_cadastral_price(cad_num)
    if not data:
        raise HTTPException(
            status_code=404, detail="Сведения о кадастровой стоимости в НСПД не найдены"
        )
    return data


@router.get("/property")
async def get_full_property_data(cad_num: str):
    """
    Сбор всех доступных сведений об объекте недвижимости из НСПД по кадастровому номеру.
    Выполняет цепочку запросов в зависимости от категории объекта (Здание или ЗУ).
    """
    # 1. Получаем базовую информацию
    base_info = await nspd_client.get_property_cadastral_price(cad_num)
    if not base_info:
        raise HTTPException(status_code=404, detail="Сведения об объекте в НСПД не найдены")

    try:
        feature = base_info["data"]["features"][0]

        # --- КОНВЕРТАЦИЯ ГЕОМЕТРИИ ---
        geometry = feature.get("geometry")
        normalized_geom = None
        if geometry:
            normalized_geom = CoordsConverter.convert_geometry(geometry)
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при разборе структуры данных НСПД: {str(e)}"
        ) from e

    # --- Категорийные вкладки (tab) ---
    details = await nspd_client.collect_details(base_info)

    if details is not None:
        return {
            "base_info": base_info,
            "geometry": normalized_geom,
            "details": details,
        }

    # Помещения/квартиры (37163) и прочие категории без детальных карточек.
    return {
        "base_info": base_info,
        "geometry": normalized_geom,
        "details": None,
        "message": "Детальные карточки доступны только для Зданий и Земельных участков",
    }


# Оставляем отдельные методы для гибкости в подпути /details
@router.get("/details/objects-list")
async def get_objects_list(objdocId: int, registersId: int | None = None, categoryId: int = 36369):
    data = await nspd_client.get_objects_list(objdocId, registersId, categoryId)
    if not data:
        raise HTTPException(status_code=404, detail="Данные не найдены")
    return data


@router.get("/details/land-links")
async def get_land_links(objdocId: int, registersId: int | None = None, categoryId: int = 36369):
    data = await nspd_client.get_land_links(objdocId, registersId, categoryId)
    if not data:
        raise HTTPException(status_code=404, detail="Данные не найдены")
    return data


@router.get("/details/build-parts")
async def get_build_parts(objdocId: int, registersId: int | None = None, categoryId: int = 36369):
    data = await nspd_client.get_build_parts(objdocId, registersId, categoryId)
    if not data:
        raise HTTPException(status_code=404, detail="Данные не найдены")
    return data


@router.get("/details/permission-types")
async def get_permission_types(
    objdocId: int, registersId: int | None = None, categoryId: int = 36369
):
    data = await nspd_client.get_permission_types(objdocId, registersId, categoryId)
    if not data:
        raise HTTPException(status_code=404, detail="Данные не найдены")
    return data
