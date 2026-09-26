"""새 Unity 후보용 계획을 작성한다. .meta/씬은 Unity Editor가 생성한다."""
import argparse
import copy
import json
from pathlib import Path
from ashfall_harness.common import HarnessError, read_json, sha_bytes
from ashfall_harness.engine import validate_config, validate_plan

def prepare(source: Path, out: Path, mock: bool=False):
    source=source.resolve();out=out.resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise HarnessError("원본 밖의 새 출력 폴더 필요")
    for rel in ["Assets","Packages/manifest.json","ProjectSettings/ProjectVersion.txt"]:
        if not (source/rel).exists():raise HarnessError("실제 Unity 프로젝트가 필요합니다: "+rel)
    root=Path(__file__).resolve().parents[1]
    config=read_json(root/"config/unity.template.json")
    roles={
      "game_designer":["Docs/HarnessLab"],
      "gameplay_engineer":["Assets/HarnessLab/Runtime"],
      "qa_engineer":["Assets/HarnessLab/Tests"],
      "unity_integrator":["Assets/HarnessLab/Editor"],
      "critic":[]}
    config["roles"]={k:{**config["roles"][k],"write_prefixes":v} for k,v in roles.items()}
    # C# code references supplied asmdefs: learner creates reviewed assembly files in baseline via Editor first.
    source_inputs=["Docs/GAME_SPEC.md", "Docs/HARNESS_LAB_SPEC.md"]
    if any(not (source/p).is_file() for p in source_inputs):raise HarnessError("GAME_SPEC과 HARNESS_LAB_SPEC을 먼저 확인하세요")
    lab=root/"unity_lab"
    groups={"implementation":("gameplay_engineer",["Assets/HarnessLab/Runtime/LootFilterPolicy.cs","Assets/HarnessLab/Runtime/LootLabelView.cs","Assets/HarnessLab/Runtime/FilterPanel.cs"]),
            "qa":("qa_engineer",["Assets/HarnessLab/Tests/Editor/LootFilterTests.cs"]),
            "integration":("unity_integrator",["Assets/HarnessLab/Editor/BuildLootLab.cs"])}
    tasks=[];previous=[];written=[]
    for tid,(role,outputs) in groups.items():
        reads=list(dict.fromkeys(source_inputs+written+[p for p in outputs if (source/p).is_file()]))
        t={"id":tid,"role":role,"kind":"proposal","depends_on":previous[-1:],"read_files":reads,"write_prefixes":outputs,
           "instruction":"독립 HarnessLab 실습만 구현. 실제 게임 클래스 변경 금지. 레퍼런스 규격과 일치하는 작은 코드를 제안.",
           "acceptance":["이름표만 숨기고 드롭/충돌은 유지","실제 실행은 아직 NOT RUN","기존 게임 씬을 변경하지 않음"]}
        # Give live roles complete specifications/source references as explicit input files in Docs.
        if mock:
            t["mock_response"]={"outcome":"proposal","summary":"고정 C# 응답의 후보 적용 실습. Unity 실행 아님","files":[{"path":p,"expected_sha256":"$CURRENT","content":(lab/p).read_text(encoding="utf-8")} for p in outputs],"findings":[]}
        tasks.append(t);previous.append(tid);written.extend(outputs)
    tasks.append({"id":"review","role":"critic","kind":"review","depends_on":[previous[-1]],"read_files":source_inputs+written,"write_prefixes":[],
        "instruction":"전체 변경·규격·테스트·통합 코드를 검토. 구현하지 말고 미검증을 분리.","acceptance":["모든 변경 확인","기존 게임 보존","실행하지 않은 Unity 성공 주장 금지"]})
    if mock:tasks[-1]["mock_response"]={"outcome":"review_pass","summary":"고정 검토 응답. 실제 독립 검토 아님","files":[],"findings":[]}
    plan={"schema_version":1,"title":"HarnessLab 전리품 표시 실습","tasks":tasks}
    validate_config(config);validate_plan(plan,config)
    out.mkdir(parents=True)
    for name,value in [("plan.json",plan),("config.json",config)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"status":"PLAN_ONLY_COMMANDS_NOT_BOUND","mock":mock,"out":str(out)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--mock",action="store_true");a=p.parse_args()
    print(json.dumps(prepare(a.source,a.out,a.mock),ensure_ascii=False))
if __name__=="__main__":main()
