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
    "create_course", "create_course_version", "create_lesson", "create_exercise",
    "submit_version_for_review", "approve_course_version", "return_version_to_draft",
    "publish_course_version", "retire_course_release", "list_staff_reports", "update_report_status",
    "import_guest_lesson", "get_guest_import_receipt", "get_guest_lesson_summary",
}

STAFF_ROLES = {
    "create_course": "curriculum_editor", "create_course_version": "curriculum_editor",
    "create_lesson": "curriculum_editor", "create_exercise": "curriculum_editor",
    "submit_version_for_review": "curriculum_editor", "return_version_to_draft": "content_reviewer",
    "approve_course_version": "content_reviewer", "publish_course_version": "moderator",
    "retire_course_release": "moderator", "list_staff_reports": "support",
    "update_report_status": "support",
}


def execute(connection, tool, user, *, now=1000, roles=(), **params):
    if tool.get("requires_auth") and not user:
        raise PermissionError(f"{tool['name']}: PAS session required")
    required_roles = tool.get("auth", {}).get("app_roles", [])
    if required_roles and not set(required_roles).intersection(roles):
        raise PermissionError(f"{tool['name']}: PAS app role required")
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
        if name in STAFF_ROLES:
            auth = tool.get("auth", {})
            assert auth.get("required") is True, name
            assert auth.get("app_roles") == [STAFF_ROLES[name]], name
            assert auth.get("caller_unscoped", {}).get("reason"), name
        assert tool["operation"] in {"query", "execute", "batch"}, name
        statements = tool.get("statements", [tool.get("sql")])
        assert statements and len(statements) <= 25
        assert (tool["operation"] == "batch") == ("statements" in tool)
        assert set(tool.get("params", {})).isdisjoint(MAGIC)
        for sql in statements:
            assert sql and ";" not in sql
            assert re.match(r"^SELECT\b" if tool["operation"] == "query" else r"^(INSERT|UPDATE|DELETE)\b", sql, re.I), name
            assert ":__user_id" in sql or tool.get("auth", {}).get("caller_unscoped", {}).get("reason"), name
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
        check_staff_actions(connection, call)
        check_guest_imports(connection, call)
    print(f"Action authorization gate passed: {len(tools)} actions, ownership, replay and stale-write fixtures")


def check_guest_imports(connection, call):
    def count():
        return connection.execute("SELECT COUNT(*) FROM guest_lesson_imports").fetchone()[0]

    guest_id = str(uuid.uuid4())
    params = dict(guest_session_id=guest_id, completed_steps=2, client_saved_at=1000)
    before = count()
    try:
        call(connection, "import_guest_lesson", None, now=2000, **params)
    except PermissionError:
        pass
    else:
        raise AssertionError("guest import accepted before sign-in")
    assert count() == before
    assert call(connection, "import_guest_lesson", "alice", now=2000, **params) == [0, 0, 1]
    assert call(connection, "get_guest_import_receipt", "alice", guest_session_id=guest_id)[0][3:5] == (2, "imported")
    assert call(connection, "get_guest_import_receipt", "bob", guest_session_id=guest_id) == []
    assert call(connection, "import_guest_lesson", "alice", now=3000, **params) == [0, 0, 0]
    assert call(connection, "import_guest_lesson", "alice", now=3000, **dict(params, completed_steps=1)) == [0, 0, 0]
    assert call(connection, "import_guest_lesson", "bob", now=3000, **params) == [0, 0, 0]
    assert call(connection, "import_guest_lesson", "unclaimed-user", now=3000, **params) == [0, 0, 0]
    assert connection.execute("SELECT 1 FROM learner_profiles WHERE user_id='unclaimed-user'").fetchone() is None
    assert call(connection, "get_guest_lesson_summary", "bob")[0] == (None, 0)
    lower = dict(guest_session_id=str(uuid.uuid4()), completed_steps=1, client_saved_at=1000)
    assert call(connection, "import_guest_lesson", "alice", now=3000, **lower) == [0, 0, 1]
    assert call(connection, "get_guest_import_receipt", "alice", guest_session_id=lower['guest_session_id'])[0][4] == "kept_existing"
    assert call(connection, "get_guest_lesson_summary", "alice")[0] == (2, 2)
    for invalid in (dict(params, guest_session_id="not-a-uuid"), dict(params, guest_session_id=str(uuid.uuid4()).upper()), dict(params, guest_session_id=str(uuid.uuid4()), completed_steps=3), dict(params, guest_session_id=str(uuid.uuid4()), client_saved_at=-1)):
        assert call(connection, "import_guest_lesson", "alice", now=3000, **invalid) == [0, 0, 0]
    assert count() == before + 2
    # A rejected request leaves no partial account rows; correcting it can be retried.
    missing = str(uuid.uuid4())
    assert call(connection, "import_guest_lesson", "new-user", now=3000, guest_session_id=missing, completed_steps=3, client_saved_at=1000) == [0, 0, 0]
    assert connection.execute("SELECT 1 FROM guest_lesson_imports WHERE id=?", (missing,)).fetchone() is None
    assert connection.execute("SELECT 1 FROM learner_profiles WHERE user_id='new-user'").fetchone() is None
    assert call(connection, "import_guest_lesson", "new-user", now=3000, guest_session_id=missing, completed_steps=1, client_saved_at=1000) == [1, 1, 1]

    class InterruptedBatch:
        def __init__(self, db):
            self.db = db
            self.statements = 0
        def __enter__(self):
            self.db.__enter__()
            return self
        def __exit__(self, *args):
            return self.db.__exit__(*args)
        def execute(self, sql, bindings):
            self.statements += 1
            if self.statements == 3:
                raise sqlite3.OperationalError("synthetic third-statement failure")
            return self.db.execute(sql, bindings)

    interrupted_id = str(uuid.uuid4())
    try:
        call(InterruptedBatch(connection), "import_guest_lesson", "interrupted-user", now=3000,
             guest_session_id=interrupted_id, completed_steps=1, client_saved_at=1000)
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("interrupted batch unexpectedly succeeded")
    assert connection.execute("SELECT 1 FROM learner_profiles WHERE user_id='interrupted-user'").fetchone() is None
    assert connection.execute("SELECT 1 FROM guest_lesson_imports WHERE id=?", (interrupted_id,)).fetchone() is None
    assert call(connection, "import_guest_lesson", "interrupted-user", now=4000,
                guest_session_id=interrupted_id, completed_steps=1, client_saved_at=1000) == [1, 1, 1]


