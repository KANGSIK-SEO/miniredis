"""체이닝 방식 해시맵 (Separate Chaining Hash Map).

파이썬의 내장 dict나 set을 전혀 사용하지 않고, 오직 '고정 길이 버킷 배열'과
직접 구현한 '이중 연결 리스트(DoublyLinkedList)'를 조합하여 구현한 해시맵입니다.

[동작 원리]
1. 해시 함수: 문자열을 정수 해시 코드로 변환 (DJB2 알고리즘)
2. 인덱스 매핑: hash_code % bucket_capacity 공식으로 해당 키가 들어갈 버킷 번호 결정
3. 충돌 해결: 같은 버킷으로 매핑되는 키들은 버킷 내의 DoublyLinkedList에 차례로 체이닝
4. 동적 확장: 저장된 키 개수 / 버킷 크기 (로드 팩터)가 0.75를 넘어서면 버킷 크기를 2배로 늘리고 모든 키를 재해싱
"""

from typing import Any, List, Optional
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datastructures.doubly_linked_list import DoublyLinkedList, Node


class HashEntry:
    """해시맵의 한 슬롯(체인)에 담기는 키-값(Key-Value) 한 쌍."""

    __slots__ = ("key", "value")

    def __init__(self, key: str, value: Any):
        self.key: str = key      # 조회 기준이 되는 고유 문자열 키
        self.value: Any = value  # 실제 저장된 데이터 객체 (MiniRedis에서는 RedisEntry가 들어감)

    def __repr__(self) -> str:
        return f"HashEntry({self.key!r}, {self.value!r})"


