"""Execute registered PAS actions against the real migrations with two identities."""

import json
import re
import sqlite3
import uuid
from pathlib import Path

from check_migrations import apply_migrations, load_migrations

ROOT = Path(__file__).resolve().parents[1]
MAGIC = {"__user_id", "__uuid", "__now"}
EXPECTED = {
    "list_items", "get_item", "create_item", "bootstrap_learner",
    "get_learner_bootstrap", "get_next_lesson", "start_lesson", "resume_lesson",
    "submit_exercise", "complete_lesson", "list_due_reviews", "record_review",
    "update_preferences", "create_content_report", "list_content_reports",
}


def execute(connection, tool, user, *, now=1000, **params):
    bindings = {"__user_id": user, "__uuid": str(uuid.uuid4()), "__now": now}
    bindings.update({key: value.get("default") for key, value in tool.get("params", {}).items()})
    bindings.update(params)
    statements = tool.get("statements", [tool.get("sql")])
    results = []
    with connection:
        for sql in statements:
            bindings["__uuid"] = str(uuid.uuid4())
            cursor = connection.execute(sql, bindings)
            results.append(cursor.fetchall() if tool["operation"] == "query" else cursor.rowcount)
    return results[0] if tool["operation"] != "batch" else results


def validate(tools):
    names = [tool["name"] for tool in tools]
    assert len(names) == len(set(names)) and set(names) == EXPECTED
    for tool in tools:
        name = tool["name"]
        assert re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", name)
        assert tool.get("requires_auth") is True, name
        assert tool["operation"] in {"query", "execute", "batch"}, name
        statements = tool.get("statements", [tool.get("sql")])
        assert statements and len(statements) <= 25
        assert (tool["operation"] == "batch") == ("statements" in tool)
        assert set(tool.get("params", {})).isdisjoint(MAGIC)
        for sql in statements:
            assert sql and ";" not in sql
            assert re.match(r"^SELECT\b" if tool["operation"] == "query" else r"^(INSERT|UPDATE|DELETE)\b", sql, re.I), name
            assert ":__user_id" in sql, name
            assert set(re.findall(r":([a-zA-Z_][a-zA-Z0-9_]*)", sql)) <= set(tool.get("params", {})) | MAGIC, name
            if re.match(r"^(UPDATE|DELETE)\b", sql, re.I):
                assert re.search(r"\bWHERE\b", sql, re.I), name


def seed(connection):
    connection.execute("INSERT INTO courses VALUES ('course','en','es','Course',1000,1000)")
    connection.execute("INSERT INTO course_versions VALUES ('v1','course',1,'pkg-1','published',1000,1000)")
    connection.execute("INSERT INTO lessons VALUES ('l1','v1','lesson-1',1,0,'Lesson',1000)")
    connection.execute("INSERT INTO lessons VALUES ('l2','v1','lesson-2',1,1,'Lesson two',1000)")
    connection.execute("INSERT INTO exercises VALUES ('e1','l1','exercise-1',1,0,'recognition','policy-1',1000)")
    connection.execute("INSERT INTO exercises VALUES ('e2','l1','exercise-2',1,1,'recognition','policy-1',1000)")
    connection.execute("INSERT INTO exercises VALUES ('e3','l2','exercise-3',1,0,'recognition','policy-1',1000)")
    connection.execute("INSERT INTO course_releases VALUES ('r1','course','v1',1,'active','editor',1000,1000)")