def check_staff_actions(connection, call):
    editor, reviewer, moderator, support = (
        ("curriculum_editor",), ("content_reviewer",), ("moderator",), ("support",)
    )

    def request(name, actor, role, now=2000, **values):
        return call(connection, name, actor, roles=role, now=now, **values)

    def audit_count():
        return connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]

    try:
        request("create_course", "forger", (), request_id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()), source_language="en", target_language="es", title="Forged")
    except PermissionError:
        pass
    else:
        raise AssertionError("ungated staff write")
    assert audit_count() == 0
    ids = {name: str(uuid.uuid4()) for name in ("course", "version", "lesson", "exercise", "release")}
    def rid():
        return str(uuid.uuid4())

    course = dict(request_id=rid(), course_id=ids["course"], source_language="en",
                  target_language="es", title="Original course")
    assert request("create_course", "ed", editor, **course) == [1, 1]
    assert request("create_course", "ed", editor, **course) == [0, 0]
    assert request("create_course", "ed", editor, request_id=rid(), **{k:v for k,v in course.items() if k != "request_id"}) == [0, 0]
    version = dict(request_id=rid(), version_id=ids["version"], course_id=ids["course"],
                   content_version=0, package_version="original-1")
    assert request("create_course_version", "ed", editor, **version) == [1, 1]
    lesson = dict(request_id=rid(), lesson_id=ids["lesson"], version_id=ids["version"],
                  stable_content_id="lesson-a", content_version=0, position=0,
                  title="Lesson", expected_updated_at=2000)
    assert request("create_lesson", "ed", editor, now=3000, **lesson) == [1, 1, 1]
    assert request("create_lesson", "ed", editor, now=4000, **lesson) == [0, 0, 0]
    bad_lesson = dict(lesson, request_id=rid(), lesson_id=rid(), stable_content_id="lesson-b",
                      expected_updated_at=3000)
    before = audit_count()
    assert request("create_lesson", "ed", editor, now=4000, **bad_lesson) == [0, 0, 0]
    assert audit_count() == before
    exercise = dict(request_id=rid(), exercise_id=ids["exercise"], lesson_id=ids["lesson"],
                    stable_content_id="exercise-a", content_version=0, position=0,
                    kind="recognition", evaluator_policy_version="policy-1", expected_updated_at=3000)
    assert request("create_exercise", "ed", editor, now=4000, **exercise) == [1, 1, 1]
    duplicate = dict(exercise, request_id=rid(), exercise_id=rid(), stable_content_id="exercise-b",
                     expected_updated_at=4000)
    before = audit_count()
    assert request("create_exercise", "ed", editor, now=5000, **duplicate) == [0, 0, 0]
    assert audit_count() == before
    transition = dict(request_id=rid(), version_id=ids["version"], expected_updated_at=4000)
    assert request("submit_version_for_review", "ed", editor, now=5000, **transition) == [1, 1]
    try:
        request("approve_course_version", "ed", editor, now=6000,
                request_id=rid(), version_id=ids["version"], expected_updated_at=5000)
    except PermissionError:
        pass
    else:
        raise AssertionError("editor approved a snapshot")
    assert request("approve_course_version", "reviewer", reviewer, now=6000,
                   request_id=rid(), version_id=ids["version"], expected_updated_at=5000) == [1, 1]
    assert request("publish_course_version", "moderator", moderator, now=7000,
                   request_id=rid(), release_id=ids["release"], course_id="course",
                   version_id=ids["version"], expected_updated_at=6000) == [0, 0, 0, 0]
    publish = dict(request_id=rid(), release_id=ids["release"], course_id=ids["course"],
                   version_id=ids["version"], expected_updated_at=6000)
    assert request("publish_course_version", "moderator", moderator, now=7000, **publish) == [1, 0, 1, 1]
    assert request("publish_course_version", "moderator", moderator, now=8000, **publish) == [0, 0, 0, 0]
    assert connection.execute("SELECT status FROM course_versions WHERE id=?", (ids["version"],)).fetchone() == ("published",)
    assert request("create_exercise", "ed", editor, now=8000,
                   **dict(exercise, request_id=rid(), exercise_id=rid(), position=1,
                          stable_content_id="exercise-new", expected_updated_at=7000)) == [0, 0, 0]
    report_id = connection.execute("SELECT id FROM content_reports WHERE user_id='alice'").fetchone()[0]
    try:
        request("list_staff_reports", "ed", editor, status="open")
    except PermissionError:
        pass
    else:
        raise AssertionError("editor read support queue")
    assert any(row[0] == report_id for row in request("list_staff_reports", "support", support, status="open"))
    triage = dict(request_id=rid(), report_id=report_id, course_id="course",
                  new_status="reviewing", expected_updated_at=6000)
    assert request("update_report_status", "support", support, now=8000,
                   **dict(triage, course_id=ids["course"])) == [0, 0]
    assert request("update_report_status", "support", support, now=8000, **triage) == [1, 1]
    assert request("update_report_status", "support", support, now=9000, **triage) == [0, 0]
    assert request("update_report_status", "support", support, now=9000,
                   request_id=rid(), report_id=report_id, course_id="course",
                   new_status="resolved", expected_updated_at=8000) == [1, 1]
    retire = dict(request_id=rid(), release_id=ids["release"], course_id=ids["course"],
                  expected_updated_at=7000)
    assert request("retire_course_release", "moderator", moderator, now=9000, **retire) == [1, 1, 1]
    assert request("retire_course_release", "moderator", moderator, now=10000, **retire) == [0, 0, 0]
    assert connection.execute("SELECT status FROM course_releases WHERE id=?", (ids["release"],)).fetchone() == ("retired",)
    assert connection.execute("SELECT COUNT(*) FROM audit_rows WHERE actor_user_id='moderator' AND action IN ('publish','retire')").fetchone() == (2,)
    assert connection.execute("SELECT subject_user_id FROM audit_rows WHERE resource_id=? AND action='triage'", (report_id,)).fetchall() == [("alice",), ("alice",)]
    next_version = rid()
    skipped_version = dict(request_id=rid(), version_id=next_version, course_id="course",
                           content_version=3, package_version="original-2")
    before = audit_count()
    assert request("create_course_version", "ed", editor, now=11000, **skipped_version) == [0, 0]
    assert audit_count() == before
    assert request("create_course_version", "ed", editor, now=11000,
                   **dict(skipped_version, content_version=2)) == [1, 1]
    next_lesson, next_exercise = rid(), rid()
    assert request("create_lesson", "ed", editor, now=12000, request_id=rid(),
                   lesson_id=next_lesson, version_id=next_version, stable_content_id="lesson-next",
                   content_version=2, position=0, title="Next lesson", expected_updated_at=11000) == [1, 1, 1]
    assert request("create_exercise", "ed", editor, now=13000, request_id=rid(),
                   exercise_id=next_exercise, lesson_id=next_lesson, stable_content_id="exercise-next",
                   content_version=2, position=0, kind="recognition",
                   evaluator_policy_version="policy-2", expected_updated_at=12000) == [1, 1, 1]
    assert request("submit_version_for_review", "ed", editor, now=14000, request_id=rid(),
                   version_id=next_version, expected_updated_at=13000) == [1, 1]
    assert request("return_version_to_draft", "reviewer", reviewer, now=15000,
                   request_id=rid(), version_id=next_version, expected_updated_at=14000) == [1, 1]
    assert request("submit_version_for_review", "ed", editor, now=16000, request_id=rid(),
                   version_id=next_version, expected_updated_at=15000) == [1, 1]
    assert request("approve_course_version", "reviewer", reviewer, now=17000,
                   request_id=rid(), version_id=next_version, expected_updated_at=16000) == [1, 1]
    next_release = rid()
    assert request("publish_course_version", "moderator", moderator, now=18000,
                   request_id=rid(), release_id=next_release, course_id="course",
                   version_id=next_version, expected_updated_at=17000) == [1, 1, 1, 1]
    assert connection.execute("SELECT status FROM course_releases WHERE id='r1'").fetchone() == ("superseded",)
    assert connection.execute("SELECT release_number,status FROM course_releases WHERE id=?", (next_release,)).fetchone() == (2, "active")
    assert audit_count() == 18
    audit = connection.execute("SELECT actor_user_id,subject_user_id,detail_json FROM audit_rows WHERE resource_id=? AND action='triage' ORDER BY created_at", (report_id,)).fetchall()
    assert [(actor, subject, json.loads(detail)["to"]) for actor, subject, detail in audit] == [
        ("support", "alice", "reviewing"), ("support", "alice", "resolved")
    ]
    assert all(row[0] and row[1] for row in connection.execute(
        "SELECT actor_user_id,detail_json FROM audit_rows"))
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    main()
