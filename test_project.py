"""Модульные тесты «Конвертера величин» (pytest).

Покрывается converter_logic.py. Графический интерфейс (converter_ui.py)
не импортируется и не тестируется: виджеты требуют дисплея.

Запуск:  pytest test_project.py -v
"""
import dataclasses
import math
import sys

import pytest

from converter_logic import (
    ABSOLUTE_ZERO,
    ALL_CATEGORIES,
    NUMBER_SYSTEMS,
    SPECIAL_CATEGORIES,
    TEMPERATURE_UNITS,
    UNITS,
    CalculationError,
    Category,
    ConversionHistory,
    ConversionResult,
    HistoryEntry,
    InputError,
    LinearCategory,
    NumberSystemCategory,
    TemperatureCategory,
    convert_linear,
    convert_number_system,
    convert_temperature,
    format_number,
    get_category,
    to_base,
)

# --------------------------------------------------------------------------
#  Короткие названия единиц
# --------------------------------------------------------------------------
C, F, K = "Цельсий (°C)", "Фаренгейт (°F)", "Кельвин (K)"
BIN, TER, OCT = "Двоичная (2)", "Троичная (3)", "Восьмеричная (8)"
DEC, HEX = "Десятичная (10)", "Шестнадцатеричная (16)"
KM, M = "Километр (км)", "Метр (м)"
DEG, RAD = "Градус (°)", "Радиан (рад)"

PLAIN, PREFIX, GROUP = "Обычный", "С префиксом", "С группировкой разрядов"

MSG_FORMAT = "Некорректный формат ввода"
MSG_NEGATIVE = "Значение не может быть отрицательным"
MSG_ABS_ZERO = "Температура ниже абсолютного нуля"
MSG_MISMATCH = "Введенное значение не соответствует выбранной системе счисления"
MSG_CALC = "Не удалось выполнить перевод"


def _entry(n, fmt=None, **overrides):
    """Фабрика записей истории с уникальным ключом по номеру n."""
    data = dict(
        category="Длина",
        from_unit=KM,
        to_unit=M,
        input_raw=str(n),
        display=f"запись {n}",
        format_option=fmt,
    )
    data.update(overrides)
    return HistoryEntry(**data)


# ==========================================================================
#  1. ЦЕЛОСТНОСТЬ ДАННЫХ И РЕЕСТР КАТЕГОРИЙ
# ==========================================================================
def test_all_categories_sorted_and_complete():
    assert ALL_CATEGORIES == sorted(ALL_CATEGORIES)
    assert set(ALL_CATEGORIES) == set(UNITS) | SPECIAL_CATEGORIES
    assert len(ALL_CATEGORIES) == len(set(ALL_CATEGORIES))


@pytest.mark.parametrize("category", sorted(UNITS))
def test_units_factors_positive_and_enough_units(category):
    factors = UNITS[category]
    assert len(factors) >= 2, "для выбора «из/в» нужно минимум 2 единицы"
    assert all(isinstance(v, float) or isinstance(v, int) for v in factors.values())
    assert all(v > 0 and math.isfinite(v) for v in factors.values())


@pytest.mark.parametrize("name", ALL_CATEGORIES)
def test_registry_contains_every_category(name):
    category = get_category(name)
    assert isinstance(category, Category)
    assert category.name == name
    assert len(category.units) >= 2


def test_get_category_unknown_raises_keyerror():
    with pytest.raises(KeyError):
        get_category("Несуществующая величина")


def test_registry_category_types():
    assert isinstance(get_category("Длина"), LinearCategory)
    assert isinstance(get_category("Температура"), TemperatureCategory)
    assert isinstance(get_category("Система счисления"), NumberSystemCategory)


def test_only_number_system_has_format_option():
    for name in ALL_CATEGORIES:
        expected = (name == "Система счисления")
        assert get_category(name).has_format_option is expected


def test_category_units_match_source_data():
    assert get_category("Длина").units == list(UNITS["Длина"].keys())
    assert get_category("Температура").units == TEMPERATURE_UNITS
    assert get_category("Система счисления").units == list(NUMBER_SYSTEMS.keys())


def test_category_units_returns_copy():
    units = get_category("Температура").units
    units.append("мусор")
    assert "мусор" not in TEMPERATURE_UNITS
    assert "мусор" not in get_category("Температура").units


