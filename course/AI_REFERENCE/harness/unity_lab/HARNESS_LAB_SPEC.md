# 독립 전리품 표시 실습 규격
namespace는 HarnessLab. Runtime assembly HarnessLab.Runtime, Tests는 HarnessLab.Tests, Editor는 HarnessLab.Editor다.
Rarity=Normal,Magic,Rare / Filter=All,MagicPlus,RareOnly.
LootFilterPolicy.Visible(rarity,mode,quest,reveal)는 순수 bool: quest/reveal true 또는 미등록 enum은 표시. 그 외 희귀도 임계값으로 표시.
LootLabelView는 이름표 TextMesh만 활성화/비활성화. 부모 드롭과 BoxCollider2D는 건드리지 않는다.
FilterPanel은 독립 실습용 IMGUI 버튼 두 개로 All/RareOnly를 적용. 실제 게임의 터치/UGUI 완료가 아니다.
정적 public HarnessLab.Editor.BuildLootLab.Build가 새로운 LootLab.unity에 카메라, 드롭3개, 각 이름표, 조작 패널을 만들고 저장한다.
대상은 Assets/HarnessLab/Scenes/LootLab.unity 하나뿐이다. 원본이나 다른 게임 씬은 건드리지 않는다.
NUnit 메서드: HarnessLab.Tests.LootFilterTests.NormalHiddenByRareFilter, RareShownByRareFilter, QuestAlwaysVisible, RevealShowsEverything, UnknownModePreservesVisibility.
세 개 asmdef는 검토한 기준선에서 먼저 만들고 참조를 연결한다. 실제 Unity import/compile/test 결과로 검증한다.
