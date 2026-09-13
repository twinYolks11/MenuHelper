# Menu Helper

A small desktop meal-planning app built with Python, Tkinter, and SQLite.

## Project structure

- `main.py` is the application engine and owns the meal library, dialogs, and shopping-list UI.
- `database.py` owns SQLite tables, migrations, meal assignments, and shopping-list queries.
- `calendar_view.py` owns the Sunday-first calendar, month picker, and drag-and-drop scheduling.

## Run

Install Python 3.10+ with Tk support, then run:

```powershell
python main.py
```

The app creates `menuhelper.db` on first launch. The database stores meals, ingredients, and calendar assignments in the project folder.

## Use

- Drag a meal from the left library onto any day in the calendar.
- Drop another meal on an occupied day to replace the existing meal.
- Sunday is the first day shown in each calendar week.
- Click the month title to choose another month and year.
- Select **Generate List** to create a monthly pantry list and weekly produce lists for the visible month.
- Use **Add a meal** to add ingredients one at a time, entering each ingredient's amount and checking **Produce** when appropriate.
- Use the `x` beside a meal to remove it from the library, or the `x` on a calendar assignment to clear only that day.
