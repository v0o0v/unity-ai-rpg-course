"""Verify the imported course baseline without executing course code or using a network.

The AI operator runs this before the first upload. Later deliberate edits should be
reported as mismatches and documented as a new revision, not hidden by rewriting
IMPORT_MANIFEST.json. This script never writes to the course files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise ValueError(f'Unsafe manifest path: {relative}')
    path = root.joinpath(*rel.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path leaves repository: {relative}')
    if path.is_symlink():
        raise ValueError(f'Symbolic link: {relative}')
    return path


def verify(root: Path) -> dict:
    imported = json.loads((root / 'IMPORT_MANIFEST.json').read_text(encoding='utf-8'))
    expected = imported['files']
    errors: list[str] = []
    for relative, record in expected.items():
        try:
            path = safe_file(root, relative)
            if not path.is_file():
                errors.append(f'Missing: {relative}')
            elif path.stat().st_size != record['bytes'] or sha256(path) != record['sha256']:
                errors.append(f'Changed: {relative}')
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    observed = {str(path.relative_to(root)).replace('\\', '/')
                for path in (root / 'course').rglob('*') if path.is_file()}
    for relative in sorted(observed - set(expected)):
        errors.append(f'Unexpected baseline file: {relative}')
    count = imported['source_file_count']
    if len(expected) != count or len(observed) != count:
        errors.append('Baseline file count does not match import manifest')
    lessons = json.loads((root / 'course/data/lessons.json').read_text(encoding='utf-8'))
    terms = json.loads((root / 'course/data/terms.json').read_text(encoding='utf-8'))
    if len(lessons) != 256 or len(terms) != 331:
        errors.append('Baseline lesson or glossary count mismatch')
    for name in ('README.md', 'HANDOFF.md', 'START_CODEX.md', 'AGENTS.md',
                 'NOTICE.md', 'TRANSFER_STATUS.json', '.gitignore'):
        if not (root / name).is_file():
            errors.append(f'Missing handoff document: {name}')
    return {
        'status': 'PASS' if not errors else 'FAIL',
        'scope': 'LOCAL_IMPORT_INTEGRITY_ONLY',
        'source_files_checked': len(expected),
        'lesson_count': len(lessons),
        'technical_guide_count': len(terms),
        'remote_upload_verified': False,
        'game_or_unity_tests_executed': False,
        'errors': errors,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        result = verify(root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
