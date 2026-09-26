'Evidence is produced by trusted commands / named human attestations, never by model prose.'

from __future__ import annotations

import json

import os

import re

import tempfile

import time

import uuid

import xml.etree.ElementTree as ET

from pathlib import Path

from .common import HarnessError, FileLock, atomic_json, assert_config_unchanged, digest, event, read_json, scan, sha_bytes

from .provider import run_process



def parse_nunit(path: Path, minimum: int=1, required_names: list[str] | None=None) -> dict:
    # v8 parser contract: fail closed before reading execution evidence.
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise HarnessError('최소 검사는 양의 정수여야 합니다')
    if required_names is not None and (not isinstance(required_names, list) or
            not all(isinstance(n, str) and n.strip() for n in required_names) or
            len(required_names) != len(set(required_names))):
        raise HarnessError('필수 테스트 이름은 중복 없는 문자열 목록이어야 합니다')
    if not path.is_file():
        raise HarnessError('이번 실행의 NUnit XML이 없습니다')
    data = path.read_bytes()
    if len(data) > 20000000 or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise HarnessError('비정상 XML 크기/선언')
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HarnessError('NUnit XML 구문 오류') from exc
    if root.tag != 'test-run':
        raise HarnessError('지원 범위는 NUnit3 test-run 형식입니다. 설치 버전 출력을 확인하세요')
    cases = list(root.iter('test-case'))
    valid = {'Passed', 'Failed', 'Skipped', 'Inconclusive'}
    if any((c.get('result') not in valid for c in cases)):
        raise HarnessError('알 수 없는 test-case 결과')
    # v8 unique identity: repeated XML rows cannot inflate test counts.
    identities = [c.get('fullname') or c.get('name') for c in cases]
    ids = [c.get('id') for c in cases if c.get('id') is not None]
    if (any(not isinstance(n, str) or not n.strip() for n in identities)
            or len(identities) != len(set(identities)) or len(ids) != len(set(ids))):
        raise HarnessError('NUnit 테스트 이름/ID 누락 또는 중복. 파라미터별 고유 fullname을 확인하세요')
    passed = [c for c in cases if c.get('result') == 'Passed']
    failed = [c for c in cases if c.get('result') in {'Failed', 'Inconclusive'}]
    names = {c.get('fullname') or c.get('name') for c in passed}
    if any((not isinstance(n, str) or not n.strip() for n in names)):
        raise HarnessError('통과 테스트 이름이 없습니다')
    metrics = {'total': len(cases), 'passed': len(passed), 'failed': sum((c.get('result') == 'Failed' for c in cases)), 'skipped': sum((c.get('result') == 'Skipped' for c in cases)), 'inconclusive': sum((c.get('result') == 'Inconclusive' for c in cases))}
    for key, value in metrics.items():
        if key in root.attrib:
            try:
                reported = int(root.attrib[key])
            except ValueError as exc:
                raise HarnessError('NUnit 집계 형식 오류') from exc
            if reported != value:
                raise HarnessError('NUnit 루트 집계와 실제 case 수 불일치')
    if root.get('result') != 'Passed' or failed:
        raise HarnessError('NUnit 실패/미확정 결과')
    if len(passed) < minimum:
        raise HarnessError('실행·통과 테스트 수 부족. 0개/전부 skipped는 PASS가 아닙니다')
    missing = set(required_names or []) - names
    if missing:
        raise HarnessError('필수 테스트가 실제 통과하지 않았습니다: ' + ', '.join(sorted(missing)))
    return {'passed': len(passed), 'failed_or_inconclusive': len(failed), 'skipped': len(cases) - len(passed) - len(failed), 'passed_names': sorted(names)}


def parse_unittest(stdout: Path, stderr: Path, minimum: int=1) -> dict:
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise HarnessError('최소 검사는 양의 정수여야 합니다')
    streams = [p.read_text(encoding='utf-8', errors='replace') for p in (stdout, stderr)]
    text = '\n'.join(streams)
    # One gate runs exactly one unittest invocation. Mixed/multiple summaries are ambiguous.
    counts = re.findall(r'^Ran (\d+) tests? in [^\n]+$', text, re.MULTILINE)
    endings = re.findall(r'^(OK(?: \(skipped=\d+\))?|FAILED[^\n]*)$', text, re.MULTILINE)
    if len(counts) != 1 or len(endings) != 1 or not endings[0].startswith('OK'):
        raise HarnessError('Python 검사 요약이 없거나 중복·상충합니다. 게이트를 나눠 실행하세요')
    owner = next((s for s in streams if re.search(r'^Ran \d+ tests? in ', s, re.MULTILINE)), '')
    if not re.search(r'^Ran \d+ tests? in [^\n]+\n\s*OK(?: \(skipped=\d+\))?\s*\Z', owner, re.MULTILINE):
        raise HarnessError('동일 출력 스트림의 마지막 unittest 결과가 성공이 아닙니다')
    count = int(counts[0])
    match = re.search(r'skipped=(\d+)', endings[0])
    skipped = int(match.group(1)) if match else 0
    if not 0 <= skipped <= count or count - skipped < minimum:
        raise HarnessError('실제 통과 테스트 부족/집계 불일치')
    return {'passed': count - skipped, 'skipped': skipped, 'framework': 'unittest demo'}


