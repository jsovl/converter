"""Интерфейс «Конвертера величин» (customtkinter). Вся логика — в converter_logic.py."""
import customtkinter as ctk

from converter_logic import (
    ALL_CATEGORIES,
    CalculationError,
    ConversionHistory,
    HistoryEntry,
    InputError,
    get_category,
)

#  ПАЛИТРА  (тёплая для светлой темы, холодная для тёмной)
LIGHT_BG          = "#FBF3E6"
DARK_BG           = "#0E1620"
LIGHT_CARD        = "#F5E7D2"
DARK_CARD         = "#1A2433"
LIGHT_ENTRY       = "#FFFBF4"
DARK_ENTRY        = "#0A1118"
LIGHT_ACCENT      = "#D97757"
DARK_ACCENT       = "#5B9BD5"
LIGHT_ACCENT_HOV  = "#BF6244"
DARK_ACCENT_HOV   = "#4A87BD"
LIGHT_TEXT        = "#3A2E22"
DARK_TEXT         = "#E6EEF7"
LIGHT_TEXT_DIM    = "#8B7355"
DARK_TEXT_DIM     = "#8A97A8"
LIGHT_BORDER      = "#E4CDA9"
DARK_BORDER       = "#2A3446"

# Контрастный красный для окна ошибки
ERR_BG_LIGHT      = "#8B1A1A"
ERR_BG_DARK       = "#B71C1C"
ERR_ACCENT_LIGHT  = "#FFD6D6"
ERR_ACCENT_DARK   = "#FFCDD2"

FONT_FAMILY = "Segoe UI"

#  КОНТРАСТНОЕ ОКНО ОШИБКИ
class ErrorDialog(ctk.CTkToplevel):

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=(ERR_BG_LIGHT, ERR_BG_DARK))

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=26, pady=22)

        icon = ctk.CTkLabel(
            container,
            text="!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=42, weight="bold"),
            text_color=(ERR_ACCENT_LIGHT, ERR_ACCENT_DARK),
        )
        icon.pack(pady=(0, 6))

        head = ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color="#FFFFFF",
        )
        head.pack(pady=(0, 4))

        msg = ctk.CTkLabel(
            container,
            text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color="#FFF0F0",
            wraplength=380,
            justify="center",
        )
        msg.pack(pady=(0, 16), fill="x")

        btn = ctk.CTkButton(
            container,
            text="Понятно",
            width=140,
            height=38,
            corner_radius=19,
            command=self._close,
            fg_color="#FFFFFF",
            hover_color="#FFE0E0",
            text_color="#7A1010",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        btn.pack()

        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 420)
        h = max(self.winfo_reqheight(), 240)
        self.geometry(f"{w}x{h}")

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

        self.transient(parent)
        self.grab_set()
        self.bind("<Return>", lambda e: self._close())
        self.bind("<Escape>", lambda e: self._close())
        self.after(50, self.lift)
        self.after(60, self.focus_force)

    def _close(self):
        self.grab_release()
        self.destroy()

