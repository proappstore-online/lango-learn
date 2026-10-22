"""Execute registered PAS actions against the real migrations with two identities."""

import json
import re
import sqlite3
import tempfile
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
    "create_course_locale", "create_course_map", "create_course_unit",
    "place_lesson_in_unit", "add_lesson_prerequisite",
    "create_objective", "create_lexeme", "create_phrase", "create_grammar_point",
    "create_pronunciation_pattern", "create_register_tag", "create_confusable_pair",
    "link_objective_lexeme", "link_objective_phrase", "link_objective_grammar_point",
    "link_objective_pronunciation_pattern", "link_objective_register_tag",
    "link_objective_confusable_pair", "add_objective_prerequisite",
    "update_objective", "read_objective_graph",
}

ROLE_ACTIONS = json.loads((ROOT / "contracts/staff-roles.json").read_text())
assert set(ROLE_ACTIONS) == {"curriculum_editor", "content_reviewer", "support", "moderator"}
STAFF_ROLES = {action: role for role, actions in ROLE_ACTIONS.items() for action in actions}
assert sum(map(len, ROLE_ACTIONS.values())) == len(STAFF_ROLES)


def execute(connection, tool, user, *, now=1000, roles=(), **params):
    if tool.get("requires_auth") and not user:
        raise PermissionError(f"{tool['name']}: PAS session required")
    required_roles = tool.get("auth", {}).get("app_roles", [])
    if required_roles and not set(required_roles).intersection(roles):
        raise PermissionError(f"{tool['name']}: PAS app role required")
    # PAS supplies these bindings from the session, never from request data.
    if set(params) & MAGIC:
        raise ValueError("request cannot override PAS session bindings")
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
            assert "platform_roles" not in auth, name
            assert auth.get("caller_unscoped", {}).get("reason"), name
            assert "role" not in tool.get("params", {}), name
            assert "roles" not in tool.get("params", {}), name
            assert "app_roles" not in tool.get("params", {}), name
        else:
            assert not tool.get("auth", {}).get("app_roles"), name
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
    with tempfile.TemporaryDirectory() as directory:
        for mode in ("fresh", "upgraded"):
            path = Path(directory) / f"{mode}.sqlite"
            migrations = load_migrations()
            if mode == "upgraded":
                with sqlite3.connect(path) as legacy:
                    legacy.execute("PRAGMA foreign_keys = ON")
                    apply_migrations(legacy, migrations[:-1])
                    legacy.execute("INSERT INTO items VALUES ('legacy','alice','Before upgrade',NULL,500)")
            with sqlite3.connect(path) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                apply_migrations(connection, migrations)
                apply_migrations(connection, migrations)
                assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
                if mode == "upgraded":
                    assert connection.execute("SELECT title FROM items WHERE id='legacy'").fetchone() == ("Before upgrade",)
                run_contracts(connection, actions)
                check_course_map(connection, actions)
                check_objective_graph(connection, actions)
            # Reopen the file so the result is checked as durable data.
            with sqlite3.connect(path) as persisted:
                persisted.execute("PRAGMA foreign_keys = ON")
                assert persisted.execute("PRAGMA foreign_key_check").fetchall() == []
                assert persisted.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] >= 18
                assert persisted.execute("SELECT COUNT(*) FROM guest_lesson_imports").fetchone()[0] >= 4
                assert persisted.execute("SELECT COUNT(*) FROM course_releases WHERE status='superseded'").fetchone() == (1,)
                assert persisted.execute("SELECT COUNT(*) FROM course_releases WHERE status='retired'").fetchone() == (2,)
                assert persisted.execute("SELECT COUNT(*) FROM course_releases WHERE status='active'").fetchone() == (1,)
                assert persisted.execute("SELECT COUNT(*) FROM exercise_attempts WHERE user_id='alice'").fetchone() == (2,)
                assert persisted.execute("SELECT COUNT(*) FROM exercise_attempts WHERE user_id='bob'").fetchone() == (0,)
                assert persisted.execute("SELECT COUNT(*) FROM objective WHERE course_version_id='graph-v1'").fetchone() == (2,)
    print(f"Action authorization gate passed: {len(tools)} actions on fresh and upgraded persisted databases")


