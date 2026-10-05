import os

os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"

from datetime import date

from kivy.config import Config

Config.set("graphics", "width", "430")
Config.set("graphics", "height", "800")
Config.set("graphics", "resizable", "1")

from kivy.core.window import Window
Window.clearcolor = (0.96, 0.97, 0.99, 1)

try:
    Window.softinput_mode = "below_target"
except Exception:
    pass

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle

from kivymd.app import MDApp

from database import (
    init_db,
    add_model,
    add_stock,
    add_order,
    get_dashboard_counts,
    search_orders,
    get_order_status,
    get_order_for_load,
    save_load,
    get_current_stock,
    get_load_history,
)

BLUE = (0.05, 0.18, 0.38, 1)
WHITE = (1, 1, 1, 1)
RED = (0.80, 0.08, 0.08, 1)
GREEN = (0.08, 0.55, 0.20, 1)
LIGHT_BLUE = (0.08, 0.45, 0.70, 1)
ORANGE = (0.85, 0.45, 0.05, 1)
PURPLE = (0.45, 0.20, 0.65, 1)
BG = (0.96, 0.97, 0.99, 1)
FIELD_BG = (0.94, 0.96, 0.98, 1)
DARK_TEXT = (0.08, 0.08, 0.10, 1)
LIGHT_ROW = (0.97, 0.98, 1, 1)


def display_battery_model(model):
    value = str(model or "").strip().upper()

    if not value:
        return ""

    value = " ".join(value.split())

    if value.startswith("XP "):
        value = "XP" + value[3:].strip()

    if value.startswith("XP"):
        remaining = value[2:].strip()

        if remaining:
            return "XP" + remaining

        return "XP"

    if value.isdigit():
        return "XP" + value

    return value


def make_button(text, bg=BLUE, font_size=18, height=56):
    return Button(
        text=text,
        font_size=dp(font_size),
        bold=True,
        color=WHITE,
        background_normal="",
        background_color=bg,
        size_hint_y=None,
        height=dp(height),
    )


def make_field(hint="", font_size=18, input_filter=None):
    return TextInput(
        hint_text=hint,
        font_size=dp(font_size),
        multiline=False,
        input_filter=input_filter,
        padding=[dp(12), dp(12)],
        background_color=FIELD_BG,
        foreground_color=DARK_TEXT,
        cursor_color=BLUE,
        size_hint_y=None,
        height=dp(54),
    )