def test_hectopascal_equals_millibar():
    assert convert_linear("Давление", "Гектопаскаль (гПа)",
                          "Миллибар (мбар)", 1) == pytest.approx(1)


# ==========================================================================
#  2. convert_linear
# ==========================================================================
@pytest.mark.parametrize(
    "category, src, dst, value, expected",
    [
        ("Длина", KM, M, 1, 1000),
        ("Длина", "Дюйм (in)", "Сантиметр (см)", 1, 2.54),
        ("Длина", "Миля (mi)", KM, 1, 1.609344),
        ("Время", "Час (ч)", "Секунда (с)", 1, 3600),
        ("Время", "Сутки", "Час (ч)", 2, 48),
        ("Масса", "Тонна (т)", "Килограмм (кг)", 1.5, 1500),
        ("Объём информации", "Бит (бит)", "Байт (Б)", 8, 1),
        ("Объём информации", "Килобайт (КБ)", "Байт (Б)", 1, 1024),
        ("Объём информации", "Килобит (Кбит)", "Байт (Б)", 1, 128),
        ("Скорость", "Километр/час (км/ч)", "Метр/сек (м/с)", 36, 10),
        ("Скорость передачи данных", "Мегабайт/сек (МБ/с)",
         "Мегабит/сек (Мбит/с)", 1, 8),
        ("Углы", DEG, RAD, 180, math.pi),
        ("Углы", "Оборот", DEG, 1, 360),
        ("Энергия", "Киловатт-час (кВт·ч)", "Мегаджоуль (МДж)", 1, 3.6),
        ("Проценты и доли", "Процент (%)", "Доля", 50, 0.5),
    ],
)
def test_convert_linear_success(category, src, dst, value, expected):
    assert convert_linear(category, src, dst, value) == pytest.approx(expected)


@pytest.mark.parametrize("category", sorted(UNITS))
def test_convert_linear_same_unit_is_identity(category):
    unit = next(iter(UNITS[category]))
    assert convert_linear(category, unit, unit, 42.5) == pytest.approx(42.5)


@pytest.mark.parametrize("category", sorted(UNITS))
def test_convert_linear_round_trip(category):
    units = list(UNITS[category])
    a, b = units[0], units[-1]
    forward = convert_linear(category, a, b, 123.456)
    back = convert_linear(category, b, a, forward)
    assert back == pytest.approx(123.456, rel=1e-9)


def test_convert_linear_zero():
    assert convert_linear("Длина", KM, M, 0) == 0


def test_convert_linear_unknown_unit_raises_keyerror():
    with pytest.raises(KeyError):
        convert_linear("Длина", "Парсек", M, 1)


def test_convert_linear_unknown_category_raises_keyerror():
    with pytest.raises(KeyError):
        convert_linear("Нет такой", KM, M, 1)


# ==========================================================================
#  3. convert_temperature
# ==========================================================================
@pytest.mark.parametrize(
    "src, dst, value, expected",
    [
        (C, F, 0, 32),
        (C, F, 100, 212),
        (C, K, 0, 273.15),
        (F, C, 32, 0),
        (F, K, 32, 273.15),
        (K, C, 0, -273.15),
        (K, F, 0, -459.67),
        (C, F, -40, -40),          
        (C, C, 25, 25),
        (F, F, 77, 77),
        (K, K, 300, 300),
    ],
)
def test_convert_temperature_success(src, dst, value, expected):
    assert convert_temperature(src, dst, value) == pytest.approx(expected)


@pytest.mark.parametrize("src, dst", [(C, F), (C, K), (F, K)])
def test_convert_temperature_round_trip(src, dst):
    forward = convert_temperature(src, dst, 36.6)
    assert convert_temperature(dst, src, forward) == pytest.approx(36.6)


def test_convert_temperature_unknown_source_unit():
    with pytest.raises(ValueError, match="Неизвестная единица температуры"):
        convert_temperature("Ранкин", C, 1)


def test_convert_temperature_unknown_target_unit():
    with pytest.raises(ValueError, match="Неизвестная единица температуры"):
        convert_temperature(C, "Ранкин", 1)


def test_absolute_zero_constants_are_consistent():
    for unit, value in ABSOLUTE_ZERO.items():
        assert convert_temperature(unit, K, value) == pytest.approx(0, abs=1e-9)