def run_contracts(connection, actions):
    def call(connection, name, user, **kwargs):
        return execute(connection, actions[name], user, **kwargs)
    seed(connection)
    for name in actions:
        try:
            call(connection, name, None)
        except PermissionError:
            pass
        else:
            raise AssertionError(f"signed-out caller used {name}")
    try:
        call(connection, "get_learner_bootstrap", "mallory", __user_id="alice")
    except ValueError:
        pass
    else:
        raise AssertionError("request overrode PAS identity")
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
    assert call(connection, "get_learner_bootstrap", "bob")[0][9] == bob_session
    assert call(connection, "get_learner_bootstrap", "alice")[0][9] == alice_session
    assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=1000) == 0
    submit = dict(attempt_id=str(uuid.uuid4()), session_id=alice_session, exercise_id="e1", expected_updated_at=1000)
    assert call(connection, "submit_exercise", "bob", **submit) == [0, 0]
    assert call(connection, "submit_exercise", "alice", **{**submit, "exercise_id": "e3"}) == [0, 0]
    assert call(connection, "submit_exercise", "alice", **{**submit, "expected_updated_at": 999}) == [0, 0]
    assert call(connection, "submit_exercise", "alice", now=1000, **submit) == [0, 0]
    assert call(connection, "submit_exercise", "alice", now=2000, **{**submit, "attempt_id": "not-a-uuid"}) == [0, 0]
    assert call(connection, "submit_exercise", "alice", now=2000, **submit) == [1, 1]
    assert call(connection, "submit_exercise", "alice", now=3000, **submit) == [0, 0]
    assert call(connection, "submit_exercise", "alice", now=3000, **{**submit, "attempt_id": str(uuid.uuid4())}) == [0, 0]
    assert connection.execute("SELECT attempt_number,evaluator_policy_version,result_code FROM exercise_attempts WHERE id=?", (submit['attempt_id'],)).fetchone() == (1, "policy-1", "pending_evaluation")
    assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=2000) == 0
    assert call(connection, "submit_exercise", "alice", now=3000, attempt_id=str(uuid.uuid4()), session_id=alice_session, exercise_id="e2", expected_updated_at=2000) == [1, 1]
    assert call(connection, "complete_lesson", "bob", session_id=alice_session, expected_updated_at=3000) == 0
    assert call(connection, "complete_lesson", "alice", session_id=alice_session, expected_updated_at=2000) == 0
    assert call(connection, "complete_lesson", "alice", now=3000, session_id=alice_session, expected_updated_at=3000) == 0
    assert call(connection, "complete_lesson", "alice", now=4000, session_id=alice_session, expected_updated_at=3000) == 1
    assert call(connection, "complete_lesson", "alice", now=5000, session_id=alice_session, expected_updated_at=4000) == 0
    assert call(connection, "get_next_lesson", "alice")[0][0] == "l2"
    assert call(connection, "get_next_lesson", "bob")[0][0] == "l1"
    assert call(connection, "resume_lesson", "alice", session_id=alice_session) == []
    assert call(connection, "update_preferences", "bob", source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=999) == 0
    assert call(connection, "update_preferences", "alice", now=1000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=1000) == 0
    assert call(connection, "update_preferences", "alice", now=5000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=1000) == 1
    assert call(connection, "update_preferences", "alice", now=6000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=1000) == 0
    assert call(connection, "update_preferences", "bob", now=6000, source_language="en", target_language="es", region=None, timezone="UTC", reminders_enabled=1, expected_updated_at=5000) == 0
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
    check_staff_role_matrix(connection, actions)
    check_guest_imports(connection, call)

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


