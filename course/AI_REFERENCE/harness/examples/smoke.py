"""학습자가 만든 실행기로 mock 역할 + 실제 5개 Python 검사를 끝까지 실행한다."""
from pathlib import Path
import argparse
import json
from ashfall_harness.common import HarnessError, read_json
from ashfall_harness.engine import init_run, run_tasks, stage, seal, status, dashboard
from ashfall_harness.evidence import run_gate

def smoke(base: Path) -> dict:
    base=base.resolve()
    if base.exists():raise HarnessError("새 결과 폴더를 지정하세요")
    root=Path(__file__).resolve().parents[1]
    if base.is_relative_to(root):raise HarnessError("결과는 하네스 소스 밖에 두세요")
    base.mkdir(parents=True)
    run=base/"run";candidate=base/"candidate"
    init_run(root/"examples/demo_project",run,read_json(root/"examples/demo.plan.json"),read_json(root/"config/demo.json"),"mock")
    result=run_tasks(run)
    # Fixed local teaching fixture only. This automatic approval is NOT used for live/generated code.
    stage(run,candidate,result["candidate_sha256"])
    seal(run,"교육용 고정 mock fixture의 자동 smoke. 라이브 후보 승인으로 재사용 금지")
    gate=run_gate(run,"demo_rules",True)
    report=status(run);report["gate_report"]=gate;report["dashboard"]=str(dashboard(run))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    report=smoke(a.out);print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report["gate_report"]["status"]=="PASS" else 3
if __name__=="__main__":raise SystemExit(main())
