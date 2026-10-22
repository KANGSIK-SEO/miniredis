"""Mini Redis 명령어 파서 모듈.

터미널에서 사용자가 입력한 한 줄의 텍스트를 공백과 따옴표 규칙에 맞게
토큰(단어) 목록으로 쪼개주는 역할을 담당합니다.

예시:
  SET user:1 "Alice"          -> ['SET', 'user:1', 'Alice']
  SET msg "Hello World"       -> ['SET', 'msg', 'Hello World']
  CONFIG SET maxmemory 100    -> ['CONFIG', 'SET', 'maxmemory', '100']
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import shlex
from typing import List


def tokenize(line: str) -> List[str]:
    """명령줄 문자열을 토큰 목록으로 파싱합니다.

    [특징]
    - 큰따옴표(")나 작은따옴표(')로 감싸진 문자열은 공백이 들어있더라도 하나의 인자로 온전히 묶어줍니다.
    - 닫히지 않은 따옴표 등 문법 오류가 있을 경우 사용자에게 명확한 에러 메시지를 전달할 수 있도록 예외를 던집니다.

    Args:
        line: 사용자가 입력한 원본 텍스트 한 줄

    Returns:
        파싱되어 분리된 토큰 문자열들의 리스트

    Raises:
        ValueError: 따옴표가 닫히지 않은 경우 등 구문 오류 발생 시
    """
    if not line or not line.strip():
        return []

    try:
        # posix=True 옵션을 주면 셸과 동일하게 따옴표를 벗겨내고 이스케이프 문자(\)를 해석합니다.
        return shlex.split(line.strip(), posix=True)
    except ValueError as exc:
        raise ValueError(f"ERR syntax error in quotation: {exc}") from exc
