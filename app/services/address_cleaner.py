import logging
import re

logger = logging.getLogger(__name__)


class AddressCleaner:
    """
    Сервис для очистки адресов от избыточной информации (квартиры, помещения,
    специфические пометки), которая мешает поиску в ФИАС и других государственных реестрах.
    """

    # Список паттернов для полного удаления фрагментов строки
    EXCLUDE = [
        r"внутригородской\sрайон",
        r"внутригородской\sокруг",
        r"городской округ",
        r"Помещения\s",
        r"помещения\s",
        r"помещение\s",
        r"б/н",
        r"гаражный\sбокс",
        r"пом\s",
        r"лит\.",
        r"апартаменты\s",
        r"апартамент\s",
        r"[Кк]урортный\sмногофункциональный\sкомплекс\s",
        r"стр\.\s",
        r"строение",
        r"квартал\sзастройки",
        r"район\sКурортного\sгородка",
        r"напротив\sадминистративного\sздания",
        r"квартира\s",
        r"муниципальный\sрайон",
        r"городское\sпоселение",
        r"относительно\sориентира",
        r"расположенного\sв\sграницах",
        r"номер\sна\sэтаже\s",
    ]

    # Текст, который нужно заменить на пробел
    REPLACE_TEXT = [
        r"на земельном участке расположен жилой",
        r"з/у",
        r"в\sрайоне\s",
        r"с/т",
        r"c\\т",
        r"здание\s",
        r"при\sжилом\sдоме",
    ]

    # Части строки, после которых всё остальное должно быть отброшено
    CUT_PART_TEXT = [r"оздоровительный\sкомплекс", r"нежилые\sпомещения"]

    @classmethod
    def clean(cls, address: str | None) -> str | None:
        """
        Основной метод очистки адреса.
        """
        if not address:
            return None

        try:
            # 1. Нормализация пробелов и удаление спецсимволов
            adr = re.sub(pattern=r"\s+", string=address, repl=" ")
            adr = adr.replace("&#x0d,", "").replace('"', "").replace("(", "").replace(")", "")

            # 2. Обработка заменяемого текста
            for repl_text in cls.REPLACE_TEXT:
                if re.search(pattern=repl_text, string=adr, flags=re.IGNORECASE):
                    adr = re.sub(pattern=r"дома\s", string=adr, repl="дом ", flags=re.IGNORECASE)
                    adr = re.sub(pattern=repl_text, string=adr, repl=" ", flags=re.IGNORECASE)

            # 3. Обрезание строки по "стоп-словам" (Cut parts)
            for cut_part in cls.CUT_PART_TEXT:
                search_part = re.search(pattern=cut_part, string=adr, flags=re.IGNORECASE)
                if search_part:
                    adr = adr[: search_part.start() - 2].strip()

            # 4. Удаление фрагментов по списку EXCLUDE
            parts = adr.split(",")
            cl_parts = []
            for part in parts:
                bad_part = False
                for exc in cls.EXCLUDE:
                    if re.search(pattern=exc, string=part.strip(), flags=re.IGNORECASE):
                        bad_part = True
                        break
                if not bad_part:
                    cl_parts.append(part)

            adr = ", ".join(cl_parts)
            adr = adr.replace("№", "")

            # 5. Специфическая логика для районов и городов
            if (
                re.search(pattern=r"г\.\s?", string=adr, flags=re.IGNORECASE)
                or re.search(pattern=r"город\s", string=adr, flags=re.IGNORECASE)
            ) and (
                re.search(pattern=r"р-он", string=adr, flags=re.IGNORECASE)
                or re.search(pattern=r"район", string=adr, flags=re.IGNORECASE)
                or re.search(pattern=r"р-н", string=adr, flags=re.IGNORECASE)
            ):
                search_district = re.search(pattern=r"(п|с)\.\s?[А-я]{1,}\s?[А-я]*", string=adr)
                if search_district:
                    adr = adr[: search_district.start()] + adr[search_district.end() + 2 :]

            # 6. Обработка хуторов
            search_hutor = re.search(pattern=r"х\.\s[А-я]{1,}", string=adr)
            if search_hutor:
                return adr[: search_hutor.end()]

            # 7. Финальное обрезание: удаляем всё, что идет после квартиры, участка или помещения
            # (Самая важная часть для ФИАС, чтобы поиск шел по дому)
            stop_patterns = [r"(кв|к)\.\s?", r"(участок\s)|(уч\.)", r"(пом|помещ)\.\s?"]
            for pat in stop_patterns:
                search = re.search(pattern=pat, string=adr, flags=re.IGNORECASE)
                if search:
                    adr = adr[: search.start() - 3]

            adr = re.sub(pattern=r"\s+", string=adr, repl=" ")

            return adr.strip()

        except Exception as e:
            logger.error(f"Error cleaning address '{address}': {e}")
            return address  # Возвращаем оригинал, если произошла ошибка, чтобы не терять данные
