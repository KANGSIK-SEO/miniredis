"""최소 힙 단위 테스트."""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import unittest
from datastructures.min_heap import MinHeap


class TestMinHeap(unittest.TestCase):
    def test_empty_heap(self):
        heap = MinHeap()
        self.assertEqual(heap.size(), 0)
        self.assertTrue(heap.is_empty())
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())

    def test_push_and_peek(self):
        heap = MinHeap()
        heap.push((10, "k1"))
        self.assertEqual(heap.peek(), (10, "k1"))
        self.assertEqual(heap.size(), 1)

        heap.push((5, "k2"))
        self.assertEqual(heap.peek(), (5, "k2"))
        self.assertEqual(heap.size(), 2)

        heap.push((15, "k3"))
        self.assertEqual(heap.peek(), (5, "k2"))

        heap.push((1, "k4"))
        self.assertEqual(heap.peek(), (1, "k4"))

    def test_pop_ascending_order(self):
        heap = MinHeap()
        values = [(40, "d"), (10, "a"), (30, "c"), (20, "b"), (50, "e"), (5, "zero")]
        for item in values:
            heap.push(item)

        self.assertEqual(heap.size(), len(values))

        extracted = []
        while not heap.is_empty():
            extracted.append(heap.pop())

        expected = sorted(values)
        self.assertEqual(extracted, expected)
        self.assertEqual(heap.size(), 0)

    def test_duplicate_priorities(self):
        heap = MinHeap()
        heap.push((100, "user:b"))
        heap.push((100, "user:a"))
        heap.push((100, "user:c"))

        first = heap.pop()
        second = heap.pop()
        third = heap.pop()

        self.assertEqual(first, (100, "user:a"))
        self.assertEqual(second, (100, "user:b"))
        self.assertEqual(third, (100, "user:c"))


if __name__ == "__main__":
    unittest.main()
