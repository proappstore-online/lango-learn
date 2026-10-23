"""Validate a version-pinned, original Lango Learn content package (stdlib only)."""
import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path

LOCALE = re.compile(r"^[a-z]{2,8}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|[0-9]{3}))?$")
ID = re.compile(r"^[a-z][a-z0-9-]*$")
MEDIA_TYPES = {"image/png": 5 * 1024**2, "image/jpeg": 5 * 1024**2,
               "image/webp": 5 * 1024**2, "audio/mpeg": 10 * 1024**2,
               "audio/mp4": 10 * 1024**2, "audio/ogg": 10 * 1024**2}


def validate(package):
    errors = []

    def fail(path, message):
        errors.append(f"{path}: {message}")

    def obj(value, path, required, optional=()):
        if not isinstance(value, dict):
            fail(path, "must be an object")
            return {}
        for key in required:
            if key not in value:
                fail(f"{path}.{key}", "required")
        for key in value.keys() - set(required) - set(optional):
            fail(f"{path}.{key}", "unknown field")
        return value

    def string(value, path):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            fail(path, "must be nonempty trimmed text")
            return ""
        if any(ord(c) < 32 and c not in '\n\t' for c in value) or '<' in value or '>' in value:
            fail(path, "control characters or markup are not allowed")
        return value

    def identifier(value, path):
        if not isinstance(value, str) or not ID.fullmatch(value):
            fail(path, "must be a lower-case stable id")
        return value

    def locale(value, path, allowed):
        if not isinstance(value, str) or not LOCALE.fullmatch(value):
            fail(path, "invalid canonical locale tag")
        elif value not in allowed:
            fail(path, "locale is outside the course pair/regions")
        return value

    root = obj(package, '$', ['schemaVersion', 'packageVersion', 'courseVersionId',
                               'sourceLocale', 'targetLocale', 'regionalLocales',
                               'objectives', 'assets', 'lessons'])
    if root.get('schemaVersion') != 1:
        fail('$.schemaVersion', 'must be 1')
    string(root.get('packageVersion'), '$.packageVersion')
    string(root.get('courseVersionId'), '$.courseVersionId')
    source, target = root.get('sourceLocale'), root.get('targetLocale')
    if source == target:
        fail('$.targetLocale', 'must differ from sourceLocale')
    allowed = {source, target}
    for key in ('sourceLocale', 'targetLocale'):
        locale(root.get(key), f'$.{key}', allowed)
    regions = root.get('regionalLocales')
    if not isinstance(regions, list):
        fail('$.regionalLocales', 'must be an array')
        regions = []
    for i, tag in enumerate(regions):
        if not isinstance(tag, str) or not LOCALE.fullmatch(tag):
            fail(f'$.regionalLocales[{i}]', 'invalid canonical locale tag')
        elif tag in allowed:
            fail(f'$.regionalLocales[{i}]', 'duplicate locale')
        elif tag.split('-')[0] not in {str(source).split('-')[0], str(target).split('-')[0]}:
            fail(f'$.regionalLocales[{i}]', 'language outside course pair')
        allowed.add(tag)

    objectives = root.get('objectives')
    if not isinstance(objectives, list) or not objectives:
        fail('$.objectives', 'must be a nonempty array')
        objectives = []
    objective_ids = set()
    for i, raw in enumerate(objectives):
        path = f'$.objectives[{i}]'
        entry = obj(raw, path, ['id', 'locale'])
        oid = identifier(entry.get('id'), path + '.id')
        if oid in objective_ids:
            fail(path + '.id', 'duplicate objective')
        objective_ids.add(oid)
        locale(entry.get('locale'), path + '.locale', allowed)

    assets = root.get('assets')
    if not isinstance(assets, list):
        fail('$.assets', 'must be an array')
        assets = []
    asset_ids = set()
    for i, raw in enumerate(assets):
        path = f'$.assets[{i}]'
        asset = obj(raw, path, ['id', 'mimeType', 'byteSize', 'origin', 'rights',
                                'accessibility', 'storageKey'], ['durationSeconds', 'locale', 'accent'])
        aid = identifier(asset.get('id'), path + '.id')
        if aid in asset_ids:
            fail(path + '.id', 'duplicate asset')
        asset_ids.add(aid)
        mime = asset.get('mimeType')
        if not isinstance(mime, str) or mime not in MEDIA_TYPES:
            fail(path + '.mimeType', 'unsupported media format')
        size = asset.get('byteSize')
        max_size = MEDIA_TYPES.get(mime, 0) if isinstance(mime, str) else 0
        if type(size) is not int or not 0 < size <= max_size:
            fail(path + '.byteSize', 'invalid size for format')
        key = string(asset.get('storageKey'), path + '.storageKey')
        if key.startswith('/') or '..' in key or '://' in key:
            fail(path + '.storageKey', 'must be a relative private asset key')
        origin = obj(asset.get('origin'), path + '.origin', ['type', 'creator', 'source'])
        if origin.get('type') != 'original_lango':
            fail(path + '.origin.type', 'only original Lango Learn assets are accepted')
        for field in ('creator', 'source'):
            string(origin.get(field), path + '.origin.' + field)
        rights = obj(asset.get('rights'), path + '.rights', ['owner', 'licence', 'territories',
                                                           'attribution', 'expiresOn', 'replacement'])
        for field in ('owner', 'licence', 'attribution', 'replacement'):
            string(rights.get(field), path + '.rights.' + field)
        if rights.get('licence') != 'owned-original':
            fail(path + '.rights.licence', 'requires owned-original pending rights policy')
        territories = rights.get('territories')
        if not isinstance(territories, list) or not territories or not all(isinstance(t, str) and t for t in territories):
            fail(path + '.rights.territories', 'must list approved territories')
        expiry = rights.get('expiresOn')
        if expiry is not None:
            try:
                expiry_date = date.fromisoformat(expiry) if isinstance(expiry, str) else None
            except ValueError:
                expiry_date = None
            if expiry_date is None:
                fail(path + '.rights.expiresOn', 'must be null or a real YYYY-MM-DD date')
            elif expiry_date < date.today():
                fail(path + '.rights.expiresOn', 'rights have expired')
        access = obj(asset.get('accessibility'), path + '.accessibility', ['altText', 'decorative',
                                                                         'transcript', 'nonAudioAlternative'])
        for field in ('decorative', 'nonAudioAlternative'):
            if type(access.get(field)) is not bool:
                fail(path + '.accessibility.' + field, 'must be boolean')
        if isinstance(mime, str) and mime.startswith('image/'):
            if access.get('decorative') is not True:
                string(access.get('altText'), path + '.accessibility.altText')
            elif access.get('altText') is not None and not isinstance(access.get('altText'), str):
                fail(path + '.accessibility.altText', 'must be text or null')
            if access.get('transcript') is not None:
                fail(path + '.accessibility.transcript', 'only valid for audio')
        elif isinstance(mime, str) and mime.startswith('audio/'):
            if access.get('altText') is not None:
                fail(path + '.accessibility.altText', 'only valid for images')
            if access.get('decorative') is True:
                fail(path + '.accessibility.decorative', 'audio cannot be decorative')
            string(access.get('transcript'), path + '.accessibility.transcript')
            if access.get('nonAudioAlternative') is not True:
                fail(path + '.accessibility.nonAudioAlternative', 'required for audio')
            duration = asset.get('durationSeconds')
            if type(duration) not in (int, float) or not 0 < duration <= 120:
                fail(path + '.durationSeconds', 'must be 0–120 seconds')
            locale(asset.get('locale'), path + '.locale', allowed)
            string(asset.get('accent'), path + '.accent')
        if not (isinstance(mime, str) and mime.startswith('audio/')):
            for key in ('durationSeconds', 'locale', 'accent'):
                if key in asset:
                    fail(path + '.' + key, 'only valid for audio')

    lessons = root.get('lessons')
    if not isinstance(lessons, list) or not lessons:
        fail('$.lessons', 'must be a nonempty array')
        lessons = []
    lesson_ids = set()
    for li, raw in enumerate(lessons):
        path = f'$.lessons[{li}]'
        lesson = obj(raw, path, ['id', 'exercises'])
        lid = identifier(lesson.get('id'), path + '.id')
        if lid in lesson_ids:
            fail(path + '.id', 'duplicate lesson')
        lesson_ids.add(lid)
        exercises = lesson.get('exercises')
        if not isinstance(exercises, list) or not exercises:
            fail(path + '.exercises', 'must be a nonempty array')
            continue
        positions, exercise_ids = set(), set()
        for ei, raw_ex in enumerate(exercises):
            ep = f'{path}.exercises[{ei}]'
            ex = obj(raw_ex, ep, ['id', 'position', 'kind', 'objectiveIds', 'prompt', 'response',
                                  'variants', 'hint', 'explanation', 'distractors', 'mediaAssetIds',
                                  'regionLocales', 'provenance'])
            eid = identifier(ex.get('id'), ep + '.id')
            if eid in exercise_ids:
                fail(ep + '.id', 'duplicate exercise')
            exercise_ids.add(eid)
            pos = ex.get('position')
            if type(pos) is not int or pos < 0 or pos in positions:
                fail(ep + '.position', 'must be a unique nonnegative integer')
            else:
                positions.add(pos)
            if ex.get('kind') not in ('recognition', 'construction', 'typed-recall', 'listening'):
                fail(ep + '.kind', 'unsupported exercise kind')
            refs = ex.get('objectiveIds')
            if not isinstance(refs, list) or not refs:
                fail(ep + '.objectiveIds', 'must reference at least one objective')
            else:
                for ref in refs:
                    if ref not in objective_ids:
                        fail(ep + '.objectiveIds', f'unknown objective {ref!r}')
            prompt = obj(ex.get('prompt'), ep + '.prompt', ['text', 'locale', 'accessibleName'])
            for field in ('text', 'accessibleName'):
                string(prompt.get(field), ep + '.prompt.' + field)
            locale(prompt.get('locale'), ep + '.prompt.locale', allowed)
            response = obj(ex.get('response'), ep + '.response', ['text', 'locale'])
            answer = string(response.get('text'), ep + '.response.text')
            locale(response.get('locale'), ep + '.response.locale', allowed)
            variants = ex.get('variants')
            if not isinstance(variants, list):
                fail(ep + '.variants', 'must be an array')
                variants = []
            accepted = {answer}
            for vi, raw_variant in enumerate(variants):
                vp = f'{ep}.variants[{vi}]'
                variant = obj(raw_variant, vp, ['text', 'locale', 'reason'])
                value = string(variant.get('text'), vp + '.text')
                locale(variant.get('locale'), vp + '.locale', allowed)
                string(variant.get('reason'), vp + '.reason')
                if value in accepted:
                    fail(vp + '.text', 'duplicate accepted response')
                accepted.add(value)
            for field in ('hint', 'explanation'):
                string(ex.get(field), ep + '.' + field)
            distractors = ex.get('distractors')
            if not isinstance(distractors, list):
                fail(ep + '.distractors', 'must be an array')
                distractors = []
            seen = set()
            for di, value in enumerate(distractors):
                value = string(value, f'{ep}.distractors[{di}]')
                if value in accepted or value in seen:
                    fail(f'{ep}.distractors[{di}]', 'duplicate or accepted response')
                seen.add(value)
            if ex.get('kind') == 'recognition' and not distractors:
                fail(ep + '.distractors', 'recognition needs distractors')
            media = ex.get('mediaAssetIds')
            if not isinstance(media, list):
                fail(ep + '.mediaAssetIds', 'must be an array')
            else:
                for aid in media:
                    if aid not in asset_ids:
                        fail(ep + '.mediaAssetIds', f'unknown asset {aid!r}')
            regions = ex.get('regionLocales')
            if not isinstance(regions, list) or not regions:
                fail(ep + '.regionLocales', 'must be a nonempty array')
            else:
                for tag in regions:
                    locale(tag, ep + '.regionLocales', allowed)
            prov = obj(ex.get('provenance'), ep + '.provenance', ['type', 'creator', 'source', 'rightsOwner'])
            if prov.get('type') != 'original_lango':
                fail(ep + '.provenance.type', 'only original Lango Learn text is accepted')
            for field in ('creator', 'source', 'rightsOwner'):
                string(prov.get(field), ep + '.provenance.' + field)
        if positions != set(range(len(exercises))):
            fail(path + '.exercises', 'positions must be contiguous from 0')
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', nargs='+', type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.packages:
        try:
            errors = validate(json.loads(path.read_text(encoding='utf-8')))
        except (OSError, ValueError, TypeError, KeyError) as error:
            errors = [str(error)]
        for error in errors:
            print(f'{path}: {error}', file=sys.stderr)
        if not errors:
            print(f'{path}: valid')
        failed |= bool(errors)
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
