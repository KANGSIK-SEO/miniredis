"""Mini Redis 핵심 스토리지 엔진 모듈.

자체 구현한 3대 기초 자료구조를 유기적으로 결합하여 완성한 인메모리 저장소입니다:
1. HashMap: O(1) Key -> RedisEntry 초고속 탐색
2. DoublyLinkedList: O(1) LRU(최근 사용 순서) 추적 및 메모리 초과 시 희생양 키 방출
3. MinHeap: O(1) 확인 / O(log n) 제거를 통한 효율적인 TTL(만료 시각) 스케줄링

[핵심 설계 원칙]
- 파이썬 내장 dict, set, collections를 일절 사용하지 않습니다.
- 모든 키 기반 명령은 실행 전 만료 여부를 먼저 체크하여 일관성을 유지합니다.
- used_memory 공식: len(utf8(key)) + len(utf8(value)) 합계를 실시간 증분 갱신합니다.
"""

import time
from typing import Callable, List, Optional, Union

from datastructures.doubly_linked_list import DoublyLinkedList
from datastructures.hash_map import HashMap
from datastructures.min_heap import MinHeap
from mini_redis.entry import RedisEntry
from mini_redis.parser import tokenize
from mini_redis.pubsub import PubSubBroker, Subscriber


class MiniRedisStore:
    """Mini Redis의 모든 데이터 보관 및 명령어 처리를 관장하는 코어 엔진 클래스."""

    def __init__(self, now_func: Optional[Callable[[], float]] = None):
        # 1. 메인 키-값 저장소 (체이닝 해시맵)
        self._map: HashMap = HashMap()

        # 2. LRU 순서 관리 리스트 (Head: 가장 최근 사용(MRU) <---> Tail: 가장 오래 미사용(LRU))
        self._lru: DoublyLinkedList = DoublyLinkedList()

        # 3. 만료 시각 우선순위 큐 (가장 빠른 만료 시각이 루트에 위치하는 최소 힙)
        self._expire_heap: MinHeap = MinHeap()

        # 4. 실시간 Pub/Sub 브로커 (보너스 기능)
        self._pubsub: PubSubBroker = PubSubBroker()

        # 메모리 관련 지표
        self.used_memory: int = 0    # 현재 사용 중인 바이트 수
        self.maxmemory: int = 0      # 최대 허용 메모리 (0이면 무제한)
        self.evicted_keys: int = 0   # 메모리 부족으로 강제 쫓겨난 키의 누적 개수

        # 테스트 시 시간 조작을 위한 가상 시계 주입 지원 (기본값: time.time)
        self._now: Callable[[], float] = now_func if now_func is not None else time.time

    # ---------------- 1. 메모리 계산 및 엔트리 삭제 내부 도우미 ----------------

    def _entry_memory(self, key: str, value: str) -> int:
        """단일 엔트리가 차지하는 메모리를 UTF-8 바이트 길이 기준으로 계산합니다.

        공식: len(utf8(key)) + len(utf8(value))
        (자료구조 노드/포인터 등의 오버헤드는 요구사항에 따라 계산에서 제외합니다)
        """
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    def _delete_entry(self, key: str, count_eviction: bool = False) -> bool:
        """키를 해시맵, LRU 리스트, 메모리에서 완전히 지우는 통합 삭제 메서드.

        DEL 명령어, TTL 만료 삭제, LRU 메모리 초과 방출에서 공통으로 사용됩니다.
        """
        entry: Optional[RedisEntry] = self._map.remove(key)
        if entry is None:
            return False

        # 1. LRU 리스트에서 해당 노드를 O(1)로 떼어냅니다.
        self._lru.remove_node(entry.lru_node)

        # 2. 힙에 남아있을지 모를 옛날 예약 항목을 무효화하기 위해 버전을 1 올립니다.
        entry.expire_version += 1

        # 3. 메모리 사용량을 차감합니다.
        self.used_memory -= self._entry_memory(entry.key, entry.value)

        # 4. 메모리 부족으로 인한 방출인 경우 누적 카운터를 올립니다.
        if count_eviction:
            self.evicted_keys += 1

        return True

    # ---------------- 2. TTL 만료 확인 및 정리 내부 도우미 ----------------

    def _expire_key_if_needed(self, key: str) -> bool:
        """특정 키가 만료되었는지 확인하고, 만료되었다면 즉시 지웁니다 (Lazy Deletion).

        만료되어 삭제되었다면 True, 살아있다면 False를 반환합니다.
        """
        entry: Optional[RedisEntry] = self._map.get(key)
        if entry is None:
            return False

        if entry.expire_at is not None and entry.expire_at <= self._now():
            self._delete_entry(key)
            return True

        return False

    def _sweep_expired(self) -> None:
        """최소 힙의 머리(Root)를 확인하여 이미 만료 시간이 지난 키들을 능동적으로 정리합니다 (Active Sweep).

        [Lazy Deletion 전략의 핵심]
        힙에서 꺼낸 아이템의 (expire_at, version)이 현재 해시맵에 보관된 엔트리와
        정확히 일치할 때만 삭제를 진행합니다.
        만약 SET 명령어로 값을 덮어써서 TTL이 취소되었거나 버전이 달라졌다면
        그냥 힙에서 버리고 다음으로 넘어갑니다.
        """
        now = self._now()
        while not self._expire_heap.is_empty():
            top = self._expire_heap.peek()
            # 가장 빠른 만료 시각이 아직 오지 않았다면 뒤쪽은 검사할 필요도 없이 중단!
            if top is None or top[0] > now:
                break

            expire_at, key, version = self._expire_heap.pop()
            entry: Optional[RedisEntry] = self._map.get(key)
            if entry is not None and entry.expire_version == version and entry.expire_at == expire_at:
                self._delete_entry(key)

    # ---------------- 3. LRU 캐시 교체 정책 내부 도우미 ----------------

    def _evict_lru_until_fit(self) -> None:
        """maxmemory 한도가 설정되어 있고, 현재 메모리가 이를 초과한 경우
        한도 이하가 될 때까지 가장 오래 사용되지 않은 키(LRU Victim)부터 방출합니다.
        """
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            tail_node = self._lru.back_node()
            if tail_node is None:
                break
            victim_key: str = tail_node.data
            # count_eviction=True로 넘겨 evicted_keys 카운터를 증가시킵니다.
            self._delete_entry(victim_key, count_eviction=True)

    # ---------------- 4. String 기본 명령어 (6개) ----------------

    def cmd_set(self, key: str, value: str) -> str:
        """SET key value: 키와 값을 저장합니다.

        규칙:
        1. 단일 엔트리 크기가 maxmemory를 초과하면 저장하지 않고 OOM 에러 출력
        2. 기존 키가 있으면 값 덮어쓰기 & 기존 TTL은 초기화(삭제) & LRU 최신화
        3. 신규 키는 LRU 맨 앞 삽입 & 해시맵 등록
        4. 메모리 초과 시 LRU 방출 실행
        """
        self._sweep_expired()
        self._expire_key_if_needed(key)

        new_size = self._entry_memory(key, value)
        # 단일 키+값 자체가 최대 메모리보다 크면 수용 불가!
        if self.maxmemory > 0 and new_size > self.maxmemory:
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"

        existing: Optional[RedisEntry] = self._map.get(key)
        if existing is not None:
            # 덮어쓰기: 이전 메모리 빼고 새 메모리 더하기
            old_size = self._entry_memory(existing.key, existing.value)
            self.used_memory -= old_size
            existing.value = value
            existing.expire_at = None       # 기존 TTL 초기화
            existing.expire_version += 1    # 힙의 이전 만료 예약 무효화
            self.used_memory += new_size
            self._lru.move_to_front(existing.lru_node)  # 최근 사용으로 이동
        else:
            # 신규 삽입: LRU 리스트 헤드에 먼저 달고 노드 참조를 엔트리에 보관
            lru_node = self._lru.insert_front(key)
            entry = RedisEntry(key, value, lru_node)
            self._map.put(key, entry)
            self.used_memory += new_size

        # 메모리가 넘쳤다면 LRU 정책에 따라 오래된 키 방출
        self._evict_lru_until_fit()
        return "OK"

    def cmd_get(self, key: str) -> str:
        """GET key: 키의 값을 조회합니다.

        규칙:
        - 키가 없거나 만료되었으면 (nil) 반환 (LRU 갱신 안 함)
        - 조회가 성공한 경우에만 LRU 위치를 맨 앞으로 갱신
        """
        self._sweep_expired()
        if self._expire_key_if_needed(key):
            return "(nil)"

        entry: Optional[RedisEntry] = self._map.get(key)
        if entry is None:
            return "(nil)"

        # 조회 성공 시에만 LRU 리스트 맨 앞으로 이동!
        self._lru.move_to_front(entry.lru_node)
        return f'"{entry.value}"'

    def cmd_del(self, key: str) -> str:
        """DEL key: 키를 삭제합니다. (성공 시 1, 없으면 0)"""
        self._sweep_expired()
        self._expire_key_if_needed(key)

        if self._delete_entry(key):
            return "(integer) 1"
        return "(integer) 0"

    def cmd_exists(self, key: str) -> str:
        """EXISTS key: 키가 존재하는지 확인합니다. (존재하면 1, 없으면 0)"""
        self._sweep_expired()
        self._expire_key_if_needed(key)

        if self._map.contains(key):
            return "(integer) 1"
        return "(integer) 0"

    def cmd_dbsize(self) -> str:
        """DBSIZE: 현재 저장된 유효 키의 총 개수를 반환합니다."""
        self._sweep_expired()
        return f"(integer) {self._map.size()}"

    def cmd_keys(self) -> str:
        """KEYS: 전체 키 목록을 출력합니다."""
        self._sweep_expired()
        raw_keys = self._map.keys()
        live_keys = []
        for k in raw_keys:
            if not self._expire_key_if_needed(k):
                live_keys.append(k)

        if not live_keys:
            return "(empty array)"

        lines = [f'{i}. "{k}"' for i, k in enumerate(live_keys, start=1)]
        return "\n".join(lines)

    # ---------------- 5. 메모리 관리 명령어 (2개) ----------------

    def cmd_config_set_maxmemory(self, bytes_str: str) -> str:
        """CONFIG SET maxmemory bytes: 최대 메모리 제한(바이트)을 설정합니다."""
        try:
            val = int(bytes_str)
        except ValueError:
            return "(error) ERR value is not an integer or out of range"

        if val < 0:
            return "(error) ERR value is not an integer or out of range"

        self.maxmemory = val
        # 새 제한 설정 후 즉시 초과분 방출 트리거
        self._evict_lru_until_fit()
        return "OK"

    def cmd_info_memory(self) -> str:
        """INFO memory: 메모리 사용량, 한도, 방출된 키 개수를 출력합니다."""
        self._sweep_expired()
        return (
            f"used_memory:{self.used_memory}\n"
            f"maxmemory:{self.maxmemory}\n"
            f"evicted_keys:{self.evicted_keys}"
        )

    # ---------------- 6. TTL 관리 명령어 (2개) ----------------

    def cmd_expire(self, key: str, seconds_str: str) -> str:
        """EXPIRE key seconds: 키의 만료 시간을 설정합니다. (초 단위)"""
        self._sweep_expired()
        if self._expire_key_if_needed(key):
            return "(integer) 0"

        entry: Optional[RedisEntry] = self._map.get(key)
        if entry is None:
            return "(integer) 0"

        try:
            seconds = int(seconds_str)
        except ValueError:
            return "(error) ERR value is not an integer or out of range"

        # seconds <= 0 인 경우 즉시 삭제 처리
        if seconds <= 0:
            self._delete_entry(key)
            return "(integer) 1"

        entry.expire_version += 1
        entry.expire_at = self._now() + seconds
        # 최소 힙에 (만료시각, 키, 버전)을 등록합니다.
        self._expire_heap.push((entry.expire_at, key, entry.expire_version))
        return "(integer) 1"

    def cmd_ttl(self, key: str) -> str:
        """TTL key: 키의 남은 만료 시간(초)을 조회합니다.

        반환값:
        - key가 없거나 만료된 경우: (integer) -2
        - key는 존재하지만 만료 시간이 없는 경우: (integer) -1
        - 만료 시간이 있는 경우: (integer) 남은초
        """
        self._sweep_expired()
        if self._expire_key_if_needed(key):
            return "(integer) -2"

        entry: Optional[RedisEntry] = self._map.get(key)
        if entry is None:
            return "(integer) -2"

        if entry.expire_at is None:
            return "(integer) -1"

        remaining = entry.expire_at - self._now()
        rem_sec = int(remaining)
        if rem_sec < 0:
            self._delete_entry(key)
            return "(integer) -2"

        return f"(integer) {rem_sec}"

    # ---------------- 7. Pub/Sub (보너스 과제 5) ----------------

    def cmd_publish(self, channel: str, message: str) -> str:
        """PUBLISH channel message: 채널로 메시지를 발행합니다."""
        count = self._pubsub.publish(channel, message)
        return f"(integer) {count}"

    def cmd_subscribe(self, channel: str, client_id: str = "cli-client") -> str:
        """SUBSCRIBE channel [client_id]: 채널을 구독합니다."""
        sub = Subscriber(client_id)
        count = self._pubsub.subscribe(channel, sub)
        return f"1) \"subscribe\"\n2) \"{channel}\"\n3) (integer) {count}"

    # ---------------- 8. 명령 디스패처 ----------------

    def execute(self, command_line: Union[str, List[str]]) -> Optional[str]:
        """명령어 입력을 받아 토큰화하고 적절한 실행 함수로 라우팅합니다."""
        if isinstance(command_line, str):
            try:
                tokens = tokenize(command_line)
            except ValueError as exc:
                return f"(error) {exc}"
        else:
            tokens = command_line

        if not tokens:
            return None

        cmd_raw = tokens[0]
        cmd = cmd_raw.upper()
        args = tokens[1:]

        def arity_err() -> str:
            return f"(error) ERR wrong number of arguments for '{cmd}' command"

        # String 기본 명령어
        if cmd == "SET":
            if len(args) != 2:
                return arity_err()
            return self.cmd_set(args[0], args[1])

        if cmd == "GET":
            if len(args) != 1:
                return arity_err()
            return self.cmd_get(args[0])

        if cmd == "DEL":
            if len(args) != 1:
                return arity_err()
            return self.cmd_del(args[0])

        if cmd == "EXISTS":
            if len(args) != 1:
                return arity_err()
            return self.cmd_exists(args[0])

        if cmd == "DBSIZE":
            if len(args) != 0:
                return arity_err()
            return self.cmd_dbsize()

        if cmd == "KEYS":
            if len(args) != 0:
                return arity_err()
            return self.cmd_keys()

        # 메모리 관리 명령어
        if cmd == "CONFIG":
            if len(args) != 3 or args[0].upper() != "SET" or args[1].lower() != "maxmemory":
                return arity_err()
            return self.cmd_config_set_maxmemory(args[2])

        if cmd == "INFO":
            if len(args) != 1 or args[0].lower() != "memory":
                return arity_err()
            return self.cmd_info_memory()

        # TTL 관리 명령어
        if cmd == "EXPIRE":
            if len(args) != 2:
                return arity_err()
            return self.cmd_expire(args[0], args[1])

        if cmd == "TTL":
            if len(args) != 1:
                return arity_err()
            return self.cmd_ttl(args[0])

        # Pub/Sub 보너스 명령어
        if cmd == "PUBLISH":
            if len(args) != 2:
                return arity_err()
            return self.cmd_publish(args[0], args[1])

        if cmd == "SUBSCRIBE":
            if len(args) < 1 or len(args) > 2:
                return arity_err()
            client = args[1] if len(args) == 2 else "cli-client"
            return self.cmd_subscribe(args[0], client)

        return f"(error) ERR unknown command '{cmd_raw}'"
