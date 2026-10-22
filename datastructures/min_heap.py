"""최소 힙 (Min-Heap).

Mini Redis의 TTL(Time-To-Live, 만료 시각) 처리를 담당하는 핵심 우선순위 큐입니다.

[왜 최소 힙을 사용할까요?]
키가 10,000개 있을 때 매초마다 모든 키를 하나하나 확인(O(n))하면 CPU가 낭비됩니다.
최소 힙을 사용하면:
- '가장 먼저 만료될 키(만료 시각이 가장 작은 값)'가 항상 힙의 맨 꼭대기(루트, index 0)에 위치합니다.
- 따라서 가장 빠른 만료 시각을 O(1)에 바로 확인(peek)할 수 있습니다.
- 루트의 만료 시각이 아직 현재 시각보다 미래라면, 그 아래에 있는 수천 개의 키는 검사할 필요도 없이 안전합니다!
"""

from typing import Any, List, Optional


class MinHeap:
    """완전 이진 트리(Complete Binary Tree)를 연속 배열로 구현한 최소 힙.

    [배열 인덱스 공식]
    어떤 노드의 인덱스가 `i`일 때:
    - 부모 노드의 인덱스: `(i - 1) // 2`
    - 왼쪽 자식의 인덱스: `i * 2 + 1`
    - 오른쪽 자식의 인덱스: `i * 2 + 2`
    
    포인터 없이 오직 인덱스 산술 연산만으로 트리 위아래를 O(1)에 탐색합니다.
    저장되는 요소: (expire_at, key, version) 튜플 형태
    """

    def __init__(self):
        # 힙 원소들을 순서대로 담아둘 1차원 내부 배열
        self._items: List[Any] = []

    def push(self, item: Any) -> None:
        """새 요소를 힙에 넣습니다. (시간복잡도: O(log n))

        1. 배열의 맨 끝에 새 원소를 추가합니다.
        2. 부모 노드와 비교하면서 내가 더 작으면 위로 거슬러 올라갑니다 (_heapify_up).
        """
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self) -> Optional[Any]:
        """힙에서 가장 작은 원소(루트, 만료 시간이 가장 임박한 키)를 꺼내고 반환합니다. (시간복잡도: O(log n))

        1. 루트(0번 인덱스) 원소를 꺼냅니다.
        2. 맨 마지막 원소를 루트 자리로 옮깁니다.
        3. 자식 노드들과 비교하면서 더 작은 자식과 자리를 바꾸며 아래로 내려갑니다 (_heapify_down).
        """
        n = len(self._items)
        if n == 0:
            return None
        if n == 1:
            return self._items.pop()

        root = self._items[0]
        # 맨 끝 원소를 루트로 데려와 트리의 구조적 완전성(Complete Binary Tree)을 유지합니다.
        self._items[0] = self._items.pop()
        # 내려보내기 시작!
        self._heapify_down(0)
        return root

    def peek(self) -> Optional[Any]:
        """힙의 최솟값(가장 임박한 만료 시각)을 꺼내지 않고 구경만 합니다. (시간복잡도: O(1))

        루트가 0번 인덱스에 있으므로 즉시 조회가 가능합니다.
        """
        if len(self._items) == 0:
            return None
        return self._items[0]

    def size(self) -> int:
        """현재 힙에 등록된 예약 작업(만료 건)의 총 개수입니다. (시간복잡도: O(1))"""
        return len(self._items)

    def is_empty(self) -> bool:
        """힙이 비어있는지 확인합니다. (시간복잡도: O(1))"""
        return len(self._items) == 0

    def _heapify_up(self, index: int) -> None:
        """상향 힙화: 새로 들어온 자식이 부모보다 작다면 부모와 자리를 바꾸며 위로 올라갑니다.

        올라가다가 부모보다 내가 크거나 같아지면 그 자리에 정착합니다.
        트리의 높이(log n)만큼만 비교하므로 아주 빠릅니다.
        """
        while index > 0:
            parent_idx = (index - 1) // 2
            # 파이썬 튜플 비교: (expire_at, ...) 에서 expire_at을 먼저 비교합니다.
            if self._items[index] < self._items[parent_idx]:
                # 부모와 내 위치를 맞바꿉니다 (스왑).
                self._items[index], self._items[parent_idx] = (
                    self._items[parent_idx],
                    self._items[index],
                )
                index = parent_idx
            else:
                # 부모가 나보다 작거나 같다면 힙 성질 만족! 멈춥니다.
                break

    def _heapify_down(self, index: int) -> None:
        """하향 힙화: 루트로 올라온 원소를 왼쪽/오른쪽 자식 중 '더 작은 녀석'과 비교하여 내려보냅니다.

        더 작은 자식과 스왑해야 부모 노드가 두 자식보다 항상 작다는 최소 힙 불변식(Invariant)이 지켜집니다.
        """
        size = len(self._items)
        while True:
            left_child_idx = index * 2 + 1
            right_child_idx = index * 2 + 2
            smallest_idx = index

            # 1. 왼쪽 자식이 존재하고, 현재 smallest보다 더 작다면?
            if left_child_idx < size and self._items[left_child_idx] < self._items[smallest_idx]:
                smallest_idx = left_child_idx

            # 2. 오른쪽 자식이 존재하고, 지금까지 중 가장 작은 녀석보다 더 작다면?
            if right_child_idx < size and self._items[right_child_idx] < self._items[smallest_idx]:
                smallest_idx = right_child_idx

            # 3. 만약 내가 두 자식보다 다 작다면 제자리를 찾은 것이므로 멈춥니다.
            if smallest_idx == index:
                break

            # 4. 더 작은 자식과 자리를 바꾸고, 그 자리에서 다시 아래로 검사를 이어갑니다.
            self._items[index], self._items[smallest_idx] = (
                self._items[smallest_idx],
                self._items[index],
            )
            index = smallest_idx
