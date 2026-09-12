import calendar
import sqlite3
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "menuhelper.db"


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_meals()

    def _create_tables(self):
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                ingredients TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS assignments (
                day TEXT PRIMARY KEY,
                meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE
            );
            """
        )
        self.connection.commit()

    def _seed_meals(self):
        meals = [
            ("Lemon herb chicken", "chicken breast|2 lb\nlemon|2\ngarlic|4 cloves\nolive oil|2 tbsp\nparsley|1 bunch"),
            ("Tomato basil pasta", "pasta|1 lb\ncrushed tomatoes|28 oz\nbasil|1 bunch\nparmesan|4 oz\ngarlic|3 cloves"),
            ("Ginger sesame bowls", "ground turkey|1 lb\nrice|2 cups\nbroccoli|1 head\nsoy sauce|1/3 cup\nginger|1 piece"),
            ("Black bean tacos", "corn tortillas|12\nblack beans|2 cans\navocado|2\nlime|2\ncheddar cheese|8 oz\ncilantro|1 bunch"),
            ("Cozy lentil soup", "brown lentils|1 lb\ncarrots|4\ncelery|4 stalks\nonion|1\nvegetable stock|6 cups"),
        ]
        self.connection.executemany(
            "INSERT OR IGNORE INTO meals (name, ingredients) VALUES (?, ?)", meals
        )
        self.connection.commit()

    def meals(self):
        return self.connection.execute("SELECT * FROM meals ORDER BY name").fetchall()

    def add_meal(self, name, ingredients):
        cursor = self.connection.execute(
            "INSERT INTO meals (name, ingredients) VALUES (?, ?)", (name, ingredients)
        )
        self.connection.commit()
        return cursor.lastrowid

    def delete_meal(self, meal_id):
        self.connection.execute("DELETE FROM assignments WHERE meal_id = ?", (meal_id,))
        self.connection.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        self.connection.commit()

    def assignments_for_month(self, year, month):
        prefix = f"{year:04d}-{month:02d}-%"
        rows = self.connection.execute(
            """
            SELECT assignments.day, meals.*
            FROM assignments JOIN meals ON meals.id = assignments.meal_id
            WHERE assignments.day LIKE ?
            """,
            (prefix,),
        ).fetchall()
        return {row["day"]: row for row in rows}

    def assign(self, day_key, meal_id):
        self.connection.execute(
            "INSERT INTO assignments(day, meal_id) VALUES (?, ?) "
            "ON CONFLICT(day) DO UPDATE SET meal_id=excluded.meal_id",
            (day_key, meal_id),
        )
        self.connection.commit()

    def clear_assignment(self, day_key):
        self.connection.execute("DELETE FROM assignments WHERE day = ?", (day_key,))
        self.connection.commit()

    def shopping_list(self, year, month):
        rows = self.connection.execute(
            """
            SELECT meals.ingredients FROM assignments
            JOIN meals ON meals.id = assignments.meal_id
            WHERE assignments.day LIKE ?
            """,
            (f"{year:04d}-{month:02d}-%",),
        ).fetchall()
        totals = {}
        for row in rows:
            for line in row["ingredients"].splitlines():
                if "|" not in line:
                    continue
                ingredient, amount = line.split("|", 1)
                ingredient = ingredient.strip()
                amount = amount.strip()
                if ingredient:
                    totals.setdefault(ingredient, []).append(amount)
        return [(ingredient, " + ".join(amounts)) for ingredient, amounts in sorted(totals.items())]


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
        self.database = Database(DB_PATH)
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.assignments = {}
        self.dragged_meal = None
        self._build_styles()
        self._build_shell()
        self._render_meals()
        self._render_calendar()

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=self.PANEL, background=self.PANEL, bordercolor=self.LINE, padding=6)
        style.configure("Vertical.TScrollbar", troughcolor=self.BG, background="#c9c5bb", bordercolor=self.BG, arrowcolor=self.MUTED)

    def _build_shell(self):
        self.grid_columnconfigure(1, weight=2, uniform="main")
        self.grid_columnconfigure(0, weight=1, uniform="main")
        self.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=self.BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=28, pady=(24, 18))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="MENU HELPER", bg=self.BG, fg=self.TERRACOTTA, font=("Georgia", 11, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(header, text="Plan a month of good eating", bg=self.BG, fg=self.INK, font=("Georgia", 22, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.generate_button = tk.Button(header, text="Generate List  →", command=self._show_shopping_list, bg=self.TERRACOTTA, fg="white", activebackground="#af563a", activeforeground="white", relief="flat", borderwidth=0, padx=18, pady=11, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.generate_button.grid(row=0, column=2, rowspan=2, sticky="e")

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
        tk.Button(self.meal_panel, text="+  Add a meal", command=self._add_meal_dialog, bg=self.PALE_GREEN, fg=self.SAGE, activebackground="#d5e1d2", relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"), pady=10, cursor="hand2").grid(row=3, column=0, columnspan=2, sticky="ew", padx=22, pady=22)

        self.calendar_panel = tk.Frame(self, bg=self.PANEL, highlightbackground=self.LINE, highlightthickness=1)
        self.calendar_panel.grid(row=1, column=1, sticky="nsew", padx=(12, 28), pady=(0, 28))
        self.calendar_panel.grid_rowconfigure(2, weight=1)
        self.calendar_panel.grid_columnconfigure(0, weight=1)
        self.month_button = tk.Button(self.calendar_panel, command=self._month_picker, bg=self.PANEL, fg=self.INK, activebackground=self.PANEL, relief="flat", borderwidth=0, font=("Georgia", 21, "bold"), cursor="hand2")
        self.month_button.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 2))
        tk.Label(self.calendar_panel, text="Click the month to jump around your plan", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=25, pady=(0, 18))
        self.calendar_grid = tk.Frame(self.calendar_panel, bg=self.PANEL)
        self.calendar_grid.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 22))
        for column in range(7):
            self.calendar_grid.grid_columnconfigure(column, weight=1, uniform="day")
        for row in range(7):
            self.calendar_grid.grid_rowconfigure(row, weight=1, uniform="week")
        self.bind_all("<ButtonRelease-1>", self._drop_meal)

    def _render_meals(self):
        for child in self.meal_inner.winfo_children():
            child.destroy()
        for meal in self.database.meals():
            item = tk.Frame(self.meal_inner, bg=self.PANEL, highlightbackground=self.LINE, highlightthickness=1, cursor="hand2")
            item.pack(fill="x", padx=4, pady=5)
            item.meal_id = meal["id"]
            tk.Label(item, text="=", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 4), pady=12)
            text = tk.Frame(item, bg=self.PANEL)
            text.pack(side="left", fill="x", expand=True, pady=10)
            tk.Label(text, text=meal["name"], bg=self.PANEL, fg=self.INK, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            count = len(meal["ingredients"].splitlines())
            tk.Label(text, text=f"{count} ingredients", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(2, 0))
            delete_button = tk.Button(item, text="x", command=lambda meal_id=meal["id"], meal_name=meal["name"]: self._delete_meal(meal_id, meal_name), bg=self.PANEL, fg=self.MUTED, activebackground="#f3ddd5", activeforeground=self.TERRACOTTA, relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"), cursor="hand2", padx=10)
            delete_button.pack(side="right", padx=(0, 5))
            for widget in (item, text, *text.winfo_children()):
                widget.bind("<ButtonPress-1>", lambda event, meal_id=meal["id"]: self._start_drag(event, meal_id))

    def _render_calendar(self):
        self.month_button.configure(text=f"{calendar.month_name[self.month]} {self.year} v")
        self.assignments = self.database.assignments_for_month(self.year, self.month)
        for child in self.calendar_grid.winfo_children():
            child.destroy()
        for column, name in enumerate(("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")):
            tk.Label(self.calendar_grid, text=name, bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=column, sticky="w", padx=8, pady=(0, 8))
        month_days = calendar.monthcalendar(self.year, self.month)
        for week_index, week in enumerate(month_days, start=1):
            for column, day_number in enumerate(week):
                if day_number == 0:
                    tk.Frame(self.calendar_grid, bg=self.PANEL).grid(row=week_index, column=column, sticky="nsew", padx=3, pady=3)
                    continue
                day_key = f"{self.year:04d}-{self.month:02d}-{day_number:02d}"
                assignment = self.assignments.get(day_key)
                cell = tk.Frame(self.calendar_grid, bg="#faf8f2", highlightbackground=self.LINE, highlightthickness=1, cursor="hand2")
                cell.grid(row=week_index, column=column, sticky="nsew", padx=3, pady=3)
                cell.day_key = day_key
                tk.Label(cell, text=str(day_number), bg="#faf8f2", fg=self.TERRACOTTA if column >= 5 else self.INK, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=8, pady=(7, 2))
                if assignment:
                    meal_row = tk.Frame(cell, bg=self.PALE_GREEN)
                    meal_row.pack(fill="x", padx=6, pady=(3, 6))
                    tk.Label(meal_row, text=assignment["name"], bg=self.PALE_GREEN, fg=self.SAGE, font=("Segoe UI", 8, "bold"), wraplength=82, justify="left", anchor="w", padx=7, pady=5).pack(side="left", fill="x", expand=True)
                    tk.Button(meal_row, text="x", command=lambda day_key=day_key: self._clear_day(day_key), bg=self.PALE_GREEN, fg=self.SAGE, activebackground="#d5e1d2", activeforeground=self.TERRACOTTA, relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=5).pack(side="right", padx=(0, 2))
                else:
                    tk.Label(cell, text="drop meal here", bg="#faf8f2", fg="#b5b5aa", font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=8, pady=(8, 4))

    def _delete_meal(self, meal_id, meal_name):
        if not messagebox.askyesno(
            "Remove meal",
            f"Remove {meal_name} from the meal library?\n\nAny scheduled days using it will also be cleared.",
            parent=self,
        ):
            return
        self.database.delete_meal(meal_id)
        self._render_meals()
        self._render_calendar()

    def _clear_day(self, day_key):
        self.database.clear_assignment(day_key)
        self._render_calendar()

    def _start_drag(self, event, meal_id):
        self.dragged_meal = meal_id
        self.configure(cursor="hand2")

    def _drop_meal(self, event):
        if self.dragged_meal is None:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None and widget is not self:
            if hasattr(widget, "day_key"):
                self.database.assign(widget.day_key, self.dragged_meal)
                self._render_calendar()
                break
            widget = widget.master
        self.dragged_meal = None
        self.configure(cursor="")

    def _month_picker(self):
        popup = tk.Toplevel(self)
        popup.title("Choose month")
        popup.configure(bg=self.PANEL)
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        tk.Label(popup, text="VIEW A MONTH", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(20, 8))
        month_var = tk.StringVar(value=calendar.month_name[self.month])
        year_var = tk.IntVar(value=self.year)
        ttk.Combobox(popup, textvariable=month_var, values=list(calendar.month_name)[1:], state="readonly", width=15).grid(row=1, column=0, padx=(22, 6), pady=6)
        ttk.Spinbox(popup, textvariable=year_var, from_=2020, to=2100, width=7).grid(row=1, column=1, padx=(6, 22), pady=6)
        def apply_month():
            self.month = list(calendar.month_name).index(month_var.get())
            self.year = int(year_var.get())
            self._render_calendar()
            popup.destroy()
        tk.Button(popup, text="Show month", command=apply_month, bg=self.SAGE, fg="white", relief="flat", borderwidth=0, padx=15, pady=9, cursor="hand2").grid(row=2, column=0, columnspan=2, pady=(12, 20))
        popup.update_idletasks()
        popup.geometry(f"+{self.winfo_rootx() + 260}+{self.winfo_rooty() + 100}")

    def _add_meal_dialog(self):
        popup = tk.Toplevel(self)
        popup.title("Add meal")
        popup.configure(bg=self.PANEL)
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        tk.Label(popup, text="NEW MEAL", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(popup, text="Name", bg=self.PANEL, fg=self.INK, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(8, 3))
        name_entry = tk.Entry(popup, bg="#faf8f2", fg=self.INK, relief="flat", width=38, font=("Segoe UI", 10))
        name_entry.pack(padx=24, ipady=7)
        tk.Label(popup, text="Ingredients (one per line: ingredient | amount)", bg=self.PANEL, fg=self.INK, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(14, 3))
        ingredients = tk.Text(popup, bg="#faf8f2", fg=self.INK, relief="flat", width=38, height=8, font=("Segoe UI", 10))
        ingredients.pack(padx=24)
        def save():
            if not name_entry.get().strip() or not ingredients.get("1.0", "end").strip():
                messagebox.showwarning("Missing details", "Add a meal name and at least one ingredient.", parent=popup)
                return
            try:
                self.database.add_meal(name_entry.get().strip(), ingredients.get("1.0", "end").strip())
            except sqlite3.IntegrityError:
                messagebox.showwarning("Meal already exists", "Choose a different meal name.", parent=popup)
                return
            self._render_meals()
            popup.destroy()
        tk.Button(popup, text="Save meal", command=save, bg=self.SAGE, fg="white", relief="flat", borderwidth=0, padx=18, pady=10, cursor="hand2").pack(pady=(16, 22))
        name_entry.focus_set()

    def _show_shopping_list(self):
        items = self.database.shopping_list(self.year, self.month)
        popup = tk.Toplevel(self)
        popup.title("Shopping list")
        popup.geometry("420x560")
        popup.configure(bg=self.PANEL)
        popup.transient(self)
        tk.Label(popup, text="SHOPPING LIST", bg=self.PANEL, fg=self.TERRACOTTA, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=26, pady=(24, 3))
        tk.Label(popup, text=f"{calendar.month_name[self.month]} {self.year}", bg=self.PANEL, fg=self.INK, font=("Georgia", 21, "bold")).pack(anchor="w", padx=26)
        tk.Label(popup, text="Combined from every planned meal", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=27, pady=(3, 16))
        list_frame = tk.Frame(popup, bg="#faf8f2", highlightbackground=self.LINE, highlightthickness=1)
        list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        if not items:
            tk.Label(list_frame, text="No meals planned yet.\nDrag meals onto the calendar to begin.", bg="#faf8f2", fg=self.MUTED, font=("Segoe UI", 10), justify="left").pack(anchor="w", padx=18, pady=22)
        else:
            for ingredient, amount in items:
                row = tk.Frame(list_frame, bg="#faf8f2")
                row.pack(fill="x", padx=16, pady=(13, 0))
                tk.Label(row, text="[ ]", bg="#faf8f2", fg=self.TERRACOTTA, font=("Segoe UI", 10, "bold")).pack(side="left")
                tk.Label(row, text=ingredient.title(), bg="#faf8f2", fg=self.INK, font=("Segoe UI", 10, "bold"), anchor="w").pack(side="left", padx=8)
                tk.Label(row, text=amount, bg="#faf8f2", fg=self.MUTED, font=("Segoe UI", 9), anchor="e").pack(side="right")


if __name__ == "__main__":
    app = MenuHelper()
    app.mainloop()
