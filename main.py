import calendar
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from calendar_view import CalendarView
from database import Database


class MenuHelper(tk.Tk):
    BG = "#f4f1ea"
    PANEL = "#fffdf8"
    INK = "#26332f"
    MUTED = "#78817a"
    SAGE = "#607b68"
    TERRACOTTA = "#c86c4b"
    LINE = "#dedbd2"
    PALE_GREEN = "#e7eee5"

    def __init__(self):
        super().__init__()
        self.title("Menu Helper")
        self.geometry("1180x760")
        self.minsize(900, 620)
        self.configure(bg=self.BG)
        self.database = Database()
        self._build_styles()
        self._build_shell()
        self._render_meals()

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=self.PANEL, background=self.PANEL, bordercolor=self.LINE, padding=6)
        style.configure("Vertical.TScrollbar", troughcolor=self.BG, background="#c9c5bb", bordercolor=self.BG, arrowcolor=self.MUTED)

    def _build_shell(self):
        self.grid_columnconfigure(0, weight=1, uniform="main")
        self.grid_columnconfigure(1, weight=2, uniform="main")
        self.grid_rowconfigure(1, weight=1)
        header = tk.Frame(self, bg=self.BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=28, pady=(24, 18))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="MENU HELPER", bg=self.BG, fg=self.TERRACOTTA, font=("Georgia", 11, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(header, text="Plan a month of good eating", bg=self.BG, fg=self.INK, font=("Georgia", 22, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 0))
        tk.Button(header, text="Generate List  ->", command=self._show_shopping_list, bg=self.TERRACOTTA, fg="white", activebackground="#af563a", relief="flat", borderwidth=0, padx=18, pady=11, font=("Segoe UI", 10, "bold"), cursor="hand2").grid(row=0, column=2, rowspan=2, sticky="e")

        self.meal_panel = tk.Frame(self, bg=self.PANEL, highlightbackground=self.LINE, highlightthickness=1)
        self.meal_panel.grid(row=1, column=0, sticky="nsew", padx=(28, 12), pady=(0, 28))
        self.meal_panel.grid_rowconfigure(2, weight=1)
        self.meal_panel.grid_columnconfigure(0, weight=1)
        tk.Label(self.meal_panel, text="MEAL LIBRARY", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 3))
        tk.Label(self.meal_panel, text="Drag a meal onto a day", bg=self.PANEL, fg=self.INK, font=("Georgia", 16, "bold")).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))
        self.meal_canvas = tk.Canvas(self.meal_panel, bg=self.PANEL, highlightthickness=0)
        self.meal_canvas.grid(row=2, column=0, sticky="nsew", padx=(18, 4))
        scrollbar = ttk.Scrollbar(self.meal_panel, orient="vertical", command=self.meal_canvas.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", padx=(0, 12))
        self.meal_canvas.configure(yscrollcommand=scrollbar.set)
        self.meal_inner = tk.Frame(self.meal_canvas, bg=self.PANEL)
        self.meal_window = self.meal_canvas.create_window((0, 0), window=self.meal_inner, anchor="nw")
        self.meal_inner.bind("<Configure>", lambda event: self.meal_canvas.configure(scrollregion=self.meal_canvas.bbox("all")))
        self.meal_canvas.bind("<Configure>", lambda event: self.meal_canvas.itemconfigure(self.meal_window, width=event.width))
        tk.Button(self.meal_panel, text="+  Add a meal", command=self._add_meal_dialog, bg=self.PALE_GREEN, fg=self.SAGE, relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"), pady=10, cursor="hand2").grid(row=3, column=0, columnspan=2, sticky="ew", padx=22, pady=22)
        self.calendar_view = CalendarView(self, self.database, self._colors())
        self.calendar_view.grid(row=1, column=1, sticky="nsew", padx=(12, 28), pady=(0, 28))

    def _colors(self):
        return {name: getattr(self, name) for name in ("PANEL", "LINE", "INK", "MUTED", "SAGE", "TERRACOTTA", "PALE_GREEN")}

    def _render_meals(self):
        for child in self.meal_inner.winfo_children():
            child.destroy()
        for meal in self.database.meals():
            item = tk.Frame(self.meal_inner, bg=self.PANEL, highlightbackground=self.LINE, highlightthickness=1, cursor="hand2")
            item.pack(fill="x", padx=4, pady=5)
            tk.Label(item, text="=", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 4), pady=12)
            text = tk.Frame(item, bg=self.PANEL)
            text.pack(side="left", fill="x", expand=True, pady=10)
            tk.Label(text, text=meal["name"], bg=self.PANEL, fg=self.INK, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(text, text=f"{len(meal['ingredients'].splitlines())} ingredients", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(2, 0))
            tk.Button(item, text="x", command=lambda meal_id=meal["id"], name=meal["name"]: self._delete_meal(meal_id, name), bg=self.PANEL, fg=self.MUTED, activebackground="#f3ddd5", relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"), cursor="hand2", padx=10).pack(side="right", padx=(0, 5))
            tk.Button(item, text="Edit", command=lambda meal_id=meal["id"]: self._add_meal_dialog(meal_id), bg=self.PANEL, fg=self.SAGE, activebackground=self.PALE_GREEN, relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=6).pack(side="right", padx=(0, 2))
            for widget in (item, text, *text.winfo_children()):
                widget.bind("<ButtonPress-1>", lambda event, meal_id=meal["id"]: self.calendar_view.start_drag(event, meal_id))

    def _delete_meal(self, meal_id, meal_name):
        if messagebox.askyesno("Remove meal", f"Remove {meal_name} from the meal library?\n\nAny scheduled days using it will also be cleared.", parent=self):
            self.database.delete_meal(meal_id)
            self._render_meals()
            self.calendar_view.render()

    def _add_meal_dialog(self, meal_id=None):
        editing = meal_id is not None
        meal = next((item for item in self.database.meals() if item["id"] == meal_id), None) if editing else None
        popup = tk.Toplevel(self)
        popup.title("Edit meal" if editing else "Add meal")
        popup.configure(bg=self.PANEL)
        popup.geometry("520x520")
        popup.transient(self)
        popup.grab_set()
        tk.Label(popup, text="EDIT MEAL" if editing else "NEW MEAL", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(popup, text="Name", bg=self.PANEL, fg=self.INK, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(8, 3))
        name_entry = tk.Entry(popup, bg="#faf8f2", fg=self.INK, relief="flat", width=38, font=("Segoe UI", 10))
        name_entry.pack(padx=24, ipady=7)
        if meal:
            name_entry.insert(0, meal["name"])
        tk.Label(popup, text="Ingredients", bg=self.PANEL, fg=self.INK, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(14, 3))
        ingredient_list = tk.Frame(popup, bg=self.PANEL)
        ingredient_list.pack(fill="x", padx=24)
        ingredient_rows = []

        def remove_row(row_data):
            if len(ingredient_rows) > 1:
                ingredient_rows.remove(row_data)
                row_data[0].destroy()

        def add_row(name="", amount_value="", produce_value=False):
            row = tk.Frame(ingredient_list, bg=self.PANEL)
            row.pack(fill="x", pady=3)
            ingredient = tk.Entry(row, bg="#faf8f2", fg=self.INK, relief="flat", font=("Segoe UI", 10))
            ingredient.pack(side="left", fill="x", expand=True, ipady=6)
            amount = tk.Entry(row, bg="#faf8f2", fg=self.INK, relief="flat", width=12, font=("Segoe UI", 10))
            amount.pack(side="left", padx=(8, 0), ipady=6)
            produce = tk.BooleanVar(value=produce_value)
            ingredient.insert(0, name)
            amount.insert(0, amount_value)
            tk.Checkbutton(row, text="Produce", variable=produce, bg=self.PANEL, activebackground=self.PANEL, selectcolor=self.PALE_GREEN, font=("Segoe UI", 9)).pack(side="left", padx=6)
            data = (row, ingredient, amount, produce)
            ingredient_rows.append(data)
            tk.Button(row, text="x", command=lambda: remove_row(data), bg=self.PANEL, fg=self.MUTED, relief="flat", borderwidth=0, cursor="hand2").pack(side="left")

        existing_ingredients = self.database.meal_ingredients(meal_id) if editing else []
        for ingredient_data in existing_ingredients:
            add_row(ingredient_data["name"], ingredient_data["amount"], bool(ingredient_data["produce"]))
        for _ in range(max(3 - len(existing_ingredients), 0)):
            add_row()
        tk.Button(popup, text="+  Add ingredient", command=add_row, bg=self.PALE_GREEN, fg=self.SAGE, relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=10, pady=6).pack(anchor="w", padx=24, pady=(8, 0))

        def save():
            ingredients = []
            for _, ingredient_entry, amount_entry, produce_var in ingredient_rows:
                ingredient, amount = ingredient_entry.get().strip(), amount_entry.get().strip()
                if ingredient or amount:
                    if not ingredient or not amount:
                        messagebox.showwarning("Missing details", "Every ingredient needs a name and amount.", parent=popup)
                        return
                    ingredients.append({"name": ingredient, "amount": amount, "produce": int(produce_var.get())})
            if not name_entry.get().strip() or not ingredients:
                messagebox.showwarning("Missing details", "Add a meal name and at least one ingredient.", parent=popup)
                return
            try:
                if editing:
                    self.database.update_meal(meal_id, name_entry.get().strip(), ingredients)
                else:
                    self.database.add_meal(name_entry.get().strip(), ingredients)
            except sqlite3.IntegrityError:
                messagebox.showwarning("Meal already exists", "Choose a different meal name.", parent=popup)
                return
            self._render_meals()
            popup.destroy()

        tk.Button(popup, text="Save changes" if editing else "Save meal", command=save, bg=self.SAGE, fg="white", relief="flat", borderwidth=0, padx=18, pady=10, cursor="hand2").pack(pady=(16, 22))
        name_entry.focus_set()

    def _show_shopping_list(self):
        year, month = self.calendar_view.year, self.calendar_view.month
        calendar.setfirstweekday(calendar.MONDAY)
        month_days = calendar.monthcalendar(year, month)
        popup = tk.Toplevel(self)
        popup.title("Shopping list")
        popup.geometry("500x650")
        popup.configure(bg=self.PANEL)
        popup.transient(self)
        tk.Label(popup, text="SHOPPING LISTS", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=26, pady=(24, 3))
        tk.Label(popup, text=f"{calendar.month_name[month]} {year}", bg=self.PANEL, fg=self.INK, font=("Georgia", 21, "bold")).pack(anchor="w", padx=26)
        tk.Label(popup, text="Monthly pantry items plus fresh produce by week", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=27, pady=(3, 12))
        canvas = tk.Canvas(popup, bg=self.PANEL, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=(0, 24))
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 18), pady=(0, 24))
        list_frame = tk.Frame(canvas, bg=self.PANEL)
        canvas.create_window((0, 0), window=list_frame, anchor="nw", width=435)
        list_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        self._render_shopping_section(list_frame, "Monthly pantry list", "All non-produce items for the month", self.database.shopping_list(year, month, False))
        for week_number, week in enumerate(month_days, start=1):
            days = [f"{year:04d}-{month:02d}-{day:02d}" for day in week if day]
            first_day = next(day for day in week if day)
            last_day = next(day for day in reversed(week) if day)
            title = f"Week {week_number}  |  {calendar.month_abbr[month]} {first_day}-{last_day}"
            self._render_shopping_section(list_frame, title, "Produce used this week", self.database.shopping_list(year, month, True, days))

    def _render_shopping_section(self, parent, title, subtitle, items):
        section = tk.Frame(parent, bg="#faf8f2", highlightbackground=self.LINE, highlightthickness=1)
        section.pack(fill="x", pady=(0, 12))
        tk.Label(section, text=title, bg="#faf8f2", fg=self.INK, font=("Georgia", 14, "bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 1))
        tk.Label(section, text=subtitle, bg="#faf8f2", fg=self.MUTED, font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=17, pady=(0, 8))
        if not items:
            tk.Label(section, text="Nothing planned", bg="#faf8f2", fg=self.MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=17, pady=(2, 14))
            return
        for ingredient, amount in items:
            row = tk.Frame(section, bg="#faf8f2")
            row.pack(fill="x", padx=16, pady=(4, 0))
            tk.Label(row, text="[ ]", bg="#faf8f2", fg=self.TERRACOTTA, font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(row, text=ingredient.title(), bg="#faf8f2", fg=self.INK, font=("Segoe UI", 10, "bold"), anchor="w").pack(side="left", padx=8)
            tk.Label(row, text=amount, bg="#faf8f2", fg=self.MUTED, font=("Segoe UI", 9), anchor="e").pack(side="right")
        tk.Frame(section, bg="#faf8f2", height=12).pack()


if __name__ == "__main__":
    MenuHelper().mainloop()
