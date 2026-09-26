"""퀘스트 참조/보상 중복 검사용 실제 확장 게이트."""
import argparse
import json
from pathlib import Path

def audit(value: dict) -> dict:
    quests=value.get("quests",[])
    ids=[q.get("id") for q in quests if isinstance(q,dict)]
    known={x for x in ids if isinstance(x,str)}
    seen_rewards=set();unique_rewards=True
    for q in quests:
        if not isinstance(q,dict):unique_rewards=False;continue
        reward=q.get("reward_key")
        if not isinstance(reward,str) or not reward.strip() or reward in seen_rewards:unique_rewards=False
        else:seen_rewards.add(reward)
    checks=[{"id":"quest_ids","passed":bool(ids) and len(ids)==len(quests)==len(known) and all(isinstance(x,str) and bool(x.strip()) for x in ids),"detail":"고유 퀘스트 ID"},
            {"id":"next_exists","passed":all(isinstance(q,dict) and (q.get("next") is None or q.get("next") in known) for q in quests),"detail":"후속 참조가 존재"},
            {"id":"reward_keys_unique","passed":unique_rewards and bool(quests),"detail":"한 번 지급 보상 키가 퀘스트 사이에서 고유"}]
    return {"schema_version":1,"checks":checks}

def main():
    p=argparse.ArgumentParser();p.add_argument("path",type=Path);a=p.parse_args()
    try:result=audit(json.loads(a.path.read_text(encoding="utf-8-sig")))
    except (OSError,ValueError,TypeError,AttributeError):result={"schema_version":1,"checks":[{"id":"read","passed":False,"detail":"입력 오류"}]}
    print(json.dumps(result,ensure_ascii=False));return 0 if all(x["passed"] for x in result["checks"]) else 1
if __name__=="__main__":raise SystemExit(main())
