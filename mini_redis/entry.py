"""Mini Redis 캐시 엔트리 정의 모듈.

해시맵에 저장되는 실제 값 객체입니다.
단순히 문자열 value만 보관하는 것이 아니라,
LRU 리스트의 노드 위치와 TTL 만료 시각 및 버전을 함께 들고 있어
O(1) 캐시 갱신과 안전한 힙 만료 처리를 가능하게 합니다.
"""

from typing import Optional
from datastructures.doubly_linked_list import Node


class RedisEntry:
    """Mini Redis의 한 키-값 엔트리 레코드.

    [핵심 필드 해설]
    - key: 키 문자열
    - value: 실제 저장된 데이터 문자열
    - lru_node: LRU 이중 연결 리스트 안에서 이 키를 가리키는 Node 객체 참조.
      -> 이 포인터 덕분에 키를 조회(GET)할 때 LRU 리스트를 처음부터 찾지 않고도 O(1)에 맨 앞으로 쏙 이동시킬 수 있습니다!
    - expire_at: 유닉스 타임스탬프 기준 만료 시각 (None이면 영구 보관)
    - expire_version: 키를 덮어쓰거나(SET) 만료 시간을 재지정(EXPIRE)할 때마다 1씩 증가하는 번호표.
      -> 힙(MinHeap)에 들어가 있는 옛날 예약 항목(Stale item)과 최신 설정을 구분하는 핵심 장치입니다.
    """

    __slots__ = ("key", "value", "lru_node", "expire_at", "expire_version")

    def __init__(self, key: str, value: str, lru_node: Node):
        self.key: str = key
        self.value: str = value
        self.lru_node: Node = lru_node
        self.expire_at: Optional[float] = None
        self.expire_version: int = 0

    def __repr__(self) -> str:
        return f"RedisEntry(key={self.key!r}, value={self.value!r}, expire_at={self.expire_at})"
