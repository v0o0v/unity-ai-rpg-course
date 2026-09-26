# AI 전용 구현 참고

학생에게 코드/JSON/명령 입력을 시키지 마세요. 실제 프로젝트를 읽고 현재 구현과 패키지를 확인한 뒤 후보에서 구현합니다. 이 폴더의 예시는 Unity 자산으로 자동 연결되어 있지 않습니다.

PRODUCT_SPEC는 범위, quest_catalog는28개 이야기의 제작 brief, quest_draft_example은 H01의14노드 예시, editor_tools는23개 제작/진단 도구의 기대 결과입니다. 실제 데이터 ID와 저장·CLI 스키마는 조사한 프로젝트에 바인딩합니다. 없는 자산/명령을 이미 있는 것으로 가정하지 마세요.

AI 요청은 동일 requestId·projectId·baseRevision·schema를 추적하고 허용 DSL만 해석합니다. 셸/C# 실행 코드를 quest JSON에 받아 실행하지 마세요. 임시 stage→검증→diff→사람 승인→revision 재검사→백업→커밋→실제 테스트 순서를 지킵니다.

동봉 검증 reference는 파이썬 논리 예제이며 Unity runtime/Editor를 구현하거나 검증한 결과가 아닙니다. AI가 프로젝트 구현의 반례를 설계하는 참고로 사용합니다. 원본 Unity 프로젝트·기기·유료 생성·클라우드는 이 제작 환경에서 실행하지 않았습니다.
