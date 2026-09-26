from pathlib import Path
import json
from ashfall_harness.common import read_json
from ashfall_harness.customize import add_role

def main():
    base=Path(__file__).resolve().parents[1]
    config=read_json(base/"config/roles15.demo.json")
    derived=add_role(config,"catalog_auditor","콘텐츠 ID 검수","ID 중복과 잘못된 참조를 검토한다",["Docs/CatalogAudit"])
    out=base/"config/catalog.demo.json"
    with out.open("x",encoding="utf-8") as f:
        json.dump(derived,f,ensure_ascii=False,indent=2)
    print(out)

if __name__=="__main__":main()