# ==========================================================================
#  4. to_base / format_number / convert_number_system
# ==========================================================================
@pytest.mark.parametrize(
    "n, base, expected",
    [
        (0, 2, "0"),
        (5, 2, "101"),
        (255, 16, "FF"),
        (255, 8, "377"),
        (8, 8, "10"),
        (35, 36, "Z"),
        (-5, 2, "-101"),
        (-255, 16, "-FF"),
    ],
)
def test_to_base(n, base, expected):
    assert to_base(n, base) == expected


@pytest.mark.parametrize(
    "s, base, option, expected",
    [
        ("FF", 16, PREFIX, "0xFF"),
        ("101", 2, PREFIX, "0b101"),
        ("17", 8, PREFIX, "0o17"),
        ("12", 3, PREFIX, "12"),
        ("12", 10, PREFIX, "12"),
        ("-FF", 16, PREFIX, "-0xFF"),     
        ("11111111", 2, GROUP, "1111 1111"),
        ("1", 2, GROUP, "1"),
        ("10000", 16, GROUP, "1 0000"),    
        ("1234567", 10, GROUP, "1 234 567"),
        ("100", 10, GROUP, "100"),
        ("100000", 3, GROUP, "10 0000"),
        ("-1234567", 10, GROUP, "-1 234 567"),
        ("FF", 16, PLAIN, "FF"),
        ("FF", 16, None, "FF"),
        ("-FF", 16, PLAIN, "-FF"),
        ("FF", 16, "Неизвестный формат", "FF"),
    ],
)
def test_format_number(s, base, option, expected):
    assert format_number(s, base, option) == expected


@pytest.mark.parametrize(
    "src, dst, text, option, expected",
    [
        (DEC, BIN, "10", PLAIN, "1010"),
        (DEC, HEX, "255", PLAIN, "FF"),
        (HEX, DEC, "FF", PLAIN, "255"),
        (HEX, DEC, "ff", PLAIN, "255"),            
        (BIN, HEX, "11111111", PLAIN, "FF"),
        (OCT, DEC, "377", PLAIN, "255"),
        (DEC, TER, "10", PLAIN, "101"),
        (DEC, DEC, "123", PLAIN, "123"),
        (DEC, BIN, "0", PLAIN, "0"),
        (DEC, BIN, "-10", PLAIN, "-1010"),         
        (DEC, BIN, "+5", PLAIN, "101"),         
        (DEC, BIN, "-0", PLAIN, "0"),
        (DEC, HEX, "255", PREFIX, "0xFF"),       
        (DEC, BIN, "5", PREFIX, "0b101"),
        (DEC, OCT, "255", PREFIX, "0o377"),
        (DEC, HEX, "-255", PREFIX, "-0xFF"),
        (DEC, BIN, "255", GROUP, "1111 1111"),
        (DEC, DEC, "1234567", GROUP, "1 234 567"),
        (DEC, DEC, "  42  ", PLAIN, "42"),        
        (DEC, DEC, "1 000", PLAIN, "1000"),      
        (DEC, DEC, "1_000", PLAIN, "1000"),       
        (BIN, HEX, "1111_1111", PREFIX, "0xFF"),
    ],
)
def test_convert_number_system_success(src, dst, text, option, expected):
    assert convert_number_system(src, dst, text, option) == expected


@pytest.mark.parametrize("text", ["", "   ", "-", "+", "_", "- "])
def test_convert_number_system_empty_input(text):
    with pytest.raises(ValueError, match=MSG_FORMAT):
        convert_number_system(DEC, BIN, text, PLAIN)


@pytest.mark.parametrize(
    "src, text",
    [
        (DEC, "abc!"),
        (DEC, "1.5"),
        (DEC, "1,5"),
        (HEX, "G"),
        (HEX, "XYZ"),
        (HEX, "0xFF"),    
        (OCT, "0o17"),
        (DEC, "10\n5"),
    ],
)
def test_convert_number_system_forbidden_characters(src, text):
    with pytest.raises(ValueError, match=MSG_FORMAT):
        convert_number_system(src, BIN, text, PLAIN)


@pytest.mark.parametrize(
    "src, text",
    [
        (BIN, "12"),
        (BIN, "2"),
        (TER, "3"),
        (OCT, "8"),
        (OCT, "9"),
        (DEC, "FF"),
        (DEC, "--5"),
    ],
)
def test_convert_number_system_digit_not_in_base(src, text):
    with pytest.raises(ValueError, match=MSG_MISMATCH):
        convert_number_system(src, DEC, text, PLAIN)


