"""이중 연결 리스트 (Doubly Linked List).

Mini Redis의 핵심 뼈대가 되는 자료구조입니다.
이 클래스는 다음 두 가지 핵심 역할을 완벽하게 수행합니다:
1. 해시맵의 충돌 해결 체인 (Separate Chaining)
2. 캐시 메모리가 가득 찼을 때 가장 오래 사용되지 않은 키를 O(1)에 제거하는 LRU(Least Recently Used) 큐

[핵심 포인트]
- 헤드(Head)와 테일(Tail)에 '더미 센티넬(Sentinel) 노드'를 두어 노드가 0개이거나 1개일 때의
  귀찮은 if 분기 처리를 완전히 제거하고 모든 연산을 깔끔한 O(1)로 유지합니다.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from typing import Any, Generator, Optional


class Node:
    """이중 연결 리스트의 기본 마디(Node).

    각 노드는 세 가지 정보를 들고 있습니다:
    - prev: 나보다 앞에 있는 노드를 가리키는 손 (이전 노드 참조)
    - next: 나보다 뒤에 있는 노드를 가리키는 손 (다음 노드 참조)
    - data: 실제로 보관할 데이터 값 (예: 문자열, 객체 등)
    """

    __slots__ = ("prev", "next", "data")

    def __init__(self, data: Any):
        self.prev: Optional["Node"] = None
        self.next: Optional["Node"] = None
        self.data: Any = data

    def __repr__(self) -> str:
        return f"Node({self.data!r})"


class DoublyLinkedList:
    """더미 센티넬 노드를 활용한 O(1) 이중 연결 리스트.

    구조 미리보기:
      [Head 더미] <--> [실제 노드 1] <--> [실제 노드 2] <--> [Tail 더미]
    
    센티넬 노드 덕분에 리스트가 텅 비어있든, 원소가 1개든 1000개든
    동일한 포인터 연결 로직(_link_after)으로 동작하므로 버그가 생기지 않습니다.
    """

    def __init__(self):
        # 시작과 끝을 나타내는 가짜(더미) 노드 2개를 생성합니다.
        self._head: Node = Node(None)
        self._tail: Node = Node(None)

        # 초기 상태: Head 바로 뒤에 Tail이 오도록 서로 맞잡아 둡니다.
        self._head.next = self._tail
        self._tail.prev = self._head

        # 현재 리스트에 담긴 실제 유효 데이터 개수
        self._size: int = 0

    def insert_front(self, data: Any) -> Node:
        """리스트의 맨 앞(Head 바로 뒤)에 새 데이터를 삽입합니다. (시간복잡도: O(1))

        LRU 캐시에서 '방금 사용된 키'를 가장 최신 위치로 등록할 때 주로 사용됩니다.
        """
        node = Node(data)
        self._link_after(self._head, node)
        self._size += 1
        return node

    def insert_back(self, data: Any) -> Node:
        """리스트의 맨 뒤(Tail 바로 앞)에 새 데이터를 삽입합니다. (시간복잡도: O(1))

        해시맵 체이닝에서 충돌난 새 엔트리를 꼬리에 덧붙이거나 메시지 큐에 넣을 때 사용합니다.
        """
        node = Node(data)
        # Tail 직전 노드 바로 뒤에 새 노드를 끼워 넣습니다.
        self._link_after(self._tail.prev, node)  # type: ignore[arg-type]
        self._size += 1
        return node

    def remove_front(self) -> Optional[Any]:
        """리스트의 맨 앞 유효 노드를 떼어내고 그 안의 데이터를 반환합니다. (시간복잡도: O(1))
        
        리스트가 비어있다면 None을 반환합니다. FIFO 큐의 Dequeue 역할을 합니다.
        """
        if self._size == 0:
            return None
        node = self._head.next
        return self.remove_node(node)

    def remove_back(self) -> Optional[Any]:
        """리스트의 맨 뒤 유효 노드를 떼어내고 그 안의 데이터를 반환합니다. (시간복잡도: O(1))

        LRU 캐시에서 메모리가 부족할 때 '가장 오랫동안 사용되지 않은 희생양(Victim) 키'를
        골라내어 방출(Eviction)할 때 핵심적으로 사용됩니다.
        """
        if self._size == 0:
            return None
        node = self._tail.prev
        return self.remove_node(node)

    def remove_node(self, node: Node) -> Optional[Any]:
        """주어진 노드를 리스트의 어느 위치에 있든 O(1)만에 바로 뽑아냅니다. (시간복잡도: O(1))

        이중 연결 리스트의 최대 강점입니다! 노드의 prev와 next를 이미 알고 있으므로,
        앞에서부터 순차 탐색할 필요 없이 양쪽 이웃끼리 직접 손을 잡게 해주면 끝납니다.
        """
        # 더미 센티넬 노드는 절대 삭제하면 안 되므로 안전하게 보호합니다.
        if node is None or node is self._head or node is self._tail:
            return None

        prev_node = node.prev
        next_node = node.next

        # 노드의 이전 노드와 다음 노드를 서로 이어줍니다 (나를 건너뛰기).
        if prev_node is not None:
            prev_node.next = next_node
        if next_node is not None:
            next_node.prev = prev_node

        # 혹시 모를 메모리 누수와 잘못된 참조 방지를 위해 링크를 끊어줍니다.
        data = node.data
        node.prev = None
        node.next = None
        self._size -= 1
        return data

    def move_to_front(self, node: Node) -> Node:
        """이미 리스트에 존재하는 노드를 맨 앞(최신 위치)으로 쓱 옮깁니다. (시간복잡도: O(1))

        [중요한 테크닉]
        새 노드를 메모리에 새로 할당(new)하지 않고, 기존 노드의 연결선만 풀었다가
        Head 바로 뒤로 다시 이어붙입니다.
        따라서 RedisEntry 객체가 쥐고 있던 `lru_node` 참조가 바뀌지 않고 그대로 유지됩니다!
        """
        if node is None or node is self._head or node is self._tail:
            return node
        if self._head.next is node:
            return node  # 이미 맨 앞에 있다면 아무것도 할 필요가 없습니다.

        # 1단계: 현재 위치에서 노드를 조용히 분리합니다.
        prev_node = node.prev
        next_node = node.next
        if prev_node is not None:
            prev_node.next = next_node
        if next_node is not None:
            next_node.prev = prev_node

        # 2단계: Head 바로 뒤에 쏙 끼워 넣습니다.
        self._link_after(self._head, node)
        return node

    def front_node(self) -> Optional[Node]:
        """가장 최근에 사용된(맨 앞) 실제 노드를 반환합니다. 비어있으면 None."""
        return self._head.next if self._size > 0 else None

    def back_node(self) -> Optional[Node]:
        """가장 오래된(맨 뒤) 실제 노드를 반환합니다. 비어있으면 None."""
        return self._tail.prev if self._size > 0 else None

    def size(self) -> int:
        """현재 리스트에 들어있는 실제 데이터 노드의 개수입니다. (시간복잡도: O(1))"""
        return self._size

    def is_empty(self) -> bool:
        """리스트가 비어있는지 확인합니다. (시간복잡도: O(1))"""
        return self._size == 0

    def iter_nodes(self) -> Generator[Node, None, None]:
        """Head부터 Tail까지 유효 노드를 하나씩 꺼내주는 제너레이터입니다."""
        curr = self._head.next
        while curr is not None and curr is not self._tail:
            nxt = curr.next  # 순회 도중 현재 노드가 삭제되더라도 안전하도록 다음 노드를 미리 확보합니다.
            yield curr
            curr = nxt

    def __iter__(self) -> Generator[Any, None, None]:
        """`for item in dll:` 문법으로 저장된 데이터를 바로 순회할 수 있게 지원합니다."""
        for node in self.iter_nodes():
            yield node.data

    def to_list(self) -> list:
        """디버깅 및 테스트 편의를 위해 파이썬 리스트 형태로 변환합니다."""
        return list(self)

    def _link_after(self, anchor: Node, node: Node) -> None:
        """내부 도우미 함수: anchor 노드 바로 뒤에 node를 안전하게 끼워 넣습니다."""
        nxt = anchor.next
        anchor.next = node
        node.prev = anchor
        node.next = nxt
        if nxt is not None:
            nxt.prev = node
