# Menu Helper

A small desktop meal-planning app built with Python, Tkinter, and SQLite.

## Run

Install Python 3.10+ with Tk support, then run:

```powershell
python main.py
```

The app creates `menuhelper.db` on first launch. The database stores meals, ingredients, and calendar assignments in the project folder.

## Use

- Drag a meal from the left library onto any day in the calendar.
- Drop another meal on an occupied day to replace the existing meal.
- Click the month title to choose another month and year.
- Select **Generate List** to combine ingredient amounts for all planned meals in the visible month.
- Use **Add a meal** to add your own meals. Enter one ingredient per line as `ingredient | amount`.