def main():
    tools = json.loads((ROOT / "mcp.json").read_text())["tools"]
    validate(tools)
    actions = {tool["name"]: tool for tool in tools}
    def call(connection, name, user, **kwargs):
        return execute(connection, actions[name], user, **kwargs)
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        apply_migrations(connection, load_migrations())
        seed(connection)
        assert call(connection, "create_item", "alice", title="Alice item") == 1
        assert call(connection, "create_item", "bob", title="Bob item") == 1
        alice_item = call(connection, "list_items", "alice")[0][0]
        bob_item = call(connection, "list_items", "bob")[0][0]
        assert alice_item != bob_item
        assert call(connection, "get_item", "bob", id=alice_item) == []
        assert call(connection, "get_item", "alice", id=bob_item) == []
        for user in ("alice", "bob"):
            assert call(connection, "bootstrap_learner", user) == [1, 1]
            assert call(connection, "bootstrap_learner", user) == [0, 0]
            assert len(call(connection, "get_learner_bootstrap", user)) == 1
            assert call(connection, "get_next_lesson", user)[0][0] == "l1"
        assert call(connection, "get_learner_bootstrap", "mallory") == []
        assert call(connection, "start_lesson", "mallory", lesson_id="l1") == 0
        assert call(connection, "start_lesson", "alice", lesson_id="l2") == 0
        assert call(connection, "start_lesson", "alice", lesson_id="l1") == 1
        assert call(connection, "start_lesson", "alice", lesson_id="l1") == 0
        assert call(connection, "start_lesson", "bob", lesson_id="l1") == 1
        alice_session = call(connection, "get_learner_bootstrap", "alice")[0][9]
        bob_session = call(connection, "get_learner_bootstrap", "bob")[0][9]
        assert alice_session != bob_session
        assert call(connection, "resume_lesson", "bob", session_id=alice_session) == []
        assert call(connection, "resume_lesson", "alice", session_id=bob_session) == []
        assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=1000) == 0
        submit = dict(attempt_id=str(uuid.uuid4()), session_id=alice_session, exercise_id="e1", expected_updated_at=1000)
        assert call(connection, "submit_exercise", "bob", **submit) == [0, 0]
        assert call(connection, "submit_exercise", "alice", **{**submit, "exercise_id": "e3"}) == [0, 0]
        assert call(connection, "submit_exercise", "alice", **{**submit, "expected_updated_at": 999}) == [0, 0]
        assert call(connection, "submit_exercise", "alice", now=2000, **{**submit, "attempt_id": "not-a-uuid"}) == [0, 0]
        assert call(connection, "submit_exercise", "alice", now=2000, **submit) == [1, 1]
        assert call(connection, "submit_exercise", "alice", now=3000, **submit) == [0, 0]
        assert call(connection, "submit_exercise", "alice", now=3000, **{**submit, "attempt_id": str(uuid.uuid4())}) == [0, 0]
        assert connection.execute("SELECT attempt_number,evaluator_policy_version,result_code FROM exercise_attempts WHERE id=?", (submit['attempt_id'],)).fetchone() == (1, "policy-1", "pending_evaluation")
        assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=2000) == 0
        assert call(connection, "submit_exercise", "alice", now=3000, attempt_id=str(uuid.uuid4()), session_id=alice_session, exercise_id="e2", expected_updated_at=2000) == [1, 1]
        assert call(connection, "complete_lesson", "bob", session_id=alice_session, expected_updated_at=3000) == 0
        assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=2000) == 0
        assert call(connection, "complete_lesson", "alice", now=4000, session_id=alice_session, expected_updated_at=3000) == 1
        assert call(connection, "complete_lesson", "alice", now=5000, session_id=alice_session, expected_updated_at=4000) == 0
        assert call(connection, "get_next_lesson", "alice")[0][0] == "l2"
        assert call(connection, "get_next_lesson", "bob")[0][0] == "l1"
        assert call(connection, "resume_lesson", "alice", session_id=alice_session) == []
        assert call(connection, "update_preferences", "bob", source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=999) == 0
        assert call(connection, "update_preferences", "alice", now=5000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=1000) == 1
        assert call(connection, "update_preferences", "alice", now=6000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=1000) == 0
        assert connection.execute("SELECT reminders_enabled FROM learner_preferences WHERE user_id='bob'").fetchone() == (0,)
        connection.execute("INSERT INTO review_states (id,user_id,course_id,stable_content_id,source_exercise_id,due_at,created_at,updated_at) VALUES ('rev-a','alice','course','exercise-1','e1',1000,1000,1000)")
        assert [row[0] for row in call(connection, "list_due_reviews", "alice", now=6000)] == ["rev-a"]
        assert call(connection, "list_due_reviews", "alice", now=6000, before_due_at=1000, before_id="rev-a") == []
        assert call(connection, "list_due_reviews", "bob", now=6000) == []
        review = dict(exposure_id=str(uuid.uuid4()), review_id="rev-a", session_id=alice_session)
        assert call(connection, "record_review", "bob", now=6000, **review) == 0
        assert call(connection, "record_review", "alice", now=6000, **{**review, "exposure_id": "not-a-uuid"}) == 0
        assert call(connection, "record_review", "alice", now=6000, **review) == 1
        assert call(connection, "record_review", "alice", now=7000, **review) == 0
        assert call(connection, "record_review", "alice", now=7000, **{**review, "exposure_id": str(uuid.uuid4())}) == 0
        report = dict(report_id=str(uuid.uuid4()), session_id=alice_session, exercise_id="e1", category="answer")
        assert call(connection, "create_content_report", "bob", **report) == 0
        assert call(connection, "create_content_report", "alice", **{**report, "category": "invalid"}) == 0
        assert call(connection, "create_content_report", "alice", **{**report, "exercise_id": "e3"}) == 0
        assert call(connection, "create_content_report", "alice", now=6000, **{**report, "report_id": "not-a-uuid"}) == 0
        assert call(connection, "create_content_report", "alice", now=6000, **report) == 1
        assert call(connection, "create_content_report", "alice", now=7000, **report) == 0
        assert len(call(connection, "list_content_reports", "alice")) == 1
        assert call(connection, "list_content_reports", "bob") == []
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    print(f"Action authorization gate passed: {len(tools)} actions, ownership, replay and stale-write fixtures")


if __name__ == "__main__":
    main()
