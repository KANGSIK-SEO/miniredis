"""체이닝 방식 해시맵 단위 테스트."""
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import unittest
from datastructures.hash_map import HashMap


class TestHashMap(unittest.TestCase):
    def test_put_and_get(self):
        hm = HashMap(capacity=4)
        self.assertEqual(hm.size(), 0)
        self.assertIsNone(hm.get("user:1"))
        self.assertFalse(hm.contains("user:1"))

        hm.put("user:1", "Alice")
        self.assertEqual(hm.size(), 1)
        self.assertTrue(hm.contains("user:1"))
        self.assertEqual(hm.get("user:1"), "Alice")

    def test_update_existing_key(self):
        hm = HashMap()
        old = hm.put("key", "val1")
        self.assertIsNone(old)
        self.assertEqual(hm.get("key"), "val1")

        old2 = hm.put("key", "val2")
        self.assertEqual(old2, "val1")
        self.assertEqual(hm.get("key"), "val2")
        self.assertEqual(hm.size(), 1)

    def test_remove(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")

        removed = hm.remove("k1")
        self.assertEqual(removed, "v1")
        self.assertEqual(hm.size(), 1)
        self.assertIsNone(hm.get("k1"))
        self.assertFalse(hm.contains("k1"))

        # 존재하지 않는 키 삭제
        self.assertIsNone(hm.remove("nonexistent"))

    def test_keys(self):
        hm = HashMap()
        self.assertEqual(hm.keys(), [])

        hm.put("a", "1")
        hm.put("b", "2")
        hm.put("c", "3")
        keys = hm.keys()
        self.assertEqual(len(keys), 3)
        self.assertIn("a", keys)
        self.assertIn("b", keys)
        self.assertIn("c", keys)

    def test_resize_and_rehashing(self):
        # 초기 capacity=4, 로드 팩터 0.75 초과 시 확장
        # 4 * 0.75 = 3개 초과 (즉 4번째 삽입 시 resize)
        hm = HashMap(capacity=4)
        self.assertEqual(hm.capacity(), 4)

        hm.put("k1", "v1")
        hm.put("k2", "v2")
        hm.put("k3", "v3")
        self.assertEqual(hm.capacity(), 4)

        # 4번째 원소 삽입 시 로드 팩터(4/4 = 1.0 > 0.75)로 리사이즈
        hm.put("k4", "v4")
        self.assertEqual(hm.capacity(), 8)
        self.assertEqual(hm.size(), 4)

        # 기존 및 신규 키 모두 정상 접근 가능한지 검증
        for i in range(1, 5):
            self.assertEqual(hm.get(f"k{i}"), f"v{i}")

        # 추가 대량 삽입으로 다단계 리사이즈 검증
        for i in range(5, 50):
            hm.put(f"key_{i}", f"val_{i}")

        self.assertEqual(hm.size(), 49)
        for i in range(5, 50):
            self.assertEqual(hm.get(f"key_{i}"), f"val_{i}")


if __name__ == "__main__":
    unittest.main()
