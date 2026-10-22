"""Mini Redis 기본 및 확장 자료구조 패키지."""

import sys
from pathlib import Path

# 단독 실행 시에도 상위 프로젝트 루트 경로(miniredis)를 인식하도록 보정
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datastructures.doubly_linked_list import DoublyLinkedList, Node
from datastructures.hash_map import HashMap, HashEntry
from datastructures.min_heap import MinHeap
from datastructures.dynamic_array import DynamicArray
from datastructures.binary_tree import BinaryTree, TreeNode
from datastructures.binary_search_tree import BinarySearchTree, BSTNode

__all__ = [
    "DoublyLinkedList",
    "Node",
    "HashMap",
    "HashEntry",
    "MinHeap",
    "DynamicArray",
    "BinaryTree",
    "TreeNode",
    "BinarySearchTree",
    "BSTNode",
]

if __name__ == "__main__":
    print("✅ datastructures 패키지가 성공적으로 로드되었습니다.")
    print(f"   포함된 자료구조: {', '.join(__all__)}")