def test_convert_number_system_unknown_unit_raises_keyerror():
    with pytest.raises(KeyError):
        convert_number_system("Двенадцатеричная", BIN, "1", PLAIN)


def test_convert_number_system_long_binary_string_over_1000_chars():
    text = "1" * 1001
    n = int(text, 2)
    assert convert_number_system(BIN, HEX, text, PLAIN) == format(n, "X")
    assert convert_number_system(BIN, DEC, text, PLAIN) == str(n)


def test_convert_number_system_long_hex_string_over_1000_chars():
    text = "F" * 1001
    result = convert_number_system(HEX, BIN, text, PLAIN)
    assert result == "1" * (4 * 1001)


def test_convert_number_system_long_decimal_string_over_1000_chars():
    text = "9" * 1001
    n = int(text)
    assert convert_number_system(DEC, BIN, text, PLAIN) == bin(n)[2:]
    binary = convert_number_system(DEC, BIN, text, PLAIN)
    assert convert_number_system(BIN, DEC, binary, PLAIN) == text


def test_convert_number_system_long_string_with_prefix_and_grouping():
    text = "1" * 1001
    prefixed = convert_number_system(BIN, BIN, text, PREFIX)
    assert prefixed == "0b" + text
    grouped = convert_number_system(BIN, BIN, text, GROUP)
    assert grouped.replace(" ", "") == text
    assert all(len(part) <= 4 for part in grouped.split(" "))


@pytest.mark.skipif(
    not hasattr(sys, "get_int_max_str_digits")
    or not (0 < sys.get_int_max_str_digits() < 5000),
    reason="лимит int()<->str есть только в CPython 3.11+ (и если не отключён)",
)
def test_convert_number_system_decimal_beyond_cpython_digit_limit():
    with pytest.raises(ValueError, match=MSG_MISMATCH):
        convert_number_system(DEC, BIN, "9" * 5000, PLAIN)


# ==========================================================================
#  5. LinearCategory
# ==========================================================================
def test_convert_linear_category_success_and_result_format():
    result = get_category("Длина").convert(KM, M, "1")
    assert isinstance(result, ConversionResult)
    assert result.display == f"1 {KM}  =  1000 {M}"
    assert result.copy_text == f"1000 {M}"


def test_linear_category_accepts_decimal_comma():
    result = get_category("Длина").convert(KM, M, "1,5")
    assert result.display.startswith(f"1.5 {KM}")
    assert result.copy_text == f"1500 {M}"


def test_linear_category_accepts_scientific_notation():
    result = get_category("Длина").convert(KM, M, "1e3")
    assert result.display.startswith(f"1000 {KM}")
    assert result.copy_text == f"1e+06 {M}"


def test_linear_category_zero():
    result = get_category("Масса").convert("Тонна (т)", "Килограмм (кг)", "0")
    assert result.copy_text == "0 Килограмм (кг)"


@pytest.mark.parametrize("category", sorted(set(UNITS) - {"Углы"}))
def test_linear_negative_value_rejected(category):
    units = get_category(category).units
    with pytest.raises(InputError, match=MSG_NEGATIVE):
        get_category(category).convert(units[0], units[1], "-1")


def test_angles_allow_negative_value():
    result = get_category("Углы").convert(DEG, RAD, "-90")
    assert result.display.startswith(f"-90 {DEG}")
    assert result.copy_text == f"-1.5708 {RAD}"


@pytest.mark.parametrize("text", ["", "   ", "abc", "12abc", "1.2.3", "--5",
                                  "один", "1 2", "0x10"])
@pytest.mark.parametrize("category", ["Длина", "Углы", "Температура"])
def test_numeric_category_invalid_text(category, text):
    units = get_category(category).units
    with pytest.raises(InputError, match=MSG_FORMAT):
        get_category(category).convert(units[0], units[1], text)


def test_linear_category_unknown_unit_raises_calculation_error():
    with pytest.raises(CalculationError, match=MSG_CALC) as exc_info:
        get_category("Длина").convert("Парсек", M, "1")
    assert isinstance(exc_info.value.__cause__, KeyError)


# ==========================================================================
#  6. inf / nan  (по ТЗ должны отклоняться как InputError)
#     ВНИМАНИЕ: на текущем коде эти тесты падают, нужна правка из отчёта.
# ==========================================================================
NON_FINITE = ["inf", "+inf", "-inf", "Infinity", "nan", "NaN", "-nan"]