def _start(run: Path, name: str) -> tuple[dict, dict, dict, Path, Path]:
    meta = read_json(run / 'run.json')
    _, config = assert_config_unchanged(run, meta)
    if name not in config['gates']:
        raise HarnessError('등록되지 않은 게이트')
    if not meta.get('seal_sha256'):
        raise HarnessError('먼저 stage를 열고 통합한 후 seal하세요')
    stage = Path(meta['stage'])
    if digest(scan(stage, config['source_roots'])) != meta['seal_sha256']:
        raise HarnessError('seal 이후 소스 변경. 기존 증거는 STALE입니다')
    gate = config['gates'][name]
    folder = run / 'gates' / name / f'{time.time_ns():020d}-{uuid.uuid4().hex[:8]}'
    folder.mkdir(parents=True)
    return (meta, config, gate, stage, folder)


def run_gate(run: Path, name: str, execute: bool) -> dict:
    if not execute:
        raise HarnessError('등록 명령을 검토한 뒤 --execute-approved-gates를 명시하세요')
    with FileLock(run / 'coordinator.lock', 'run coordinator'):
        meta, config, gate, stage, folder = _start(run, name)
        report = {'gate': name, 'status': 'BLOCKED', 'seal_id': meta['seal_id'], 'seal_sha256': meta['seal_sha256'], 'basis': 'deterministic command parser', 'provider': meta['provider'], 'artifacts': []}
        try:
            if not gate.get('enabled'):
                raise HarnessError('명령 미설정/비활성 게이트. 연결 없이 PASS 처리하지 않습니다')
            if gate['kind'] == 'manual':
                raise HarnessError('이 게이트는 사람이 실제 수행한 뒤 attest하세요')
            tokens = {'{python}': os.sys.executable, '{project}': str(stage), '{result_xml}': str(folder / 'results.xml'), '{log_file}': str(folder / 'editor.log')}
            argv = []
            for item in gate['argv']:
                if not isinstance(item, str):
                    raise HarnessError('argv 항목은 문자열')
                value = item
                for k, v in tokens.items():
                    value = value.replace(k, v)
                if '{' in value or '}' in value:
                    raise HarnessError('알 수 없는 명령 자리표시자')
                argv.append(value)
            if not Path(argv[0]).is_absolute():
                raise HarnessError('게이트 실행 파일은 확인한 절대경로를 사용하세요')
            lockdir = Path(os.environ.get('ASHFALL_LOCK_DIR', str(Path(tempfile.gettempdir()) / 'ashfall-harness-locks')))
            key = digest({'project': os.path.normcase(str(stage.resolve()))})
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            with FileLock(lockdir / (key + '.lock'), 'Unity/verification:' + str(stage)):
                info = run_process(argv, stage, '', gate.get('timeout_seconds', 300), folder / 'stdout.txt', folder / 'stderr.txt', env)
            report['process'] = info
            if info['timed_out'] or info['exit_code'] != 0:
                raise HarnessError('검증 명령 오류/중단')
            if gate['kind'] == 'unity_nunit':
                report['counts'] = parse_nunit(folder / 'results.xml', gate.get('minimum_tests', 1), gate.get('required_test_names', []))
            elif gate['kind'] == 'json_checks':
                from .json_gate import parse_json_checks
                report['counts'] = parse_json_checks(folder / 'stdout.txt', gate.get('minimum_tests', 1), gate.get('required_test_names', []))
            else:
                report['counts'] = parse_unittest(folder / 'stdout.txt', folder / 'stderr.txt', gate.get('minimum_tests', 1))
            if digest(scan(stage, config['source_roots'])) != meta['seal_sha256']:
                raise HarnessError('검증 중 소스 변경: 결과를 이전 seal의 PASS로 사용할 수 없습니다')
            report['status'] = 'PASS'
        except (HarnessError, OSError, ValueError) as exc:
            report.update(status='FAIL' if gate.get('enabled') else 'BLOCKED', error=str(exc))
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.name != 'report.json':
                report['artifacts'].append({'path': str(p.relative_to(run)), 'sha256': sha_bytes(p.read_bytes())})
        atomic_json(folder / 'report.json', report)
        event(run, 'GATE_FINISHED', gate=name, status=report['status'])
        return report


