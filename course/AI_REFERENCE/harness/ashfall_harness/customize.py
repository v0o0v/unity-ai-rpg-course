"""새 설정 사본에 역할을 추가한다. 실행 중인 run 설정을 고치지 않는다."""
from __future__ import annotations
import copy
import re
from .common import HarnessError, safe_relative, is_inside, sensitive_path
from .engine import validate_config

def add_role(config: dict, name: str, title: str, mission: str, paths: list[str]) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}",name) or name in config["roles"]:
        raise HarnessError("새 역할 ID가 유효하지 않거나 이미 있습니다")
    if not title.strip() or not mission.strip():
        raise HarnessError("역할의 목적과 이름을 써야 합니다")
    for path in paths:
        safe_relative(path)
        if sensitive_path(path) or not any(is_inside(path,r) for r in config["source_roots"]):
            raise HarnessError("역할 쓰기 범위가 원본 범위를 벗어납니다")
        if any(p.casefold() in {"packages","projectsettings","library","harness"} for p in path.split("/")):
            raise HarnessError("보호 경로는 새 역할에도 허용하지 않습니다")
    result=copy.deepcopy(config)
    result["roles"][name]={"title":title,"mission":mission,"write_prefixes":paths,
        "deliverable":"검토 가능한 작은 변경안 또는 진단 보고서","delegate":False,
        "never":"실제 실행·배포 승인 및 검증 결과를 스스로 선언하지 않는다"}
    validate_config(result)
    return result
