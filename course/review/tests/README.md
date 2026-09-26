# 검토용 실행 자료

학생은 index.html을 읽습니다. 코드·명령은 AI가 처리하며 이 폴더를 직접 수정하거나 명령을 입력할 학습 과제가 없습니다.

검토 에이전트가 test_course_content.py를 Python으로 실행하면 현재 패키지와 동봉한 이전 데이터·원본 해시를 대조합니다. BeautifulSoup이 필요합니다. test_reader.py는 Playwright와 Chromium이 필요한 웹 읽기 검사이며, 코드에 명시된 /usr/bin/chromium 경로는 실제 환경에 맞게 AI가 확인해야 합니다. 이 제작 환경은 Chromium set_content 방식이며 Windows file://·OS 클립보드·원격 AI·Unity를 실행한 검사가 아닙니다.

기존 하네스 테스트는 AI_REFERENCE/validate_references.py, 퀘스트 참고 처리는 AI_REFERENCE/GRAY_OATH/test_quest_reference.py에 있습니다. 실제 Unity 런타임 테스트와 혼동하지 않습니다. 비교 데이터는 검토용 원본이며 학생이 만든 하네스 대신 실행하면 안 됩니다.
