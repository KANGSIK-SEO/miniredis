"""동적 배열 (Dynamic Array) 직접 구현체 (보너스 과제 1).

파이썬의 내장 `list`가 내부적으로 어떻게 C 언어 수준의 정적 배열 크기를 늘리고 줄이는지,
그 '동적 리사이징(Dynamic Resizing)'과 '분할 상환 시간복잡도(Amortized O(1))'의 원리를
명확하게 보여주는 학습용 자료구조입니다.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from typing import Any, Generator, Optional


class DynamicArray:
    """고정 크기 슬롯 버퍼를 기반으로 용량이 필요할 때마다 2배로 확장되는 동적 배열."""

    _INITIAL_CAPACITY: int = 4

    def __init__(self, capacity: int = _INITIAL_CAPACITY):
        self._capacity: int = max(1, capacity)
        self._size: int = 0
        # 파이썬의 [None] * capacity 를 통해 고정 크기 메모리 블록을 시뮬레이션합니다.
        self._array: list = [None] * self._capacity

    def append(self, item: Any) -> None:
        """배열 맨 끝에 새 원소를 추가합니다. (분할 상환 시간복잡도: Amortized O(1))

        방이 꽉 찼다면 기존 방 크기의 2배 크기로 새 집을 짓고 이사합니다(_resize).
        """
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._array[self._size] = item
        self._size += 1

    def get(self, index: int) -> Any:
        """지정한 인덱스의 원소를 O(1)에 조회합니다. 유효 범위를 벗어나면 IndexError 발생."""
        self._validate_index(index)
        return self._array[index]

    def set(self, index: int, value: Any) -> None:
        """지정한 인덱스의 원소를 새 값으로 O(1)에 덮어씁니다."""
        self._validate_index(index)
        self._array[index] = value

    def pop(self, index: Optional[int] = None) -> Any:
        """원소를 꺼내고 배열에서 삭제합니다. (기본값: 맨 끝 원소)

        중간 원소를 꺼낼 때는 뒤에 있는 원소들을 한 칸씩 앞으로 당겨주어야 합니다 (O(n)).
        원소 수가 전체 용량의 1/4 이하로 떨어지면 메모리 낭비를 막기 위해 용량을 절반으로 줄입니다.
        """
        if self._size == 0:
            raise IndexError("pop from empty dynamic array")
        idx = self._size - 1 if index is None else index
        self._validate_index(idx)

        val = self._array[idx]
        # 원소들을 왼쪽으로 한 칸씩 이동
        for i in range(idx, self._size - 1):
            self._array[i] = self._array[i + 1]
        self._array[self._size - 1] = None
        self._size -= 1

        # 축소 정책 (Shrinking): 1/4 이하일 때 1/2로 줄여 진동 현상(Thrashing) 방지
        if 0 < self._size <= self._capacity // 4 and self._capacity > self._INITIAL_CAPACITY:
            self._resize(max(self._INITIAL_CAPACITY, self._capacity // 2))

        return val

    def insert(self, index: int, item: Any) -> None:
        """원하는 인덱스 자리에 새 원소를 끼워 넣습니다. (시간복잡도: O(n))

        끼워 넣을 자리부터 맨 뒤까지의 원소들을 오른쪽으로 한 칸씩 밀어내야 합니다.
        """
        if index < 0 or index > self._size:
            raise IndexError("Index out of bounds")
        if self._size == self._capacity:
            self._resize(self._capacity * 2)

        # 뒤에서부터 거꾸로 한 칸씩 밀어 공간을 만듭니다.
        for i in range(self._size, index, -1):
            self._array[i] = self._array[i - 1]
        self._array[index] = item
        self._size += 1

    def remove(self, item: Any) -> bool:
        """주어진 값과 일치하는 첫 번째 원소를 찾아서 삭제합니다. (시간복잡도: O(n))"""
        for i in range(self._size):
            if self._array[i] == item:
                self.pop(i)
                return True
        return False

    def size(self) -> int:
        """현재 담겨있는 실제 원소 개수입니다."""
        return self._size

    def capacity(self) -> int:
        """현재 할당되어 있는 총 슬롯(방) 개수입니다."""
        return self._capacity

    def is_empty(self) -> bool:
        return self._size == 0

    def _resize(self, new_capacity: int) -> None:
        """새 크기의 메모리 블록을 할당하고 기존 원소들을 일괄 복사합니다. (시간복잡도: O(n))"""
        new_array = [None] * new_capacity
        for i in range(self._size):
            new_array[i] = self._array[i]
        self._array = new_array
        self._capacity = new_capacity

    def _validate_index(self, index: int) -> None:
        if index < 0 or index >= self._size:
            raise IndexError(f"Index {index} out of range [0, {self._size})")

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, index: int) -> Any:
        return self.get(index)

    def __setitem__(self, index: int, value: Any) -> None:
        self.set(index, value)

    def __iter__(self) -> Generator[Any, None, None]:
        for i in range(self._size):
            yield self._array[i]

    def to_list(self) -> list:
        return [self._array[i] for i in range(self._size)]
