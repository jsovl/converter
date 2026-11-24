"""Логика «Конвертера величин»: данные, конвертация, категории, история.
Модуль не зависит от customtkinter и тестируется напрямую через pytest."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

#  ЕДИНИЦЫ ИЗМЕРЕНИЯ
UNITS = {
    # -------------------- ВРЕМЯ --------------------
    "Время": {
        "Наносекунда (нс)": 1e-9,
        "Микросекунда (мкс)": 1e-6,
        "Миллисекунда (мс)": 1e-3,
        "Секунда (с)": 1.0,
        "Минута (мин)": 60.0,
        "Час (ч)": 3600.0,
        "Сутки": 86400.0,
        "Неделя": 7 * 86400.0,
        "Месяц (30 суток)": 30 * 86400.0,
        "Год (365 суток)": 365 * 86400.0,
    },
    # -------------------- ДАВЛЕНИЕ --------------------
    "Давление": {
        "Паскаль (Па)": 1.0,
        "Миллибар (мбар)": 100.0,
        "Гектопаскаль (гПа)": 100.0,
        "Миллиметр ртутного столба (мм рт. ст.)": 133.322,
        "Килопаскаль (кПа)": 1000.0,
        "Фунт на квадратный дюйм (psi)": 6894.757,
        "Бар": 100000.0,
        "Атмосфера (атм)": 101325.0,
        "Мегапаскаль (МПа)": 1e6,
    },
    # -------------------- ДЛИНА --------------------
    "Длина": {
        "Нанометр (нм)": 1e-9,
        "Микрометр (мкм)": 1e-6,
        "Миллиметр (мм)": 0.001,
        "Сантиметр (см)": 0.01,
        "Дюйм (in)": 0.0254,
        "Фут (ft)": 0.3048,
        "Ярд (yd)": 0.9144,
        "Метр (м)": 1.0,
        "Километр (км)": 1000.0,
        "Миля (mi)": 1609.344,
        "Морская миля": 1852.0,
    },
    # -------------------- ЗАРЯД --------------------
    "Заряд": {
        "Элементарный заряд (e)": 1.602176634e-19,
        "Микрокулон (мкКл)": 1e-6,
        "Милликулон (мКл)": 1e-3,
        "Кулон (Кл)": 1.0,
        "Ампер-час (А·ч)": 3600.0,
    },
    # -------------------- МАССА --------------------
    "Масса": {
        "Микрограмм (мкг)": 1e-9,
        "Миллиграмм (мг)": 1e-6,
        "Грамм (г)": 0.001,
        "Унция (oz)": 0.028349523125,
        "Фунт (lb)": 0.45359237,
        "Килограмм (кг)": 1.0,
        "Тонна (т)": 1000.0,
    },
    # -------------------- МОЩНОСТЬ --------------------
    "Мощность": {
        "Микроватт (мкВт)": 1e-6,
        "Милливатт (мВт)": 1e-3,
        "Ватт (Вт)": 1.0,
        "Лошадиная сила (л.с.)": 735.49875,
        "Киловатт (кВт)": 1000.0,
        "Мегаватт (МВт)": 1e6,
    },
    # -------------------- НАПРЯЖЕНИЕ --------------------
    "Напряжение": {
        "Микровольт (мкВ)": 1e-6,
        "Милливольт (мВ)": 1e-3,
        "Вольт (В)": 1.0,
        "Киловольт (кВ)": 1000.0,
        "Мегавольт (МВ)": 1e6,
    },
    # -------------------- ОБЪЁМ --------------------
    "Объём": {
        "Миллилитр (мл)": 0.001,
        "Пинта (US)": 0.473176473,
        "Литр (л)": 1.0,
        "Галлон (US)": 3.785411784,
        "Кубометр (м³)": 1000.0,
    },
    # ------------- ОБЪЁМ ИНФОРМАЦИИ ----------------
    "Объём информации": {
        "Бит (бит)": 0.125,
        "Байт (Б)": 1.0,
        "Килобит (Кбит)": 128.0,
        "Килобайт (КБ)": 1024.0,
        "Мегабит (Мбит)": 131072.0,
        "Мегабайт (МБ)": 1024.0 ** 2,
        "Гигабит (Гбит)": 134217728.0,
        "Гигабайт (ГБ)": 1024.0 ** 3,
        "Терабит (Тбит)": 137438953472.0,
        "Терабайт (ТБ)": 1024.0 ** 4,
        "Петабит (Пбит)": 140737488355328.0,
        "Петабайт (ПБ)": 1024.0 ** 5,
    },
    # -------------------- ПЛОЩАДЬ --------------------
    "Площадь": {
        "Квадратный сантиметр (см²)": 1e-4,
        "Квадратный метр (м²)": 1.0,
        "Ар (сотка)": 100.0,
        "Гектар (га)": 10000.0,
        "Квадратный километр (км²)": 1e6,
        "Квадратная миля (mi²)": 2589988.110336,
    },
    # --------------- ПРОЦЕНТЫ И ДОЛИ ----------------
    "Проценты и доли": {
        "Частей на миллион (ppm)": 1e-6,
        "Промилле (‰)": 0.001,
        "Процент (%)": 0.01,
        "Доля": 1.0,
    },
    # --------------- РАЗРЕШЕНИЕ ЭКРАНА ----------------
    "Разрешение экрана": {
        "Пиксель (px)": 1.0,
        "Килопиксель (Kpx)": 1000.0,
        "Мегапиксель (Mpx)": 1e6,
        "Гигапиксель (Gpx)": 1e9,
    },
    # -------------------- СИЛА --------------------
    "Сила": {
        "Миллиньютон (мН)": 1e-3,
        "Ньютон (Н)": 1.0,
        "Фунт-сила (lbf)": 4.4482216152605,
        "Килограмм-сила (кгс)": 9.80665,
        "Килоньютон (кН)": 1000.0,
    },
    # ---------------- СИЛА ТОКА -------------------
    "Сила тока": {
        "Микроампер (мкА)": 1e-6,
        "Миллиампер (мА)": 1e-3,
        "Ампер (А)": 1.0,
        "Килоампер (кА)": 1000.0,
    },
    # ---------------- СКОРОСТЬ -----------------
    "Скорость": {
        "Километр/час (км/ч)": 1 / 3.6,
        "Миля/час (mph)": 0.44704,
        "Узел (kt)": 0.514444,
        "Метр/сек (м/с)": 1.0,
    },
    # ------------- СКОРОСТЬ ПЕРЕДАЧИ ДАННЫХ ----------------
    "Скорость передачи данных": {
        "Бит/сек (бит/с)": 1.0,
        "Килобит/сек (Кбит/с)": 1000.0,
        "Килобайт/сек (КБ/с)": 8000.0,
        "Мегабит/сек (Мбит/с)": 1e6,
        "Мегабайт/сек (МБ/с)": 8e6,
        "Гигабит/сек (Гбит/с)": 1e9,
        "Гигабайт/сек (ГБ/с)": 8e9,
        "Терабит/сек (Тбит/с)": 1e12,
        "Терабайт/сек (ТБ/с)": 8e12,
    },
    # ---------------- СОПРОТИВЛЕНИЕ -------------------
    "Сопротивление": {
        "Микроом (мкОм)": 1e-6,
        "Миллиом (мОм)": 1e-3,
        "Ом (Ом)": 1.0,
        "Килоом (кОм)": 1000.0,
        "Мегаом (МОм)": 1e6,
    },
    # -------------------- УГЛЫ --------------------
    "Углы": {
        "Угловая секунда (″)": math.pi / (180 * 3600),
        "Угловая минута (′)": math.pi / (180 * 60),
        "Град (gon)": math.pi / 200,
        "Градус (°)": math.pi / 180,
        "Радиан (рад)": 1.0,
        "Оборот": 2 * math.pi,
    },
    # -------------------- ЧАСТОТА --------------------
    "Частота": {
        "Герц (Гц)": 1.0,
        "Килогерц (кГц)": 1000.0,
        "Мегагерц (МГц)": 1e6,
        "Гигагерц (ГГц)": 1e9,
        "Терагерц (ТГц)": 1e12,
    },
    # -------------------- ЭНЕРГИЯ --------------------
    "Энергия": {
        "Электронвольт (эВ)": 1.602176634e-19,
        "Джоуль (Дж)": 1.0,
        "Калория (кал)": 4.184,
        "Килоджоуль (кДж)": 1000.0,
        "Ватт-час (Вт·ч)": 3600.0,
        "Килокалория (ккал)": 4184.0,
        "Мегаджоуль (МДж)": 1e6,
        "Киловатт-час (кВт·ч)": 3.6e6,
    },
}

TEMPERATURE_UNITS = ["Цельсий (°C)", "Фаренгейт (°F)", "Кельвин (K)"]

NUMBER_SYSTEMS = {
    "Двоичная (2)": 2,
    "Троичная (3)": 3,
    "Четверичная (4)": 4,
    "Пятеричная (5)": 5,
    "Восьмеричная (8)": 8,
    "Десятичная (10)": 10,
    "Шестнадцатеричная (16)": 16,
}

SPECIAL_CATEGORIES = {"Температура", "Система счисления"}
ALL_CATEGORIES = sorted(list(UNITS.keys()) + list(SPECIAL_CATEGORIES))

ABSOLUTE_ZERO = {
    "Цельсий (°C)": -273.15,
    "Фаренгейт (°F)": -459.67,
    "Кельвин (K)": 0.0,
}

#  ЛОГИКА КОНВЕРТАЦИИ
def convert_linear(category, from_unit, to_unit, value):
    factors = UNITS[category]
    return value * factors[from_unit] / factors[to_unit]

def convert_temperature(from_unit, to_unit, value):
    if from_unit == "Цельсий (°C)":
        c = value
    elif from_unit == "Фаренгейт (°F)":
        c = (value - 32) * 5 / 9
    elif from_unit == "Кельвин (K)":
        c = value - 273.15
    else:
        raise ValueError("Неизвестная единица температуры")

    if to_unit == "Цельсий (°C)":
        return c
    if to_unit == "Фаренгейт (°F)":
        return c * 9 / 5 + 32
    if to_unit == "Кельвин (K)":
        return c + 273.15
    raise ValueError("Неизвестная единица температуры")

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def to_base(n, base):
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    result = ""
    while n:
        result = DIGITS[n % base] + result
        n //= base
    return sign + result

def format_number(s, base, option):
    sign = ""
    if s.startswith("-"):
        sign, s = "-", s[1:]

    if option == "С префиксом":
        prefix = {2: "0b", 8: "0o", 16: "0x"}.get(base, "")
        return sign + prefix + s

    if option == "С группировкой разрядов":
        if base in (2, 16):
            group_size = 4
        elif base == 10:
            group_size = 3
        else:
            group_size = 4

        rev = s[::-1]
        grouped = " ".join(
            rev[i:i + group_size] for i in range(0, len(rev), group_size)
        )
        return sign + grouped[::-1]

    return sign + s

ALLOWED_CHARS = set("0123456789ABCDEFabcdef")

def convert_number_system(from_unit, to_unit, value_str, format_option):
    from_n = NUMBER_SYSTEMS[from_unit]
    to_n = NUMBER_SYSTEMS[to_unit]

    value_str = value_str.strip().replace(" ", "").replace("_", "")
    check_str = value_str.lstrip("+-")

    if not check_str:
        raise ValueError("Некорректный формат ввода")

    for ch in check_str:
        if ch not in ALLOWED_CHARS:
            raise ValueError("Некорректный формат ввода")

    try:
        n = int(value_str, from_n)
    except ValueError:
        raise ValueError(
            "Введенное значение не соответствует выбранной системе счисления"
        )

    return format_number(to_base(n, to_n), to_n, format_option)


#  КАТЕГОРИИ (СТРАТЕГИИ) И ВАЛИДАЦИЯ ВВОДА
class InputError(ValueError):
    """Некорректный ввод пользователя (в UI: «Ошибка ввода»)."""


class CalculationError(Exception):
    """Непредвиденный сбой вычисления (в UI: «Ошибка»)."""


@dataclass(frozen=True)
class ConversionResult:
    """Результат: строка для показа и строка для буфера обмена."""
    display: str
    copy_text: str


class Category(ABC):
    """Базовый интерфейс категории величин."""

    has_format_option = False

    def __init__(self, name):
        self.name = name

    @property
    @abstractmethod
    def units(self):
        """Названия единиц в порядке отображения."""

    @abstractmethod
    def convert(self, from_unit, to_unit, text, format_option=None):
        """Валидирует ввод и конвертирует. Бросает InputError / CalculationError."""


class _NumericCategory(Category):
    """Общий шаблон для категорий с вводом вещественного числа."""

    def convert(self, from_unit, to_unit, text, format_option=None):
        try:
            value = float(text.replace(",", "."))
        except ValueError as exc:
            raise InputError("Некорректный формат ввода") from exc

        if not math.isfinite(value):
            raise InputError("Некорректный формат ввода")

        self._validate(value, from_unit)

        try:
            result = self._compute(from_unit, to_unit, value)
        except Exception as exc:
            raise CalculationError("Не удалось выполнить перевод") from exc

        if not math.isfinite(result):
            raise CalculationError("Результат слишком велик для вычисления")

        display = f"{value:g} {from_unit}  =  {result:.6g} {to_unit}"
        return ConversionResult(display, f"{result:.6g} {to_unit}")
            

    @abstractmethod
    def _validate(self, value, from_unit):
        """Проверка допустимости значения (бросает InputError)."""

    @abstractmethod
    def _compute(self, from_unit, to_unit, value):
        """Вычисление."""


class LinearCategory(_NumericCategory):
    """Единицы, связанные коэффициентами (длина, масса, время и т.д.)."""

    def __init__(self, name, allow_negative=False):
        super().__init__(name)
        self._allow_negative = allow_negative

    @property
    def units(self):
        return list(UNITS[self.name].keys())

    def _validate(self, value, from_unit):
        if not self._allow_negative and value < 0:
            raise InputError("Значение не может быть отрицательным")

    def _compute(self, from_unit, to_unit, value):
        return convert_linear(self.name, from_unit, to_unit, value)


class TemperatureCategory(_NumericCategory):
    """Температура: минус допустим, но не ниже абсолютного нуля."""

    def __init__(self):
        super().__init__("Температура")

    @property
    def units(self):
        return list(TEMPERATURE_UNITS)

    def _validate(self, value, from_unit):
        min_val = ABSOLUTE_ZERO.get(from_unit)
        if min_val is not None and value < min_val:
            raise InputError("Температура ниже абсолютного нуля")

    def _compute(self, from_unit, to_unit, value):
        return convert_temperature(from_unit, to_unit, value)


class NumberSystemCategory(Category):
    """Системы счисления: ввод — строка, вывод — с выбранным форматом."""

    has_format_option = True

    def __init__(self):
        super().__init__("Система счисления")

    @property
    def units(self):
        return list(NUMBER_SYSTEMS.keys())

    def convert(self, from_unit, to_unit, text, format_option=None):
        try:
            result_str = convert_number_system(
                from_unit, to_unit, text, format_option
            )
        except ValueError as exc:
            raise InputError(str(exc)) from exc
        display = f"{text} ({from_unit})  →  {result_str} ({to_unit})"
        return ConversionResult(display, result_str)


CATEGORIES_ALLOWING_NEGATIVE = {"Углы"}


def _build_registry():
    registry = {
        name: LinearCategory(name, allow_negative=name in CATEGORIES_ALLOWING_NEGATIVE)
        for name in UNITS
    }
    registry["Температура"] = TemperatureCategory()
    registry["Система счисления"] = NumberSystemCategory()
    return registry


_REGISTRY = _build_registry()


def get_category(name):
    """Возвращает объект категории по названию."""
    return _REGISTRY[name]


#  ИСТОРИЯ КОНВЕРТАЦИЙ
@dataclass(frozen=True)
class HistoryEntry:
    category: str
    from_unit: str
    to_unit: str
    input_raw: str
    display: str
    format_option: Optional[str] = None

    @property
    def key(self):
        """Ключ дубликата: тот же перевод и то же введённое значение."""
        return (self.category, self.from_unit, self.to_unit,
                self.input_raw, self.format_option)


class ConversionHistory:
    """Хранит не более `limit` последних уникальных записей."""

    def __init__(self, limit=3):
        self._limit = limit
        self._entries = []

    def add(self, entry):
        self._entries = [e for e in self._entries if e.key != entry.key]
        self._entries.append(entry)
        if len(self._entries) > self._limit:
            self._entries = self._entries[-self._limit:]

    def newest_first(self):
        return list(reversed(self._entries))

    def __len__(self):
        return len(self._entries)
