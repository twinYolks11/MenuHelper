import os
import sqlite3
import shutil
from pathlib import Path


if os.name == "nt":
    DATA_ROOT = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
else:
    DATA_ROOT = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

APP_DIR = DATA_ROOT / "MenuHelper"
DB_PATH = APP_DIR / "menuhelper.db"
LEGACY_DB_PATH = Path(__file__).resolve().parent / "menuhelper.db"


class Database:
    def __init__(self, path=DB_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path == DB_PATH and not path.exists() and LEGACY_DB_PATH.exists():
            shutil.copy2(LEGACY_DB_PATH, path)
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
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                amount TEXT NOT NULL,
                produce INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS shopping_days (
                day TEXT PRIMARY KEY
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
        self._migrate_ingredients()
        self.connection.commit()

    def _migrate_ingredients(self):
        meals = self.connection.execute("SELECT id, ingredients FROM meals").fetchall()
        for meal in meals:
            existing = self.connection.execute(
                "SELECT 1 FROM ingredients WHERE meal_id = ? LIMIT 1", (meal["id"],)
            ).fetchone()
            if existing:
                continue
            rows = []
            for line in meal["ingredients"].splitlines():
                if "|" in line:
                    name, amount = line.split("|", 1)
                    if name.strip() and amount.strip():
                        rows.append((meal["id"], name.strip(), amount.strip(), 0))
            self.connection.executemany(
                "INSERT INTO ingredients (meal_id, name, amount, produce) VALUES (?, ?, ?, ?)",
                rows,
            )

    def meals(self):
        return self.connection.execute("SELECT * FROM meals ORDER BY name").fetchall()

    def meal_ingredients(self, meal_id):
        return self.connection.execute(
            "SELECT name, amount, produce FROM ingredients WHERE meal_id = ? ORDER BY id",
            (meal_id,),
        ).fetchall()

    def add_meal(self, name, ingredients):
        cursor = self.connection.execute(
            "INSERT INTO meals (name, ingredients) VALUES (?, ?)",
            (name, "\n".join(f"{item['name']}|{item['amount']}" for item in ingredients)),
        )
        self.connection.executemany(
            "INSERT INTO ingredients (meal_id, name, amount, produce) VALUES (?, ?, ?, ?)",
            [(cursor.lastrowid, item["name"], item["amount"], item["produce"]) for item in ingredients],
        )
        self.connection.commit()
        return cursor.lastrowid

    def update_meal(self, meal_id, name, ingredients):
        self.connection.execute(
            "UPDATE meals SET name = ?, ingredients = ? WHERE id = ?",
            (name, "\n".join(f"{item['name']}|{item['amount']}" for item in ingredients), meal_id),
        )
        self.connection.execute("DELETE FROM ingredients WHERE meal_id = ?", (meal_id,))
        self.connection.executemany(
            "INSERT INTO ingredients (meal_id, name, amount, produce) VALUES (?, ?, ?, ?)",
            [(meal_id, item["name"], item["amount"], item["produce"]) for item in ingredients],
        )
        self.connection.commit()

    def delete_meal(self, meal_id):
        self.connection.execute("DELETE FROM assignments WHERE meal_id = ?", (meal_id,))
        self.connection.execute("DELETE FROM ingredients WHERE meal_id = ?", (meal_id,))
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

    def shopping_days_for_month(self, year, month):
        prefix = f"{year:04d}-{month:02d}-%"
        rows = self.connection.execute(
            "SELECT day FROM shopping_days WHERE day LIKE ? ORDER BY day", (prefix,)
        ).fetchall()
        return {row["day"] for row in rows}

    def set_shopping_day(self, day_key, selected):
        if selected:
            self.connection.execute(
                "INSERT OR IGNORE INTO shopping_days(day) VALUES (?)", (day_key,)
            )
        else:
            self.connection.execute("DELETE FROM shopping_days WHERE day = ?", (day_key,))
        self.connection.commit()

    def shopping_list(self, year, month, produce, week_days=None):
        query = (
            "SELECT ingredients.name, ingredients.amount FROM assignments "
            "JOIN ingredients ON ingredients.meal_id = assignments.meal_id "
            "WHERE assignments.day LIKE ? AND ingredients.produce = ?"
        )
        parameters = [f"{year:04d}-{month:02d}-%", int(produce)]
        if week_days:
            placeholders = ", ".join("?" for _ in week_days)
            query += f" AND assignments.day IN ({placeholders})"
            parameters.extend(week_days)
        rows = self.connection.execute(query, parameters).fetchall()
        totals = {}
        for row in rows:
            ingredient = row["name"].strip()
            amount = row["amount"].strip()
            if ingredient:
                totals.setdefault(ingredient, []).append(amount)
        return [(ingredient, " + ".join(amounts)) for ingredient, amounts in sorted(totals.items())]

    def shopping_list_range(self, start_day, end_day, produce=True):
        rows = self.connection.execute(
            """
            SELECT ingredients.name, ingredients.amount
            FROM assignments
            JOIN ingredients ON ingredients.meal_id = assignments.meal_id
            WHERE assignments.day >= ? AND assignments.day <= ?
              AND ingredients.produce = ?
            """,
            (start_day, end_day, int(produce)),
        ).fetchall()
        totals = {}
        for row in rows:
            ingredient = row["name"].strip()
            amount = row["amount"].strip()
            if ingredient:
                totals.setdefault(ingredient, []).append(amount)
        return [(ingredient, " + ".join(amounts)) for ingredient, amounts in sorted(totals.items())]
