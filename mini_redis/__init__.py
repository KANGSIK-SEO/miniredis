"""Mini Redis 패키지."""

import sys
from pathlib import Path

# 단독 실행 시에도 상위 프로젝트 루트 경로(miniredis)를 인식하도록 보정
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from mini_redis.store import MiniRedisStore
from mini_redis.entry import RedisEntry
from mini_redis.parser import tokenize
from mini_redis.pubsub import PubSubBroker, Subscriber

__all__ = [
    "MiniRedisStore",
    "RedisEntry",
    "tokenize",
    "PubSubBroker",
    "Subscriber",
]

if __name__ == "__main__":
    print("✅ mini_redis 패키지가 성공적으로 로드되었습니다.")
    print(f"   포함된 모듈: {', '.join(__all__)}")
