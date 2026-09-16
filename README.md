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

## Linux CI

The GitHub Actions workflow in `.github/workflows/linux-mint-check.yml` checks the app on Ubuntu 24.04, the base used by Linux Mint 22. It installs Tk/X11 dependencies, validates the SQLite layer, launches the GUI under Xvfb, builds a PyInstaller executable, and uploads the Linux build artifact.

## Install on Linux Mint Cinnamon

From the project directory on the Mint machine, run:

```bash
chmod +x deploy_linux.sh
sudo ./deploy_linux.sh
```

The script builds a PyInstaller **onedir** package, installs it under `/opt/MenuHelper`, creates the system launcher `/usr/local/bin/menuhelper`, and adds Menu Helper to the Cinnamon application menu for all users. Each user gets a separate writable database at `~/.local/share/MenuHelper/menuhelper.db`.

## Use

- Drag a meal from the left library onto any day in the calendar.
- Drop another meal on an occupied day to replace the existing meal.
- Sunday is the first day shown in each calendar week.
- Click the month title to choose another month and year.
- Mark any calendar day as a shopping day using its **shop** toggle. Toggle it again to unset the day.
- Select **Generate List** to create a monthly pantry list and produce lists grouped by shopping day. Each produce list includes items from its shopping day through the day before the next shopping day.
- Use **Add a meal** to add ingredients one at a time, entering each ingredient's amount and checking **Produce** when appropriate.
- Use the `x` beside a meal to remove it from the library, or the `x` on a calendar assignment to clear only that day.