class HashMap:
    """별도 체이닝(Separate Chaining)을 통한 해시맵 구현체.

    - 버킷 테이블: 크기가 N인 배열(파이썬 list를 고정 크기 슬롯으로 활용)
    - 해시 함수: Daniel J. Bernstein의 전설적인 DJB2 알고리즘
    - 부하율(Load Factor) 임계치: 0.75 (키 개수가 버킷의 75%를 넘어가면 자동 2배 확장)
    """

    _INITIAL_CAPACITY: int = 8
    _LOAD_FACTOR_THRESHOLD: float = 0.75

    def __init__(self, capacity: int = _INITIAL_CAPACITY):
        # 버킷의 초기 크기는 최소 4개 이상으로 안전하게 설정합니다.
        self._capacity: int = max(4, capacity)
        self._buckets: List[DoublyLinkedList] = self._make_buckets(self._capacity)
        self._size: int = 0

    def _make_buckets(self, capacity: int) -> List[DoublyLinkedList]:
        """새로운 크기의 버킷 배열을 만들고, 각 칸마다 빈 DoublyLinkedList 체인을 꽂아줍니다."""
        return [DoublyLinkedList() for _ in range(capacity)]

    def _hash(self, key: str) -> int:
        """DJB2 해시 함수 직접 구현.

        [왜 DJB2인가요?]
        단순히 각 문자의 아스키 코드를 더하면 "ab"와 "ba"처럼 아나그램 문자열이 무조건 충돌합니다.
        DJB2는 5381이라는 소수(Magic Number)로 시작하여 매 바이트마다 33을 곱하고 바이트 값을 더합니다.
        h = ((h * 33) + byte)
        비트 연산으로는 ((h << 5) + h) + byte 로 표현되며, 매우 빠르고 문자열 충돌이 골고루 분산됩니다.
        마지막에 0x7FFFFFFF(31비트 양수 마스크)를 씌워 음수가 나오지 않도록 보장합니다.
        """
        h = 5381
        for byte in key.encode("utf-8"):
            h = (((h << 5) + h) + byte) & 0x7FFFFFFF
        return h

    def _bucket_index(self, key: str, capacity: Optional[int] = None) -> int:
        """키의 해시값을 현재 버킷 크기(capacity)로 나눈 나머지(Modulo)를 구해 버킷 번호(0 ~ cap-1)를 얻습니다."""
        cap = capacity if capacity is not None else self._capacity
        return self._hash(key) % cap

    def _find_in_bucket(self, bucket: DoublyLinkedList, key: str) -> Optional[Node]:
        """특정 버킷(연결 리스트)을 처음부터 순회하며 동일한 키를 가진 노드가 있는지 찾습니다."""
        for node in bucket.iter_nodes():
            entry: HashEntry = node.data
            if entry.key == key:
                return node
        return None

    def put(self, key: str, value: Any) -> Optional[Any]:
        """키-값 쌍을 해시맵에 저장하거나 갱신합니다. (평균 시간복잡도: O(1))

        - 이미 키가 존재하는 경우: 기존 value를 새 value로 덮어쓰고 예전 value를 반환합니다.
        - 새로운 키인 경우: 해당 버킷 리스트의 맨 뒤에 새 HashEntry를 추가합니다.
        - 추가 후 로드 팩터가 0.75를 초과하면 즉시 버킷 크기를 2배로 늘리고 재해싱을 실행합니다.
        """
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        existing_node = self._find_in_bucket(bucket, key)

        if existing_node is not None:
            # 1. 기존 키가 있으면 값만 살짝 바꿔치기합니다.
            old_value = existing_node.data.value
            existing_node.data.value = value
            return old_value

        # 2. 신규 키인 경우 체인 뒤쪽에 등록합니다.
        entry = HashEntry(key, value)
        bucket.insert_back(entry)
        self._size += 1

        # 3. 로드 팩터 검사: 데이터가 많아지면 체인이 길어져서 탐색이 느려지므로 2배 확장!
        if self._size / self._capacity > self._LOAD_FACTOR_THRESHOLD:
            self._resize()

        return None

    def get(self, key: str) -> Optional[Any]:
        """키를 기반으로 저장된 값을 찾아옵니다. 키가 없으면 None을 반환합니다. (평균 시간복잡도: O(1))"""
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        node = self._find_in_bucket(bucket, key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key: str) -> Optional[Any]:
        """해당 키의 엔트리를 해시맵에서 삭제하고 그 값을 반환합니다. 없으면 None. (평균 시간복잡도: O(1))"""
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        node = self._find_in_bucket(bucket, key)
        if node is None:
            return None

        # 버킷 연결 리스트에서 해당 노드를 떼어냅니다.
        entry: HashEntry = bucket.remove_node(node)  # type: ignore[assignment]
        self._size -= 1
        return entry.value

    def contains(self, key: str) -> bool:
        """키가 해시맵에 등록되어 있는지 O(1) 시간복잡도로 빠르게 확인합니다."""
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        return self._find_in_bucket(bucket, key) is not None

    def keys(self) -> List[str]:
        """해시맵에 들어있는 모든 키 목록을 파이썬 리스트로 뽑아냅니다."""
        result: List[str] = []
        for bucket in self._buckets:
            for node in bucket.iter_nodes():
                result.append(node.data.key)
        return result

    def size(self) -> int:
        """현재 저장된 고유 키의 총 개수를 반환합니다. (시간복잡도: O(1))"""
        return self._size

    def capacity(self) -> int:
        """현재 버킷 슬롯의 총 용량을 반환합니다."""
        return self._capacity

    def load_factor(self) -> float:
        """현재 부하율(로드 팩터 = 원소 수 / 버킷 수)을 반환합니다."""
        return self._size / self._capacity

    def _resize(self) -> None:
        """버킷 배열 크기를 2배로 확장하고 기존 모든 키를 새 버킷 주소로 다시 배치(Rehash)합니다.

        [재해싱이 꼭 필요한 이유]
        버킷 인덱스는 `hash % capacity`로 계산됩니다.
        용량(capacity)이 바뀌면 같은 해시값이라도 새로운 인덱스로 옮겨가야 하기 때문에
        기존의 모든 엔트리를 꺼내서 새 버킷 배열에 알맞게 다시 꽂아줍니다.
        """
        old_buckets = self._buckets
        new_capacity = self._capacity * 2
        new_buckets = self._make_buckets(new_capacity)

        # 기존 모든 버킷의 체인을 순회하며 새 버킷으로 이사시킵니다.
        for bucket in old_buckets:
            for node in bucket.iter_nodes():
                entry: HashEntry = node.data
                new_idx = self._bucket_index(entry.key, new_capacity)
                new_buckets[new_idx].insert_back(entry)

        self._buckets = new_buckets
        self._capacity = new_capacity
