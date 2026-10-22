"""이중 연결 리스트 단위 테스트."""

import unittest
from datastructures.doubly_linked_list import DoublyLinkedList, Node


class TestDoublyLinkedList(unittest.TestCase):
    def test_empty_list(self):
        dll = DoublyLinkedList()
        self.assertEqual(dll.size(), 0)
        self.assertTrue(dll.is_empty())
        self.assertIsNone(dll.remove_front())
        self.assertIsNone(dll.remove_back())
        self.assertIsNone(dll.front_node())
        self.assertIsNone(dll.back_node())

    def test_insert_front_and_back(self):
        dll = DoublyLinkedList()
        n1 = dll.insert_front("A")
        self.assertEqual(dll.size(), 1)
        self.assertFalse(dll.is_empty())
        self.assertEqual(dll.to_list(), ["A"])

        n2 = dll.insert_back("B")
        self.assertEqual(dll.size(), 2)
        self.assertEqual(dll.to_list(), ["A", "B"])

        n0 = dll.insert_front("Z")
        self.assertEqual(dll.to_list(), ["Z", "A", "B"])
        self.assertEqual(dll.front_node(), n0)
        self.assertEqual(dll.back_node(), n2)

    def test_remove_front_and_back(self):
        dll = DoublyLinkedList()
        dll.insert_back("1")
        dll.insert_back("2")
        dll.insert_back("3")

        self.assertEqual(dll.remove_front(), "1")
        self.assertEqual(dll.to_list(), ["2", "3"])
        self.assertEqual(dll.size(), 2)

        self.assertEqual(dll.remove_back(), "3")
        self.assertEqual(dll.to_list(), ["2"])
        self.assertEqual(dll.size(), 1)

        self.assertEqual(dll.remove_front(), "2")
        self.assertEqual(dll.to_list(), [])
        self.assertEqual(dll.size(), 0)
        self.assertTrue(dll.is_empty())

    def test_remove_node(self):
        dll = DoublyLinkedList()
        a = dll.insert_back("A")
        b = dll.insert_back("B")
        c = dll.insert_back("C")

        # 중간 노드 b 삭제
        data = dll.remove_node(b)
        self.assertEqual(data, "B")
        self.assertEqual(dll.to_list(), ["A", "C"])
        self.assertEqual(dll.size(), 2)

        # 맨 앞 노드 a 삭제
        data = dll.remove_node(a)
        self.assertEqual(data, "A")
        self.assertEqual(dll.to_list(), ["C"])
        self.assertEqual(dll.size(), 1)

        # 맨 뒤 노드 c 삭제
        data = dll.remove_node(c)
        self.assertEqual(data, "C")
        self.assertEqual(dll.to_list(), [])
        self.assertEqual(dll.size(), 0)

    def test_move_to_front(self):
        dll = DoublyLinkedList()
        a = dll.insert_back("A")
        b = dll.insert_back("B")
        c = dll.insert_back("C")
        self.assertEqual(dll.to_list(), ["A", "B", "C"])

        # 끝 노드 c를 맨 앞으로 이동
        dll.move_to_front(c)
        self.assertEqual(dll.to_list(), ["C", "A", "B"])

        # 중간 노드 A를 맨 앞으로 이동
        dll.move_to_front(a)
        self.assertEqual(dll.to_list(), ["A", "C", "B"])

        # 이미 맨 앞인 노드 A를 다시 이동
        dll.move_to_front(a)
        self.assertEqual(dll.to_list(), ["A", "C", "B"])


if __name__ == "__main__":
    unittest.main()
