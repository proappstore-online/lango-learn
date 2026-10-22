"""Check committed PAS D1 migrations on a fresh SQLite database."""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = re.compile(r"^CREATE\s+(?:TABLE|INDEX|UNIQUE\s+INDEX)\s+IF\s+NOT\s+EXISTS\b", re.I)


def load_migrations():
    migrations = json.loads((ROOT / "migrations.json").read_text())["migrations"]
    assert migrations, "at least one migration is required"
    names = [item["name"] for item in migrations]
    assert len(names) == len(set(names)), "migration names must be unique"
    assert names == sorted(names), "migration names must be ordered"
    for item in migrations:
        statements = [part.strip() for part in item["sql"].split(";") if part.strip()]
        assert statements, f"{item['name']} has no SQL"
        for statement in statements:
            assert ALLOWED.match(statement), f"{item['name']} has a non-additive statement: {statement}"
    return migrations


def apply_migrations(connection, migrations):
    for item in migrations:
        connection.executescript(item["sql"])


def main():
    migrations = load_migrations()
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        apply_migrations(connection, migrations)
        first_schema = connection.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        apply_migrations(connection, migrations)
        second_schema = connection.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        assert first_schema == second_schema, "migrations are not idempotent"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    print(f"Migration gate passed: {len(migrations)} additive, ordered, idempotent migration(s)")


if __name__ == "__main__":
    main()
