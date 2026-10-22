CREATE TABLE IF NOT EXISTS objective (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  lesson_id TEXT,
  label TEXT NOT NULL CHECK (length(trim(label))>0),
  description TEXT NOT NULL CHECK (length(trim(description))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag),
  FOREIGN KEY (course_version_id,lesson_id) REFERENCES lessons(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_order ON objective(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_insert_guard BEFORE INSERT ON objective WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'objective requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS objective_update_guard BEFORE UPDATE ON objective WHEN NEW.id<>OLD.id OR NEW.course_version_id<>OLD.course_version_id OR NEW.created_at<>OLD.created_at OR NEW.created_by<>OLD.created_by OR NEW.updated_at<=OLD.updated_at OR (NEW.locale<>OLD.locale AND (EXISTS (SELECT 1 FROM objective_lexeme WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_phrase WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_grammar WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_pronunciation WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_register WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_confusable WHERE objective_id=OLD.id) OR EXISTS (SELECT 1 FROM objective_prerequisite WHERE objective_id=OLD.id OR prerequisite_objective_id=OLD.id))) OR NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'objective update requires mapped draft version and newer timestamp'); END;
CREATE TRIGGER IF NOT EXISTS objective_no_delete BEFORE DELETE ON objective BEGIN SELECT RAISE(ABORT,'objective is immutable'); END;
CREATE TABLE IF NOT EXISTS lexeme (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  form TEXT NOT NULL CHECK (length(trim(form))>0),
  lemma TEXT NOT NULL CHECK (length(trim(lemma))>0),
  part_of_speech TEXT NOT NULL CHECK (length(trim(part_of_speech))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_lexeme_order ON lexeme(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS lexeme_insert_guard BEFORE INSERT ON lexeme WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'lexeme requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS lexeme_no_update BEFORE UPDATE ON lexeme BEGIN SELECT RAISE(ABORT,'lexeme is immutable'); END;
CREATE TRIGGER IF NOT EXISTS lexeme_no_delete BEFORE DELETE ON lexeme BEGIN SELECT RAISE(ABORT,'lexeme is immutable'); END;
CREATE TABLE IF NOT EXISTS phrase (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  text TEXT NOT NULL CHECK (length(trim(text))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_phrase_order ON phrase(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS phrase_insert_guard BEFORE INSERT ON phrase WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'phrase requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS phrase_no_update BEFORE UPDATE ON phrase BEGIN SELECT RAISE(ABORT,'phrase is immutable'); END;
CREATE TRIGGER IF NOT EXISTS phrase_no_delete BEFORE DELETE ON phrase BEGIN SELECT RAISE(ABORT,'phrase is immutable'); END;
CREATE TABLE IF NOT EXISTS grammar_point (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (length(trim(label))>0),
  description TEXT NOT NULL CHECK (length(trim(description))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_grammar_point_order ON grammar_point(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS grammar_point_insert_guard BEFORE INSERT ON grammar_point WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'grammar_point requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS grammar_point_no_update BEFORE UPDATE ON grammar_point BEGIN SELECT RAISE(ABORT,'grammar_point is immutable'); END;
CREATE TRIGGER IF NOT EXISTS grammar_point_no_delete BEFORE DELETE ON grammar_point BEGIN SELECT RAISE(ABORT,'grammar_point is immutable'); END;
CREATE TABLE IF NOT EXISTS pronunciation_pattern (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  pattern TEXT NOT NULL CHECK (length(trim(pattern))>0),
  example TEXT NOT NULL CHECK (length(trim(example))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_pronunciation_pattern_order ON pronunciation_pattern(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS pronunciation_pattern_insert_guard BEFORE INSERT ON pronunciation_pattern WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'pronunciation_pattern requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS pronunciation_pattern_no_update BEFORE UPDATE ON pronunciation_pattern BEGIN SELECT RAISE(ABORT,'pronunciation_pattern is immutable'); END;
CREATE TRIGGER IF NOT EXISTS pronunciation_pattern_no_delete BEFORE DELETE ON pronunciation_pattern BEGIN SELECT RAISE(ABORT,'pronunciation_pattern is immutable'); END;
CREATE TABLE IF NOT EXISTS register_tag (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  name TEXT NOT NULL CHECK (length(trim(name))>0),
  description TEXT NOT NULL CHECK (length(trim(description))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_register_tag_order ON register_tag(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS register_tag_insert_guard BEFORE INSERT ON register_tag WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'register_tag requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS register_tag_no_update BEFORE UPDATE ON register_tag BEGIN SELECT RAISE(ABORT,'register_tag is immutable'); END;
CREATE TRIGGER IF NOT EXISTS register_tag_no_delete BEFORE DELETE ON register_tag BEGIN SELECT RAISE(ABORT,'register_tag is immutable'); END;
CREATE TABLE IF NOT EXISTS confusable_pair (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  item_a TEXT NOT NULL CHECK (length(trim(item_a))>0),
  item_b TEXT NOT NULL CHECK (length(trim(item_b))>0),
  note TEXT NOT NULL CHECK (length(trim(note))>0),
  locale TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(course_version_id,id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (locale) REFERENCES course_locales(tag)
);
CREATE INDEX IF NOT EXISTS idx_confusable_pair_order ON confusable_pair(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS confusable_pair_insert_guard BEFORE INSERT ON confusable_pair WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN course_maps m ON m.course_id=v.course_id WHERE v.id=NEW.course_version_id AND v.status='draft' AND NEW.locale IN (m.source_tag,m.target_tag)) BEGIN SELECT RAISE(ABORT,'confusable_pair requires mapped draft version and course locale'); END;
CREATE TRIGGER IF NOT EXISTS confusable_pair_no_update BEFORE UPDATE ON confusable_pair BEGIN SELECT RAISE(ABORT,'confusable_pair is immutable'); END;
CREATE TRIGGER IF NOT EXISTS confusable_pair_no_delete BEFORE DELETE ON confusable_pair BEGIN SELECT RAISE(ABORT,'confusable_pair is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_lexeme (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  lexeme_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,lexeme_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,lexeme_id) REFERENCES lexeme(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_lexeme_order ON objective_lexeme(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_lexeme_insert_guard BEFORE INSERT ON objective_lexeme WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN lexeme c ON c.id=NEW.lexeme_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_lexeme requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_lexeme_no_update BEFORE UPDATE ON objective_lexeme BEGIN SELECT RAISE(ABORT,'objective_lexeme is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_lexeme_no_delete BEFORE DELETE ON objective_lexeme BEGIN SELECT RAISE(ABORT,'objective_lexeme is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_phrase (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  phrase_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,phrase_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,phrase_id) REFERENCES phrase(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_phrase_order ON objective_phrase(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_phrase_insert_guard BEFORE INSERT ON objective_phrase WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN phrase c ON c.id=NEW.phrase_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_phrase requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_phrase_no_update BEFORE UPDATE ON objective_phrase BEGIN SELECT RAISE(ABORT,'objective_phrase is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_phrase_no_delete BEFORE DELETE ON objective_phrase BEGIN SELECT RAISE(ABORT,'objective_phrase is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_grammar (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  grammar_point_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,grammar_point_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,grammar_point_id) REFERENCES grammar_point(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_grammar_order ON objective_grammar(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_grammar_insert_guard BEFORE INSERT ON objective_grammar WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN grammar_point c ON c.id=NEW.grammar_point_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_grammar requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_grammar_no_update BEFORE UPDATE ON objective_grammar BEGIN SELECT RAISE(ABORT,'objective_grammar is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_grammar_no_delete BEFORE DELETE ON objective_grammar BEGIN SELECT RAISE(ABORT,'objective_grammar is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_pronunciation (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  pronunciation_pattern_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,pronunciation_pattern_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,pronunciation_pattern_id) REFERENCES pronunciation_pattern(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_pronunciation_order ON objective_pronunciation(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_pronunciation_insert_guard BEFORE INSERT ON objective_pronunciation WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN pronunciation_pattern c ON c.id=NEW.pronunciation_pattern_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_pronunciation requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_pronunciation_no_update BEFORE UPDATE ON objective_pronunciation BEGIN SELECT RAISE(ABORT,'objective_pronunciation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_pronunciation_no_delete BEFORE DELETE ON objective_pronunciation BEGIN SELECT RAISE(ABORT,'objective_pronunciation is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_register (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  register_tag_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,register_tag_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,register_tag_id) REFERENCES register_tag(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_register_order ON objective_register(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_register_insert_guard BEFORE INSERT ON objective_register WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN register_tag c ON c.id=NEW.register_tag_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_register requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_register_no_update BEFORE UPDATE ON objective_register BEGIN SELECT RAISE(ABORT,'objective_register is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_register_no_delete BEFORE DELETE ON objective_register BEGIN SELECT RAISE(ABORT,'objective_register is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_confusable (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  confusable_pair_id TEXT NOT NULL,
  rel_type TEXT NOT NULL DEFAULT 'teaches' CHECK (rel_type IN ('teaches','reinforces','assesses')),
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  UNIQUE(objective_id,confusable_pair_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,confusable_pair_id) REFERENCES confusable_pair(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_confusable_order ON objective_confusable(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_confusable_insert_guard BEFORE INSERT ON objective_confusable WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN confusable_pair c ON c.id=NEW.confusable_pair_id AND c.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=c.locale) BEGIN SELECT RAISE(ABORT,'objective_confusable requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_confusable_no_update BEFORE UPDATE ON objective_confusable BEGIN SELECT RAISE(ABORT,'objective_confusable is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_confusable_no_delete BEFORE DELETE ON objective_confusable BEGIN SELECT RAISE(ABORT,'objective_confusable is immutable'); END;
CREATE TABLE IF NOT EXISTS objective_prerequisite (
  id TEXT PRIMARY KEY,
  course_version_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
  prerequisite_objective_id TEXT NOT NULL,
  sort_order INTEGER NOT NULL CHECK (sort_order>=0),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL CHECK (updated_at>=created_at),
  created_by TEXT NOT NULL CHECK (length(trim(created_by))>0),
  updated_by TEXT NOT NULL CHECK (length(trim(updated_by))>0),
  CHECK(objective_id<>prerequisite_objective_id),
  UNIQUE(objective_id,prerequisite_objective_id),
  FOREIGN KEY (course_version_id) REFERENCES course_versions(id),
  FOREIGN KEY (course_version_id,objective_id) REFERENCES objective(course_version_id,id),
  FOREIGN KEY (course_version_id,prerequisite_objective_id) REFERENCES objective(course_version_id,id)
);
CREATE INDEX IF NOT EXISTS idx_objective_prerequisite_order ON objective_prerequisite(course_version_id,sort_order,id);
CREATE TRIGGER IF NOT EXISTS objective_prerequisite_insert_guard BEFORE INSERT ON objective_prerequisite WHEN NOT EXISTS (SELECT 1 FROM course_versions v JOIN objective o ON o.id=NEW.objective_id AND o.course_version_id=v.id JOIN objective p ON p.id=NEW.prerequisite_objective_id AND p.course_version_id=v.id WHERE v.id=NEW.course_version_id AND v.status='draft' AND o.locale=p.locale) BEGIN SELECT RAISE(ABORT,'objective prerequisite requires same-version and same-locale draft nodes'); END;
CREATE TRIGGER IF NOT EXISTS objective_prerequisite_no_cycle BEFORE INSERT ON objective_prerequisite WHEN EXISTS (WITH RECURSIVE ancestors(id) AS (SELECT NEW.prerequisite_objective_id UNION SELECT p.prerequisite_objective_id FROM objective_prerequisite p JOIN ancestors a ON p.objective_id=a.id WHERE p.course_version_id=NEW.course_version_id) SELECT 1 FROM ancestors WHERE id=NEW.objective_id) BEGIN SELECT RAISE(ABORT,'objective prerequisite cycle'); END;
CREATE TRIGGER IF NOT EXISTS objective_prerequisite_no_update BEFORE UPDATE ON objective_prerequisite BEGIN SELECT RAISE(ABORT,'objective prerequisite is immutable'); END;
CREATE TRIGGER IF NOT EXISTS objective_prerequisite_no_delete BEFORE DELETE ON objective_prerequisite BEGIN SELECT RAISE(ABORT,'objective prerequisite is immutable'); END;
