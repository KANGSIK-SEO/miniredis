"""이진 트리 및 순회 알고리즘 단위 테스트."""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import unittest
from datastructures.binary_tree import BinaryTree, TreeNode


class TestBinaryTree(unittest.TestCase):
    def test_traversals(self):
        #        1
        #       / \
        #      2   3
        #     / \
        #    4   5
        tree = BinaryTree()
        for v in [1, 2, 3, 4, 5]:
            tree.insert_level_order(v)

        self.assertEqual(tree.level_order(), [1, 2, 3, 4, 5])
        self.assertEqual(tree.preorder(), [1, 2, 4, 5, 3])
        self.assertEqual(tree.inorder(), [4, 2, 5, 1, 3])
        self.assertEqual(tree.postorder(), [4, 5, 2, 3, 1])

    def test_empty_tree(self):
        tree = BinaryTree()
        self.assertEqual(tree.preorder(), [])
        self.assertEqual(tree.inorder(), [])
        self.assertEqual(tree.postorder(), [])
        self.assertEqual(tree.level_order(), [])


if __name__ == "__main__":
    unittest.main()
