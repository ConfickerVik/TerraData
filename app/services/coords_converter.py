import math
import logging
from typing import List, Tuple, Union, Dict, Any

logger = logging.getLogger(__name__)

class CoordsConverter:
    # Константы для проекции Web Mercator (EPSG:3857) -> WGS 84 (EPSG:4326)
    EARTH_RADIUS = 6378137.0
    MAX_EXTENT = 20037508.342789244

    @classmethod
    def normalize_coordinates(cls, x: float, y: float) -> Tuple[float, float]:
        """
        Перевод координат из EPSG:3857 (Web Mercator) в EPSG:4326 (WGS 84).
        :param x: Долгота (longitude / easting) в метрах.
        :param y: Широта (latitude / northing) в метрах.
        :return: Кортеж (latitude, longitude) в градусах.
        """
        try:
            # Аналог Java: Math.toDegrees(Math.atan(Math.sinh(latitude / EARTH_RADIUS)))
            lat_deg = math.degrees(math.atan(math.sinh(y / cls.EARTH_RADIUS)))
            
            # Аналог Java: (longitude / MAX_EXTENT) * 180
            lon_deg = (x / cls.MAX_EXTENT) * 180
            
            return lat_deg, lon_deg
        except Exception as e:
            logger.error(f"Error normalizing coordinates {x}, {y}: {e}")
            return 0.0, 0.0

    @classmethod
    def get_center(cls, coordinates: Union[List[float], List[List[float]]]) -> Tuple[float, float]:
        """
        Вычисляет центр объекта для центрирования карты.
        :param coordinates: Либо список [x, y] (Point), либо список списков [[x,y], [x,y]...] (Polygon).
        :return: Центр в формате (lat, lon) в градусах.
        """
        if not coordinates:
            return 0.0, 0.0

        # Если это Point [x, y]
        if isinstance(coordinates[0], (int, float)):
            return cls.normalize_coordinates(coordinates[0], coordinates[1])

        # Если это Polygon [[[x,y], [x,y]...]] - берем первый контур
        # НСПД часто присылает Polygon как список списков координат
        points = coordinates[0] if isinstance(coordinates[0][0], list) else coordinates
        
        sum_x = 0.0
        sum_y = 0.0
        count = len(points)
        
        for pt in points:
            sum_x += pt[0]
            sum_y += pt[1]
            
        center_x = sum_x / count
        center_y = sum_y / count
        
        return cls.normalize_coordinates(center_x, center_y)

    @classmethod
    def convert_geometry(cls, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Универсальный метод для конвертации геометрии из ответа НСПД.
        """
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])
        
        if geom_type == "Point":
            lat, lon = cls.normalize_coordinates(coords[0], coords[1])
            return {
                "type": "Point",
                "coordinates": [lat, lon], # GeoJSON стандарт: [lon, lat]
                "center": [lat, lon]
            }
            
        elif geom_type == "Polygon":
            # Обрабатываем первый контур полигона
            polygon_coords = coords[0]
            normalized_polygon = [cls.normalize_coordinates(pt[0], pt[1]) for pt in polygon_coords]
            # Для GeoJSON полигоны должны быть [[ [lon, lat], ... ]]
            # geojson_coords = [[ [pt[1], pt[0]] for pt in normalized_polygon ]]
            
            return {
                "type": "Polygon",
                "coordinates": normalized_polygon,
                "center": cls.get_center(polygon_coords)
            }
            
        return {"type": "Unknown", "coordinates": [], "center": [0.0, 0.0]}
