"""Mini Redis 대화형 REPL (CLI) 모듈.

사용자가 터미널에서 `mini-redis> ` 프롬프트와 상호작용하며
명령어를 입력하고 즉시 실행 결과를 확인할 수 있는 REPL(Read-Eval-Print Loop) 환경을 제공합니다.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from mini_redis.store import MiniRedisStore


def repl() -> None:
    """Mini Redis REPL 메인 실행 루프.

    - 사용자 입력을 읽어들이고(Read)
    - Store 엔진을 통해 명령을 실행하며(Eval)
    - Redis 표준 규격에 맞추어 결과를 화면에 출력합니다(Print).
    - `exit` 또는 `quit`을 입력하거나 EOF(Ctrl+D) / KeyboardInterrupt(Ctrl+C) 발생 시 안전하게 종료됩니다.
    """
    store = MiniRedisStore()

    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        stripped = line.strip()
        # 빈 줄 입력은 가볍게 무시하고 다시 프롬프트를 띄웁니다.
        if not stripped:
            continue

        # 종료 명령어 검사 (대소문자 무관)
        if stripped.lower() in ("exit", "quit"):
            break

        # 명령어 실행 및 결과 출력
        result = store.execute(line)
        if result is not None:
            print(result)


if __name__ == "__main__":
    repl()
