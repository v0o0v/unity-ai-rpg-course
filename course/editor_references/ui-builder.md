# UI Builder — 편집기 화면을 구성하는 기본 작업창

도구의 화면 요소·배치·속성을 나누어 읽는 공식 UI Builder 예시입니다. 수강생이 직접 UXML·USS를 작성하지 않고 AI가 화면과 동작을 연결합니다.

**공식 문서 기준:** Unity Manual 6.3. 그림 안에는 UI Builder 1.0.0-preview.11이 보이는 이전 UI 예시가 사용되었습니다. 현재 설치본의 동일 배치를 보장하지 않습니다.

![Unity 공식 문서의 실제 UI 예시 — 내 프로젝트 실행 결과 아님](https://docs.unity3d.com/6000.3/Documentation/uploads/Main/UIBuilder/UIBuilderAnnotatedMainWindow.png)

**출처:** [Unity Technologies · Unity Documentation](https://docs.unity3d.com/6000.3/Documentation/Manual/UIB-interface-overview.html) · [원본 이미지](https://docs.unity3d.com/6000.3/Documentation/uploads/Main/UIBuilder/UIBuilderAnnotatedMainWindow.png) · [이용 조건](https://unity.com/legal/docs-terms). 원본 수정 없음. 사진은 온라인에서 읽습니다.

## 화면 읽기

### 1. 2 · Hierarchy / 4 · Viewport

요소 트리와 미리보기입니다. 트리의 Start 버튼이 가운데 어느 영역에 대응하는지 연결해 봅니다.

### 2. 6 · Inspector

선택 요소의 이름·문구·배치 등을 확인합니다. 버튼이 보이는 것과 클릭 시 기능이 실행되는 것은 별개입니다.

### 3. 1 · StyleSheets / 3 · Library / 5 · 코드 미리보기

화면 스타일, 사용할 요소, UXML·USS 표현을 구분합니다. 자료에 코드가 보여도 학생이 직접 입력하는 과제가 아닙니다.

## 잠깐 확인하기

이 그림이 퀘스트 편집기의 완성 화면일까요? 아닙니다. 퀘스트 목록·노드·AI 초안·차이 비교·승인은 별도로 제작한 도구에서 실제로 열고 검사해야 합니다.

## 이 화면이 증명하지 않는 것

공식 예시의 TANKS 메뉴는 이 과정의 Quest Editor가 아닙니다. UI Toolkit 설명용이며 UGUI 인벤토리와 같은 제작 경로라고 가정하지 않습니다.

## 내 프로젝트의 실제 창 확인 요청

공식 예시와 실제 프로젝트가 같은지, 캡처 기능이 연결되어 있는지 확인하기 위한 추가 요청입니다. 구현·설정 변경은 자동 승인하지 않습니다.

```text
현재 제작 중인 Unity Editor 도구와 실제 UI 방식부터 확인해 줘. UI Toolkit이면 요소 트리·미리보기·속성의 연결을 보여 주고 UXML·USS·이벤트 연결은 네가 관리해 줘. 퀘스트 편집기가 이미 있으면 실제 창을 열어 목록·흐름·AI 초안 상태를 캡처해 줘. 아직 없으면 UI Builder 참고와 미구현 기능을 구분하고 존재하지 않는 완성 화면을 생성하지 마.
화면을 보여 줄 수 있는 도구가 있다면 실제 창을 캡처해 새 파일로 남기고 파일 경로·프로젝트·버전·현재 상태를 함께 알려 줘. 민감정보가 보이면 먼저 안전한 화면으로 준비해 줘. 캡처 도구가 없으면 연결이 없다고 설명하고 AI가 그린 가짜 Editor 화면으로 대신하지 마. 코드를 직접 입력하도록 요구하지 마.
```

기존 실습과 필수 검사는 유지합니다. 창 캡처가 없으면 없다고 기록하고 다른 그림으로 실행 결과를 만들어 채우지 않습니다.
