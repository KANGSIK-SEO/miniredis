"""이진 트리 (Binary Tree) 및 순회 알고리즘 (보너스 과제 3).

힙(Min-Heap)이 완전 이진 트리를 1차원 배열로 효율화한 것이라면,
이 모듈은 노드 참조(left, right)로 직접 연결된 정통 이진 트리 구조와
컴퓨터 과학의 기초가 되는 4대 순회(전위, 중위, 후위, 레벨) 방식을 보여줍니다.
"""

import sys
from pathlib import Path
from typing import Any, List, Optional

# 단독 실행 시에도 상위 프로젝트 루트 경로(miniredis)를 인식하도록 보정
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datastructures.doubly_linked_list import DoublyLinkedList


class TreeNode:
    """이진 트리의 한 노드 (데이터, 왼쪽 자식, 오른쪽 자식)."""

    __slots__ = ("val", "left", "right")

    def __init__(self, val: Any):
        self.val: Any = val
        self.left: Optional["TreeNode"] = None
        self.right: Optional["TreeNode"] = None

    def __repr__(self) -> str:
        return f"TreeNode({self.val!r})"


class BinaryTree:
    """이진 트리 및 순회 알고리즘 모음."""

    def __init__(self, root: Optional[TreeNode] = None):
        self.root: Optional[TreeNode] = root

    def insert_level_order(self, val: Any) -> None:
        """너비 우선(Level-order) 순서로 빈자리를 찾아 새 노드를 삽입합니다. (완전 이진 트리 형태 유지)
        
        자체 구현한 DoublyLinkedList를 FIFO 큐로 활용하여 레벨 순으로 빈자리를 탐색합니다.
        """
        new_node = TreeNode(val)
        if self.root is None:
            self.root = new_node
            return

        queue = DoublyLinkedList()
        queue.insert_back(self.root)

        while not queue.is_empty():
            curr: TreeNode = queue.remove_front()
            if curr.left is None:
                curr.left = new_node
                return
            else:
                queue.insert_back(curr.left)

            if curr.right is None:
                curr.right = new_node
                return
            else:
                queue.insert_back(curr.right)

    def preorder(self) -> List[Any]:
        """전위 순회: [나(Root) -> 왼쪽 자식 -> 오른쪽 자식] 순으로 방문합니다."""
        result: List[Any] = []

        def _traverse(node: Optional[TreeNode]):
            if node is None:
                return
            result.append(node.val)
            _traverse(node.left)
            _traverse(node.right)

        _traverse(self.root)
        return result

    def inorder(self) -> List[Any]:
        """중위 순회: [왼쪽 자식 -> 나(Root) -> 오른쪽 자식] 순으로 방문합니다."""
        result: List[Any] = []

        def _traverse(node: Optional[TreeNode]):
            if node is None:
                return
            _traverse(node.left)
            result.append(node.val)
            _traverse(node.right)

        _traverse(self.root)
        return result

    def postorder(self) -> List[Any]:
        """후위 순회: [왼쪽 자식 -> 오른쪽 자식 -> 나(Root)] 순으로 방문합니다."""
        result: List[Any] = []

        def _traverse(node: Optional[TreeNode]):
            if node is None:
                return
            _traverse(node.left)
            _traverse(node.right)
            result.append(node.val)

        _traverse(self.root)
        return result

    def level_order(self) -> List[Any]:
        """레벨 순회 (BFS): 트리의 층(레벨)별로 위에서 아래로, 왼쪽에서 오른쪽으로 훑습니다."""
        if self.root is None:
            return []

        result: List[Any] = []
        queue = DoublyLinkedList()
        queue.insert_back(self.root)

        while not queue.is_empty():
            curr: TreeNode = queue.remove_front()
            result.append(curr.val)
            if curr.left is not None:
                queue.insert_back(curr.left)
            if curr.right is not None:
                queue.insert_back(curr.right)

        return result


if __name__ == "__main__":
    print("🌲 BinaryTree (이진 트리) 순회 알고리즘 동작 테스트:")
    tree = BinaryTree()
    for v in [1, 2, 3, 4, 5, 6, 7]:
        tree.insert_level_order(v)
    print(f"  • 전위 순회 (Preorder)   : {tree.preorder()}")
    print(f"  • 중위 순회 (Inorder)    : {tree.inorder()}")
    print(f"  • 후위 순회 (Postorder)  : {tree.postorder()}")
    print(f"  • 레벨 순회 (Level-order): {tree.level_order()}")
    print("✅ BinaryTree 정상 작동 확인 완료!")
