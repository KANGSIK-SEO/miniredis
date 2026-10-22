"""이진 탐색 트리 (Binary Search Tree, BST) 구현체 (보너스 과제 4).

[이진 탐색 트리의 성질]
- 왼쪽 서브트리의 모든 키는 부모 노드의 키보다 작습니다 (key < parent).
- 오른쪽 서브트리의 모든 키는 부모 노드의 키보다 큽니다 (key > parent).
- 따라서 중위 순회(Inorder Traversal: Left -> Root -> Right)를 수행하면
  별도의 정렬 알고리즘 없이도 **모든 키가 오름차순으로 자동 정렬**되어 나옵니다!
- Redis의 Sorted Set(ZSET)이나 범위 쿼리(ZRANGE)의 기본 이론적 배경이 됩니다.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from typing import Any, List, Optional, Tuple


class BSTNode:
    """BST 노드 (key, value, left, right)."""

    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key: Any, value: Any):
        self.key: Any = key          # 비교 기준이 되는 키
        self.value: Any = value      # 연결된 실제 데이터
        self.left: Optional["BSTNode"] = None   # 나보다 작은 값들이 있는 왼쪽 가지
        self.right: Optional["BSTNode"] = None  # 나보다 큰 값들이 있는 오른쪽 가지

    def __repr__(self) -> str:
        return f"BSTNode({self.key!r}: {self.value!r})"


class BinarySearchTree:
    """이진 탐색 트리 클래스."""

    def __init__(self):
        self.root: Optional[BSTNode] = None
        self._size: int = 0

    def insert(self, key: Any, value: Any) -> None:
        """키-값 쌍을 알맞은 자리에 삽입합니다. (평균 시간복잡도: O(log n))

        이미 같은 키가 있다면 값(value)만 갱신합니다.
        """
        def _insert(node: Optional[BSTNode], k: Any, v: Any) -> BSTNode:
            if node is None:
                self._size += 1
                return BSTNode(k, v)
            if k < node.key:
                node.left = _insert(node.left, k, v)
            elif k > node.key:
                node.right = _insert(node.right, k, v)
            else:
                node.value = v
            return node

        self.root = _insert(self.root, key, value)

    def search(self, key: Any) -> Optional[Any]:
        """키를 기준으로 값을 탐색합니다. (평균 시간복잡도: O(log n))

        작으면 왼쪽 가지로, 크면 오른쪽 가지로 반씩 줄여가며 내려갑니다.
        """
        curr = self.root
        while curr is not None:
            if key < curr.key:
                curr = curr.left
            elif key > curr.key:
                curr = curr.right
            else:
                return curr.value
        return None

    def contains(self, key: Any) -> bool:
        """키의 존재 여부를 반환합니다."""
        return self.search(key) is not None

    def delete(self, key: Any) -> bool:
        """키를 찾아 트리에서 안전하게 삭제합니다. (평균 시간복잡도: O(log n))

        [삭제 시 3가지 경우의 수]
        1. 자식이 없는 리프 노드: 그냥 삭제
        2. 자식이 1개인 노드: 자식 노드를 부모에게 입양 보냄
        3. 자식이 2개인 노드: 오른쪽 서브트리에서 가장 작은 값(후임자, Inorder Successor)을 찾아
           내 자리에 앉힌 뒤, 후임자가 있던 원래 위치의 노드를 삭제
        """
        deleted = False

        def _min_value_node(node: BSTNode) -> BSTNode:
            """가장 왼쪽 끝까지 내려가 최솟값 노드를 찾습니다."""
            current = node
            while current.left is not None:
                current = current.left
            return current

        def _delete(node: Optional[BSTNode], k: Any) -> Optional[BSTNode]:
            nonlocal deleted
            if node is None:
                return None
            if k < node.key:
                node.left = _delete(node.left, k)
            elif k > node.key:
                node.right = _delete(node.right, k)
            else:
                # 삭제 대상 노드 발견!
                deleted = True
                # 경우 1 & 2: 자식이 0개이거나 1개인 경우
                if node.left is None:
                    return node.right
                elif node.right is None:
                    return node.left

                # 경우 3: 자식이 둘 다 있는 경우 (오른쪽 서브트리의 최솟값으로 교체)
                successor = _min_value_node(node.right)
                node.key = successor.key
                node.value = successor.value
                node.right = _delete(node.right, successor.key)
            return node

        self.root = _delete(self.root, key)
        if deleted:
            self._size -= 1
        return deleted

    def inorder_keys(self) -> List[Any]:
        """중위 순회를 통해 오름차순으로 정렬된 키 목록을 획득합니다."""
        keys: List[Any] = []

        def _inorder(node: Optional[BSTNode]):
            if node is None:
                return
            _inorder(node.left)
            keys.append(node.key)
            _inorder(node.right)

        _inorder(self.root)
        return keys

    def inorder_items(self) -> List[Tuple[Any, Any]]:
        """중위 순회를 통해 오름차순으로 정렬된 (key, value) 목록을 획득합니다."""
        items: List[Tuple[Any, Any]] = []

        def _inorder(node: Optional[BSTNode]):
            if node is None:
                return
            _inorder(node.left)
            items.append((node.key, node.value))
            _inorder(node.right)

        _inorder(self.root)
        return items

    def size(self) -> int:
        return self._size
