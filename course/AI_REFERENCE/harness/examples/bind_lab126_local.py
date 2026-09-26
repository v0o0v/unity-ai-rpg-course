"""사람이 확인한 Editor 경로를 독립 실습 config에 기록한다. 아직 실행하지 않는다."""
import sys
from pathlib import Path
from ashfall_harness.common import read_json, atomic_json
from ashfall_harness.engine import validate_config
from ashfall_harness.unity_config import editmode_gate, integration_command

editor = Path(sys.argv[1])
config_path = Path(sys.argv[2])
config = read_json(config_path)
required = [
    "HarnessLab.Tests.LootFilterTests.NormalHiddenByRareFilter",
    "HarnessLab.Tests.LootFilterTests.RareShownByRareFilter",
    "HarnessLab.Tests.LootFilterTests.QuestAlwaysVisible",
    "HarnessLab.Tests.LootFilterTests.RevealShowsEverything",
    "HarnessLab.Tests.LootFilterTests.UnknownModePreservesVisibility",
]
config["gates"]["editmode"] = editmode_gate(editor, required)
config["integration_commands"]["integrate_scene"] = integration_command(
    editor, "HarnessLab.Editor.BuildLootLab.Build")
validate_config(config)
atomic_json(config_path, config)
print("명령 연결 완료. 실행과 Unity 검증은 아직 NOT RUN.")