def attest(run: Path, name: str, evidence: Path, note: str, identity: str, passed: bool, confirmed: bool) -> dict:
    if not confirmed or not note.strip() or (not identity.strip()):
        raise HarnessError('실제 수행 확인·담당자·관찰 내용을 입력하세요')
    with FileLock(run / 'coordinator.lock', 'run coordinator'):
        meta, config, gate, stage, folder = _start(run, name)
        if not gate.get('enabled'):
            raise HarnessError('비활성 사람 검사에는 확인 기록을 등록할 수 없습니다')
        if gate['kind'] != 'manual':
            raise HarnessError('자동 게이트를 사람 선언으로 대체할 수 없습니다')
        if not evidence.is_file() or evidence.stat().st_size == 0:
            raise HarnessError('비어 있지 않은 증거 파일 필요')
        dest = folder / ('human-evidence' + evidence.suffix.lower())
        dest.write_bytes(evidence.read_bytes())
        report = {'gate': name, 'status': 'PASS' if passed else 'FAIL', 'basis': 'human_attestation_NOT_machine_verified', 'identity': identity, 'note': note, 'at': time.time(), 'seal_id': meta['seal_id'], 'seal_sha256': meta['seal_sha256'], 'artifacts': [{'path': str(dest.relative_to(run)), 'sha256': sha_bytes(dest.read_bytes())}]}
        atomic_json(folder / 'report.json', report)
        event(run, 'HUMAN_ATTESTED', gate=name, identity=identity, status=report['status'])
        return report


def integrate(run: Path, name: str, execute: bool) -> dict:
    """Execute one pre-reviewed local integration command, never arbitrary model text.

    Success here means the command exited cleanly, NOT that the scene or game passed QA.
    Even a failed integration invalidates the former seal; there is no automatic rollback.
    """
    if not execute:
        raise HarnessError('명령 검토 후 --execute-approved-commands가 필요합니다')
    with FileLock(run / 'coordinator.lock', 'run coordinator'):
        meta = read_json(run / 'run.json')
        _, config = assert_config_unchanged(run, meta)
        commands = config.get('integration_commands', {})
        if name not in commands or not meta.get('stage'):
            raise HarnessError('등록된 통합 명령과 stage가 필요합니다')
        spec = commands[name]
        if not spec.get('enabled') or not spec.get('argv'):
            raise HarnessError('통합 명령을 아직 연결하지 않았습니다')
        folder = run / 'integration' / f'{time.time_ns():020d}-{uuid.uuid4().hex[:8]}'
        folder.mkdir(parents=True)
        stage = Path(meta['stage'])
        before = scan(stage, config['source_roots'])
        meta.pop('seal_sha256', None)
        meta.pop('seal_id', None)
        meta['status'] = 'INTEGRATING'
        atomic_json(run / 'run.json', meta)
        report = {'action': name, 'before_sha256': digest(before), 'status': 'FAILED', 'game_verification': 'NOT RUN'}
        try:
            tokens = {'{python}': os.sys.executable, '{project}': str(stage), '{log_file}': str(folder / 'editor.log')}
            argv = []
            for item in spec['argv']:
                if not isinstance(item, str):
                    raise HarnessError('통합 argv는 문자열 배열')
                value = item
                for k, v in tokens.items():
                    value = value.replace(k, v)
                if '{' in value or '}' in value:
                    raise HarnessError('통합 명령 자리표시자 불일치')
                argv.append(value)
            if not Path(argv[0]).is_absolute():
                raise HarnessError('확인한 절대 실행 파일 경로 필요')
            lockdir = Path(os.environ.get('ASHFALL_LOCK_DIR', str(Path(tempfile.gettempdir()) / 'ashfall-harness-locks')))
            key = digest({'project': os.path.normcase(str(stage.resolve()))})
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            with FileLock(lockdir / (key + '.lock'), 'Unity/integration:' + str(stage)):
                report['process'] = run_process(argv, stage, '', spec.get('timeout_seconds', 300), folder / 'stdout.txt', folder / 'stderr.txt', env)
            if report['process']['timed_out'] or report['process']['exit_code'] != 0:
                raise HarnessError('통합 명령 오류/중단. 자동 재실행하지 않습니다')
            report['status'] = 'EXECUTED_NOT_VERIFIED'
        except (HarnessError, OSError, ValueError) as exc:
            report['error'] = str(exc)
        report['after_sha256'] = digest(scan(stage, config['source_roots']))
        report['artifacts'] = [{'path': str(p.relative_to(run)), 'sha256': sha_bytes(p.read_bytes())} for p in sorted(folder.iterdir()) if p.is_file()]
        atomic_json(folder / 'report.json', report)
        meta['status'] = 'INTEGRATION_NEEDS_REVIEW'
        atomic_json(run / 'run.json', meta)
        event(run, 'INTEGRATION_FINISHED', action=name, status=report['status'])
        return report
