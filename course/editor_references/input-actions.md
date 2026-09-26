# Input Actions — 입력 묶음·행동·값의 종류 읽기

왼쪽에서 사용할 입력 묶음을 고르고, 가운데에서 게임 행동을 고르며, 오른쪽에서 그 행동이 어떤 값을 받는지 읽는 화면입니다.

**공식 문서 기준:** Input System 패키지 1.17. 패키지 버전과 Unity Editor 버전은 다른 번호입니다. 설치된 Input System에 따라 표시가 달라질 수 있습니다.

![Unity 공식 문서의 실제 UI 예시 — 내 프로젝트 실행 결과 아님](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.17/manual/images/ActionsEditorCallout.png)

**출처:** [Unity Technologies · Unity Documentation](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.17/manual/ActionsEditor.html) · [원본 이미지](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.17/manual/images/ActionsEditorCallout.png) · [이용 조건](https://unity.com/legal/docs-terms). 원본 수정 없음. 사진은 온라인에서 읽습니다.

## 화면 읽기

### 1. A · Action Maps

Player와 UI처럼 역할이 다른 입력 묶음입니다. 메뉴를 열었을 때 어떤 묶음을 활성화하는지 실제 실행과 함께 확인합니다.

### 2. B · Actions

Move·Look·Attack 같은 행동입니다. 특정 키 이름이 아니라 게임이 받을 의도를 나타냅니다. 바인딩은 각 행동 아래에서 확인합니다.

### 3. C · Action Properties

선택한 Move의 Value·Vector2 설정이 보입니다. 이동 벡터와 누름 버튼을 혼동하지 않도록 출력 값의 종류를 확인합니다.

## 잠깐 확인하기

조이스틱과 키보드가 같은 Move에 연결되면 두 손가락 공격 검사도 끝난 걸까요? 아닙니다. 설정 화면 이후 실제 이동 유지·공격·각 손가락 해제를 별도로 시험합니다.

## 이 화면이 증명하지 않는 것

설정이 저장되어 있다는 사실과 런타임에 입력 묶음이 활성화됐다는 사실은 다릅니다. 이 그림은 모바일 터치 성공 증거가 아닙니다.

## 내 프로젝트의 실제 창 확인 요청

공식 예시와 실제 프로젝트가 같은지, 캡처 기능이 연결되어 있는지 확인하기 위한 추가 요청입니다. 구현·설정 변경은 자동 승인하지 않습니다.

```text
현재 플레이어가 실제로 참조하는 Input Actions 자산을 찾아 Maps·Move·Attack과 바인딩, Action Type·Control Type을 보여 줘. 사용하지 않는 예제 자산과 구분해 줘. 화면 확인은 설정 검사로만 기록하고, 실행 중 활성 맵과 모바일 동시 입력은 별도 확인 항목으로 남겨 줘. 바인딩이나 키 설정을 임의로 바꾸지 마.
화면을 보여 줄 수 있는 도구가 있다면 실제 창을 캡처해 새 파일로 남기고 파일 경로·프로젝트·버전·현재 상태를 함께 알려 줘. 민감정보가 보이면 먼저 안전한 화면으로 준비해 줘. 캡처 도구가 없으면 연결이 없다고 설명하고 AI가 그린 가짜 Editor 화면으로 대신하지 마. 코드를 직접 입력하도록 요구하지 마.
```

기존 실습과 필수 검사는 유지합니다. 창 캡처가 없으면 없다고 기록하고 다른 그림으로 실행 결과를 만들어 채우지 않습니다.