def check_staff_role_matrix(connection, actions):
    """The platform role projection, not caller data or team status, gates every action."""
    def snapshot():
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                     for table in ("courses", "course_versions", "lessons", "exercises",
                                   "course_releases", "content_reports", "audit_rows"))

    before = snapshot()
    identities = {
        "member": (),
        "platform-admin": ("admin",),
        "team-owner": ("owner",),
        **{role: (role,) for role in ROLE_ACTIONS},
    }
    for name, required in STAFF_ROLES.items():
        tool = actions[name]
        for actor, projected_roles in identities.items():
            if required in projected_roles:
                continue
            try:
                execute(connection, tool, actor, roles=projected_roles,
                        request_id=str(uuid.uuid4()), role=required,
                        app_roles=[required], platform_role="admin", team_role="owner")
            except PermissionError:
                pass
            else:
                raise AssertionError(f"{actor} crossed {required} boundary on {name}")
            assert snapshot() == before, (name, actor)
        try:
            execute(connection, tool, None, roles=(required,), request_id=str(uuid.uuid4()))
        except PermissionError:
            pass
        else:
            raise AssertionError(f"signed-out caller used {name}")
        assert snapshot() == before, name

    # Multiple grants combine without turning one grant into another. The mixed
    # actor can use support's read action, while an editor alone cannot.
    mixed = ("curriculum_editor", "support")
    reports = execute(connection, actions["list_staff_reports"], "mixed", roles=mixed,
                      status="resolved")
    assert reports
    try:
        execute(connection, actions["approve_course_version"], "mixed", roles=mixed,
                request_id=str(uuid.uuid4()))
    except PermissionError:
        pass
    else:
        raise AssertionError("mixed editor/support grant acquired reviewer permission")
    assert snapshot() == before

    # A failure after an audit insert must roll the whole staff batch back.
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
            if self.statements == 2:
                raise sqlite3.OperationalError("synthetic staff write failure")
            return self.db.execute(sql, bindings)

    course_id, request_id = str(uuid.uuid4()), str(uuid.uuid4())
    values = dict(request_id=request_id, course_id=course_id, source_language="en",
                  target_language="es", title="Failure fixture")
    try:
        execute(InterruptedBatch(connection), actions["create_course"], "mixed",
                roles=mixed, now=20000, **values)
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("interrupted staff batch unexpectedly succeeded")
    assert snapshot() == before
    assert execute(connection, actions["create_course"], "mixed", roles=mixed,
                   now=20000, **values) == [1, 1]
    assert execute(connection, actions["create_course"], "mixed", roles=mixed,
                   now=21000, **values) == [0, 0]
    assert connection.execute("SELECT actor_user_id FROM audit_rows WHERE id=?",
                              (request_id,)).fetchone() == ("mixed",)

    # The same app role in a separate app database cannot resolve a foreign
    # report or release ID. No local resource or audit row is created.
    foreign_report = connection.execute("SELECT id FROM content_reports LIMIT 1").fetchone()[0]
    with tempfile.TemporaryDirectory() as directory:
        with sqlite3.connect(Path(directory) / "other-app.sqlite") as other_app:
            other_app.execute("PRAGMA foreign_keys = ON")
            apply_migrations(other_app, load_migrations())
            assert execute(other_app, actions["list_staff_reports"], "support",
                           roles=("support",), status="resolved") == []
            assert execute(other_app, actions["update_report_status"], "support",
                           roles=("support",), now=22000, request_id=str(uuid.uuid4()),
                           report_id=foreign_report, course_id="course",
                           new_status="reviewing", expected_updated_at=1000) == [0, 0]
            assert execute(other_app, actions["retire_course_release"], "moderator",
                           roles=("moderator",), now=22000, request_id=str(uuid.uuid4()),
                           release_id="r1", course_id="course",
                           expected_updated_at=1000) == [0, 0, 0]
            assert other_app.execute("SELECT COUNT(*) FROM audit_rows").fetchone() == (0,)




