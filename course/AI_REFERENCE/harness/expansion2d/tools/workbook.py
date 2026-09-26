"""Bind reviewed, real 2D project paths to the unchanged Ashfall 0.1 harness.

No model calls, game writes, approvals, or fabricated test results. Python 3.11+.
Path/anchor checks aid review; they are not semantic understanding or an OS sandbox.
"""
from __future__ import annotations
import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'harness'))
sys.path.insert(0, str(ROOT))
from ashfall_harness.common import HarnessError, child, digest, is_inside, read_json, safe_relative, scan, sensitive_path, sha_bytes
from ashfall_harness.engine import ALLOWED_EXT, validate_config, validate_plan, status
MAX_INPUT_BYTES = 550000
PROTECTED = {'.git', '.claude', 'packages', 'projectsettings', 'library', 'usersettings', 'harness'}

def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')

def _outside(project: Path, output: Path) -> None:
    if output.resolve().is_relative_to(project.resolve()) or project.resolve().is_relative_to(output.resolve()):
        raise HarnessError('출력과 프로젝트는 서로의 하위 폴더일 수 없습니다')

def inspect(project: Path, out: Path) -> dict:
    """List names and hashes, never send source text or guess semantic bindings."""
    project = project.resolve()
    _outside(project, out)
    for p in ['Assets', 'Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt']:
        if not child(project, p).exists():
            raise HarnessError(f'Unity 프로젝트 필수 경로 없음: {p}')
    manifest = scan(project, ['Assets', 'Packages', 'ProjectSettings', 'Docs'])
    scripts = [{'path': p, 'sha256': h} for p, h in manifest.items() if Path(p).suffix.lower() in {'.cs', '.asmdef'}]
    result = {'status': 'INVENTORY_ONLY_NOT_SEMANTICALLY_BOUND', 'source_sha256': digest(manifest), 'scripts': scripts, 'note': '목록은 2D 여부·호출 관계·실행 성공을 증명하지 않습니다.'}
    write_new(out, result)
    return result

