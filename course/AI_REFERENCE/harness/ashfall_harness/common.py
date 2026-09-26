'Local, proposal-first teaching harness. No command here edits the source project.'

from __future__ import annotations

import hashlib

import json

import os

import re

import socket

import stat

import time

import uuid

from contextlib import AbstractContextManager

from pathlib import Path, PurePosixPath

from typing import Any

VERSION = '0.1.0'

WINDOWS_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(1, 10)], *[f'LPT{i}' for i in range(1, 10)]}

SECRET_PARTS = {'.git', '.claude', '.env', 'credentials', 'secrets', 'keystore'}

SECRET_SUFFIXES = {'.pem', '.key', '.p12', '.pfx', '.jks', '.keystore'}



class HarnessError(RuntimeError):
    """An expected, fail-closed refusal, not a successful game test."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError, ValueError) as exc:
        raise HarnessError(f'JSON 읽기 실패: {path}: {exc}') from exc


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as f:
            f.write(canonical_json(value))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def safe_relative(text: str) -> str:
    if not isinstance(text, str) or not text or '\\' in text or (':' in text) or ('\x00' in text):
        raise HarnessError('경로는 비어 있지 않은 / 구분 상대경로여야 합니다')
    raw = text.split('/')
    if any((not s or s in {'.', '..'} or s.endswith((' ', '.')) or any((ord(c) < 32 for c in s)) for s in raw)):
        raise HarnessError(f'비정규 경로 거부: {text}')
    if any((s.split('.')[0].upper() in WINDOWS_RESERVED for s in raw)):
        raise HarnessError(f'예약 장치 경로 거부: {text}')
    if any((any((c in s for c in '<>"|?*')) for s in raw)):
        raise HarnessError(f'Windows 호환 불가 경로: {text}')
    p = PurePosixPath(text)
    if p.is_absolute() or str(p) != text:
        raise HarnessError(f'절대/별칭 경로 거부: {text}')
    return text


def is_inside(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + '/')


def child(root: Path, relative: str) -> Path:
    rel = safe_relative(relative)
    root = root.resolve()
    p = root / rel
    for part in [p, *list(p.parents)[:len(PurePosixPath(rel).parts)]]:
        reparse = bool(part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
        if part.is_symlink() or reparse or (hasattr(part, 'is_junction') and part.is_junction()):
            raise HarnessError(f'심볼릭 링크/정션 경로 거부: {part}')
    if not p.resolve().is_relative_to(root):
        raise HarnessError('허용 루트 밖 경로 거부')
    return p


def sensitive_path(rel: str) -> bool:
    parts = [s.casefold() for s in PurePosixPath(rel).parts]
    return any((s in SECRET_PARTS or s.startswith('.env.') for s in parts)) or PurePosixPath(rel).suffix.casefold() in SECRET_SUFFIXES


def scan(root: Path, roots: list[str], *, max_files: int=60000, max_bytes: int=4000000000) -> dict[str, str]:
    """Hash declared source roots only; fail on links/secrets/case collisions instead of hiding them."""
    result: dict[str, str] = {}
    folded: set[str] = set()
    total = 0
    for top in roots:
        p = child(root, top)
        if not p.exists():
            continue
        for f in [p] if p.is_file() else sorted(p.rglob('*')):
            rel = f.relative_to(root).as_posix()
            child(root, rel)
            if not f.is_file():
                continue
            if sensitive_path(rel):
                raise HarnessError(f'소스 스냅샷에 민감한 경로가 있습니다. 먼저 분리하세요: {rel}')
            if rel in result:
                continue
            key = rel.casefold()
            if key in folded:
                raise HarnessError(f'대소문자 충돌: {rel}')
            folded.add(key)
            data = f.read_bytes()
            total += len(data)
            if len(result) >= max_files or total > max_bytes:
                raise HarnessError('스냅샷 크기 제한 초과. 실행 전에 설정과 불필요한 자료를 검토하세요')
            result[rel] = sha_bytes(data)
    if not result:
        raise HarnessError('소스 스냅샷이 비어 있습니다')
    return dict(sorted(result.items()))


def copy_manifest(source: Path, destination: Path, manifest: dict[str, str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for rel, expected in manifest.items():
        data = child(source, rel).read_bytes()
        if sha_bytes(data) != expected:
            raise HarnessError(f'복사 중 원본 변경: {rel}')
        out = child(destination, rel)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('xb') as f:
            f.write(data)


class FileLock(AbstractContextManager):
    """Cooperative single-host lock. Never automatically steals an expired lock."""

    def __init__(self, path: Path, resource: str):
        self.path, self.resource = (path, resource)
        self.token = uuid.uuid4().hex

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open('x', encoding='utf-8') as f:
                json.dump({'token': self.token, 'pid': os.getpid(), 'host': socket.gethostname(), 'resource': self.resource, 'created': time.time()}, f)
        except FileExistsError as exc:
            raise HarnessError(f'리소스 잠김: {self.resource}; {self.path}. TTL만으로 해제하지 마세요') from exc
        return self

    def __exit__(self, *args):
        if self.path.exists() and read_json(self.path).get('token') == self.token:
            self.path.unlink()
        return False


def event(run: Path, kind: str, **data: Any) -> None:
    with (run / 'events.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'at': time.time(), 'kind': kind, **data}, ensure_ascii=False, allow_nan=False) + '\n')
        f.flush()


def check_source(run: Path, meta: dict) -> None:
    now = scan(Path(meta['source']), meta['source_roots'])
    if digest(now) != meta['source_sha256']:
        raise HarnessError('원본이 초기 스냅샷에서 변경되었습니다. 자동 덮어쓰기/계속 실행을 중단합니다. 새 run으로 재기준화하세요')


def assert_config_unchanged(run: Path, meta: dict) -> tuple[dict, dict]:
    plan, config = (read_json(run / 'plan.json'), read_json(run / 'config.json'))
    if digest(plan) != meta['plan_sha256'] or digest(config) != meta['config_sha256']:
        raise HarnessError('실행 중 계획/권한/게이트 설정 변경 거부. 검토한 새 설정으로 새 run을 만드세요')
    return (plan, config)