def check_course_map(connection, actions):
    """Persisted synthetic curriculum contract, including rejected transactions."""
    editor = ("curriculum_editor",)
    def call(name, *, actor="editor", roles=editor, now=2000, **values):
        return execute(connection, actions[name], actor, roles=roles, now=now, **values)
    def rid():
        return str(uuid.uuid4())
    def rejects(action, **values):
        before = connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]
        try:
            call(action, **values)
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(f"expected atomic rejection: {action}")
        assert connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] == before

    # Canonicalize case without dropping script or region. The two variants
    # remain separate keys; malformed components roll the audit back too.
    en = dict(request_id=rid(), language="EN", script="latn", region="us")
    ar = dict(request_id=rid(), language="AR", script="arab", region="eg")
    assert call("create_course_locale", **en) == [1, 1]
    assert call("create_course_locale", **en) == [0, 0]
    assert call("create_course_locale", **ar) == [1, 1]
    assert connection.execute("SELECT tag FROM course_locales ORDER BY tag").fetchall() == [("ar-Arab-EG",), ("en-Latn-US",)]
    rejects("create_course_locale", request_id=rid(), language="e1", script="Latn", region="US")
    rejects("create_course_locale", request_id=rid(), language="en", script="Latin", region="US")
    rejects("create_course_locale", request_id=rid(), language="en", script="Latn", region="USA1")
    assert call("create_course_locale", request_id=rid(), language="en", script="Latn", region="GB") == [1, 1]
    assert connection.execute("SELECT COUNT(*) FROM course_locales").fetchone() == (3,)

    connection.execute("INSERT INTO courses VALUES ('map-course','en','ar','Synthetic course',1000,1000)")
    connection.execute("INSERT INTO course_versions VALUES ('map-v1','map-course',1,'synthetic-1','draft',1000,1000)")
    for position in range(3):
        connection.execute("INSERT INTO lessons VALUES (?, 'map-v1', ?, 1, ?, ?, 1000)",
                           (f"map-l{position}", f"stable-{position}", position, f"Synthetic {position}"))
    mapping = dict(request_id=rid(), map_id=rid(), course_id="map-course",
                   source_tag="en-Latn-US", target_tag="ar-Arab-EG")
    try:
        call("create_course_map", roles=(), **mapping)
    except PermissionError:
        pass
    else:
        raise AssertionError("missing editor role was allowed")
    assert call("create_course_map", **mapping) == [1, 1]
    assert call("create_course_map", **mapping) == [0, 0]
    assert connection.execute("SELECT release_state FROM course_map_release_state WHERE course_id='map-course'").fetchone() == ("draft",)
    assert call("create_course_map", request_id=rid(), map_id=rid(), course_id="map-course",
                source_tag="en-Latn-GB", target_tag="ar-Arab-EG") == [0, 0]
    try:
        connection.execute("UPDATE course_maps SET target_tag='en-Latn-GB' WHERE course_id='map-course'")
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("course map changed")

    unit = dict(request_id=rid(), unit_id=rid(), version_id="map-v1", stable_content_id="unit-1",
                position=0, title="Synthetic unit", expected_updated_at=1000)
    assert call("create_course_unit", now=2000, **unit) == [1, 1, 1]
    assert call("create_course_unit", now=3000, **unit) == [0, 0, 0]
    assert call("create_course_unit", now=3000, **{**unit, "request_id":rid(), "unit_id":rid()}) == [0, 0, 0]
    placement = dict(request_id=rid(), placement_id=rid(), version_id="map-v1", unit_id=unit["unit_id"],
                     lesson_id="map-l0", position=0, expected_updated_at=2000)
    assert call("place_lesson_in_unit", now=3000, **placement) == [1, 1, 1]
    assert call("place_lesson_in_unit", now=4000, **placement) == [0, 0, 0]
    missing = dict(request_id=rid(), prerequisite_id=rid(), version_id="map-v1",
                   lesson_id="map-l1", prerequisite_lesson_id="missing", expected_updated_at=3000)
    assert call("add_lesson_prerequisite", now=4000, **missing) == [0, 0, 0]
    first = {**missing, "request_id":rid(), "prerequisite_lesson_id":"map-l0"}
    assert call("add_lesson_prerequisite", now=4000, **first) == [1, 1, 1]
    second = {**first, "request_id":rid(), "prerequisite_id":rid(), "lesson_id":"map-l2",
              "prerequisite_lesson_id":"map-l1", "expected_updated_at":4000}
    assert call("add_lesson_prerequisite", now=5000, **second) == [1, 1, 1]
    cycle = {**second, "request_id":rid(), "prerequisite_id":rid(), "lesson_id":"map-l0",
             "prerequisite_lesson_id":"map-l2", "expected_updated_at":5000}
    rejects("add_lesson_prerequisite", now=6000, **cycle)
    # Composite foreign keys reject a lesson from another version even when both
    # IDs exist; the existing course shell has a distinct published snapshot.
    connection.execute("INSERT INTO course_versions VALUES ('map-v2','map-course',2,'synthetic-2','draft',1000,1000)")
    connection.execute("INSERT INTO lessons VALUES ('map-foreign','map-v2','foreign',2,0,'Foreign',1000)")
    assert call("place_lesson_in_unit", now=6000, request_id=rid(), placement_id=rid(),
                version_id="map-v1", unit_id=unit["unit_id"], lesson_id="map-foreign",
                position=1, expected_updated_at=5000) == [0, 0, 0]
    assert call("add_lesson_prerequisite", now=6000, request_id=rid(), prerequisite_id=rid(),
                version_id="map-v1", lesson_id="map-l0", prerequisite_lesson_id="map-foreign",
                expected_updated_at=5000) == [0, 0, 0]
    assert call("add_lesson_prerequisite", now=6000, request_id=rid(), prerequisite_id=rid(),
                version_id="map-v1", lesson_id="map-l0", prerequisite_lesson_id="map-l0",
                expected_updated_at=5000) == [0, 0, 0]
    assert connection.execute("SELECT COUNT(*) FROM lesson_prerequisites").fetchone() == (2,)
    assert connection.execute("SELECT updated_at FROM course_versions WHERE id='map-v1'").fetchone() == (5000,)
    connection.execute("UPDATE course_versions SET status='review',updated_at=6000 WHERE id='map-v1'")
    assert call("create_course_unit", now=7000, **{**unit, "request_id":rid(), "unit_id":rid(),
                                                    "position":1, "expected_updated_at":6000}) == [0, 0, 0]
    for sql in ("UPDATE course_versions SET package_version='changed' WHERE id='map-v1'",
                "UPDATE course_versions SET status='published' WHERE id='map-v1'",
                "DELETE FROM course_units WHERE id='" + unit["unit_id"] + "'"):
        try:
            connection.execute(sql)
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(f"immutable or transition contract failed: {sql}")
    connection.execute("UPDATE course_versions SET status='approved',updated_at=7000 WHERE id='map-v1'")
    connection.execute("UPDATE course_versions SET status='published',updated_at=8000 WHERE id='map-v1'")
    connection.execute("INSERT INTO course_releases VALUES ('map-release','map-course','map-v1',1,'active','moderator',8000,8000)")
    assert connection.execute("SELECT release_state FROM course_map_release_state WHERE course_id='map-course'").fetchone() == ("published",)
    connection.execute("UPDATE course_releases SET status='retired',updated_at=9000 WHERE id='map-release'")
    assert connection.execute("SELECT release_state FROM course_map_release_state WHERE course_id='map-course'").fetchone() == ("deprecated",)
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

