"""독립 도구의 구조화된 검사 결과를 읽는다. summary=PASS는 믿지 않는다."""
from pathlib import Path
from .common import HarnessError, read_json

def parse_json_checks(path: Path, minimum: int = 1, required_names: list[str] | None = None) -> dict:
    if isinstance(minimum,bool) or not isinstance(minimum,int) or minimum<1:
        raise HarnessError("최소 검사는 양의 정수여야 합니다")
    if not path.is_file() or path.stat().st_size>2_000_000:
        raise HarnessError("현재 JSON 검사 결과 없음/크기 초과")
    value=read_json(path)
    if not isinstance(value,dict) or value.get("schema_version")!=1 or not isinstance(value.get("checks"),list):
        raise HarnessError("JSON 검사 형식 오류")
    names=set()
    for check in value["checks"]:
        if not isinstance(check,dict) or set(check)!={"id","passed","detail"}:
            raise HarnessError("검사 case 필드 불일치")
        name=check["id"]
        if not isinstance(name,str) or not name.strip() or name in names:
            raise HarnessError("검사 이름 누락/중복")
        names.add(name)
        if check["passed"] is not True or not isinstance(check["detail"],str):
            raise HarnessError("실패하거나 불명확한 검사: "+name)
    if len(names)<minimum or set(required_names or [])-names:
        raise HarnessError("필수 검사 누락/0개 검사")
    return {"passed":len(names),"passed_names":sorted(names),"framework":"json_checks"}
