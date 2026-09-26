---
name: asset-workbench
description: Unity 내부 모델·Meshy 생성·리깅·아트 도입 요청에 사용합니다.
---

내부 모델 도구와 Meshy 작업대를 대안으로 제시한다. 내부 제작만으로 최소 플레이 외형을 완성할 수 있게 한다. Meshy 사용은 실제 공식 API/현재 계정/비용/참조 권리 확인 후 별도 승인한다.
키는 로컬 제작 broker가 관리하며 Editor 자산이나 Player 빌드에 넣지 않는다. taskId와 입력 hash를 저장하고 timeout/reload 뒤 중복 제출하지 않는다. 비용 미상은0으로 보고하지 않는다.
실제 결과 파일을 내려받아 hash/출처/제작 조건/변환 이력을 남긴다. 인간형과 비인간형 리그를 구분한다. 임포트한 모델의 축·1m 단위·피벗·UV·PBR·material 수·bone/Avatar·애니메이션·collider·LOD·bounds를 확인한다.
그림이 좋아 보인다는 이유로 production-ready라고 판정하지 않는다. 승인한 candidate를 기존 VisualRoot에 연결하고 실제 움직임과 성능을 검증한다. 검증을 못 하면 외형 준비 상태까지만 보고한다.