def check_objective_graph(connection, actions):
    """Exercise every authoring edge against persisted, version-pinned fixtures."""
    editor = ("curriculum_editor",)
    checkpoint = 1000

    def rid():
        return str(uuid.uuid4())

    def call(action_name, *, roles=editor, now=None, **values):
        return execute(connection, actions[action_name], "graph-editor", roles=roles,
                       now=checkpoint + 1000 if now is None else now, **values)

    def write(action_name, **values):
        nonlocal checkpoint
        request_id = rid()
        result = call(action_name, request_id=request_id, version_id="graph-v1",
                      expected_updated_at=checkpoint, **values)
        assert result == [1, 1, 1], (action_name, result)
        checkpoint += 1000
        return request_id

    def denied(action_name, values):
        before = connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]
        for role in ((), ("support",), ("moderator",), ("content_reviewer",)):
            try:
                call(action_name, roles=role, **values)
            except PermissionError:
                pass
            else:
                raise AssertionError(f"{action_name} allowed role {role}")
        assert connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] == before

    def no_write(action_name, values):
        before = connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]
        assert call(action_name, **values) == [0, 0, 0], action_name
        assert connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] == before

    # Both locales are tied to the actual course pair, not merely valid tags.
    for tag in ("en", "es", "fr"):
        assert call("create_course_locale", request_id=rid(), language=tag,
                    script="", region="") == [1, 1]
    connection.execute("INSERT INTO courses VALUES ('graph-course','en','es','Synthetic graph',1000,1000)")
    connection.execute("INSERT INTO course_versions VALUES ('graph-v1','graph-course',1,'graph-1','draft',1000,1000)")
    connection.execute("INSERT INTO lessons VALUES ('graph-lesson','graph-v1','graph-lesson',1,0,'Synthetic lesson',1000)")
    assert call("create_course_map", request_id=rid(), map_id=rid(),
                course_id="graph-course", source_tag="en", target_tag="es") == [1, 1]

    first = dict(objective_id=rid(), lesson_id="graph-lesson", label="Ask a question",
                 description="Use a phrase in context", locale="es", sort_order=1)
    second = dict(objective_id=rid(), lesson_id=None, label="Greet a person",
                  description="Use a greeting in context", locale="es", sort_order=0)
    denied("create_objective", {**first, "request_id":rid(), "version_id":"graph-v1",
                                "expected_updated_at":checkpoint})
    first_request = write("create_objective", **first)
    no_write("create_objective", {**first, "request_id":first_request,
                                  "version_id":"graph-v1", "expected_updated_at":1000})
    write("create_objective", **second)
    component_specs = [
        ("lexeme", dict(form="hola", lemma="hola", part_of_speech="interjection")),
        ("phrase", dict(text="Hola, Ana")),
        ("grammar_point", dict(label="Vocative", description="Address a person")),
        ("pronunciation_pattern", dict(pattern="/ola/", example="hola")),
        ("register_tag", dict(name="informal", description="Familiar greeting")),
        ("confusable_pair", dict(item_a="hola", item_b="ola", note="The initial letter differs")),
    ]
    component_ids = {}
    for component, fields in component_specs:
        entity_id = rid()
        component_ids[component] = entity_id
        values = {component + "_id": entity_id, "locale":"es", "sort_order":0, **fields}
        denied("create_" + component, {**values, "request_id":rid(),
                                       "version_id":"graph-v1", "expected_updated_at":checkpoint})
        write("create_" + component, **values)

    for index, (component, _) in enumerate(component_specs):
        name = "link_objective_" + component
        edge_table = {"grammar_point":"objective_grammar", "pronunciation_pattern":"objective_pronunciation",
                      "register_tag":"objective_register", "confusable_pair":"objective_confusable"}.get(component, "objective_" + component)
        values = {edge_table + "_id":rid(), "objective_id":first["objective_id"],
                  component + "_id":component_ids[component], "rel_type":"teaches",
                  "sort_order":index}
        denied(name, {**values, "request_id":rid(), "version_id":"graph-v1",
                      "expected_updated_at":checkpoint})
        write(name, **values)
        no_write(name, {**values, "request_id":rid(), "version_id":"graph-v1",
                        "expected_updated_at":checkpoint})

    extra_lexeme = rid()
    write("create_lexeme", lexeme_id=extra_lexeme, form="buenos", lemma="bueno",
          part_of_speech="adjective", locale="es", sort_order=1)
    write("link_objective_lexeme", objective_lexeme_id=rid(), objective_id=first["objective_id"],
          lexeme_id=extra_lexeme, rel_type="reinforces", sort_order=1)
    source_lexeme = rid()
    write("create_lexeme", lexeme_id=source_lexeme, form="hello", lemma="hello",
          part_of_speech="interjection", locale="en", sort_order=2)
    wrong_locale = dict(objective_lexeme_id=rid(), objective_id=first["objective_id"],
                        lexeme_id=source_lexeme, rel_type="teaches", sort_order=2)
    no_write("link_objective_lexeme", {**wrong_locale, "request_id":rid(),
                                       "version_id":"graph-v1", "expected_updated_at":checkpoint})
    no_write("link_objective_lexeme", {**wrong_locale, "request_id":rid(),
                                       "version_id":"map-v2", "expected_updated_at":1000})

    missing = dict(objective_lexeme_id=rid(), objective_id=first["objective_id"],
                   lexeme_id="missing", rel_type="teaches", sort_order=10)
    no_write("link_objective_lexeme", {**missing, "request_id":rid(),
                                       "version_id":"graph-v1", "expected_updated_at":checkpoint})
    edge = dict(prerequisite_id=rid(), objective_id=first["objective_id"],
                prerequisite_objective_id=second["objective_id"], sort_order=0)
    denied("add_objective_prerequisite", {**edge, "request_id":rid(),
                                         "version_id":"graph-v1", "expected_updated_at":checkpoint})
    write("add_objective_prerequisite", **edge)
    no_write("add_objective_prerequisite", {**edge, "request_id":rid(),
                                           "version_id":"graph-v1", "expected_updated_at":checkpoint})
    before = connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]
    reverse = {**edge, "prerequisite_id":rid(), "objective_id":second["objective_id"],
               "prerequisite_objective_id":first["objective_id"]}
    try:
        call("add_objective_prerequisite", request_id=rid(), version_id="graph-v1",
             expected_updated_at=checkpoint, **reverse)
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("objective prerequisite cycle was accepted")
    assert connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] == before
    assert connection.execute("SELECT COUNT(*) FROM objective_prerequisite").fetchone() == (1,)

    update = {**first, "label":"Ask a clear question", "request_id":rid(),
              "version_id":"graph-v1", "expected_updated_at":1000}
    denied("update_objective", update)
    no_write("update_objective", update)
    update["expected_updated_at"] = checkpoint
    before = connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0]
    assert call("update_objective", now=checkpoint, **update) == [0, 0, 0]
    assert connection.execute("SELECT COUNT(*) FROM audit_rows").fetchone()[0] == before
    assert call("update_objective", **update) == [1, 1, 1]
    checkpoint += 1000
    no_write("update_objective", update)
    assert connection.execute("SELECT label,updated_by FROM objective WHERE id=?",
                              (first["objective_id"],)).fetchone() == ("Ask a clear question", "graph-editor")

    page = call("read_objective_graph", version_id="graph-v1", limit=1,
                after_sort_order=None, after_id=None)
    assert len(page) == 1 and page[0][0] == second["objective_id"]
    rest = call("read_objective_graph", version_id="graph-v1", limit=1,
                after_sort_order=page[0][6], after_id=page[0][0])
    assert len(rest) == 1 and rest[0][0] == first["objective_id"]
    for offset, (component, _) in enumerate(component_specs):
        assert json.loads(rest[0][7 + offset])[0]["id"] == component_ids[component]
    assert [x["id"] for x in json.loads(rest[0][7])] == [component_ids["lexeme"], extra_lexeme]
    assert json.loads(rest[0][-1])[0]["id"] == second["objective_id"]
    assert call("read_objective_graph", version_id="graph-v1", limit=1,
                after_sort_order=rest[0][6], after_id=rest[0][0]) == []
    assert call("read_objective_graph", version_id="map-v2", limit=10,
                after_sort_order=None, after_id=None) == []
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    main()