def bind(project: Path, bindings: dict, recipe: dict, config: dict, out: Path, approved: bool) -> dict:
    project = project.resolve()
    out = out.resolve()
    _outside(project, out)
    if out.exists():
        raise HarnessError('기존 실행 계획 폴더 덮어쓰기 거부')
    if not approved:
        raise HarnessError('실제 경로와 의미를 읽은 뒤 --i-reviewed-bindings가 필요합니다')
    if bindings.get('mode') != '2D' or not str(bindings.get('reviewed_by', '')).strip():
        raise HarnessError('mode=2D와 실제 검토자 기록 필요')
    if bindings.get('status') != 'REVIEWED':
        raise HarnessError('바인딩의 status가 REVIEWED여야 합니다')
    validate_config(config)
    for p in ['Assets', 'Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt']:
        if not child(project, p).exists():
            raise HarnessError(f'Unity 프로젝트 필수 경로 없음: {p}')
    inputs = bindings.get('inputs', {})
    outputs = bindings.get('outputs', {})
    if not isinstance(inputs, dict) or not isinstance(outputs, dict):
        raise HarnessError('inputs/outputs 객체 필요')
    if set(inputs) & set(outputs):
        raise HarnessError('입력과 출력 alias 이름 충돌')
    expected = set(recipe.get('input_aliases', []))
    if expected != set(inputs):
        raise HarnessError('이 recipe의 input_aliases와 inputs가 정확히 일치해야 합니다')
    expected_out = set(recipe.get('output_aliases', []))
    if expected_out != set(outputs):
        raise HarnessError('이 recipe의 output_aliases와 outputs가 정확히 일치해야 합니다')
    table = {}
    observed = {}
    reasons = {}
    case_paths = {}
    for key, entry in inputs.items():
        if not isinstance(entry, dict):
            raise HarnessError('입력은 path/anchor/reason 객체')
        path = safe_relative(entry.get('path', ''))
        if sensitive_path(path):
            raise HarnessError('민감한 입력 경로')
        if not any((is_inside(path, r) for r in config['source_roots'])):
            raise HarnessError('source_roots 밖 입력')
        f = child(project, path)
        if not f.is_file():
            raise HarnessError(f'실제 입력 파일 없음: {path}')
        if f.stat().st_size > MAX_INPUT_BYTES:
            raise HarnessError('입력 파일이 너무 큼: 작은 계약으로 분리')
        try:
            text = f.read_text(encoding='utf-8-sig')
        except UnicodeError as exc:
            raise HarnessError('바인딩 입력은 UTF-8 텍스트만 지원') from exc
        anchor = entry.get('anchor', '')
        reason = entry.get('reason', '')
        if not isinstance(anchor, str) or not anchor.strip() or anchor not in text or (not str(reason).strip()):
            raise HarnessError(f'입력 anchor/reason 불일치: {key}')
        table[key] = path
        observed[path] = sha_bytes(f.read_bytes())
        reasons[key] = entry
    for key, path in outputs.items():
        path = safe_relative(path)
        if sensitive_path(path) or any((p.casefold() in PROTECTED for p in path.split('/'))):
            raise HarnessError('보호 경로 쓰기 거부')
        if Path(path).suffix.lower() not in ALLOWED_EXT:
            raise HarnessError('씬/메타/프리팹/바이너리 텍스트 출력 거부')
        if not any((is_inside(path, r) for r in config['source_roots'])):
            raise HarnessError('source_roots 밖 출력')
        f = child(project, path)
        if f.exists() and (not f.is_file()):
            raise HarnessError('출력 경로가 디렉터리')
        if f.exists() and path not in observed:
            raise HarnessError('기존 출력 파일을 입력에도 선언하세요: ' + path)
        table[key] = path
        observed.setdefault(path, None)
    for path in table.values():
        cf = path.casefold()
        if cf in case_paths and case_paths[cf] != path:
            raise HarnessError('대소문자 별칭 충돌')
        case_paths[cf] = path

    def resolve(value):
        if isinstance(value, str) and value.startswith('@'):
            if value[1:] not in table:
                raise HarnessError('정의되지 않은 alias: ' + value)
            return table[value[1:]]
        if isinstance(value, list):
            return [resolve(x) for x in value]
        if isinstance(value, dict):
            return {k: resolve(v) for k, v in value.items()}
        return value
    plan = resolve(copy.deepcopy(recipe['plan']))
    plan['binding_required'] = False
    ordered = validate_plan(plan, config)
    declared_outputs = {}
    byid = {t['id']: t for t in ordered}

    def ancestors(tid):
        result = set()
        for dep in byid[tid]['depends_on']:
            result.add(dep)
            result |= ancestors(dep)
        return result
    for t in ordered:
        declared = t.get('outputs', [])
        if set(declared) != set(t['write_prefixes']):
            raise HarnessError('실습 계획은 write_prefixes를 출력 파일 단위로 명시해야 합니다')
        for path in t['read_files']:
            if path not in table.values():
                raise HarnessError('바인딩에 없는 read_file')
            if child(project, path).is_file():
                continue
            if path not in declared_outputs or declared_outputs[path] not in ancestors(t['id']):
                raise HarnessError('선행 작업이 제공하지 않는 입력: ' + path)
        size = sum((child(project, p).stat().st_size for p in t['read_files'] if child(project, p).is_file()))
        if size > MAX_INPUT_BYTES:
            raise HarnessError('역할 입력이 너무 큼: read_files를 줄이세요')
        for path in declared:
            if path not in outputs.values():
                raise HarnessError('바인딩에 없는 output')
            declared_outputs[path] = t['id']
    reviews = [t for t in ordered if t['kind'] == 'review']
    if not any((set(declared_outputs) <= set(t['read_files']) for t in reviews)):
        raise HarnessError('최종 검토자의 read_files에 모든 제안 출력이 필요합니다')
    locked = {'schema_version': 1, 'mode': '2D', 'project': str(project), 'observed': observed, 'reviewed_by': bindings['reviewed_by'], 'input_reasons': reasons, 'plan_sha256': digest(plan), 'config_sha256': digest(config), 'note': '해시와 문자열 검사는 의미·컴파일·실기기 성공을 증명하지 않습니다.'}
    out.mkdir()
    write_new(out / 'plan.json', plan)
    write_new(out / 'config.json', config)
    write_new(out / 'binding.lock.json', locked)
    gaps = [k for k, v in config['gates'].items() if v.get('required') and (not v.get('enabled'))]
    write_new(out / 'gate_readiness.json', {'disabled_required_gates': gaps, 'unity_executed': False, 'model_called': False, 'status': 'BOUND_NOT_RUN'})
    return {'status': 'BOUND_NOT_RUN', 'plan': str(out / 'plan.json'), 'disabled_required_gates': gaps}

