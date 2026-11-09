import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.services.types.court_types import court_type_label
from app.services.types.obj_types import obj_type_label
from app.services.types.purpose_types import purpose_type_label

# Кандидаты TTF-шрифтов с поддержкой кириллицы (в порядке приоритета).
# Стандартные шрифты ReportLab (Helvetica и т.п.) НЕ содержат кириллицу,
# поэтому для русского текста обязательно регистрируем TTF.
_FONT_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "..", "fonts", "DejaVuSans.ttf"),
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

_DATA_UNAVAILABLE = "данные недоступны"


def _register_font() -> str:
    """
    Регистрирует кириллический TTF-шрифт и возвращает его имя.
    Возвращает 'Helvetica' как fallback, если ни один TTF не найден.
    """
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("TerraDataFont", path))
                return "TerraDataFont"
            except Exception:
                continue
    return "Helvetica"


_FONT_NAME = _register_font()


def format_timestamp(ts):
    if not ts:
        return "н/д"
    try:
        # Timestamp is in milliseconds
        return datetime.fromtimestamp(ts / 1000.0).strftime("%d.%m.%Y")
    except Exception:
        return str(ts)


class PDFService:
    """Генератор аналитического PDF-отчёта через ReportLab."""

    def generate_report(self, report: dict, output_path: str | None = None) -> bytes | bool:
        """
        Формирует PDF-отчёт по нормализованной структуре report (см. ReportService).

        :param report: dict с ключами general/spatial/legal/fias/court.
        :param output_path: если задан — дополнительно сохраняет PDF в файл.
        :return: байты PDF, либо False, если отчёт пуст.
        """
        general = report.get("general") or {}
        if not general.get("cad_num") and not general.get("address"):
            return False

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title="Отчёт об объекте недвижимости",
        )

        story = self._build_story(report)
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        return pdf_bytes

    # --- Вспомогательные методы построения документа ---

    def _build_story(self, report: dict):
        story = []
        general = report.get("general") or {}

        # Заголовок
        story.append(Paragraph("ОТЧЁТ ОБ ОБЪЕКТЕ НЕДВИЖИМОСТИ", self._h1()))
        story.append(Spacer(1, 4 * mm))

        # 1. Общая информация
        story.append(Paragraph("1. Общая информация", self._h2()))
        story.append(self._key_value_table(general_rows(general)))
        story.append(Spacer(1, 6 * mm))

        # 2. Пространственные данные
        story.append(Paragraph("2. Пространственные данные", self._h2()))
        story.extend(self._spatial_paragraph(report.get("spatial")))
        story.append(Spacer(1, 6 * mm))

        # 3. Правовой статус
        story.append(Paragraph("3. Правовой статус", self._h2()))
        story.append(self._legal_paragraph(report.get("legal")))
        story.append(Spacer(1, 6 * mm))

        # 4. Судебная принадлежность
        story.append(Paragraph("4. Судебная принадлежность", self._h2()))
        story.append(self._court_paragraph(report.get("court")))
        story.append(Spacer(1, 6 * mm))

        # 5. Сведения ФИАС
        story.append(Paragraph("5. Сведения ФИАС", self._h2()))
        story.extend(self._fias_paragraph(report.get("fias")))
        story.append(Spacer(1, 6 * mm))

        return story

    # --- Стили ---

    def _h1(self):
        return ParagraphStyle(
            "H1",
            fontName=_FONT_NAME,
            fontSize=18,
            leading=22,
            alignment=1,  # center
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a1a"),
        )

    def _h2(self):
        return ParagraphStyle(
            "H2",
            fontName=_FONT_NAME,
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#333333"),
        )

    def _body(self):
        return ParagraphStyle(
            "Body",
            fontName=_FONT_NAME,
            fontSize=10,
            leading=13,
        )

    # --- Рендер секций ---

    def _key_value_table(self, rows):
        if not rows:
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        table_data = [[Paragraph(f"<b>{k}</b>", self._body()), Paragraph(str(v), self._body())] for k, v in rows]
        table = Table(table_data, colWidths=[60 * mm, 110 * mm])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def _spatial_paragraph(self, spatial):
        if not spatial:
            return [Paragraph(_DATA_UNAVAILABLE, self._body())]

        geometry = spatial.get("geometry")
        if not geometry:
            return [Paragraph("Геометрия не задана.", self._body())]

        geom_type = geometry.get("type", "Unknown")
        flowables = [Paragraph(f"Тип геометрии: {geom_type}", self._body())]
        coords = geometry.get("coordinates")

        if geom_type == "Point":
            # Для точки центр не показываем — он дублирует саму точку.
            if coords:
                flowables.append(Paragraph(f"Координаты: {coords}", self._body()))
            return flowables

        if geom_type == "Polygon":
            center = geometry.get("center")
            if center and len(center) >= 2:
                flowables.append(
                    Paragraph(
                        f"Центр (широта, долгота): {center[0]}, {center[1]}",
                        self._body(),
                    )
                )
            flowables.append(self._coordinates_table(coords))
            return flowables

        # Прочие типы геометрии
        if coords:
            flowables.append(Paragraph(f"Координаты: {coords}", self._body()))
        return flowables

    def _coordinates_table(self, coords):
        """
        Таблица координат полигона с заголовком № | x | y.

        GeoJSON Polygon: coordinates = [[ [x, y], [x, y], ... ], ...].
        Берём первый (внешний) контур; x = долгота, y = широта.
        """
        if not coords:
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        ring = coords
        if isinstance(coords[0], list) and coords[0] and isinstance(coords[0][0], list):
            ring = coords[0]

        header = [
            Paragraph("<b>№</b>", self._body()),
            Paragraph("<b>x</b>", self._body()),
            Paragraph("<b>y</b>", self._body()),
        ]
        rows = [header]
        for i, pt in enumerate(ring, start=1):
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                continue
            rows.append([
                Paragraph(str(i), self._body()),
                Paragraph(self._fmt_coord(pt[0]), self._body()),
                Paragraph(self._fmt_coord(pt[1]), self._body()),
            ])

        if len(rows) == 1:
            # Только заголовок — координат нет.
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        table = Table(rows, colWidths=[20 * mm, 75 * mm, 75 * mm])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return table

    @staticmethod
    def _fmt_coord(value):
        """Форматирует координату: float -> 6 знаков после запятой."""
        try:
            return f"{float(value):.6f}"
        except (TypeError, ValueError):
            return str(value)

    def _legal_paragraph(self, legal):
        legal = legal or {}
        rights = legal.get("rights", [])
        encs = legal.get("encumbrances", [])

        parts = []
        parts.append("<b>Права собственности:</b>")
        if rights:
            for r in rights:
                parts.append(
                    f"— {r.get('rightTypeDesc', '—')}, "
                    f"рег. дата: {format_timestamp(r.get('rightRegDate'))}, "
                    f"номер: {r.get('rightNumber', '—')}"
                )
        else:
            parts.append(_DATA_UNAVAILABLE)

        parts.append("<b>Обременения:</b>")
        if encs:
            for e in encs:
                parts.append(
                    f"— {e.get('typeDesc', '—')}, "
                    f"дата: {format_timestamp(e.get('startDate'))}, "
                    f"номер: {e.get('encumbranceNumber', '—')}"
                )
        else:
            parts.append(_DATA_UNAVAILABLE)

        return Paragraph("<br/>".join(parts), self._body())

    def _court_paragraph(self, court):
        if not court:
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        courts = court.get("courts")
        if not courts:
            # Обратная совместимость со старым форматом (court_name/vncod)
            parts = [f"Судебный участок: {court.get('court_name', '—')}"]
            if court.get("vncod"):
                parts.append(f"Код участка (VNKOD): {court.get('vncod')}")
            return Paragraph("<br/>".join(parts), self._body())

        # Новый формат: суды по зоне ответственности.
        parts = []
        for c in courts:
            label = court_type_label(c.get("type"))
            parts.append(f"{label}: {c.get('name', '—')}")

        return Paragraph("<br/>".join(parts), self._body())

    def _fias_paragraph(self, fias):
        if not fias:
            return [Paragraph(_DATA_UNAVAILABLE, self._body())]

        addresses = fias.get("addresses", [])
        if not addresses:
            return [Paragraph(_DATA_UNAVAILABLE, self._body())]

        flowables = []
        for addr in addresses:
            if addr.get("full_name"):
                flowables.append(
                    Paragraph(f"Полный адрес: {addr['full_name']}", self._body())
                )
            if addr.get("address_type") is not None:
                flowables.append(
                    Paragraph(f"Деление: {'Административное деление' if addr['address_type'] == 1 else 'Муниципальное'}", self._body())
                )
            if addr.get("object_id") is not None:
                flowables.append(
                    Paragraph(f"Уникальный номер в ГАР: {addr['object_id']}", self._body())
                )
            if addr.get("object_guid") is not None:
                flowables.append(
                    Paragraph(f"Уникальный номер в ГАР (ID FIAS): {addr['object_guid']}", self._body())
                )

            address_detail = addr.get("address_detail", {})
            if address_detail.get("postal_code") is not None:
                flowables.append(
                    Paragraph(f"Почтовый индекс: {addr['postal_code']}", self._body())
                )

            if address_detail.get("okato") is not None:
                flowables.append(
                    Paragraph(f"ОКАТО: {addr['okato']}", self._body())
                )
            if address_detail.get("oktmo") is not None:
                flowables.append(
                    Paragraph(f"ОКТМО код: {addr['oktmo']}", self._body())
                )
            if address_detail.get("oktmo_budget") is not None:
                flowables.append(
                    Paragraph(f"ОКТМО бюджетополучателя: {addr['oktmo_budget']}", self._body())
                )
            if address_detail.get("postal_code") is not None:
                flowables.append(
                    Paragraph(f"Почтовый код: {addr['postal_code']}", self._body())
                )
            if address_detail.get("ifns_fl") is not None:
                flowables.append(
                    Paragraph(f"Налоговый орган ФЛ: {addr['ifns_fl']}", self._body())
                )
            if address_detail.get("ifns_ul") is not None:
                flowables.append(
                    Paragraph(f"Налоговый орган ЮЛ: {addr['ifns_ul']}", self._body())
                )

            hierarchy = addr.get("hierarchy", [])
            if hierarchy:
                flowables.append(Paragraph("<b>Иерархия:</b>", self._body()))
                flowables.append(Spacer(1, 2 * mm))
                for item in hierarchy:
                    flowables.append(self._hierarchy_item_table(item))
                    flowables.append(Spacer(1, 3 * mm))

        # Дополнительная информация по объекту (из /Search/ObjectDetails)
        details = fias.get("object_details")
        if details:
            flowables.append(Paragraph("<b>Дополнительная информация:</b>", self._body()))
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(self._object_details_table(details))
            flowables.append(Spacer(1, 3 * mm))

        if not flowables:
            return [Paragraph(_DATA_UNAVAILABLE, self._body())]
        return flowables

    def _object_details_table(self, details):
        """Таблица с дополнительной информацией об объекте из ObjectDetails."""
        rows = []
        if details.get("ReesterNumber"):
            rows.append(("Уникальный номер реестровой записи", details["ReesterNumber"]))
        if details.get("StartDate"):
            rows.append(("Дата внесения записи", details["StartDate"]))
        if details.get("UpdateDate"):
            rows.append(("Дата актуализации записи", details["UpdateDate"]))
        if details.get("FederalDistrict"):
            rows.append(("Федеральный округ", details["FederalDistrict"]))

        if not rows:
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        return self._key_value_table(rows)

    def _hierarchy_item_table(self, item):
        """
        Маленькая таблица с информацией об одном адресообразующем
        элементе иерархии ФИАС.
        """
        rows = []

        name = item.get("full_name") or item.get("name")
        if name:
            rows.append(("Наименование", name))

        type_name = item.get("type_name")
        type_short = item.get("type_short_name")
        if type_name:
            label = f"{type_name} ({type_short})" if type_short else type_name
            rows.append(("Тип", label))

        if item.get("object_id") is not None:
            rows.append(("ObjectID", item["object_id"]))
        if item.get("object_guid"):
            rows.append(("GUID", item["object_guid"]))

        if not rows:
            return Paragraph(_DATA_UNAVAILABLE, self._body())

        return self._key_value_table(rows)