KV = r"""
<DashboardScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            BoxLayout:
                orientation: "vertical"
                spacing: dp(11)
                size_hint_y: None
                height: self.minimum_height

                Widget:
                    size_hint_y: None
                    height: dp(4)

                Image:
                    source: "phoenix_logo.jpg"
                    size_hint_y: None
                    height: dp(125)
                    allow_stretch: True
                    keep_ratio: True

                Label:
                    text: "PHOENIX LOAD & STOCK"
                    font_size: dp(25)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(42)

                Label:
                    text: "Battery Order & Load Management"
                    font_size: dp(15)
                    color: 0.30,0.30,0.30,1
                    size_hint_y: None
                    height: dp(28)

                Widget:
                    size_hint_y: None
                    height: dp(5)

                Button:
                    text: "NEW ORDER"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "new_order"

                Button:
                    text: "ORDER STATUS"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.08,0.45,0.70,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "order_status"

                Button:
                    text: "NEW LOAD"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.08,0.55,0.20,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "new_load"

                Button:
                    text: "STOCK IN"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.85,0.45,0.05,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "stock"

                Button:
                    text: "STOCK"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.45,0.20,0.65,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "current_stock"

                Button:
                    text: "LOAD HISTORY"
                    font_size: dp(20)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.35,0.25,0.65,1
                    size_hint_y: None
                    height: dp(60)
                    on_release: root.manager.current = "load_history"

                Widget:
                    size_hint_y: None
                    height: dp(12)


<NewOrderScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "NEW ORDER"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(46)

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            BoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "Order No"
                    font_size: dp(17)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(29)

                TextInput:
                    id: order_no
                    hint_text: "Enter Order No"
                    font_size: dp(18)
                    multiline: False
                    padding: dp(12)
                    background_color: 0.94,0.96,0.98,1
                    foreground_color: 0.05,0.05,0.05,1
                    cursor_color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(54)

                Label:
                    text: "Dealer Name"
                    font_size: dp(17)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(29)

                TextInput:
                    id: dealer_name
                    hint_text: "Enter Dealer Name"
                    font_size: dp(18)
                    multiline: False
                    padding: dp(12)
                    background_color: 0.94,0.96,0.98,1
                    foreground_color: 0.05,0.05,0.05,1
                    cursor_color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(54)

                Label:
                    text: "Battery Models & Quantity"
                    font_size: dp(18)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(35)

                GridLayout:
                    id: model_rows
                    cols: 1
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                Button:
                    text: "+ ADD MODEL"
                    font_size: dp(17)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.08,0.45,0.70,1
                    size_hint_y: None
                    height: dp(54)
                    on_release: root.add_model_row()

                Widget:
                    size_hint_y: None
                    height: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            spacing: dp(8)

            Button:
                text: "SAVE ORDER"
                font_size: dp(18)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.55,0.20,1
                on_release: root.save_order()

            Button:
                text: "BACK"
                font_size: dp(18)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.80,0.08,0.08,1
                on_release: root.manager.current = "dashboard"


<StockScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "STOCK IN"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(46)

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            BoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "Battery Model"
                    font_size: dp(17)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(29)

                TextInput:
                    id: model
                    hint_text: "Example: XP70"
                    font_size: dp(18)
                    multiline: False
                    padding: dp(12)
                    background_color: 0.94,0.96,0.98,1
                    foreground_color: 0.05,0.05,0.05,1
                    cursor_color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(54)

                Label:
                    text: "Quantity"
                    font_size: dp(17)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(29)

                TextInput:
                    id: qty
                    hint_text: "Enter Quantity"
                    font_size: dp(18)
                    multiline: False
                    input_filter: "int"
                    padding: dp(12)
                    background_color: 0.94,0.96,0.98,1
                    foreground_color: 0.05,0.05,0.05,1
                    cursor_color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(54)

                Button:
                    text: "ADD STOCK"
                    font_size: dp(18)
                    bold: True
                    color: 1,1,1,1
                    background_normal: ""
                    background_color: 0.08,0.55,0.20,1
                    size_hint_y: None
                    height: dp(56)
                    on_release: root.add_stock()

                Label:
                    text: "CURRENT STOCK"
                    font_size: dp(20)
                    bold: True
                    color: 0.05,0.18,0.38,1
                    size_hint_y: None
                    height: dp(40)

                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    bar_width: dp(7)
                    scroll_type: ["bars", "content"]

                    GridLayout:
                        id: stock_table
                        cols: 1
                        spacing: dp(5)
                        size_hint_y: None
                        height: self.minimum_height

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            spacing: dp(8)

            Button:
                text: "REFRESH"
                font_size: dp(17)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.45,0.70,1
                on_release: root.refresh_stock()

            Button:
                text: "BACK"
                font_size: dp(17)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.80,0.08,0.08,1
                on_release: root.manager.current = "dashboard"


<NewLoadScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "NEW LOAD"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(46)

        Label:
            text: "Order No"
            font_size: dp(17)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(29)

        BoxLayout:
            size_hint_y: None
            height: dp(54)
            spacing: dp(8)

            TextInput:
                id: load_order_no
                hint_text: "Enter Order No"
                font_size: dp(18)
                multiline: False
                padding: dp(12)
                background_color: 0.94,0.96,0.98,1
                foreground_color: 0.05,0.05,0.05,1
                cursor_color: 0.05,0.18,0.38,1
                on_text_validate: root.load_order()

            Button:
                text: "LOAD ORDER"
                font_size: dp(16)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.45,0.70,1
                size_hint_x: 0.45
                on_release: root.load_order()

        Label:
            id: order_info
            text: ""
            font_size: dp(16)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(82)
            text_size: self.width, None
            halign: "left"
            valign: "middle"

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            GridLayout:
                id: load_cards
                cols: 1
                spacing: dp(8)
                padding: dp(2)
                size_hint_y: None
                height: self.minimum_height

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            spacing: dp(8)

            Button:
                text: "SAVE LOAD"
                font_size: dp(18)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.55,0.20,1
                on_release: root.save_current_load()

            Button:
                text: "BACK"
                font_size: dp(18)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.80,0.08,0.08,1
                on_release: root.manager.current = "dashboard"


<OrderStatusScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "ORDER STATUS"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(45)

        TextInput:
            id: search
            hint_text: "Order No or Dealer Name"
            font_size: dp(18)
            multiline: False
            padding: dp(12)
            background_color: 0.94,0.96,0.98,1
            foreground_color: 0.05,0.05,0.05,1
            cursor_color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(52)
            on_text_validate: root.do_search()

        Button:
            text: "SEARCH"
            font_size: dp(18)
            bold: True
            color: 1,1,1,1
            background_normal: ""
            background_color: 0.08,0.45,0.70,1
            size_hint_y: None
            height: dp(54)
            on_release: root.do_search()

        ScrollView:
            id: status_scroll
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            GridLayout:
                id: results
                cols: 1
                spacing: dp(6)
                padding: dp(2)
                size_hint_x: 1
                size_hint_y: None
                height: self.minimum_height

        Button:
            text: "BACK"
            font_size: dp(18)
            bold: True
            color: 1,1,1,1
            background_normal: ""
            background_color: 0.80,0.08,0.08,1
            size_hint_y: None
            height: dp(56)
            on_release: root.go_back()


<CurrentStockScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "STOCK"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(46)

        Label:
            text: "CURRENT STOCK"
            font_size: dp(20)
            bold: True
            color: 0.08,0.45,0.70,1
            size_hint_y: None
            height: dp(40)

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            GridLayout:
                id: current_stock_table
                cols: 1
                spacing: dp(1)
                padding: dp(1)
                size_hint_x: 1
                size_hint_y: None
                height: self.minimum_height

        BoxLayout:
            size_hint_y: None
            height: dp(58)
            spacing: dp(8)

            Button:
                text: "REFRESH"
                font_size: dp(17)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.45,0.70,1
                on_release: root.refresh_stock()

            Button:
                text: "BACK"
                font_size: dp(17)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.80,0.08,0.08,1
                on_release: root.manager.current = "dashboard"


<LoadHistoryScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)

        Label:
            text: "LOAD HISTORY"
            font_size: dp(24)
            bold: True
            color: 0.05,0.18,0.38,1
            size_hint_y: None
            height: dp(45)

        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(6)

            TextInput:
                id: history_search
                hint_text: "Order No / Dealer Name"
                font_size: dp(16)
                multiline: False
                padding: dp(10)
                background_color: 0.94,0.96,0.98,1
                foreground_color: 0.05,0.05,0.05,1
                cursor_color: 0.05,0.18,0.38,1
                on_text_validate: root.refresh_history()

            Button:
                text: "SEARCH"
                font_size: dp(15)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.45,0.70,1
                size_hint_x: 0.30
                on_release: root.refresh_history()

        ScrollView:
            do_scroll_x: True
            do_scroll_y: True
            bar_width: dp(7)
            scroll_type: ["bars", "content"]

            GridLayout:
                id: history_table
                cols: 1
                spacing: dp(2)
                padding: dp(2)
                size_hint_x: None
                width: self.minimum_width
                size_hint_y: None
                height: self.minimum_height

        BoxLayout:
            size_hint_y: None
            height: dp(56)
            spacing: dp(7)

            Button:
                text: "REFRESH"
                font_size: dp(16)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.08,0.45,0.70,1
                on_release:
                    root.ids.history_search.text = ""
                    root.refresh_history()

            Button:
                text: "BACK"
                font_size: dp(16)
                bold: True
                color: 1,1,1,1
                background_normal: ""
                background_color: 0.80,0.08,0.08,1
                on_release: root.manager.current = "dashboard"
"""


