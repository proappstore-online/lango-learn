"""Check committed PAS D1 migrations on a fresh SQLite database."""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = re.compile(r"^CREATE\s+(?:(?:TABLE|INDEX|UNIQUE\s+INDEX|TRIGGER|VIEW)\s+IF\s+NOT\s+EXISTS)\b", re.I)


def load_migrations():
    migrations = json.loads((ROOT / "migrations.json").read_text())["migrations"]
    assert migrations, "at least one migration is required"
    names = [item["name"] for item in migrations]
    assert len(names) == len(set(names)), "migration names must be unique"
    assert names == sorted(names), "migration names must be ordered"
    for item in migrations:
        statements = []
        pending = ""
        for line in item["sql"].splitlines(keepends=True):
            pending += line
            if sqlite3.complete_statement(pending):
                statements.append(pending.strip().rstrip(";"))
                pending = ""
        if pending.strip():
            assert sqlite3.complete_statement(pending + ";"), f"{item['name']} has incomplete SQL"
            statements.append(pending.strip())
        assert statements, f"{item['name']} has no SQL"
        for statement in statements:
            assert ALLOWED.match(statement), f"{item['name']} has a non-additive statement: {statement}"
    return migrations


def apply_migrations(connection, migrations):
    for item in migrations:
        connection.executescript(item["sql"])