@pytest.mark.parametrize("text", NON_FINITE)
@pytest.mark.parametrize("category", ["Длина", "Углы", "Температура"])
def test_non_finite_input_rejected(category, text):
    units = get_category(category).units
    with pytest.raises(InputError):
        get_category(category).convert(units[0], units[1], text)


@pytest.mark.parametrize("text", ["inf", "nan"])
def test_non_finite_input_message_is_format_error(text):
    with pytest.raises(InputError, match=MSG_FORMAT):
        get_category("Длина").convert(KM, M, text)


@pytest.mark.parametrize("text", ["inf", "nan", "Infinity"])
def test_non_finite_not_valid_in_number_systems(text):
    with pytest.raises(InputError, match=MSG_FORMAT):
        get_category("Система счисления").convert(DEC, BIN, text, PLAIN)
        

def test_finite_input_overflow_must_not_produce_inf():
    with pytest.raises(CalculationError):
        get_category("Объём информации").convert(
            "Петабайт (ПБ)", "Бит (бит)", "1e308")


def test_temperature_overflow_must_not_produce_inf():
    with pytest.raises(CalculationError, match="слишком велик"):
        get_category("Температура").convert(C, F, "1e308")


def test_large_but_finite_result_is_accepted():
    result = get_category("Длина").convert(KM, M, "1e300")
    assert result.copy_text == f"1e+303 {M}"


# ==========================================================================
#  7. TemperatureCategory
# ==========================================================================
def test_temperature_success_and_result_format():
    result = get_category("Температура").convert(C, F, "100")
    assert result.display == f"100 {C}  =  212 {F}"
    assert result.copy_text == f"212 {F}"


def test_temperature_negative_celsius_allowed():
    result = get_category("Температура").convert(C, F, "-40")
    assert result.copy_text == f"-40 {F}"


@pytest.mark.parametrize(
    "unit, text",
    [(C, "-273.16"), (F, "-459.68"), (K, "-0.1"), (K, "-1"), (C, "-1000")],
)
def test_temperature_below_absolute_zero(unit, text):
    other = K if unit != K else C
    with pytest.raises(InputError, match=MSG_ABS_ZERO):
        get_category("Температура").convert(unit, other, text)


def test_temperature_exactly_absolute_zero_celsius_allowed():
    result = get_category("Температура").convert(C, K, "-273.15")
    assert result.copy_text == f"0 {K}"


def test_temperature_exactly_absolute_zero_kelvin_allowed():
    result = get_category("Температура").convert(K, C, "0")
    assert result.copy_text == f"-273.15 {C}"


def test_temperature_exactly_absolute_zero_fahrenheit_allowed():
    result = get_category("Температура").convert(F, K, "-459.67") 
    assert isinstance(result, ConversionResult)


def test_temperature_check_uses_source_unit_only():
    with pytest.raises(InputError, match=MSG_ABS_ZERO):
        get_category("Температура").convert(K, C, "-300")


def test_temperature_unknown_unit_raises_calculation_error():
    with pytest.raises(CalculationError, match=MSG_CALC) as exc_info:
        get_category("Температура").convert("Ранкин", C, "10")
    assert isinstance(exc_info.value.__cause__, ValueError)


# ==========================================================================
#  8. NumberSystemCategory
# ==========================================================================
def test_number_system_category_success_and_result_format():
    result = get_category("Система счисления").convert(DEC, HEX, "255", PREFIX)
    assert result.display == f"255 ({DEC})  →  0xFF ({HEX})"
    assert result.copy_text == "0xFF"


def test_number_system_category_default_format_option_is_plain():
    result = get_category("Система счисления").convert(DEC, HEX, "255")
    assert result.copy_text == "FF"


def test_number_system_category_negative_with_grouping():
    result = get_category("Система счисления").convert(
        DEC, DEC, "-1234567", GROUP)
    assert result.copy_text == "-1 234 567"


@pytest.mark.parametrize("text", ["", "   ", "-", "xyz", "0xFF", "1.5"])
def test_number_system_category_format_errors(text):
    with pytest.raises(InputError, match=MSG_FORMAT):
        get_category("Система счисления").convert(DEC, BIN, text, PLAIN)


def test_number_system_category_mismatch_error():
    with pytest.raises(InputError, match=MSG_MISMATCH):
        get_category("Система счисления").convert(BIN, DEC, "102", PLAIN)


