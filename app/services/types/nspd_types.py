# --- Справочники НСПД для PDF-отчёта ---

_NSPD_CATEGORY_LABELS = {
    36369: "Здание / ОКС",
    36368: "Земельный участок",
    37163: "Помещение / квартира",
}

# Курируемые поля options по категориям: (русская подпись, [возможные ключи]).
# Ключи и их наличие отличаются даже внутри одной категории, поэтому
# перечисляем несколько синонимов (например, cad_num / cad_number).
_NSPD_FIELDS = {
    36369: [
        ("Кадастровый номер", ["cad_num", "cad_number"]),
        ("Наименование", ["building_name", "name"]),
        ("Назначение", ["purpose"]),
        ("Площадь", ["area"]),
        ("Этажность", ["floors"]),
        ("Подземные этажи", ["underground_floors"]),
        ("Материал стен", ["materials"]),
        ("Год постройки", ["year_built"]),
        ("Год ввода в эксплуатацию", ["year_commisioning"]),
        ("Кадастровая стоимость", ["cost_value"]),
        ("Адрес", ["readable_address"]),
        ("Статус", ["status"]),
        ("Форма собственности", ["ownership_type"]),
        ("Объект культурного наследия", ["cultural_heritage_object"]),
    ],
    36368: [
        ("Кадастровый номер", ["cad_num", "cad_number"]),
        ("Площадь", ["area"]),
        ("Декларированная площадь", ["declared_area"]),
        ("Уточнённая площадь", ["specified_area"]),
        ("Вид / тип ЗУ", ["land_record_type", "land_record_subtype", "land_record_category_type"]),
        ("Вид разрешённого использования", ["permitted_use_established_by_document", "permitted_use_name"]),
        ("Кадастровая стоимость", ["cost_value"]),
        ("Адрес", ["readable_address"]),
        ("Статус", ["status"]),
        ("Форма собственности", ["ownership_type"]),
    ],
    37163: [
        ("Кадастровый номер", ["cad_number", "cad_num"]),
        ("Площадь", ["area"]),
        ("Этаж", ["floor"]),
        ("Назначение", ["purpose"]),
        ("Тип", ["type"]),
        ("Кадастровая стоимость", ["cost_value"]),
        ("Адрес", ["readable_address"]),
        ("Родительский объект", ["parent_cad_number"]),
        ("Общее имущество", ["common_property"]),
        ("Форма собственности", ["ownership_type"]),
    ],
}

# Вкладки: (ключ в details, подпись, является ли групповой tab-group-data).
_NSPD_TABS = [
    ("objects_list", "Список объектов", True),
    ("land_links", "Связанные земельные участки", False),
    ("build_parts", "Части объекта", False),
    ("permission_types", "Виды разрешённого использования", False),
    ("land_parts", "Части земельного участка", False),
    ("composition_land", "Состав единого землепользования", False),
]