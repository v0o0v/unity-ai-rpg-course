# Sprite Editor — 그림 경계·테두리·기준점 구분하기

한 이미지에서 사용할 그림 영역과 그림의 기준점을 읽습니다. 같은 캐릭터의 여러 프레임을 연결할 때 기준점이 달라지면 발이 흔들리는 것처럼 보일 수 있습니다.

**공식 문서 기준:** Unity Manual 6.3. 전체 창이 아니라 공식 문서에 실린 Sprite Editor 선택 영역의 확대 예시입니다. 캡처 빌드는 미표기입니다.

![Unity 공식 문서의 실제 UI 예시 — 내 프로젝트 실행 결과 아님](https://docs.unity3d.com/6000.3/Documentation/uploads/Main/sprite-editor_sprite-selected.jpg)

**출처:** [Unity Technologies · Unity Documentation](https://docs.unity3d.com/6000.3/Documentation/Manual/sprite/sprite-editor/sprite-editor-window-reference.html) · [원본 이미지](https://docs.unity3d.com/6000.3/Documentation/uploads/Main/sprite-editor_sprite-selected.jpg) · [이용 조건](https://unity.com/legal/docs-terms). 원본 수정 없음. 사진은 온라인에서 읽습니다.

## 화면 읽기

### 1. A · 파란 선택 경계

선택한 스프라이트의 사각 영역입니다. 이미지 전체와 개별 스프라이트 영역을 구분합니다.

### 2. B · 초록 Border

9-slicing에 쓰는 테두리 설정입니다. 이동을 막는 Collider 경계가 아닙니다. 그림 경계와 충돌을 같은 것으로 해석하지 않습니다.

### 3. C · Pivot

배치·회전 등에 사용하는 기준점입니다. 발 기준으로 맞춘 캐릭터 프레임은 이 값과 실제 그림 속 발 위치를 함께 확인합니다.

## 잠깐 확인하기

초록 선을 넓히면 적과의 충돌 범위도 커질까요? 아닙니다. Border와 Collider는 별도의 설정이므로 AI가 실제 충돌 컴포넌트도 따로 확인해야 합니다.

## 이 화면이 증명하지 않는 것

그림은 암석 타일 예시입니다. 발 기준 캐릭터의 완성 예제나 학생이 만든 시트가 아닙니다. 이 화면만으로 애니메이션 연속성을 통과시키지 않습니다.

## 내 프로젝트의 실제 창 확인 요청

공식 예시와 실제 프로젝트가 같은지, 캡처 기능이 연결되어 있는지 확인하기 위한 추가 요청입니다. 구현·설정 변경은 자동 승인하지 않습니다.

```text
현재 프로젝트에서 실제 사용 중인 스프라이트나 시트를 찾아 Sprite Editor의 선택 영역·Border·Pivot과 Import 설정을 보여 줘. 그림 영역과 Collider를 구분하고, 캐릭터 프레임이라면 발 기준이 일관되는지 설명해 줘. 아직 자산이 없으면 없다고 알려 주고 공식 예시를 내 결과로 쓰지 마. 설정은 승인 없이 바꾸지 마.
화면을 보여 줄 수 있는 도구가 있다면 실제 창을 캡처해 새 파일로 남기고 파일 경로·프로젝트·버전·현재 상태를 함께 알려 줘. 민감정보가 보이면 먼저 안전한 화면으로 준비해 줘. 캡처 도구가 없으면 연결이 없다고 설명하고 AI가 그린 가짜 Editor 화면으로 대신하지 마. 코드를 직접 입력하도록 요구하지 마.
```

기존 실습과 필수 검사는 유지합니다. 창 캡처가 없으면 없다고 기록하고 다른 그림으로 실행 결과를 만들어 채우지 않습니다.
