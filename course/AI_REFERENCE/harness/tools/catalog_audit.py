"""실제 카탈로그 JSON의 ID·참조를 검사하는 로컬 명령. 게임 실행 검사는 아니다."""
import argparse
import json
from pathlib import Path

def inspect_catalog(value):
    items=value.get("items",[])
    ids=[x.get("id") for x in items if isinstance(x,dict)]
    names={x for x in ids if isinstance(x,str)}
    checks=[
        {"id":"items_present","passed":isinstance(items,list) and len(items)>0,"detail":"items가 비어 있지 않아야 한다"},
        {"id":"ids_unique","passed":len(ids)==len(items) and all(isinstance(x,str) and bool(x.strip()) for x in ids) and len(ids)==len(names),"detail":"모든 ID는 비어 있지 않은 고유 문자열"},
        {"id":"references_valid","passed":all(isinstance(x,dict) and (x.get("upgrade_to") is None or x.get("upgrade_to") in names) for x in items),"detail":"upgrade_to는 존재하는 아이템을 가리킨다"}]
    return {"schema_version":1,"checks":checks}

def main():
    p=argparse.ArgumentParser();p.add_argument("catalog",type=Path);a=p.parse_args()
    try:
        result=inspect_catalog(json.loads(a.catalog.read_text(encoding="utf-8-sig")))
    except (OSError,ValueError,TypeError,AttributeError):
        result={"schema_version":1,"checks":[{"id":"input_readable","passed":False,"detail":"카탈로그 읽기 실패"}]}
    print(json.dumps(result,ensure_ascii=False))
    return 0 if all(x["passed"] for x in result["checks"]) else 1

if __name__=="__main__":raise SystemExit(main())