def check_learning_model(connection):
    required = {
        "learner_profiles", "learner_preferences", "courses", "course_versions",
        "lessons", "exercises", "learning_sessions", "exercise_attempts",
        "learning_exposures", "review_states", "content_reports", "course_releases",
        "audit_rows", "guest_lesson_imports", "course_locales", "course_maps",
        "course_units", "course_unit_lessons", "lesson_prerequisites",
    }
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert required <= tables, f"missing learning tables: {required - tables}"
    required_indexes = {
        "idx_course_versions_status", "idx_lessons_order", "idx_exercises_order",
        "idx_sessions_resume", "idx_attempts_history", "idx_exposures_history",
        "idx_review_due", "idx_reports_queue", "idx_reports_user",
        "idx_active_release", "idx_releases_history", "idx_audit_resource",
        "idx_audit_actor", "idx_one_active_lesson_session", "idx_one_review_exposure",
        "idx_guest_imports_user", "idx_course_maps_pair", "idx_course_units_order",
        "idx_unit_lessons_order", "idx_lesson_prerequisites",
    }
    indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
    assert required_indexes <= indexes, f"missing learning indexes: {required_indexes - indexes}"
    owned = required & {"learner_profiles", "learner_preferences", "learning_sessions",
                        "exercise_attempts", "learning_exposures", "review_states", "content_reports", "guest_lesson_imports"}
    for table in owned:
        columns = {row[1]: row for row in connection.execute(f"PRAGMA table_info({table})")}
        assert columns["user_id"][3] == 1, f"{table}.user_id must be required"
    for table in required:
        columns = {row[1]: row for row in connection.execute(f"PRAGMA table_info({table})")}
        key = "tag" if table == "course_locales" else "id"
        assert columns[key][2].upper() == "TEXT" and columns[key][5] == 1
        assert columns["created_at"][2].upper() == "INTEGER" and columns["created_at"][3] == 1

    # Exercise the relationships used by later scoped actions with two users and
    # two immutable course snapshots. SQLite foreign keys are explicitly enabled.
    for user in ("alice", "bob"):
        connection.execute("INSERT INTO learner_profiles VALUES (?, ?, NULL, 1000, 1000)", (f"profile-{user}", user))
    connection.execute("INSERT INTO learner_preferences (id,user_id,created_at,updated_at) "
                       "VALUES ('preferences-a','alice',1000,1000)")
    assert connection.execute("SELECT reminders_enabled FROM learner_preferences WHERE user_id='alice'").fetchone() == (0,)
    connection.execute("INSERT INTO courses VALUES ('course', 'en', 'es', 'Course', 1000, 1000)")
    for version in (1, 2):
        connection.execute("INSERT INTO course_versions VALUES (?, 'course', ?, 'package-1', 'published', 1000, 1000)",
                           (f"version-{version}", version))
        connection.execute("INSERT INTO lessons VALUES (?, ?, 'lesson-stable', ?, 0, 'Lesson', 1000)",
                           (f"lesson-{version}", f"version-{version}", version))
        connection.execute("INSERT INTO exercises VALUES (?, ?, 'exercise-stable', ?, 0, 'recognition', 'policy-1', 1000)",
                           (f"exercise-{version}", f"lesson-{version}", version))
    connection.execute("INSERT INTO learning_sessions (id,user_id,course_version_id,lesson_id,started_at,created_at,updated_at) "
                       "VALUES ('session-a','alice','version-1','lesson-1',1000,1000,1000)")
    connection.execute("INSERT INTO learning_sessions (id,user_id,course_version_id,lesson_id,started_at,created_at,updated_at) "
                       "VALUES ('session-b','bob','version-2','lesson-2',1000,1000,1000)")
    connection.execute("INSERT INTO exercise_attempts (id,user_id,session_id,lesson_id,exercise_id,attempt_number,evaluator_policy_version,result_code,created_at) "
                       "VALUES ('attempt-a','alice','session-a','lesson-1','exercise-1',1,'policy-1','correct',1000)")
    connection.execute("INSERT INTO learning_exposures (id,user_id,session_id,lesson_id,exercise_id,exposure_kind,created_at) "
                       "VALUES ('exposure-a','alice','session-a','lesson-1','exercise-1','prompt',1000)")
    connection.execute("INSERT INTO review_states (id,user_id,course_id,stable_content_id,source_exercise_id,created_at,updated_at) "
                       "VALUES ('review-a','alice','course','exercise-stable','exercise-1',1000,1000)")
    connection.execute("INSERT INTO content_reports (id,user_id,exercise_id,category,created_at,updated_at) "
                       "VALUES ('report-a','alice','exercise-1','answer',1000,1000)")
    connection.execute("INSERT INTO course_releases (id,course_id,course_version_id,release_number,status,published_by_user_id,created_at,updated_at) "
                       "VALUES ('release-1','course','version-1',1,'active','editor',1000,1000)")
    connection.execute("INSERT INTO audit_rows (id,actor_user_id,resource_type,resource_id,action,created_at) "
                       "VALUES ('audit-1','editor','course_release','release-1','publish',1000)")
    connection.execute("INSERT INTO guest_lesson_imports VALUES ('guest-a','alice','sample-greetings',1,2,'imported',1000,1000)")

    def rejects(sql):
        try:
            connection.execute(sql)
        except sqlite3.IntegrityError:
            return
        raise AssertionError(f"expected integrity rejection: {sql}")

    rejects("INSERT INTO learning_sessions (id,user_id,course_version_id,lesson_id,started_at,created_at,updated_at) "
            "VALUES ('bad-version','alice','version-2','lesson-1',1000,1000,1000)")
    rejects("INSERT INTO exercise_attempts (id,user_id,session_id,lesson_id,exercise_id,attempt_number,evaluator_policy_version,result_code,created_at) "
            "VALUES ('bad-owner','bob','session-a','lesson-1','exercise-1',1,'policy-1','correct',1000)")
    rejects("INSERT INTO exercise_attempts (id,user_id,session_id,lesson_id,exercise_id,attempt_number,evaluator_policy_version,result_code,created_at) "
            "VALUES ('bad-exercise','alice','session-a','lesson-1','exercise-2',1,'policy-1','correct',1000)")
    rejects("INSERT INTO learning_exposures (id,user_id,session_id,lesson_id,exercise_id,exposure_kind,created_at) "
            "VALUES ('bad-exposure','bob','session-a','lesson-1','exercise-1','prompt',1000)")
    rejects("INSERT INTO learning_exposures (id,user_id,session_id,lesson_id,exercise_id,exposure_kind,created_at) "
            "VALUES ('bad-exposure-version','alice','session-a','lesson-1','exercise-2','prompt',1000)")
    rejects("INSERT INTO course_releases (id,course_id,course_version_id,release_number,status,published_by_user_id,created_at,updated_at) "
            "VALUES ('bad-release','course','version-2',2,'active','editor',1000,1000)")
    rejects("INSERT INTO learner_preferences (id,user_id,reminders_enabled,created_at,updated_at) "
            "VALUES ('bad-preference','mallory',0,1000,1000)")
    rejects("INSERT INTO guest_lesson_imports VALUES ('bad-guest','mallory','sample-greetings',1,2,'imported',1000,1000)")
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


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
        check_learning_model(connection)
        connection.execute("INSERT INTO items VALUES ('legacy','alice','Legacy',NULL,1000)")
        apply_migrations(connection, migrations)
        assert connection.execute("SELECT title FROM items WHERE id='legacy'").fetchone() == ("Legacy",)
        assert connection.execute("SELECT user_id FROM exercise_attempts WHERE id='attempt-a'").fetchone() == ("alice",)
        assert connection.execute("SELECT user_id FROM guest_lesson_imports WHERE id='guest-a'").fetchone() == ("alice",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    print(f"Migration gate passed: {len(migrations)} additive, ordered, idempotent migration(s)")


if __name__ == "__main__":
    main()