#  ВЫПАДАЮЩИЙ СПИСОК С ПРОКРУТКОЙ
class _ScrollableComboPopup(ctk.CTkToplevel):

    def __init__(self, master, values, on_select, current_value=None,
                 font=None, fg_color=None, hover_color=None, text_color=None,
                 scrollbar_color=None, scrollbar_hover_color=None,
                 border_color=None,
                 item_height=32, max_visible=6, width=200,
                 corner_radius=10, on_close=None):
        super().__init__(master)

        self.overrideredirect(True)

        try:
            self.transient(master.winfo_toplevel())
        except Exception:
            pass

        self._on_select = on_select
        self._on_close = on_close
        self._closed = False
        self._master = master
        self._closing_scheduled = False

        count = len(values)
        visible_count = min(max_visible, count) if count > 0 else 1
        needs_scroll = count > max_visible

        inner_height = visible_count * (item_height + 2) + 2
        container_pad = 2
        border = 2
        total_height = inner_height + 2 * container_pad + border

        container = ctk.CTkFrame(
            self,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=1,
            border_color=border_color,
        )
        container.pack(fill="both", expand=True)

        scroll_width = max(width - 28, 80)
        self._scroll = ctk.CTkScrollableFrame(
            container,
            width=scroll_width,
            height=inner_height,
            fg_color=fg_color,
            corner_radius=0,
            scrollbar_button_color=scrollbar_color,
            scrollbar_button_hover_color=scrollbar_hover_color,
        )
        self._scroll.pack(fill="both", expand=True,
                          padx=container_pad, pady=container_pad)

        if not needs_scroll:
            try:
                self._scroll._scrollbar.grid_remove()
            except Exception:
                pass

        for value in values:
            is_current = (value == current_value)
            btn = ctk.CTkButton(
                self._scroll,
                text=value,
                anchor="w",
                height=item_height,
                corner_radius=6,
                font=font,
                fg_color=hover_color if is_current else "transparent",
                hover_color=hover_color,
                text_color=text_color,
                command=lambda v=value: self._select(v),
            )
            btn.pack(fill="x", padx=2, pady=1)

        self.bind("<Escape>", lambda e: self._close())
        self.bind("<Button-1>", self._on_click, add="+")
        self.bind("<FocusOut>", self._on_focus_out, add="+")
        try:
            self.bind("<Unmap>", lambda e: self._close(), add="+")
        except Exception:
            pass

        self.update_idletasks()
        w = max(width, self.winfo_reqwidth())
        h = total_height

        x = master.winfo_rootx()
        y = master.winfo_rooty() + master.winfo_height() + 2

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        if x + w > screen_w:
            x = max(screen_w - w - 8, 0)
        if y + h > screen_h:
            y = master.winfo_rooty() - h - 2
            if y < 0:
                y = 0

        self.geometry(f"{w}x{h}+{x}+{y}")

        self.after(10, self._grab)
        self.after(20, self._focus)

    def _grab(self):
        if self._closed or not self.winfo_exists():
            return
        try:
            self.grab_set()
        except Exception:
            pass

    def _focus(self):
        if self._closed or not self.winfo_exists():
            return
        try:
            self.focus_force()
        except Exception:
            pass

    def _on_focus_out(self, event):
        if self._closed or not self.winfo_exists():
            return
        if self._closing_scheduled:
            return
        try:
            focus_widget = self.focus_get()
        except Exception:
            focus_widget = None
        if focus_widget is not None:
            w = focus_widget
            while w is not None:
                if w is self:
                    return
                try:
                    w = w.master
                except Exception:
                    break
        self._closing_scheduled = True
        self.after(1, self._close)

    def _on_click(self, event):
        if self._closed:
            return
        popup_x = self.winfo_rootx()
        popup_y = self.winfo_rooty()
        popup_w = self.winfo_width()
        popup_h = self.winfo_height()
        x, y = event.x_root, event.y_root
        if not (popup_x <= x < popup_x + popup_w and
                popup_y <= y < popup_y + popup_h):
            self._close()

    def _select(self, value):
        if self._closed:
            return
        try:
            self._on_select(value)
        finally:
            self._close()

    def _close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            toplevel = self._master.winfo_toplevel()
            if toplevel.winfo_exists():
                toplevel.focus_set()
        except Exception:
            pass
        if self._on_close is not None:
            try:
                self._on_close()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass

#  КОМБОБОКС С ПРОКРУТКОЙ
class ScrollableComboBox(ctk.CTkComboBox):

    def __init__(self, master, *,
                 max_visible=6,
                 item_height=32,
                 dropdown_scrollbar_color=None,
                 dropdown_scrollbar_hover_color=None,
                 **kwargs):
        super().__init__(master, **kwargs)

        self._max_visible = max_visible
        self._item_height = item_height
        self._popup = None

        # Цвет скроллбара для выпадающего списка
        if dropdown_scrollbar_color is None:
            try:
                dropdown_scrollbar_color = self.cget("button_color")
            except Exception:
                dropdown_scrollbar_color = (LIGHT_ACCENT, DARK_ACCENT)
        if dropdown_scrollbar_hover_color is None:
            try:
                dropdown_scrollbar_hover_color = self.cget("button_hover_color")
            except Exception:
                dropdown_scrollbar_hover_color = (LIGHT_ACCENT_HOV, DARK_ACCENT_HOV)

        self._dd_scrollbar_color = dropdown_scrollbar_color
        self._dd_scrollbar_hover_color = dropdown_scrollbar_hover_color

    # Перехват открытия списка
    def _open_dropdown_menu(self):

        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    return
            except Exception:
                pass
            self._popup = None

        values = list(getattr(self, "_values", []) or [])
        if not values:
            return

        # Безопасное получение параметров оформления у CTkComboBox
        def _safe_cget(name, fallback):
            try:
                return self.cget(name)
            except Exception:
                return fallback

        dd_fg = _safe_cget("dropdown_fg_color", (LIGHT_ENTRY, DARK_ENTRY))
        dd_hover = _safe_cget("dropdown_hover_color", (LIGHT_BORDER, DARK_BORDER))
        dd_text = _safe_cget("dropdown_text_color", (LIGHT_TEXT, DARK_TEXT))
        border_color = _safe_cget("border_color", (LIGHT_BORDER, DARK_BORDER))
        corner_radius = _safe_cget("corner_radius", 10)

        try:
            dd_font = self.cget("dropdown_font")
        except Exception:
            dd_font = ctk.CTkFont(family=FONT_FAMILY, size=13)

        # Ширина выпадающего списка
        try:
            max_w = max(dd_font.measure(v) for v in values)
        except Exception:
            max_w = 180
        popup_width = max(max_w + 64, 160)

        current_value = self.get()

        self._popup = _ScrollableComboPopup(
            self,
            values=values,
            current_value=current_value,
            on_select=self._on_popup_select,
            font=dd_font,
            fg_color=dd_fg,
            hover_color=dd_hover,
            text_color=dd_text,
            scrollbar_color=self._dd_scrollbar_color,
            scrollbar_hover_color=self._dd_scrollbar_hover_color,
            border_color=border_color,
            item_height=self._item_height,
            max_visible=self._max_visible,
            width=popup_width,
            corner_radius=corner_radius,
            on_close=self._on_popup_closed,
        )

    def _on_popup_closed(self):
        self._popup = None

    def _on_popup_select(self, value):
        self.set(value)
        if getattr(self, "_command", None) is not None:
            try:
                self._command(value)
            except Exception:
                pass

