import httpx
import json
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class SudrfClient:
    """
    Сервис для взаимодействия с API sudrf.ru для получения данных о судебных участках.
    """
    def __init__(self, timeout=30.0):
        self.timeout = timeout
        self.base_url = "https://sudrf.ru/api.php"
        self.suggest_url = "https://sudrf.ru/suggestions/api/4_1/rs/suggest/address"

    def get_court_by_fias_id(self, fias_id: str, region_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Получение списка судов по FIAS ID (GUID).
        Метод: getCourtListByFiasCode.
        Фильтрует результаты по коду региона (первые 2 цифры VNKOD).
        """
        url = f"{self.base_url}?opt=court_list&action=getCourtListByFiasCode&fiasId={fias_id}"
        
        try:
            with httpx.Client(timeout=self.timeout) as session:
                response = session.get(url)
            
            if response.status_code == 200:
                content = json.loads(response.text)
                courts_list = content.get("list", [])
                if not courts_list:
                    return None
                
                # Определяем код региона, если он не передан (берем из первого элемента)
                if not region_code and courts_list[0].get("VNKOD"):
                    region_code = courts_list[0]["VNKOD"][:2]

                # Собираем словарь судов, которые относятся к этому региону
                region_courts = {}
                for court in courts_list:
                    vncod = court.get("VNKOD", "")
                    if vncod.startswith(region_code):
                        # Используем VNKOD как ключ, ZNACHATR как значение
                        region_courts[vncod] = court.get("ZNACHATR", "")
                
                if not region_courts:
                    return None

                # Возвращаем основной результат (первый из отфильтрованных) и весь список
                main_court_vncod = list(region_courts.keys())[0]
                return {
                    "court_name": region_courts[main_court_vncod],
                    "vncod": main_court_vncod,
                    "all_region_courts": region_courts
                }
        except Exception as e:
            logger.error(f"Error getting court by fias_id {fias_id}: {e}")
        return None

    def get_fias_id_by_address(self, address: str) -> Optional[str]:
        """
        Поиск fias_id через внутренний сервис подсказок sudrf.ru.
        Используется как fallback-метод, если основной поиск ФИАС не дал результата.
        """
        payload = {
            "query": address, 
            "from_bound": {"value": "region"}, 
            "to_bound": {"value": "house"}
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as session:
                response = session.post(self.suggest_url, json=payload)
            
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
