# Editor 전체 배치 — 어디를 보고 있는지 구분하기

왼쪽 목록, 가운데 두 화면, 오른쪽 설정을 먼저 구분합니다. 창의 위치를 그대로 따라 만드는 것이 아니라 각 창이 무엇을 보여 주는지 읽는 참고입니다.

**공식 문서 기준:** Unity Manual 2022.3. 이전 버전의 공식 배치 예시입니다. Unity 6.3 설치본과 메뉴·아이콘·배치가 다를 수 있습니다.

![Unity 공식 문서의 실제 UI 예시 — 내 프로젝트 실행 결과 아님](https://docs.unity3d.com/2022.3/Documentation/uploads/Main/using-editor-window.png)

**출처:** [Unity Technologies · Unity Documentation](https://docs.unity3d.com/2022.3/Documentation/Manual/UsingTheEditor.html) · [원본 이미지](https://docs.unity3d.com/2022.3/Documentation/uploads/Main/using-editor-window.png) · [이용 조건](https://unity.com/legal/docs-terms). 원본 수정 없음. 사진은 온라인에서 읽습니다.

## 화면 읽기

### 1. B · Hierarchy

현재 씬의 오브젝트 목록입니다. 이 예시에서는 Camera가 선택되어 오른쪽 F의 Camera 설정과 연결됩니다.

### 2. C · Game / D · Scene

C는 카메라로 본 결과, D는 장면을 편집하며 보는 시점입니다. Scene에 물체가 보인다는 사실만으로 Game에도 보이는 것은 아닙니다.

### 3. F · Inspector / G · Project

F는 선택 대상의 설정이고 G는 프로젝트의 자산 목록입니다. 씬에 놓인 물건과 보관 중인 자산 파일을 구분해 봅니다.

## 잠깐 확인하기

캐릭터 파일은 있는데 플레이 화면에 없다면 무엇부터 확인할까요? AI에게 실제 열린 씬, Hierarchy의 배치, 활성 상태, 카메라가 보는 대상을 함께 조사하게 합니다.

## 이 화면이 증명하지 않는 것

이 화면의 3D 예제 장면은 Ashfall 또는 GrayOath의 실행 결과가 아닙니다. 2D 실습에서도 창의 역할을 읽는 참고로만 씁니다.

## 내 프로젝트의 실제 창 확인 요청

공식 예시와 실제 프로젝트가 같은지, 캡처 기능이 연결되어 있는지 확인하기 위한 추가 요청입니다. 구현·설정 변경은 자동 승인하지 않습니다.

```text
현재 실제 Unity 프로젝트와 열린 씬을 확인하고 Hierarchy·Scene·Game·Inspector·Project가 무엇을 보여 주는지 설명해 줘. 선택한 캐릭터 또는 카메라가 어느 설정에 연결되는지 실제 화면으로 보여 줘. 원본을 바꾸거나 새 예제를 만들지 말고, 프로젝트 이름·Editor 버전·Play 여부를 함께 기록해 줘.
화면을 보여 줄 수 있는 도구가 있다면 실제 창을 캡처해 새 파일로 남기고 파일 경로·프로젝트·버전·현재 상태를 함께 알려 줘. 민감정보가 보이면 먼저 안전한 화면으로 준비해 줘. 캡처 도구가 없으면 연결이 없다고 설명하고 AI가 그린 가짜 Editor 화면으로 대신하지 마. 코드를 직접 입력하도록 요구하지 마.
```

기존 실습과 필수 검사는 유지합니다. 창 캡처가 없으면 없다고 기록하고 다른 그림으로 실행 결과를 만들어 채우지 않습니다.
