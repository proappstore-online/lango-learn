"""Check committed PAS D1 migrations on a fresh SQLite database."""

import json
import re
import sqlite3
import tempfile
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
        if item["name"] == "0006_objective_graph":
            assert item["sql"] == (ROOT / "migrations/0006_objective_graph.sql").read_text(), "0006 source and deploy manifest differ"
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
        "objective", "lexeme", "phrase", "grammar_point", "pronunciation_pattern",
        "register_tag", "confusable_pair", "objective_lexeme", "objective_phrase",
        "objective_grammar", "objective_pronunciation", "objective_register",
        "objective_confusable", "objective_prerequisite",
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
        "idx_objective_order", "idx_lexeme_order", "idx_phrase_order",
        "idx_grammar_point_order", "idx_pronunciation_pattern_order",
        "idx_register_tag_order", "idx_confusable_pair_order",
        "idx_objective_lexeme_order", "idx_objective_phrase_order",
        "idx_objective_grammar_order", "idx_objective_pronunciation_order",
        "idx_objective_register_order", "idx_objective_confusable_order",
        "idx_objective_prerequisite_order",
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


def fixture_0006_objective_graph(connection):
    """Persist every graph relationship and reject invalid snapshot edges."""
    def rejects(sql, values=()):
        try:
            connection.execute(sql, values)
        except sqlite3.IntegrityError:
            return
        raise AssertionError(f"expected objective graph integrity rejection: {sql}")

    connection.execute("INSERT INTO courses VALUES ('graph-course','en','es','Synthetic graph',1000,1000)")
    connection.execute("INSERT INTO course_versions VALUES ('graph-version','graph-course',1,'graph-1','draft',1000,1000)")
    connection.execute("INSERT INTO course_versions VALUES ('graph-other','graph-course',2,'graph-2','draft',1000,1000)")
    connection.execute("INSERT INTO lessons VALUES ('graph-lesson','graph-version','lesson-graph',1,0,'Synthetic lesson',1000)")
    connection.execute("INSERT INTO lessons VALUES ('other-lesson','graph-other','lesson-other',2,0,'Other lesson',1000)")
    for tag in ('en','es','fr'):
        connection.execute("INSERT INTO course_locales VALUES (?,?,NULL,NULL,1000)", (tag,tag))
    connection.execute("INSERT INTO course_maps VALUES ('graph-map','graph-course','en','es',1000)")
    common="sort_order,created_at,updated_at,created_by,updated_by"
    connection.execute(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('obj-a','graph-version','graph-lesson','Ask','Ask in context','es',1,1000,1000,'editor','editor')")
    connection.execute(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('obj-b','graph-version',NULL,'Greet','Greet in context','es',0,1000,1000,'editor','editor')")
    connection.execute(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('obj-other','graph-other','other-lesson','Other','Other version','es',0,1000,1000,'editor','editor')")
    rejects(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('bad-lesson','graph-version','other-lesson','Bad','Wrong version','es',0,1000,1000,'editor','editor')")
    rejects(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('bad-locale','graph-version',NULL,'Bad','Wrong course locale','fr',0,1000,1000,'editor','editor')")
    nodes = [
        ('lexeme', 'form,lemma,part_of_speech', "'hola','hola','interjection'", 'objective_lexeme', 'lexeme_id'),
        ('phrase', 'text', "'Hola, Ana'", 'objective_phrase', 'phrase_id'),
        ('grammar_point', 'label,description', "'Address','Address a person'", 'objective_grammar', 'grammar_point_id'),
        ('pronunciation_pattern', 'pattern,example', "'/ola/','hola'", 'objective_pronunciation', 'pronunciation_pattern_id'),
        ('register_tag', 'name,description', "'informal','Familiar context'", 'objective_register', 'register_tag_id'),
        ('confusable_pair', 'item_a,item_b,note', "'hola','ola','Initial letter differs'", 'objective_confusable', 'confusable_pair_id'),
    ]
    for position,(table,fields,values,edge,key) in enumerate(nodes):
        connection.execute(f"INSERT INTO {table} (id,course_version_id,{fields},locale,{common}) VALUES ('node-{position}','graph-version',{values},'es',{position},1000,1000,'editor','editor')")
        edge_sql=f"INSERT INTO {edge} (id,course_version_id,objective_id,{key},rel_type,{common}) VALUES ('edge-{position}','graph-version','obj-a','node-{position}','teaches',{position},1000,1000,'editor','editor')"
        connection.execute(edge_sql)
        rejects(edge_sql.replace(f"'edge-{position}'", f"'duplicate-{position}'"))
        rejects(edge_sql.replace(f"'edge-{position}'", f"'wrong-version-{position}'").replace("'node-"+str(position)+"'", "'missing'"))
        assert connection.execute(f"SELECT {key} FROM {edge} WHERE id=?", (f'edge-{position}',)).fetchone() == (f'node-{position}',)
    connection.execute("INSERT INTO lexeme (id,course_version_id,form,lemma,part_of_speech,locale,sort_order,created_at,updated_at,created_by,updated_by) VALUES ('foreign-lexeme','graph-other','hola','hola','interjection','es',0,1000,1000,'editor','editor')")
    rejects("INSERT INTO objective_lexeme (id,course_version_id,objective_id,lexeme_id,rel_type,sort_order,created_at,updated_at,created_by,updated_by) VALUES ('foreign-edge','graph-version','obj-a','foreign-lexeme','teaches',0,1000,1000,'editor','editor')")
    assert connection.execute("SELECT id FROM objective WHERE course_version_id='graph-version' ORDER BY sort_order,id").fetchall() == [('obj-b',),('obj-a',)]
    assert connection.execute("SELECT id FROM objective_lexeme WHERE course_version_id='graph-version' ORDER BY sort_order,id").fetchall() == [('edge-0',)]
    edge="INSERT INTO objective_prerequisite (id,course_version_id,objective_id,prerequisite_objective_id,sort_order,created_at,updated_at,created_by,updated_by) VALUES (?,?,?,?,0,1000,1000,'editor','editor')"
    connection.execute(edge, ('prereq-a','graph-version','obj-a','obj-b'))
    rejects(edge, ('prereq-cycle','graph-version','obj-b','obj-a'))
    rejects(edge, ('prereq-self','graph-version','obj-a','obj-a'))
    rejects(edge, ('prereq-foreign','graph-version','obj-a','obj-other'))
    rejects(edge, ('prereq-missing','graph-version','obj-a','not-here'))
    assert connection.execute("SELECT COUNT(*) FROM objective_prerequisite").fetchone() == (1,)
    rejects("UPDATE lexeme SET form='changed' WHERE id='node-0'")
    connection.execute("UPDATE course_versions SET status='review',updated_at=2000 WHERE id='graph-version'")
    rejects(f"INSERT INTO objective (id,course_version_id,lesson_id,label,description,locale,{common}) VALUES ('after-review','graph-version',NULL,'Late','Late edit','es',2,3000,3000,'editor','editor')")
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
        fixture_0006_objective_graph(connection)
        connection.execute("INSERT INTO items VALUES ('legacy','alice','Legacy',NULL,1000)")
        apply_migrations(connection, migrations)
        assert connection.execute("SELECT title FROM items WHERE id='legacy'").fetchone() == ("Legacy",)
        assert connection.execute("SELECT user_id FROM exercise_attempts WHERE id='attempt-a'").fetchone() == ("alice",)
        assert connection.execute("SELECT user_id FROM guest_lesson_imports WHERE id='guest-a'").fetchone() == ("alice",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    # Upgrade a durable 0005 database and confirm the old data and new graph survive reopening.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "upgrade.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            apply_migrations(connection, migrations[:-1])
            connection.execute("INSERT INTO items VALUES ('legacy-graph','alice','Before graph',NULL,500)")
            apply_migrations(connection, migrations[-1:])
            fixture_0006_objective_graph(connection)
        with sqlite3.connect(path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            assert connection.execute("SELECT title FROM items WHERE id='legacy-graph'").fetchone() == ('Before graph',)
            assert connection.execute("SELECT COUNT(*) FROM objective_lexeme").fetchone() == (1,)
            assert connection.execute("SELECT COUNT(*) FROM objective_prerequisite").fetchone() == (1,)
            apply_migrations(connection, migrations[-1:])
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    print(f"Migration gate passed: {len(migrations)} additive, ordered, idempotent migration(s)")


if __name__ == "__main__":
    main()
