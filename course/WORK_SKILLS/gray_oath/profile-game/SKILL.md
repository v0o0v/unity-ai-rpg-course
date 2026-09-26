---
name: profile-game
description: 프레임 저하·로딩 끊김·메모리 증가·Android 발열 분석 요청에 사용합니다.
---

실제 기기/빌드/quality/seed/카메라 경로/측정 구간을 고정하고 baseline을 먼저 수집한다. PC60/Android30은 목표이며 실측은 별도로 적는다.
CPU main/render wait와 계산·GPU·GC·memory·loading을 나눈다. ProfilerMarker/FrameDebugger/MemoryProfiler/지원 분석기를 설치본에 맞게 사용한다. Deep Profile 오버헤드와 GPU 미지원 측정은 명시한다.
같은 시나리오를 반복하고 평균·p50/p95/p99·최대·표본수를 비교한다. 한 번에 한 가설의 변경만 수행한다. 적 반응·위험 표시·대화·저장 같은 게임 기능을 낮춰 수치를 맞추지 않는다.
Android 장시간 실제 기기 검사는 사람 조작과 기록을 준비한다. 미측정 온도/전력/기기를 만들어내지 않는다. 최종 현재 소스에서 기능 회귀와 성능을 함께 보고한다.