def general_rows(general: dict) -> list[tuple[str, str]]:
    """Формирует строки таблицы общей информации из секции general."""
    rows = []
    if general.get("cad_num"):
        rows.append(("Кадастровый номер", general["cad_num"]))
    if general.get("status"):
        rows.append(("Статус записи", f"{'Актуальный' if general['status'] == '1' else 'Погашен'}"))
    if general.get("obj_type"):
        rows.append(("Тип объекта", obj_type_label(general["obj_type"])))
    if general.get("address"):
        rows.append(("Адрес", general["address"]))
    if general.get("area") is not None:
        rows.append(("Площадь", f"{general['area']} {general.get('area_unit', 'кв.м')}"))
    if general.get("floor"):
        rows.append(("Этажность", general["floor"]))
    if general.get("under_floor"):
        rows.append(("Подземные этажи", general["under_floor"]))
    if general.get("level_floor") is not None:
        rows.append(("Этаж", general["level_floor"]))
    if general.get("ownership_type"):
        rows.append(("Тип собственности", general["ownership_type"]))
    if general.get("oks_wall_material"):
        rows.append(("Материал стен", general["oks_wall_material"]))
    if general.get("oks_commisioning_year"):
        rows.append(("Год ввода в эксплуатацию", general["oks_commisioning_year"]))
    if general.get("purpose"):
        rows.append(("Назначение объекта", purpose_type_label(general["purpose"])))
    if general.get("cad_cost") is not None:
        rows.append(("Кадастровая стоимость", f"{general['cad_cost']} руб."))
    if general.get("cad_cost_date"):
        rows.append(("Дата оценки", format_timestamp(general["cad_cost_date"])))
    if general.get("reg_date"):
        rows.append(("Дата постановки на учет", format_timestamp(general["reg_date"])))
    if general.get("info_update_date"):
        rows.append(("Дата обновления информации", format_timestamp(general["info_update_date"])))
    return rows
