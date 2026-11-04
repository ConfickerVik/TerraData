from fastapi import APIRouter, HTTPException
from app.services.nspd_client import NspdClient
from app.services.coords_converter import CoordsConverter
import asyncio
from typing import Dict, Any

router = APIRouter(prefix="/nspd", tags=["NSPD Data"])

nspd_client = NspdClient()

@router.get("/cadastral-price/{cad_num}")
async def get_cadastral_price(cad_num: str):
    """
    Запрос только кадастровой стоимости и базовых сведений об объекте.
    Вынесен в отдельный эндпоинт для дальнейшего уточнения параметров.
    """
    data = await nspd_client.get_property_cadastral_price(cad_num)
    if not data:
        raise HTTPException(status_code=404, detail="Сведения о кадастровой стоимости в НСПД не найдены")
    return data

@router.get("/property/{cad_num}")
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
        # Извлекаем ID и категорию объекта
        feature = base_info["data"]["features"][0]
        category_id = nspd_client.get_category_id(base_info)
        
        # --- КОНВЕРТАЦИЯ ГЕОМЕТРИИ ---
        geometry = feature.get("geometry")
        normalized_geom = None
        if geometry:
            normalized_geom = CoordsConverter.convert_geometry(geometry)
            
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при разборе структуры данных НСПД: {str(e)}")

    # --- Логика для Зданий (CATEGORY_BUILDINGS = 36369) ---
    if category_id == nspd_client.CATEGORY_BUILDINGS:
        objdoc_id = feature["id"]
        registers_id = feature["properties"]["options"]["registersId"]
        
        tasks = [
            nspd_client.get_objects_list(objdoc_id, registers_id),
            nspd_client.get_land_links(objdoc_id, registers_id),
            nspd_client.get_build_parts(objdoc_id, registers_id),
            nspd_client.get_permission_types(objdoc_id, registers_id),
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            "base_info": base_info,
            "geometry": normalized_geom,
            "details": {
                "objects_list": results[0],
                "land_links": results[1],
                "build_parts": results[2],
                "permission_types": results[3],
            }
        }

    # --- Логика для Земельных Участков (CATEGORY_LAND = 36368) ---
    elif category_id == nspd_client.CATEGORY_LAND:
        geom_id = feature["id"]
        
        tasks = [
            nspd_client.get_land_objects_list(geom_id),
            nspd_client.get_land_permission_types(geom_id),
            nspd_client.get_land_parts(geom_id),
            nspd_client.get_land_composition(geom_id),
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            "base_info": base_info,
            "geometry": normalized_geom,
            "details": {
                "objects_list": results[0],
                "permission_types": results[1],
                "land_parts": results[2],
                "composition_land": results[3],
            }
        }

    # --- Логика для Помещений/Квартир (CATEGORY_PREMISES = 37163) или иных ---
    else:
        return {
            "base_info": base_info,
            "geometry": normalized_geom,
            "details": None,
            "message": "Детальные карточки доступны только для Зданий и Земельных участков"
        }

# Оставляем отдельные методы для гибкости в подпути /details
@router.get("/details/objects-list")
async def get_objects_list(objdocId: int, registersId: int):
    data = await nspd_client.get_objects_list(objdocId, registersId)
    if not data: raise HTTPException(status_code=404, detail="Данные не найдены")
    return data

@router.get("/details/land-links")
async def get_land_links(objdocId: int, registersId: int):
    data = await nspd_client.get_land_links(objdocId, registersId)
    if not data: raise HTTPException(status_code=404, detail="Данные не найдены")
    return data

@router.get("/details/build-parts")
async def get_build_parts(objdocId: int, registersId: int):
    data = await nspd_client.get_build_parts(objdocId, registersId)
    if not data: raise HTTPException(status_code=404, detail="Данные не найдены")
    return data

@router.get("/details/permission-types")
async def get_permission_types(objdocId: int, registersId: int):
    data = await nspd_client.get_permission_types(objdocId, registersId)
    if not data: raise HTTPException(status_code=404, detail="Данные не найдены")
    return data
