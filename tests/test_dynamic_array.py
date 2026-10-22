"""동적 배열 단위 테스트."""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import unittest
from datastructures.dynamic_array import DynamicArray


class TestDynamicArray(unittest.TestCase):
    def test_append_and_growth(self):
        arr = DynamicArray(capacity=2)
        self.assertEqual(arr.capacity(), 2)
        self.assertEqual(arr.size(), 0)

        arr.append(10)
        arr.append(20)
        self.assertEqual(arr.size(), 2)
        self.assertEqual(arr.capacity(), 2)

        arr.append(30)  # 용량 2배 확장 트리거
        self.assertEqual(arr.size(), 3)
        self.assertEqual(arr.capacity(), 4)
        self.assertEqual(arr.to_list(), [10, 20, 30])

    def test_get_set(self):
        arr = DynamicArray()
        arr.append("a")
        arr.append("b")
        self.assertEqual(arr.get(0), "a")
        self.assertEqual(arr[1], "b")

        arr.set(0, "z")
        self.assertEqual(arr[0], "z")

        with self.assertRaises(IndexError):
            _ = arr.get(5)

    def test_pop_and_insert(self):
        arr = DynamicArray()
        arr.append("A")
        arr.append("B")
        arr.append("C")

        self.assertEqual(arr.pop(), "C")
        self.assertEqual(arr.to_list(), ["A", "B"])

        arr.insert(1, "INSERTED")
        self.assertEqual(arr.to_list(), ["A", "INSERTED", "B"])

        self.assertTrue(arr.remove("INSERTED"))
        self.assertEqual(arr.to_list(), ["A", "B"])
        self.assertFalse(arr.remove("NOT_FOUND"))


if __name__ == "__main__":
    unittest.main()
