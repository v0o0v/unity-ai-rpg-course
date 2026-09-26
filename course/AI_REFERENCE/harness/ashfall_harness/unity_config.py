"""사람이 확인한 Unity Editor 실행 파일을 검사 명령에 연결한다. Unity 실행은 하지 않는다."""
from pathlib import Path
from .common import HarnessError

def editmode_gate(editor: Path, tests: list[str]) -> dict:
    editor=editor.resolve()
    if not editor.is_file() or editor.suffix.lower() in {".cmd",".bat"}:
        raise HarnessError("실제 Editor 실행 파일을 지정하세요")
    if not tests or not all(isinstance(t,str) and t.strip() for t in tests):
        raise HarnessError("실제로 실행할 필수 테스트 이름이 필요합니다")
    # -runTests owns completion/exit. Do not combine it with -quit.
    return {"kind":"unity_nunit","enabled":True,"required":True,
        "argv":[str(editor),"-batchmode","-nographics","-projectPath","{project}",
                "-runTests","-testPlatform","EditMode","-testFilter",";".join(tests),
                "-testResults","{result_xml}","-logFile","{log_file}"],
        "minimum_tests":len(tests),"required_test_names":tests,"timeout_seconds":600}

def integration_command(editor: Path, method: str) -> dict:
    editor=editor.resolve()
    if not editor.is_file() or editor.suffix.lower() in {".cmd",".bat"}:
        raise HarnessError("실제 Editor 실행 파일을 지정하세요")
    if not method or not all(p.isidentifier() for p in method.split(".")):
        raise HarnessError("정적 public Editor 메서드의 전체 이름이 필요합니다")
    return {"enabled":True,"argv":[str(editor),"-batchmode","-nographics","-quit",
        "-projectPath","{project}","-executeMethod",method,"-logFile","{log_file}"],"timeout_seconds":600}
