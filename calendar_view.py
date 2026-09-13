import calendar
import tkinter as tk
from datetime import date


class CalendarView(tk.Frame):
    def __init__(self, parent, database, colors, on_month_changed=None):
        super().__init__(parent, bg=colors["PANEL"], highlightbackground=colors["LINE"], highlightthickness=1)
        self.database = database
        self.colors = colors
        self.on_month_changed = on_month_changed
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.dragged_meal = None
        self._build()
        self.render()

    def _build(self):
        panel = self.colors["PANEL"]
        muted = self.colors["MUTED"]
        ink = self.colors["INK"]
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.month_button = tk.Button(
            self,
            command=self._month_picker,
            bg=panel,
            fg=ink,
            activebackground=panel,
            relief="flat",
            borderwidth=0,
            font=("Georgia", 21, "bold"),
            cursor="hand2",
        )
        self.month_button.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 2))
        tk.Label(
            self,
            text="Click the month to jump around your plan",
            bg=panel,
            fg=muted,
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=25, pady=(0, 18))
        self.calendar_grid = tk.Frame(self, bg=panel)
        self.calendar_grid.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 22))
        for column in range(7):
            self.calendar_grid.grid_columnconfigure(column, weight=1, uniform="day")
        for row in range(7):
            self.calendar_grid.grid_rowconfigure(row, weight=1, uniform="week")
        self.bind_all("<ButtonRelease-1>", self._drop_meal, add="+")

    def render(self):
        panel = self.colors["PANEL"]
        ink = self.colors["INK"]
        muted = self.colors["MUTED"]
        terracotta = self.colors["TERRACOTTA"]
        pale_green = self.colors["PALE_GREEN"]
        self.month_button.configure(text=f"{calendar.month_name[self.month]} {self.year} v")
        assignments = self.database.assignments_for_month(self.year, self.month)
        for child in self.calendar_grid.winfo_children():
            child.destroy()
        calendar.setfirstweekday(calendar.SUNDAY)
        for column, name in enumerate(("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")):
            tk.Label(
                self.calendar_grid,
                text=name,
                bg=panel,
                fg=muted,
                font=("Segoe UI", 8, "bold"),
            ).grid(row=0, column=column, sticky="w", padx=8, pady=(0, 8))
        for week_index, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for column, day_number in enumerate(week):
                if day_number == 0:
                    tk.Frame(self.calendar_grid, bg=panel).grid(row=week_index, column=column, sticky="nsew", padx=3, pady=3)
                    continue
                day_key = f"{self.year:04d}-{self.month:02d}-{day_number:02d}"
                assignment = assignments.get(day_key)
                cell = tk.Frame(self.calendar_grid, bg="#faf8f2", highlightbackground=self.colors["LINE"], highlightthickness=1, cursor="hand2")
                cell.grid(row=week_index, column=column, sticky="nsew", padx=3, pady=3)
                cell.day_key = day_key
                tk.Label(
                    cell,
                    text=str(day_number),
                    bg="#faf8f2",
                    fg=terracotta if column in (0, 6) else ink,
                    font=("Segoe UI", 10, "bold"),
                    anchor="w",
                ).pack(fill="x", padx=8, pady=(7, 2))
                if assignment:
                    meal_row = tk.Frame(cell, bg=pale_green)
                    meal_row.pack(fill="x", padx=6, pady=(3, 6))
                    meal_row.grid_columnconfigure(0, weight=1)
                    tk.Label(
                        meal_row,
                        text=assignment["name"],
                        bg=pale_green,
                        fg=self.colors["SAGE"],
                        font=("Segoe UI", 8, "bold"),
                        wraplength=82,
                        justify="left",
                        anchor="w",
                        padx=7,
                        pady=5,
                    ).grid(row=0, column=0, sticky="ew")
                    tk.Button(
                        meal_row,
                        text="x",
                        command=lambda key=day_key: self._clear_day(key),
                        bg=pale_green,
                        fg=self.colors["SAGE"],
                        activebackground="#d5e1d2",
                        activeforeground=terracotta,
                        relief="flat",
                        borderwidth=0,
                        font=("Segoe UI", 9, "bold"),
                        cursor="hand2",
                        padx=5,
                    ).grid(row=0, column=1, sticky="ne", padx=(0, 2))
                else:
                    tk.Label(cell, text="drop meal here", bg="#faf8f2", fg="#b5b5aa", font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=8, pady=(8, 4))

    def start_drag(self, event, meal_id):
        self.dragged_meal = meal_id
        self.winfo_toplevel().configure(cursor="hand2")

    def _drop_meal(self, event):
        if self.dragged_meal is None:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None and widget is not self.winfo_toplevel():
            if hasattr(widget, "day_key"):
                self.database.assign(widget.day_key, self.dragged_meal)
                self.render()
                break
            widget = widget.master
        self.dragged_meal = None
        self.winfo_toplevel().configure(cursor="")

    def _clear_day(self, day_key):
        self.database.clear_assignment(day_key)
        self.render()

    def _month_picker(self):
        popup = tk.Toplevel(self)
        popup.title("Choose month")
        popup.configure(bg=self.colors["PANEL"])
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        tk.Label(popup, text="VIEW A MONTH", bg=self.colors["PANEL"], fg=self.colors["TERRACOTTA"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(20, 8))
        month_var = tk.StringVar(value=calendar.month_name[self.month])
        year_var = tk.IntVar(value=self.year)
        from tkinter import ttk
        ttk.Combobox(popup, textvariable=month_var, values=list(calendar.month_name)[1:], state="readonly", width=15).grid(row=1, column=0, padx=(22, 6), pady=6)
        ttk.Spinbox(popup, textvariable=year_var, from_=2020, to=2100, width=7).grid(row=1, column=1, padx=(6, 22), pady=6)

        def apply_month():
            self.month = list(calendar.month_name).index(month_var.get())
            self.year = int(year_var.get())
            self.render()
            if self.on_month_changed:
                self.on_month_changed(self.year, self.month)
            popup.destroy()

        tk.Button(popup, text="Show month", command=apply_month, bg=self.colors["SAGE"], fg="white", relief="flat", borderwidth=0, padx=15, pady=9, cursor="hand2").grid(row=2, column=0, columnspan=2, pady=(12, 20))
        popup.update_idletasks()
        popup.geometry(f"+{self.winfo_toplevel().winfo_rootx() + 260}+{self.winfo_toplevel().winfo_rooty() + 100}")
