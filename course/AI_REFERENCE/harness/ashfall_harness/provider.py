'Provider adapter. The real CLI path is opt-in and NOT verified against a paid account here.'

from __future__ import annotations

import json

import os

import shutil

import signal

import subprocess

import sys

import time

from pathlib import Path

from .common import HarnessError, atomic_json, canonical_json

SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'task_id': {'type': 'string'}, 'input_sha256': {'type': 'string'}, 'outcome': {'type': 'string', 'enum': ['proposal', 'review_pass', 'review_fail', 'blocked']}, 'summary': {'type': 'string'}, 'files': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'path': {'type': 'string'}, 'expected_sha256': {'type': ['string', 'null']}, 'content': {'type': 'string'}}, 'required': ['path', 'expected_sha256', 'content']}}, 'findings': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['task_id', 'input_sha256', 'outcome', 'summary', 'files', 'findings']}


def run_process(argv: list[str], cwd: Path, stdin: str, timeout: float, stdout: Path, stderr: Path, env: dict | None=None) -> dict:
    """No shell. Stdout/stderr go to files so a verbose process cannot fill RAM."""
    if not argv or not all((isinstance(s, str) for s in argv)):
        raise HarnessError('명령은 문자열 배열이어야 합니다')
    if Path(argv[0]).suffix.casefold() in {'.cmd', '.bat'}:
        raise HarnessError('자동 실행은 .cmd/.bat 대신 실제 실행 파일을 지정하세요')
    started = time.time()
    kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    timed_out = False
    with stdout.open('wb') as out, stderr.open('wb') as err:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=out, stderr=err, env=env, shell=False, **kwargs)
        try:
            proc.communicate(stdin.encode('utf-8'), timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.kill()
            proc.communicate(timeout=15)
    return {'argv': argv, 'cwd': str(cwd), 'started': started, 'finished': time.time(), 'exit_code': proc.returncode, 'timed_out': timed_out}


def command(config: dict) -> list[str]:
    executable = config['claude'].get('executable') or shutil.which('claude')
    if not executable:
        raise HarnessError('Claude CLI 실행 파일을 찾지 못했습니다')
    c = config['claude']
    flags = [str(executable), '-p', '--restricted', '--output-format', 'json', '--json-schema', json.dumps(SCHEMA), '--tools', 'Read,Glob,Grep', '--allowedTools', 'Read,Glob,Grep', '--disallowedTools', 'Bash,PowerShell,Edit,Write,Agent,Task,Skill,mcp__*', '--permission-mode', 'dontAsk', '--no-session-persistence', '--model', c['model'], '--effort', c['effort'], '--max-turns', str(c['max_turns']), '--max-budget-usd', str(c['call_budget_usd'])]
    mode = c.get('auth_mode', 'login')
    if mode == 'login':
        flags.append('--safe-mode')
    elif mode == 'api':
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise HarnessError('API 경로에는 ANTHROPIC_API_KEY가 필요합니다. 파일에 저장하지 마세요')
        flags.append('--bare')
    else:
        raise HarnessError('auth_mode는 login 또는 api여야 합니다')
    return flags


def doctor(config: dict) -> dict:
    argv = command(config)
    try:
        help_text = subprocess.run([argv[0], '--help'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, check=False)
        version = subprocess.run([argv[0], '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError(str(exc)) from exc
    need = sorted({s for s in argv[1:] if s.startswith('--')})
    missing = [s for s in need if s not in help_text.stdout]
    return {'executable': argv[0], 'version': version.stdout.strip(), 'missing_flags': missing, 'help_exit_code': help_text.returncode, 'model_requested': config['claude']['model'], 'model_access': 'NOT RUN', 'live_smoke': 'NOT RUN'}


def invoke(config: dict, prompt: str, task_dir: Path) -> tuple[dict, dict]:
    report = doctor(config)
    atomic_json(task_dir / 'doctor.json', report)
    if report['missing_flags'] or report['help_exit_code'] != 0:
        raise HarnessError('필수 CLI 옵션을 확인하지 못했습니다. 제한 옵션을 제거해 우회하지 마세요')
    workspace = task_dir / 'context'
    workspace.mkdir(exist_ok=True)
    (workspace / 'TASK_CONTEXT.txt').write_text(prompt, encoding='utf-8')
    env = os.environ.copy()
    for key in ['CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS', 'CLAUDE_CODE_SIMPLE', 'CLAUDE_CODE_EFFORT_LEVEL', 'ANTHROPIC_MODEL']:
        env.pop(key, None)
    info = run_process(command(config), workspace, prompt, config['claude']['timeout_seconds'], task_dir / 'stdout.json', task_dir / 'stderr.txt', env)
    atomic_json(task_dir / 'process.json', info)
    if info['timed_out'] or info['exit_code'] != 0:
        raise HarnessError('Claude 호출 중단/오류. 이번 호출의 사용량을 모르면 예약 예산을 유지합니다')
    output = task_dir / 'stdout.json'
    if output.stat().st_size > 4000000:
        raise HarnessError('CLI 출력 크기 제한 초과')
    try:
        raw = json.loads(output.read_text(encoding='utf-8'))
    except ValueError as exc:
        raise HarnessError('Claude stdout이 단일 JSON 객체가 아닙니다') from exc
    if not isinstance(raw, dict) or raw.get('is_error') or raw.get('subtype') not in (None, 'success'):
        raise HarnessError('Claude JSON 오류 상태')
    if raw.get('permission_denials'):
        raise HarnessError('권한 거부 기록이 있습니다. 완료로 처리하지 않습니다')
    model_usage = raw.get('modelUsage')
    if not isinstance(model_usage, dict) or not model_usage:
        raise HarnessError('실제 사용 모델 메타데이터가 없습니다. 프롬프트 속 모델 자기소개는 증거가 아닙니다')
    expected = config['claude']['model']
    if any((k != expected and (not k.startswith(expected + '-')) for k in model_usage)):
        raise HarnessError('요청 모델과 사용 모델이 다릅니다. 결과 보존 후 설정을 확인하세요')
    value = raw.get('structured_output')
    if not isinstance(value, dict):
        raise HarnessError('structured_output이 없습니다')
    return (value, {'provider': 'claude', 'session_id': raw.get('session_id'), 'actual_models': list(model_usage), 'total_cost_usd_estimate': raw.get('total_cost_usd'), 'process': info})
