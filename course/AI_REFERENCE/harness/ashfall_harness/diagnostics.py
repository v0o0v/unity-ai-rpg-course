"""저장된 실행 상태를 읽어 사람이 취할 다음 조치를 설명한다. 상태를 바꾸지 않는다."""
from pathlib import Path
from .common import read_json

def diagnose(run: Path) -> dict:
    meta=read_json(run/"run.json")
    state=read_json(run/"state.json")
    messages=[]
    if meta.get("budget_unknown"):
        messages.append("STOP_BUDGET_UNKNOWN: 비용 확인 전 새 모델 호출 금지")
    for task, entry in state.items():
        s=entry["status"]
        if s=="RUNNING":
            messages.append(f"{task}: 프로세스 종료를 확인한 뒤 recover; TTL로 잠금 탈취 금지")
        elif s in {"FAILED","BLOCKED","REVIEW_FAILED","INTERRUPTED"}:
            messages.append(f"{task}: 실패 attempt 보존; 같은 입력 transient 오류만 retry, 요구/코드 변경은 새 run")
    return {"actions":messages,"state_changed":False,"automatic_retry":False}
