"""Build a private, local-only preview from a validated content package."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from validate_content_package import validate

EXTENSIONS = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp',
              'audio/mpeg': '.mp3', 'audio/mp4': '.m4a', 'audio/ogg': '.ogg'}


def build(package_path: Path, output: Path, media_dir: Path | None) -> None:
    package = json.loads(package_path.read_text(encoding='utf-8'))
    errors = validate(package)
    if errors:
        raise ValueError('\n'.join(errors))

    # Resolve every local asset before creating output. Never follow a storage key
    # out of the chosen private media directory, including through symlinks.
    copies = []
    if media_dir:
        root = media_dir.resolve(strict=True)
        for asset in package['assets']:
            source = (root / asset['storageKey']).resolve(strict=True)
            if not source.is_relative_to(root) or not source.is_file():
                raise ValueError(f"asset {asset['id']}: storageKey leaves media directory")
            if source.stat().st_size != asset['byteSize']:
                raise ValueError(f"asset {asset['id']}: byteSize does not match local media")
            copies.append((source, asset['id'] + EXTENSIONS[asset['mimeType']]))

    if output.is_symlink() or (output / 'index.html').is_symlink() or (output / 'media').is_symlink():
        raise ValueError('output paths must not be symbolic links')
    output.mkdir(parents=True, exist_ok=True)
    media_output = output / 'media'
    media_output.mkdir(exist_ok=True)
    for source, filename in copies:
        shutil.copyfile(source, media_output / filename)

    template = (Path(__file__).parent / 'author-preview.html').read_text(encoding='utf-8')
    embedded = json.dumps(package, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    filenames = {asset['id']: asset['id'] + EXTENSIONS[asset['mimeType']] for asset in package['assets']} if media_dir else {}
    output.joinpath('index.html').write_text(
        template.replace('/*PACKAGE_JSON*/', embedded).replace('/*MEDIA_JSON*/', json.dumps(filenames)),
        encoding='utf-8',
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output', type=Path, default=Path('.cache/author-preview'))
    parser.add_argument('--media-dir', type=Path, help='Private local root containing package storage keys')
    args = parser.parse_args()
    try:
        build(args.package, args.output, args.media_dir)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Preview not built: {error}', file=sys.stderr)
        return 1
    print(f'Open {args.output.resolve() / "index.html"} locally. Keep this draft directory private.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
