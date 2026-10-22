#!/usr/bin/env python3
"""Mini Redis 진입점 스크립트.

터미널에서 `python3 main.py` 명령어로 실행하면
대화형 Mini Redis CLI REPL이 시작됩니다.
"""

import sys
import os

# 현재 프로젝트 루트 디렉토리를 파이썬 모듈 검색 경로에 추가하여 어디서든 실행 가능하도록 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mini_redis.cli import repl

if __name__ == "__main__":
    repl()
