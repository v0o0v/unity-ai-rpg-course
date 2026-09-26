"""작업 계약을 실행하는 CLI. 모델 응답을 명령으로 실행하지 않는다."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ashfall — 직접 만든 역할 하네스")
    commands = parser.add_subparsers(dest="cmd", required=True)
    sub = commands.add_parser('hello')
    sub = commands.add_parser('fingerprint')
    sub.add_argument("--json", type=Path, required=True)
    sub = commands.add_parser('snapshot')
    sub.add_argument("--source", type=Path, required=True)
    sub.add_argument("--out", type=Path, required=True)
    sub = commands.add_parser('roles')
    sub.add_argument("--config", type=Path, required=True)
    sub = commands.add_parser('validate')
    sub.add_argument("--plan", type=Path, required=True)
    sub.add_argument("--config", type=Path, required=True)
    sub = commands.add_parser('init')
    sub.add_argument("--source", type=Path, required=True)
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--plan", type=Path, required=True)
    sub.add_argument("--config", type=Path, required=True)
    sub.add_argument("--provider", choices=["mock","claude"], default="mock")
    sub = commands.add_parser('preview')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--task", required=True)
    sub.add_argument("--out", type=Path, required=True)
    sub = commands.add_parser('run')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--allow-paid", action="store_true")
    sub.add_argument("--retry-task")
    sub = commands.add_parser('stage')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--out", type=Path, required=True)
    sub.add_argument("--approve-hash", required=True)
    sub = commands.add_parser('seal')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--note", required=True)
    sub = commands.add_parser('gate')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--name", required=True)
    sub.add_argument("--execute-approved-gates", action="store_true")
    sub = commands.add_parser('status')
    sub.add_argument("--run", type=Path, required=True)
    sub = commands.add_parser('dashboard')
    sub.add_argument("--run", type=Path, required=True)
    sub = commands.add_parser('attest')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--name", required=True)
    sub.add_argument("--evidence", type=Path, required=True)
    sub.add_argument("--note", required=True)
    sub.add_argument("--by", required=True)
    sub.add_argument("--decision", choices=["PASS","FAIL"], required=True)
    sub.add_argument("--i-ran-this", action="store_true")
    sub = commands.add_parser('integrate')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--name", required=True)
    sub.add_argument("--execute-approved-commands", action="store_true")
    sub = commands.add_parser('doctor')
    sub.add_argument("--config", type=Path, required=True)
    sub = commands.add_parser('recover')
    sub.add_argument("--run", type=Path, required=True)
    sub.add_argument("--i-checked-no-child-processes", action="store_true")
    sub.add_argument("--note", required=True)
    sub = commands.add_parser('unlock')
    sub.add_argument("--lock-file", type=Path, required=True)
    sub.add_argument("--token", required=True)
    sub.add_argument("--i-checked-owner-stopped", action="store_true")
    sub = commands.add_parser('diagnose')
    sub.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    if hasattr(args, "run"):
        args.run = args.run.resolve()
    try:
        if args.cmd == 'hello':
            result = {"message": "내 하네스의 첫 실행", "provider": "NOT CONNECTED", "game_verification": "NOT RUN"}
        elif args.cmd == 'fingerprint':
            from .common import digest, read_json
            result = {"sha256": digest(read_json(args.json))}
        elif args.cmd == 'snapshot':
            from .common import scan, copy_manifest, digest, HarnessError
            if args.out.exists() or args.out.resolve().is_relative_to(args.source.resolve()) or args.source.resolve().is_relative_to(args.out.resolve()):
                raise HarnessError("원본 밖 새 목적지 폴더를 지정하세요")
            manifest = scan(args.source.resolve(), ["Game", "Tests", "Docs"])
            copy_manifest(args.source.resolve(), args.out.resolve(), manifest)
            result = {"files": len(manifest), "source_sha256": digest(manifest), "source_modified": False}
        elif args.cmd == 'roles':
            from .common import read_json
            result = read_json(args.config)["roles"]
        elif args.cmd == 'validate':
            from .common import read_json
            from .engine import validate_plan, validate_config
            config=read_json(args.config)
            validate_config(config)
            order=validate_plan(read_json(args.plan), config)
            result={"validation":"PASS","order":[t["id"] for t in order],"execution":"NOT RUN"}
        elif args.cmd == 'init':
            from .common import read_json
            from .engine import init_run
            result=init_run(args.source,args.run,read_json(args.plan),read_json(args.config),args.provider)
        elif args.cmd == 'preview':
            from .common import read_json, digest
            from .engine import validate_plan, dependency_order, prepare_task_view, make_prompt
            config=read_json(args.run/"config.json")
            order=validate_plan(read_json(args.run/"plan.json"),config)
            task=next(t for t in order if t["id"]==args.task)
            state=read_json(args.run/"state.json")
            manifest=prepare_task_view(args.run,args.out,task,dependency_order(task,order),state)
            text=make_prompt(task,config["roles"][task["role"]],args.out,manifest,digest(manifest))
            (args.out/"PROMPT.txt").write_text(text,encoding="utf-8")
            result={"prompt":str(args.out/"PROMPT.txt"),"model_called":False}
        elif args.cmd == 'run':
            from .engine import run_tasks
            result=run_tasks(args.run,allow_paid=args.allow_paid,retry_task=args.retry_task)
        elif args.cmd == 'stage':
            from .engine import stage
            result=stage(args.run,args.out,args.approve_hash)
        elif args.cmd == 'seal':
            from .engine import seal
            result=seal(args.run,args.note)
        elif args.cmd == 'gate':
            from .evidence import run_gate
            result=run_gate(args.run,args.name,args.execute_approved_gates)
        elif args.cmd == 'status':
            from .engine import status
            result=status(args.run)
        elif args.cmd == 'dashboard':
            from .engine import dashboard
            result={"dashboard":str(dashboard(args.run))}
        elif args.cmd == 'attest':
            from .evidence import attest
            result=attest(args.run,args.name,args.evidence,args.note,args.by,args.decision=="PASS",args.i_ran_this)
        elif args.cmd == 'integrate':
            from .evidence import integrate
            result=integrate(args.run,args.name,args.execute_approved_commands)
        elif args.cmd == 'doctor':
            from .common import read_json
            from .provider import doctor
            result=doctor(read_json(args.config))
        elif args.cmd == 'recover':
            from .common import HarnessError, FileLock, read_json, atomic_json, event
            if not args.i_checked_no_child_processes or not args.note.strip():
                raise HarnessError("프로세스 정리 확인과 복구 기록이 필요합니다")
            with FileLock(args.run/"coordinator.lock","recover"):
                state=read_json(args.run/"state.json")
                for value in state.values():
                    if value["status"]=="RUNNING":
                        value.update(status="INTERRUPTED",error="human recovery: "+args.note)
                atomic_json(args.run/"state.json",state)
                event(args.run,"RECOVERED",note=args.note)
            result={"status":"INTERRUPTED tasks recovered; no automatic retry"}
        elif args.cmd == 'unlock':
            from .common import HarnessError, read_json
            if not args.i_checked_owner_stopped: raise HarnessError("소유 프로세스 종료 확인 필요")
            lock=read_json(args.lock_file)
            if lock.get("token")!=args.token: raise HarnessError("소유 토큰 불일치")
            args.lock_file.unlink()
            result={"unlocked":str(args.lock_file),"basis":"human checked owner stopped"}
        elif args.cmd == 'diagnose':
            from .diagnostics import diagnose
            result=diagnose(args.run)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        expected = {"run": "PROPOSALS_REVIEWED", "gate": "PASS", "integrate": "EXECUTED_NOT_VERIFIED"}
        if args.cmd in expected and result.get("status") != expected[args.cmd]:
            return 3
        return 0
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