class DashboardScreen(Screen):
    def on_pre_enter(self):
        try:
            get_dashboard_counts()
        except Exception:
            pass


class NewOrderScreen(Screen):
    def on_pre_enter(self):
        self.clear_form()

    def clear_form(self):
        self.ids.order_no.text = ""
        self.ids.dealer_name.text = ""
        self.ids.model_rows.clear_widgets()
        self.model_inputs = []
        self.add_model_row()

    def add_model_row(self):
        row = GridLayout(
            cols=2,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(60),
        )

        model_input = TextInput(
            hint_text="Model e.g. XP70",
            font_size=dp(17),
            multiline=False,
            padding=[dp(10), dp(10)],
            background_color=FIELD_BG,
            foreground_color=DARK_TEXT,
            cursor_color=BLUE,
        )

        qty_input = TextInput(
            hint_text="Qty",
            font_size=dp(17),
            multiline=False,
            input_filter="int",
            padding=[dp(10), dp(10)],
            background_color=FIELD_BG,
            foreground_color=DARK_TEXT,
            cursor_color=BLUE,
        )

        row.add_widget(model_input)
        row.add_widget(qty_input)

        self.ids.model_rows.add_widget(row)
        self.model_inputs.append((model_input, qty_input))

    def save_order(self):
        order_no = self.ids.order_no.text.strip()
        dealer_name = self.ids.dealer_name.text.strip()

        if not order_no:
            self.show_message("Please enter Order No.")
            return

        if not dealer_name:
            self.show_message("Please enter Dealer Name.")
            return

        items = []

        for model_input, qty_input in self.model_inputs:
            model = model_input.text.strip()
            qty_text = qty_input.text.strip()

            if not model:
                continue

            if not qty_text:
                continue

            try:
                qty = int(qty_text)
            except ValueError:
                self.show_message("Quantity must be a number.")
                return

            if qty <= 0:
                continue

            items.append((model, qty))

        if not items:
            self.show_message("Please enter at least one model and quantity.")
            return

        try:
            add_order(
                order_no,
                dealer_name,
                str(date.today()),
                items,
            )

            self.show_message("Order saved successfully.")
            self.clear_form()

        except Exception as e:
            self.show_message(f"Error:\n{e}")

    def show_message(self, message):
        content = GridLayout(
            cols=1,
            padding=dp(15),
            spacing=dp(12),
        )

        msg_label = Label(
            text=str(message),
            font_size=dp(17),
            color=WHITE,
            halign="center",
            valign="middle",
        )

        ok_button = Button(
            text="OK",
            font_size=dp(17),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=ORANGE,
            size_hint_y=None,
            height=dp(48),
        )

        content.add_widget(msg_label)
        content.add_widget(ok_button)

        popup = Popup(
            title="Phoenix Load & Stock",
            content=content,
            size_hint=(0.85, 0.40),
            auto_dismiss=True,
            background_color=BLUE,
            separator_color=ORANGE,
            title_color=WHITE,
        )

        ok_button.bind(on_release=popup.dismiss)
        popup.open()