#  ГЛАВНОЕ ПРИЛОЖЕНИЕ
class ConverterApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.title("Конвертер величин")
        self.geometry("640x780")
        self.minsize(620, 760)
        self.resizable(False, False)
        self.configure(fg_color=(LIGHT_BG, DARK_BG))

        # История конвертаций
        self.history = ConversionHistory(limit=3)
        self.last_result_text = None
        self._copy_reset_job = None

        self._build_ui()
        self._update_units()
        self._render_history()

    def _build_ui(self):
        # ЗАГОЛОВОК
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=26, pady=(22, 10))

        title = ctk.CTkLabel(
            header,
            text="Конвертер величин",
            font=ctk.CTkFont(family=FONT_FAMILY, size=23, weight="bold"),
            text_color=(LIGHT_TEXT, DARK_TEXT),
        )
        title.pack(side="left")

        # ПЕРЕКЛЮЧАТЕЛЬ ТЕМЫ
        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.pack(side="right", pady=4)

        self.light_label = ctk.CTkLabel(
            theme_frame,
            text="Светлая тема",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=(LIGHT_TEXT_DIM, DARK_TEXT_DIM),
        )
        self.light_label.pack(side="left", padx=(0, 8))

        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="",
            command=self._toggle_theme,
            progress_color=(LIGHT_ACCENT, DARK_ACCENT),
            button_color=("#FFFFFF", "#E6EEF7"),
            button_hover_color=("#F0F0F0", "#C7D3E3"),
            width=42,
        )
        self.theme_switch.pack(side="left")

        self.dark_label = ctk.CTkLabel(
            theme_frame,
            text="Тёмная тема",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=(LIGHT_TEXT_DIM, DARK_TEXT_DIM),
        )
        self.dark_label.pack(side="left", padx=(8, 0))

        subtitle = ctk.CTkLabel(
            self,
            text="Быстрый перевод единиц измерения и систем счисления",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=(LIGHT_TEXT_DIM, DARK_TEXT_DIM),
        )
        subtitle.pack(anchor="w", padx=28, pady=(0, 12))

        # ФОРМА
        card = ctk.CTkFrame(
            self,
            fg_color=(LIGHT_CARD, DARK_CARD),
            corner_radius=18,
            border_width=1,
            border_color=(LIGHT_BORDER, DARK_BORDER),
        )
        card.pack(fill="x", padx=22, pady=(0, 14))
        card.grid_columnconfigure(1, weight=1)

        pad = {"padx": 16, "pady": 9}
        lbl_font = ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")

        combo_kwargs = dict(
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=(LIGHT_ENTRY, DARK_ENTRY),
            border_color=(LIGHT_BORDER, DARK_BORDER),
            button_color=(LIGHT_ACCENT, DARK_ACCENT),
            button_hover_color=(LIGHT_ACCENT_HOV, DARK_ACCENT_HOV),
            text_color=(LIGHT_TEXT, DARK_TEXT),
            dropdown_fg_color=(LIGHT_ENTRY, DARK_ENTRY),
            dropdown_hover_color=(LIGHT_BORDER, DARK_BORDER),
            dropdown_text_color=(LIGHT_TEXT, DARK_TEXT),
            max_visible=6,
        )

        # Тип величины (первое поле)
        ctk.CTkLabel(
            card, text="Тип величины", font=lbl_font,
            text_color=(LIGHT_TEXT, DARK_TEXT),
        ).grid(row=0, column=0, sticky="w", **pad)

        self.category_var = ctk.StringVar(value=ALL_CATEGORIES[0])
        self.category_cb = ScrollableComboBox(
            card,
            variable=self.category_var,
            values=ALL_CATEGORIES,
            command=lambda _v: self._update_units(),
            **combo_kwargs,
        )
        self.category_cb.grid(row=0, column=1, sticky="ew", **pad)

        # Из единицы (второе поле)
        ctk.CTkLabel(
            card, text="Из единицы", font=lbl_font,
            text_color=(LIGHT_TEXT, DARK_TEXT),
        ).grid(row=1, column=0, sticky="w", **pad)

        self.from_var = ctk.StringVar()
        self.from_cb = ScrollableComboBox(
            card, variable=self.from_var, values=[], **combo_kwargs,
        )
        self.from_cb.grid(row=1, column=1, sticky="ew", **pad)

        # В единицу (третье поле)
        ctk.CTkLabel(
            card, text="В единицу", font=lbl_font,
            text_color=(LIGHT_TEXT, DARK_TEXT),
        ).grid(row=2, column=0, sticky="w", **pad)

        self.to_var = ctk.StringVar()
        self.to_cb = ScrollableComboBox(
            card, variable=self.to_var, values=[], **combo_kwargs,
        )
        self.to_cb.grid(row=2, column=1, sticky="ew", **pad)

        # Формат вывода (четвертое поле) — только для систем счисления
        self.extra_label = ctk.CTkLabel(
            card, text="Формат вывода", font=lbl_font,
            text_color=(LIGHT_TEXT, DARK_TEXT),
        )
        self.extra_label.grid(row=3, column=0, sticky="w", **pad)

        self.extra_var = ctk.StringVar(value="Обычный")
        self.extra_cb = ScrollableComboBox(
            card,
            variable=self.extra_var,
            values=["Обычный", "С префиксом", "С группировкой разрядов"],
            **combo_kwargs,
        )
        self.extra_cb.grid(row=3, column=1, sticky="ew", **pad)
        self.extra_label.grid_remove()
        self.extra_cb.grid_remove()

        # Значение (пятое поле)
        ctk.CTkLabel(
            card, text="Значение", font=lbl_font,
            text_color=(LIGHT_TEXT, DARK_TEXT),
        ).grid(row=4, column=0, sticky="w", **pad)

        self.value_entry = ctk.CTkEntry(
            card,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=(LIGHT_ENTRY, DARK_ENTRY),
            border_color=(LIGHT_BORDER, DARK_BORDER),
            text_color=(LIGHT_TEXT, DARK_TEXT),
        )
        self.value_entry.grid(row=4, column=1, sticky="ew", **pad)
        self.value_entry.insert(0, "1")
        self.value_entry.bind("<Return>", lambda _e: self.calculate())

        # Кнопка «Рассчитать» (шестое поле)
        self.calc_btn = ctk.CTkButton(
            card,
            text="Рассчитать",
            command=self.calculate,
            height=46,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color=(LIGHT_ACCENT, DARK_ACCENT),
            hover_color=(LIGHT_ACCENT_HOV, DARK_ACCENT_HOV),
            text_color="#FFFFFF",
        )
        self.calc_btn.grid(row=5, column=0, columnspan=2,
                           pady=(18, 14), padx=16, sticky="ew")

        # ФОРМА РЕЗУЛЬТАТА
        self.result_card = ctk.CTkFrame(
            self,
            fg_color=(LIGHT_CARD, DARK_CARD),
            corner_radius=16,
            border_width=2,
            border_color=(LIGHT_ACCENT, DARK_ACCENT),
        )
        self.result_card.pack(fill="x", padx=22, pady=(0, 14))

        result_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        result_inner.pack(fill="x", padx=16, pady=14)

        self.result_label = ctk.CTkLabel(
            result_inner,
            text="Результат: —",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=(LIGHT_TEXT, DARK_TEXT),
            wraplength=450,
            justify="left",
            anchor="w",
        )
        self.result_label.pack(side="left", fill="x", expand=True)

        self.copy_btn = ctk.CTkButton(
            result_inner,
            text="Копировать",
            width=112,
            height=34,
            corner_radius=10,
            command=self._copy_result,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=(LIGHT_ACCENT, DARK_ACCENT),
            hover_color=(LIGHT_ACCENT_HOV, DARK_ACCENT_HOV),
            text_color="#FFFFFF",
        )
        self.copy_btn.pack(side="right", padx=(10, 0))
        self.copy_btn.configure(state="disabled")

        # ИСТОРИЯ
        self.history_card = ctk.CTkFrame(
            self,
            fg_color=(LIGHT_CARD, DARK_CARD),
            corner_radius=16,
            border_width=1,
            border_color=(LIGHT_BORDER, DARK_BORDER),
        )
        self.history_card.pack(fill="x", padx=22, pady=(0, 22))

        ctk.CTkLabel(
            self.history_card,
            text="История",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=(LIGHT_TEXT, DARK_TEXT),
        ).pack(anchor="w", padx=18, pady=(14, 6))

        self.history_frame = ctk.CTkFrame(
            self.history_card, fg_color="transparent"
        )
        self.history_frame.pack(fill="x", padx=14, pady=(0, 14))

    def _toggle_theme(self):
        mode = "dark" if self.theme_switch.get() else "light"
        ctk.set_appearance_mode(mode)

    def _update_units(self):
        category = get_category(self.category_var.get())
        units = category.units

        if category.has_format_option:
            self.extra_label.grid()
            self.extra_cb.grid()
        else:
            self.extra_label.grid_remove()
            self.extra_cb.grid_remove()

        self.from_cb.configure(values=units)
        self.to_cb.configure(values=units)
        self.from_var.set(units[0])
        self.to_var.set(units[1] if len(units) > 1 else units[0])
        self.result_label.configure(text="Результат: —")
        self.last_result_text = None
        self.copy_btn.configure(state="disabled")

    def calculate(self):
        category = get_category(self.category_var.get())
        from_unit = self.from_var.get()
        to_unit = self.to_var.get()
        text = self.value_entry.get().strip()
        format_option = self.extra_var.get() if category.has_format_option else None

        try:
            result = category.convert(from_unit, to_unit, text, format_option)
        except InputError as exc:
            ErrorDialog(self, "Ошибка ввода", str(exc))
            return
        except CalculationError as exc:
            ErrorDialog(self, "Ошибка", str(exc))
            return

        self.result_label.configure(text=f"Результат:\n{result.display}")
        self.last_result_text = result.copy_text
        self.copy_btn.configure(state="normal")
        self.history.add(HistoryEntry(
            category=category.name,
            from_unit=from_unit,
            to_unit=to_unit,
            input_raw=text,
            display=result.display,
            format_option=format_option,
        ))
        self._render_history()

    # КОПИРОВАНИЕ
    def _copy_result(self):
        if not self.last_result_text:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(self.last_result_text)
        except Exception:
            return

        if self._copy_reset_job is not None:
            try:
                self.after_cancel(self._copy_reset_job)
            except Exception:
                pass

        self.copy_btn.configure(text="Скопировано")
        self._copy_reset_job = self.after(1500, self._reset_copy_button)

    def _reset_copy_button(self):
        self._copy_reset_job = None
        try:
            if self.copy_btn.winfo_exists():
                self.copy_btn.configure(text="Копировать")
        except Exception:
            pass

    # ИСТОРИЯ
    def _render_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        if not len(self.history):
            ctk.CTkLabel(
                self.history_frame,
                text="Конвертации отсутствуют",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=(LIGHT_TEXT_DIM, DARK_TEXT_DIM),
            ).pack(anchor="w", padx=6, pady=6)
            return

        for entry in self.history.newest_first():
            btn = ctk.CTkButton(
                self.history_frame,
                text=entry.display,
                anchor="w",
                height=38,
                corner_radius=10,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                fg_color=(LIGHT_ENTRY, DARK_ENTRY),
                hover_color=(LIGHT_BORDER, DARK_BORDER),
                text_color=(LIGHT_TEXT, DARK_TEXT),
                border_width=1,
                border_color=(LIGHT_BORDER, DARK_BORDER),
                command=lambda e=entry: self._on_history_click(e),
            )
            btn.pack(fill="x", pady=3, padx=2)

    def _on_history_click(self, entry):
        self.category_var.set(entry.category)
        self._update_units()

        self.from_var.set(entry.from_unit)
        self.to_var.set(entry.to_unit)

        self.value_entry.delete(0, "end")
        self.value_entry.insert(0, entry.input_raw)

        if entry.format_option:
            self.extra_var.set(entry.format_option)


if __name__ == "__main__":
    ConverterApp().mainloop()