def verify(project: Path, lock: dict, plan: dict | None=None, config: dict | None=None) -> dict:
    if str(project.resolve()) != lock['project']:
        raise HarnessError('바인딩 프로젝트 불일치')
    for rel, expected in lock['observed'].items():
        p = child(project, rel)
        actual = sha_bytes(p.read_bytes()) if p.is_file() else None
        if p.exists() and (not p.is_file()):
            raise HarnessError('입출력 파일 자리에 디렉터리가 생겼습니다')
        if actual != expected:
            raise HarnessError('바인딩 이후 변경: ' + rel)
    if plan is not None and digest(plan) != lock['plan_sha256']:
        raise HarnessError('bound plan 변경')
    if config is not None and digest(config) != lock['config_sha256']:
        raise HarnessError('bound config 변경')
    return {'status': 'BINDING_UNCHANGED', 'game_verification': 'NOT RUN'}

def campaign(runs: list[Path], out: Path) -> dict:
    results = []
    for r in runs:
        try:
            s = status(r)
            results.append({'run': str(r), 'phase': s['phase'], 'gates': s['gates'], 'release_status': s['release_status'], 'provider': s['provider'], 'candidate_sha256': s.get('candidate_sha256'), 'cost_estimate_usd': s['cost_estimate_usd']})
        except (HarnessError, OSError, KeyError) as exc:
            results.append({'run': str(r), 'release_status': 'BLOCKED', 'error': str(exc)})
    report = {'status': 'HISTORY_ONLY_FINAL_INTEGRATION_REQUIRED', 'runs': results, 'note': '과거 run 합계는 최종 통합본 PASS가 아닙니다. 최종 소스에서 전체 검사를 다시 실행하세요.'}
    write_new(out, report)
    return report

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('inspect')
    a.add_argument('--project', type=Path, required=True)
    a.add_argument('--out', type=Path, required=True)
    a = sub.add_parser('bind')
    for k in ['project', 'bindings', 'recipe', 'config', 'out']:
        a.add_argument('--' + k, type=Path, required=True)
    a.add_argument('--i-reviewed-bindings', action='store_true')
    a = sub.add_parser('verify')
    for k in ['project', 'lock', 'plan', 'config']:
        a.add_argument('--' + k, type=Path, required=True)
    a = sub.add_parser('campaign')
    a.add_argument('--run', dest='runs', type=Path, action='append', required=True)
    a.add_argument('--out', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == 'inspect':
            result = inspect(a.project, a.out)
        elif a.cmd == 'bind':
            result = bind(a.project, read_json(a.bindings), read_json(a.recipe), read_json(a.config), a.out, a.i_reviewed_bindings)
        elif a.cmd == 'verify':
            result = verify(a.project, read_json(a.lock), read_json(a.plan), read_json(a.config))
        else:
            result = campaign(a.runs, a.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (HarnessError, OSError, ValueError, KeyError, TypeError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2
if __name__ == '__main__':
    raise SystemExit(main())