def test_input_error_is_value_error_and_calculation_error_is_not():
    assert issubclass(InputError, ValueError)
    assert not issubclass(CalculationError, ValueError)


def test_number_system_category_long_string():
    text = "1" * 1001
    result = get_category("Система счисления").convert(BIN, HEX, text, PLAIN)
    assert result.copy_text == format(int(text, 2), "X")


def test_conversion_result_is_immutable():
    result = ConversionResult("a", "b")
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.display = "c"


# ==========================================================================
#  9. HistoryEntry и ConversionHistory
# ==========================================================================
def test_history_starts_empty():
    history = ConversionHistory()
    assert len(history) == 0
    assert history.newest_first() == []


def test_history_add_single_entry():
    history = ConversionHistory()
    e = _entry(1)
    history.add(e)
    assert len(history) == 1
    assert history.newest_first() == [e]


def test_history_order_newest_first():
    history = ConversionHistory()
    e1, e2, e3 = _entry(1), _entry(2), _entry(3)
    for e in (e1, e2, e3):
        history.add(e)
    assert history.newest_first() == [e3, e2, e1]


def test_history_limit_and_dedupe():
    history = ConversionHistory(limit=3)
    entries = [_entry(i) for i in range(1, 6)]
    for e in entries:
        history.add(e)
    assert len(history) == 3
    assert history.newest_first() == [entries[4], entries[3], entries[2]]

    history.add(_entry(3, display="обновлённая запись"))
    assert len(history) == 3
    newest = history.newest_first()
    assert [e.input_raw for e in newest] == ["3", "5", "4"]
    assert newest[0].display == "обновлённая запись"


def test_history_default_limit_is_three():
    history = ConversionHistory()
    for i in range(10):
        history.add(_entry(i))
    assert len(history) == 3
    assert [e.input_raw for e in history.newest_first()] == ["9", "8", "7"]


def test_history_custom_limit():
    history = ConversionHistory(limit=1)
    history.add(_entry(1))
    history.add(_entry(2))
    assert len(history) == 1
    assert history.newest_first()[0].input_raw == "2"


def test_history_duplicate_at_full_capacity_evicts_nothing():
    history = ConversionHistory(limit=3)
    a, b, c = _entry(1), _entry(2), _entry(3)
    for e in (a, b, c):
        history.add(e)
    history.add(_entry(1))
    assert len(history) == 3
    assert [e.input_raw for e in history.newest_first()] == ["1", "3", "2"]


def test_history_repeating_same_entry_keeps_single_record():
    history = ConversionHistory()
    for _ in range(5):
        history.add(_entry(1))
    assert len(history) == 1


@pytest.mark.parametrize(
    "override",
    [
        dict(category="Масса"),
        dict(from_unit="Миля (mi)"),
        dict(to_unit="Дюйм (in)"),
        dict(input_raw="999"),
        dict(format_option=GROUP),
    ],
    ids=["category", "from_unit", "to_unit", "input_raw", "format_option"],
)
def test_history_entries_differing_in_key_field_are_not_duplicates(override):
    history = ConversionHistory()
    history.add(_entry(1))
    history.add(_entry(1, **override))
    assert len(history) == 2


def test_history_display_is_not_part_of_dedupe_key():
    history = ConversionHistory()
    history.add(_entry(1, display="первый вариант"))
    history.add(_entry(1, display="второй вариант"))
    assert len(history) == 1
    assert history.newest_first()[0].display == "второй вариант"


def test_history_newest_first_returns_copy():
    history = ConversionHistory()
    history.add(_entry(1))
    snapshot = history.newest_first()
    snapshot.clear()
    assert len(history) == 1


def test_history_entry_key_and_defaults():
    e = HistoryEntry("Длина", KM, M, "1", "показ")
    assert e.format_option is None
    assert e.key == ("Длина", KM, M, "1", None)


def test_history_entry_is_immutable():
    e = _entry(1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.input_raw = "2"


def test_history_integration_with_category_conversion():
    history = ConversionHistory(limit=3)
    cat = get_category("Длина")
    for text in ("1", "2", "1"):
        result = cat.convert(KM, M, text)
        history.add(HistoryEntry("Длина", KM, M, text, result.display))
    assert len(history) == 2
    assert [e.input_raw for e in history.newest_first()] == ["1", "2"]