class StockScreen(Screen):
    def on_pre_enter(self):
        self.refresh_stock()

    def add_stock(self):
        model = self.ids.model.text.strip()
        qty_text = self.ids.qty.text.strip()

        if not model:
            self.show_message("Please enter Battery Model.")
            return

        if not qty_text:
            self.show_message("Please enter Quantity.")
            return

        try:
            qty = int(qty_text)
        except ValueError:
            self.show_message("Quantity must be a number.")
            return

        if qty <= 0:
            self.show_message("Quantity must be greater than zero.")
            return

        try:
            add_stock(model, qty)

            self.ids.model.text = ""
            self.ids.qty.text = ""

            self.refresh_stock()

            self.show_message("Stock added successfully.")

        except Exception as e:
            self.show_message(f"Error:\n{e}")

    def refresh_stock(self):
        self.ids.stock_table.clear_widgets()

        try:
            rows = get_current_stock()

        except Exception as e:
            self.ids.stock_table.add_widget(
                Label(
                    text=f"Error: {e}",
                    font_size=dp(16),
                    color=RED,
                    size_hint_y=None,
                    height=dp(45),
                )
            )
            return

        if not rows:
            self.ids.stock_table.add_widget(
                Label(
                    text="No stock available.",
                    font_size=dp(17),
                    color=(0.25, 0.25, 0.25, 1),
                    size_hint_y=None,
                    height=dp(45),
                )
            )
            return

        for row in rows:
            model = row.get("model", "")
            remaining = row.get("remaining", 0)

            model_display = display_battery_model(model)

            card = Label(
                text=f"{model_display}     Stock: {remaining}",
                font_size=dp(18),
                bold=True,
                color=BLUE,
                size_hint_y=None,
                height=dp(52),
                halign="left",
                valign="middle",
            )

            self.ids.stock_table.add_widget(card)

    def show_message(self, message):
        content = GridLayout(
            cols=1,
            padding=dp(15),
            spacing=dp(12),
        )

        msg_label = Label(
            text=str(message),
            font_size=dp(17),
            color=WHITE,
            halign="center",
            valign="middle",
        )

        ok_button = Button(
            text="OK",
            font_size=dp(17),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=ORANGE,
            size_hint_y=None,
            height=dp(48),
        )

        content.add_widget(msg_label)
        content.add_widget(ok_button)

        popup = Popup(
            title="Phoenix Load & Stock",
            content=content,
            size_hint=(0.85, 0.40),
            auto_dismiss=True,
            background_color=BLUE,
            separator_color=ORANGE,
            title_color=WHITE,
        )

        ok_button.bind(on_release=popup.dismiss)
        popup.open()


class CurrentStockScreen(Screen):
    def on_pre_enter(self):
        self.refresh_stock()

    def _make_stock_cell(
        self,
        text,
        header=False,
        stock_value=False,
    ):
        if header:
            background = BLUE
            foreground = WHITE
            font_size = 17
        else:
            background = LIGHT_ROW
            foreground = GREEN if stock_value else BLUE
            font_size = 18

        cell = Label(
            text=str(text),
            font_size=dp(font_size),
            bold=True,
            color=foreground,
            halign="center",
            valign="middle",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(52),
        )

        with cell.canvas.before:
            Color(*background)
            rect = Rectangle(
                pos=cell.pos,
                size=cell.size,
            )

        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size

        cell.bind(
            pos=update_rect,
            size=update_rect,
        )

        return cell

    def refresh_stock(self):
        table = self.ids.current_stock_table
        table.clear_widgets()

        try:
            rows = get_current_stock()

        except Exception as e:
            table.add_widget(
                self._make_stock_cell(f"Error: {e}")
            )
            return

        if not rows:
            table.add_widget(
                self._make_stock_cell(
                    "No stock available."
                )
            )
            return

        header = GridLayout(
            cols=2,
            spacing=dp(1),
            padding=dp(1),
            size_hint_x=1,
            size_hint_y=None,
            height=dp(52),
        )

        header.add_widget(
            self._make_stock_cell(
                "MODEL",
                header=True,
            )
        )

        header.add_widget(
            self._make_stock_cell(
                "STOCK",
                header=True,
            )
        )

        table.add_widget(header)

        for row in rows:
            model = row.get("model", "")
            remaining = row.get("remaining", 0)

            model_display = display_battery_model(model)

            data_row = GridLayout(
                cols=2,
                spacing=dp(1),
                padding=dp(1),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(52),
            )

            data_row.add_widget(
                self._make_stock_cell(
                    model_display
                )
            )

            data_row.add_widget(
                self._make_stock_cell(
                    str(remaining),
                    stock_value=True,
                )
            )

            table.add_widget(data_row)


class NewLoadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.order_id = None
        self.current_order = None
        self.load_fields = []

    def on_pre_enter(self):
        self.ids.load_order_no.text = ""
        self.ids.order_info.text = ""
        self.ids.load_cards.clear_widgets()

        self.order_id = None
        self.current_order = None
        self.load_fields = []

    def load_order(self):
        order_no = self.ids.load_order_no.text.strip()

        if not order_no:
            self.show_message("Please enter Order No.")
            return

        try:
            result = get_order_for_load(order_no)

        except Exception as e:
            self.show_message(f"Error:\n{e}")
            return

        if not result:
            self.show_message("Order not found.")
            return

        self.current_order = result

        order = result.get("order")

        if not order:
            self.show_message("Order information not found.")
            return

        self.order_id = order[0]

        order_no_db = order[1]
        dealer_name = order[2]
        order_date = order[3]

        self.ids.order_info.text = (
            f"Order No: {order_no_db}\n"
            f"Dealer: {dealer_name}\n"
            f"Date: {order_date}\n"
            f"Next Load: {result.get('next_load_no', 1)}"
        )

        self._build_load_cards(
            result.get("items", [])
        )

    def _build_load_cards(self, items):
        self.ids.load_cards.clear_widgets()
        self.load_fields = []

        if not items:
            self.ids.load_cards.add_widget(
                Label(
                    text="No items found in this order.",
                    font_size=dp(17),
                    color=RED,
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        for item in items:
            raw_model = str(
                item.get("model", "")
            ).strip()

            model_display = display_battery_model(
                raw_model
            )

            order_qty = int(
                item.get("order_qty", 0) or 0
            )

            total_sent = int(
                item.get("total_sent", 0) or 0
            )

            pending = int(
                item.get(
                    "pending",
                    max(order_qty - total_sent, 0),
                ) or 0
            )

            stock_available = int(
                item.get("stock_available", 0) or 0
            )

            card = GridLayout(
                cols=1,
                spacing=dp(5),
                padding=dp(8),
                size_hint_y=None,
                height=dp(185),
            )

            info = Label(
                text=(
                    f"{model_display}\n"
                    f"Order: {order_qty}    "
                    f"Sent: {total_sent}    "
                    f"Pending: {pending}\n"
                    f"Stock Available: {stock_available}"
                ),
                font_size=dp(17),
                bold=True,
                color=BLUE,
                size_hint_y=None,
                height=dp(95),
                halign="left",
                valign="middle",
            )

            qty_input = TextInput(
                hint_text=f"Enter {model_display} Load Qty",
                font_size=dp(18),
                multiline=False,
                input_filter="int",
                size_hint_y=None,
                height=dp(52),
                padding=[dp(12), dp(12)],
                background_color=FIELD_BG,
                foreground_color=DARK_TEXT,
                cursor_color=BLUE,
            )

            card.add_widget(info)
            card.add_widget(qty_input)

            self.ids.load_cards.add_widget(card)

            self.load_fields.append(
                (raw_model, qty_input)
            )

    def save_current_load(self):
        if not self.order_id:
            self.show_message(
                "Please load an Order first."
            )
            return

        items_to_save = []

        for raw_model, qty_input in self.load_fields:
            qty_text = qty_input.text.strip()

            if not qty_text:
                continue

            try:
                qty = int(qty_text)

            except ValueError:
                self.show_message(
                    "Load quantity must be a number."
                )
                return

            if qty <= 0:
                continue

            items_to_save.append(
                (raw_model, qty)
            )

        if not items_to_save:
            self.show_message(
                "Please enter load quantity."
            )
            return

        next_load_no = int(
            self.current_order.get(
                "next_load_no",
                1,
            )
        )

        try:
            save_load(
                self.order_id,
                next_load_no,
                str(date.today()),
                items_to_save,
            )

            self.show_message(
                f"Load {next_load_no} saved successfully."
            )

            self.load_order()

        except Exception as e:
            self.show_message(
                f"Error:\n{e}"
            )

    def show_message(self, message):
        content = GridLayout(
            cols=1,
            padding=dp(15),
            spacing=dp(12),
        )

        msg_label = Label(
            text=str(message),
            font_size=dp(17),
            color=WHITE,
            halign="center",
            valign="middle",
        )

        ok_button = Button(
            text="OK",
            font_size=dp(17),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=ORANGE,
            size_hint_y=None,
            height=dp(48),
        )

        content.add_widget(msg_label)
        content.add_widget(ok_button)

        popup = Popup(
            title="Phoenix Load & Stock",
            content=content,
            size_hint=(0.85, 0.40),
            auto_dismiss=True,
            background_color=BLUE,
            separator_color=ORANGE,
            title_color=WHITE,
        )

        ok_button.bind(
            on_release=popup.dismiss
        )

        popup.open()


class OrderStatusScreen(Screen):
    def go_back(self):
        self.ids.results.clear_widgets()
        self.ids.search.text = ""
        self.manager.current = "dashboard"

    def show_message(self, message):
        self.ids.results.clear_widgets()

        label = Label(
            text=str(message),
            font_size=dp(17),
            bold=True,
            color=BLUE,
            size_hint_y=None,
            height=dp(65),
            halign="center",
            valign="middle",
        )

        label.bind(
            size=lambda obj, value:
            setattr(obj, "text_size", value)
        )

        self.ids.results.add_widget(label)

    def _make_status_cell(
        self,
        text,
        background,
        foreground=BLUE,
        bold=True,
    ):
        cell = Label(
            text=str(text),
            font_size=dp(14),
            bold=bold,
            color=foreground,
            halign="center",
            valign="middle",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(42),
            padding=(dp(2), dp(2)),
        )

        with cell.canvas.before:
            Color(*background)

            rect = Rectangle(
                pos=cell.pos,
                size=cell.size,
            )

        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size

        cell.bind(
            pos=update_rect,
            size=update_rect,
        )

        return cell

    def _add_status_row(
        self,
        values,
        header=False,
        total=False,
    ):
        row = GridLayout(
            cols=4,
            spacing=dp(1),
            size_hint_x=1,
            size_hint_y=None,
            height=dp(43),
        )

        if header:
            background = BLUE
            foreground = WHITE

        elif total:
            background = (
                0.82,
                0.90,
                0.97,
                1,
            )
            foreground = BLUE

        else:
            background = (
                0.95,
                0.97,
                0.99,
                1,
            )
            foreground = BLUE

        for value in values:
            row.add_widget(
                self._make_status_cell(
                    value,
                    background,
                    foreground,
                    bold=True,
                )
            )

        self.ids.results.add_widget(row)

    def _add_load_summary(
        self,
        order_no,
        loads,
    ):
        try:
            history_rows = get_load_history()

        except Exception:
            history_rows = []

        order_history = []

        for row in history_rows:
            row_order_no = str(
                row.get("order_no", "")
            ).strip()

            if row_order_no == str(
                order_no
            ).strip():
                order_history.append(row)

        grouped_loads = {}

        for row in order_history:
            load_no = str(
                row.get("load_no", "")
            ).strip()

            if not load_no:
                continue

            load_date = str(
                row.get("load_date", "")
            ).strip()

            model = display_battery_model(
                row.get("model", "")
            )

            qty = int(
                row.get("qty_sent", 0) or 0
            )

            key = (
                load_no,
                load_date,
            )

            if key not in grouped_loads:
                grouped_loads[key] = {
                    "load_no": load_no,
                    "load_date": load_date,
                    "models": {},
                    "total": 0,
                }

            if model:
                grouped_loads[key]["models"][model] = (
                    grouped_loads[key]["models"].get(
                        model,
                        0,
                    ) + qty
                )

                grouped_loads[key]["total"] += qty

        if not grouped_loads and loads:
            for index, load in enumerate(
                loads,
                start=1,
            ):
                if isinstance(load, dict):
                    load_no = str(
                        load.get(
                            "load_no",
                            index,
                        )
                    )

                    load_date = str(
                        load.get(
                            "load_date",
                            "",
                        )
                    )

                else:
                    load_no = str(index)
                    load_date = ""

                grouped_loads[
                    (load_no, load_date)
                ] = {
                    "load_no": load_no,
                    "load_date": load_date,
                    "models": {},
                    "total": 0,
                }

        if not grouped_loads:
            return

        load_title = Label(
            text="LOAD SUMMARY",
            font_size=dp(17),
            bold=True,
            color=BLUE,
            size_hint_y=None,
            height=dp(42),
            halign="center",
            valign="middle",
        )

        self.ids.results.add_widget(
            load_title
        )

        def load_sort_key(value):
            try:
                return int(value[0])
            except Exception:
                return 999999

        sorted_loads = sorted(
            grouped_loads.items(),
            key=lambda item:
            load_sort_key(item[0]),
        )

        for key, load_data in sorted_loads:
            load_no = load_data["load_no"]
            load_date = load_data["load_date"]
            model_data = load_data["models"]
            load_total = load_data["total"]

            heading_text = f"LOAD {load_no}"

            if load_date:
                heading_text += (
                    f"    Date: {load_date}"
                )

            heading = Label(
                text=heading_text,
                font_size=dp(16),
                bold=True,
                color=WHITE,
                size_hint_y=None,
                height=dp(40),
                halign="left",
                valign="middle",
                padding=(dp(10), dp(2)),
            )

            with heading.canvas.before:
                Color(*LIGHT_BLUE)

                rect = Rectangle(
                    pos=heading.pos,
                    size=heading.size,
                )

            def update_heading_rect(
                instance,
                value,
                rect=rect,
            ):
                rect.pos = instance.pos
                rect.size = instance.size

            heading.bind(
                pos=update_heading_rect,
                size=update_heading_rect,
            )

            self.ids.results.add_widget(
                heading
            )

            if model_data:
                model_items = list(
                    model_data.items()
                )

                model_items.sort(
                    key=lambda item:
                    item[0]
                )

                for model, qty in model_items:
                    model_label = Label(
                        text=(
                            f"{model}"
                            f"        Qty: {qty}"
                        ),
                        font_size=dp(15),
                        bold=True,
                        color=BLUE,
                        size_hint_y=None,
                        height=dp(36),
                        halign="left",
                        valign="middle",
                        padding=(
                            dp(15),
                            dp(2),
                        ),
                    )

                    self.ids.results.add_widget(
                        model_label
                    )

            else:
                self.ids.results.add_widget(
                    Label(
                        text="No model detail available.",
                        font_size=dp(14),
                        color=RED,
                        size_hint_y=None,
                        height=dp(34),
                    )
                )

            total_label = Label(
                text=(
                    f"LOAD {load_no} TOTAL: "
                    f"{load_total}"
                ),
                font_size=dp(16),
                bold=True,
                color=GREEN,
                size_hint_y=None,
                height=dp(40),
                halign="right",
                valign="middle",
                padding=(dp(5), dp(2)),
            )

            self.ids.results.add_widget(
                total_label
            )

    def do_search(self):
        query = self.ids.search.text.strip()

        self.ids.results.clear_widgets()

        if not query:
            self.show_message(
                "Please enter Order No or Dealer Name."
            )
            return

        try:
            rows = search_orders(query)

        except Exception as e:
            self.show_message(
                f"Error:\n{e}"
            )
            return

        if not rows:
            self.show_message(
                "No order found."
            )
            return

        if len(rows) == 1:
            order_id = rows[0][0]
            self.show_status(order_id)
            return

        heading = Label(
            text=(
                f"Orders Found: {len(rows)}\n"
                f"Select an Order"
            ),
            font_size=dp(16),
            bold=True,
            color=BLUE,
            size_hint_y=None,
            height=dp(55),
            halign="center",
            valign="middle",
        )

        self.ids.results.add_widget(
            heading
        )

        for row in rows:
            order_id = row[0]
            order_no = row[1]
            dealer_name = row[2]
            order_date = row[3]

            btn = Button(
                text=(
                    f"Order: {order_no}\n"
                    f"Dealer: {dealer_name}\n"
                    f"Date: {order_date}"
                ),
                font_size=dp(16),
                bold=True,
                color=WHITE,
                background_normal="",
                background_color=LIGHT_BLUE,
                size_hint_y=None,
                height=dp(80),
            )

            btn.bind(
                on_release=lambda instance,
                oid=order_id:
                self.show_status(oid)
            )

            self.ids.results.add_widget(
                btn
            )

    def show_status(self, order_id):
        try:
            data = get_order_status(
                order_id
            )

        except Exception as e:
            self.show_message(
                f"Error:\n{e}"
            )
            return

        if not data:
            self.show_message(
                "Order status not found."
            )
            return

        order = data.get("order")
        loads = data.get("loads", [])
        items = data.get("items", [])

        if not order:
            self.show_message(
                "Order information not found."
            )
            return

        order_no = order[1]
        dealer_name = order[2]
        order_date = order[3]

        self.ids.results.clear_widgets()

        info_box = GridLayout(
            cols=1,
            spacing=dp(2),
            padding=dp(5),
            size_hint_y=None,
            height=dp(100),
        )

        info_label = Label(
            text=(
                f"ORDER NO: {order_no}\n"
                f"DEALER: {dealer_name}\n"
                f"DATE: {order_date}\n"
                f"TOTAL LOADS: {len(loads)}"
            ),
            font_size=dp(15),
            bold=True,
            color=BLUE,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(95),
        )

        info_label.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                (value[0] - dp(10), None),
            )
        )

        info_box.add_widget(
            info_label
        )

        self.ids.results.add_widget(
            info_box
        )

        self.ids.results.add_widget(
            Label(
                text="ORDER / SENT / PENDING",
                font_size=dp(16),
                bold=True,
                color=BLUE,
                size_hint_y=None,
                height=dp(38),
            )
        )

        self._add_status_row(
            [
                "MODEL",
                "ORDER",
                "SENT",
                "PENDING",
            ],
            header=True,
        )

        total_order = 0
        total_sent = 0
        total_pending = 0

        for item in items:
            model = item.get(
                "model",
                "",
            )

            order_qty = int(
                item.get(
                    "order_qty",
                    0,
                ) or 0
            )

            sent_qty = int(
                item.get(
                    "total_sent",
                    0,
                ) or 0
            )

            pending = int(
                item.get(
                    "pending",
                    0,
                ) or 0
            )

            model_display = display_battery_model(
                model
            )

            total_order += order_qty
            total_sent += sent_qty
            total_pending += pending

            self._add_status_row(
                [
                    model_display,
                    order_qty,
                    sent_qty,
                    pending,
                ]
            )

        self._add_status_row(
            [
                "TOTAL",
                total_order,
                total_sent,
                total_pending,
            ],
            total=True,
        )

        self._add_load_summary(
            order_no,
            loads,
        )

        self.ids.status_scroll.scroll_y = 1


