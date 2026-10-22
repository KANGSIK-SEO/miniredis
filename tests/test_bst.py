"""이진 탐색 트리 (BST) 단위 테스트."""

import unittest
from datastructures.binary_search_tree import BinarySearchTree


class TestBinarySearchTree(unittest.TestCase):
    def test_insert_search_inorder(self):
        bst = BinarySearchTree()
        items = [("banana", 2), ("apple", 1), ("cherry", 3), ("date", 4)]
        for k, v in items:
            bst.insert(k, v)

        self.assertEqual(bst.size(), 4)
        self.assertEqual(bst.search("apple"), 1)
        self.assertEqual(bst.search("cherry"), 3)
        self.assertIsNone(bst.search("elderberry"))

        # 중위 순회 결과는 항상 오름차순 정렬이어야 함
        self.assertEqual(bst.inorder_keys(), ["apple", "banana", "cherry", "date"])

    def test_delete(self):
        bst = BinarySearchTree()
        for k in [50, 30, 70, 20, 40, 60, 80]:
            bst.insert(k, f"v_{k}")

        self.assertTrue(bst.delete(20))  # 리프 노드 삭제
        self.assertEqual(bst.inorder_keys(), [30, 40, 50, 60, 70, 80])

        self.assertTrue(bst.delete(30))  # 한 개 자식 노드 삭제
        self.assertEqual(bst.inorder_keys(), [40, 50, 60, 70, 80])

        self.assertTrue(bst.delete(50))  # 두 개 자식 루트 노드 삭제
        self.assertEqual(bst.inorder_keys(), [40, 60, 70, 80])
        self.assertEqual(bst.size(), 4)


if __name__ == "__main__":
    unittest.main()
