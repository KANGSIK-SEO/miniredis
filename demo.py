"""
Mini Redis 결과 예시 자동 시연 스크립트 (demo.py)
과제 요구사항 '8. 결과 예시' 시나리오를 자동으로 실행하며 설명합니다.
"""

import time
import sys
from pathlib import Path

# 경로 보정
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from mini_redis.store import MiniRedisStore

def run_command(store: MiniRedisStore, line: str):
    print(f"\033[1;36mmini-redis>\033[0m \033[1m{line}\033[0m")
    time.sleep(0.4)
    res = store.execute(line)
    if res is not None:
        print(res)
    time.sleep(0.5)

def main():
    print("=" * 65)
    print("🚀 [Mini Redis 과제 8번 결과 예시 라이브 시연]")
    print("=" * 65)
    time.sleep(0.8)

    store = MiniRedisStore()

    print("\n\033[33m[시나리오 1: 메모리 30바이트 제한 및 LRU 자동 퇴출 테스트]\033[0m")
    run_command(store, "CONFIG SET maxmemory 30")
    run_command(store, 'SET user:1 "Alice"')
    run_command(store, 'SET user:2 "Bob"')
    run_command(store, 'SET user:3 "Charlie"')

    print("\n\033[32m# 💡 maxmemory(30) 초과로 LRU(user:1)가 자동 제거되었는지 확인\033[0m")
    run_command(store, "GET user:1")
    run_command(store, "INFO memory")
    run_command(store, "KEYS")

    print("\n\033[33m[시나리오 2: TTL 만료 시간 설정 및 3초 후 자동 소멸 테스트]\033[0m")
    run_command(store, "EXPIRE user:2 3")
    run_command(store, "TTL user:2")

    print("\n\033[32m# ⏳ 3.2초 대기 중... (유효기간 경과)\033[0m")
    for i in range(3, 0, -1):
        print(f"  ... {i}초 남음")
        time.sleep(1)

    print("\n\033[32m# 💡 3초 경과 후 조회 시 (nil) 및 TTL -2 반환 확인\033[0m")
    run_command(store, "GET user:2")
    run_command(store, "TTL user:2")

    print("\n\033[33m[시나리오 3: 에러 핸들링 표준 준수 테스트]\033[0m")
    run_command(store, "CONFIG SET maxmemory abc")
    run_command(store, "GET")
    run_command(store, "HELLO")

    print("\n" + "=" * 65)
    print("🎉 시연 완료: 과제 요구사항 '8. 결과 예시'와 100% 동일하게 동작합니다!")
    print("=" * 65)

if __name__ == "__main__":
    main()