class LoadHistoryScreen(Screen):
    def on_pre_enter(self):
        self.refresh_history()

    def _make_cell(
        self,
        text,
        width,
        header=False,
    ):
        if header:
            bg = BLUE
            fg = WHITE
            font = 14

        else:
            bg = (
                0.95,
                0.96,
                0.98,
                1,
            )
            fg = BLUE
            font = 14

        cell = Label(
            text=str(text),
            font_size=dp(font),
            bold=True,
            color=fg,
            size_hint_x=None,
            width=dp(width),
            size_hint_y=None,
            height=dp(48),
            halign="center",
            valign="middle",
            text_size=(
                dp(width - 8),
                dp(46),
            ),
        )

        with cell.canvas.before:
            Color(*bg)

            rect = Rectangle(
                pos=cell.pos,
                size=cell.size,
            )

        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size

        cell.bind(
            pos=update_rect,
            size=update_rect,
        )

        return cell

    def refresh_history(self):
        table = self.ids.history_table
        table.clear_widgets()

        try:
            rows = get_load_history()

        except Exception as e:
            table.add_widget(
                Label(
                    text=f"Error: {e}",
                    font_size=dp(16),
                    color=RED,
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        search_text = (
            self.ids.history_search.text
            .strip()
            .lower()
        )

        if search_text:
            filtered_rows = []

            for row in rows:
                order_no = str(
                    row.get(
                        "order_no",
                        "",
                    )
                ).lower()

                dealer = str(
                    row.get(
                        "dealer_name",
                        "",
                    )
                ).lower()

                if (
                    search_text in order_no
                    or search_text in dealer
                ):
                    filtered_rows.append(row)

            rows = filtered_rows

        if not rows:
            table.add_widget(
                Label(
                    text="No load history available.",
                    font_size=dp(17),
                    color=(
                        0.25,
                        0.25,
                        0.25,
                        1,
                    ),
                    size_hint_x=None,
                    width=dp(600),
                    size_hint_y=None,
                    height=dp(50),
                )
            )
            return

        models = []

        for row in rows:
            model = display_battery_model(
                row.get(
                    "model",
                    "",
                )
            )

            if model and model not in models:
                models.append(model)

        grouped = {}

        for row in rows:
            order_no = str(
                row.get(
                    "order_no",
                    "",
                )
            )

            dealer = str(
                row.get(
                    "dealer_name",
                    "",
                )
            )

            load_no = str(
                row.get(
                    "load_no",
                    "",
                )
            )

            load_date = str(
                row.get(
                    "load_date",
                    "",
                )
            )

            key = (
                order_no,
                dealer,
                load_no,
                load_date,
            )

            if key not in grouped:
                grouped[key] = {
                    "order_no": order_no,
                    "dealer": dealer,
                    "load_no": load_no,
                    "load_date": load_date,
                    "models": {},
                }

            model = display_battery_model(
                row.get(
                    "model",
                    "",
                )
            )

            qty = int(
                row.get(
                    "qty_sent",
                    0,
                ) or 0
            )

            if model:
                grouped[key]["models"][model] = (
                    grouped[key]["models"].get(
                        model,
                        0,
                    ) + qty
                )

        order_width = 95
        dealer_width = 130
        load_width = 70
        date_width = 105
        model_width = 78
        total_width = 85

        headers = [
            ("Order", order_width),
            ("Dealer", dealer_width),
            ("Load", load_width),
            ("Date", date_width),
        ]

        for model in models:
            headers.append(
                (model, model_width)
            )

        headers.append(
            ("Total", total_width)
        )

        total_table_width = (
            sum(
                width
                for _, width in headers
            )
            + len(headers)
        )

        header_row = GridLayout(
            cols=len(headers),
            spacing=dp(1),
            size_hint_x=None,
            width=dp(total_table_width),
            size_hint_y=None,
            height=dp(48),
        )

        for title, width in headers:
            header_row.add_widget(
                self._make_cell(
                    title,
                    width,
                    header=True,
                )
            )

        table.add_widget(
            header_row
        )

        for data in grouped.values():
            row_widgets = GridLayout(
                cols=len(headers),
                spacing=dp(1),
                size_hint_x=None,
                width=dp(total_table_width),
                size_hint_y=None,
                height=dp(48),
            )

            row_total = 0

            row_widgets.add_widget(
                self._make_cell(
                    data["order_no"],
                    order_width,
                )
            )

            row_widgets.add_widget(
                self._make_cell(
                    data["dealer"],
                    dealer_width,
                )
            )

            row_widgets.add_widget(
                self._make_cell(
                    data["load_no"],
                    load_width,
                )
            )

            row_widgets.add_widget(
                self._make_cell(
                    data["load_date"],
                    date_width,
                )
            )

            for model in models:
                qty = int(
                    data["models"].get(
                        model,
                        0,
                    )
                    or 0
                )

                row_total += qty

                row_widgets.add_widget(
                    self._make_cell(
                        qty if qty else "-",
                        model_width,
                    )
                )

            row_widgets.add_widget(
                self._make_cell(
                    row_total,
                    total_width,
                )
            )

            table.add_widget(
                row_widgets
            )


class PhoenixApp(MDApp):
    def build(self):
        init_db()

        Builder.load_string(KV)

        sm = ScreenManager()

        sm.add_widget(
            DashboardScreen(
                name="dashboard"
            )
        )

        sm.add_widget(
            NewOrderScreen(
                name="new_order"
            )
        )

        sm.add_widget(
            StockScreen(
                name="stock"
            )
        )

        sm.add_widget(
            CurrentStockScreen(
                name="current_stock"
            )
        )

        sm.add_widget(
            NewLoadScreen(
                name="new_load"
            )
        )

        sm.add_widget(
            OrderStatusScreen(
                name="order_status"
            )
        )

        sm.add_widget(
            LoadHistoryScreen(
                name="load_history"
            )
        )

        return sm


if __name__ == "__main__":
    PhoenixApp().run()