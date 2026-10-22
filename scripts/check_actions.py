"""Exercise every registered scaffold action across two learner identities."""

import json
import re
import sqlite3
from pathlib import Path

from check_migrations import apply_migrations, load_migrations

ROOT = Path(__file__).resolve().parents[1]


def execute(connection, tool, user, **params):
    bindings = {"__user_id": user, "__uuid": params.pop("__uuid", "new-item"), "__now": 1_000}
    bindings.update({key: value.get("default") for key, value in tool.get("params", {}).items()})
    bindings.update(params)
    cursor = connection.execute(tool["sql"], bindings)
    return cursor.fetchall() if tool["operation"] == "query" else cursor.rowcount


def main():
    tools = json.loads((ROOT / "mcp.json").read_text())["tools"]
    names = [tool["name"] for tool in tools]
    assert len(names) == len(set(names)), "action names must be unique"
    assert set(names) == {"list_items", "get_item", "create_item"}, "add an explicit authorization fixture for every new action"
    for tool in tools:
        assert re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", tool["name"]), tool["name"]
        assert tool.get("requires_auth") is True, f"{tool['name']} must require authentication"
        assert ":__user_id" in tool["sql"], f"{tool['name']} must scope by platform user ID"
        assert re.search(r"\buser_id\s*=\s*:__user_id\b|\buser_id\s*\)\s*VALUES\b", tool["sql"], re.I) or (
            tool["name"] == "create_item" and "user_id" in tool["sql"]
        ), f"{tool['name']} lacks a user ownership predicate or insert"

    actions = {tool["name"]: tool for tool in tools}
    with sqlite3.connect(":memory:") as connection:
        apply_migrations(connection, load_migrations())
        assert execute(connection, actions["create_item"], "alice", title="Alice item", __uuid="alice-id") == 1
        assert execute(connection, actions["create_item"], "bob", title="Bob item", __uuid="bob-id") == 1
        assert connection.execute("SELECT user_id FROM items WHERE id = 'alice-id'").fetchone() == ("alice",)
        assert [row[0] for row in execute(connection, actions["list_items"], "alice")] == ["alice-id"]
        assert [row[0] for row in execute(connection, actions["list_items"], "bob")] == ["bob-id"]
        assert [row[0] for row in execute(connection, actions["get_item"], "alice", id="alice-id")] == ["alice-id"]
        assert execute(connection, actions["get_item"], "bob", id="alice-id") == []
        assert execute(connection, actions["get_item"], "alice", id="bob-id") == []
    print(f"Action authorization gate passed: {len(tools)} actions, two-user isolation")


if __name__ == "__main__":
    main()
