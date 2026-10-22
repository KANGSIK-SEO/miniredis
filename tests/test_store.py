"""Mini Redis 스토어 및 명령어 전체 통합 단위 테스트."""

import unittest
from mini_redis.store import MiniRedisStore


class MockClock:
    """테스트용 가상 시계 클래스."""

    def __init__(self, initial_time: float = 1000.0):
        self._current_time: float = initial_time

    def __call__(self) -> float:
        return self._current_time

    def advance(self, seconds: float) -> None:
        self._current_time += seconds


class TestMiniRedisStore(unittest.TestCase):
    def test_basic_string_commands(self):
        r = MiniRedisStore()

        # 1. SET & GET
        self.assertEqual(r.execute('SET user:1 "Alice"'), "OK")
        self.assertEqual(r.execute("GET user:1"), '"Alice"')

        # 따옴표 없는 값 저장
        self.assertEqual(r.execute("SET user:2 Bob"), "OK")
        self.assertEqual(r.execute("GET user:2"), '"Bob"')

        # 2. EXISTS
        self.assertEqual(r.execute("EXISTS user:1"), "(integer) 1")
        self.assertEqual(r.execute("EXISTS user:nonexistent"), "(integer) 0")

        # 3. DBSIZE
        self.assertEqual(r.execute("DBSIZE"), "(integer) 2")

        # 4. KEYS
        keys_output = r.execute("KEYS")
        self.assertIn('"user:1"', keys_output)
        self.assertIn('"user:2"', keys_output)

        # 5. DEL
        self.assertEqual(r.execute("DEL user:1"), "(integer) 1")
        self.assertEqual(r.execute("DEL user:1"), "(integer) 0")
        self.assertEqual(r.execute("GET user:1"), "(nil)")
        self.assertEqual(r.execute("DBSIZE"), "(integer) 1")

        # 빈 상태의 KEYS
        r.execute("DEL user:2")
        self.assertEqual(r.execute("KEYS"), "(empty array)")

    def test_prompt_example_scenario(self):
        """문제 명세서 8번 결과 예시 시나리오 그대로 검증."""
        clock = MockClock(100.0)
        r = MiniRedisStore(now_func=clock)

        self.assertEqual(r.execute("CONFIG SET maxmemory 30"), "OK")
        self.assertEqual(r.execute('SET user:1 "Alice"'), "OK")
        self.assertEqual(r.execute('SET user:2 "Bob"'), "OK")
        self.assertEqual(r.execute('SET user:3 "Charlie"'), "OK")

        # maxmemory(30) 초과로 LRU(user:1) 제거됨
        # user:2 (6+3=9), user:3 (6+7=13) => used_memory = 22
        self.assertEqual(r.execute("GET user:1"), "(nil)")

        info = r.execute("INFO memory")
        self.assertIn("used_memory:22", info)
        self.assertIn("maxmemory:30", info)
        self.assertIn("evicted_keys:1", info)

        keys_out = r.execute("KEYS")
        self.assertIn('"user:2"', keys_out)
        self.assertIn('"user:3"', keys_out)
        self.assertNotIn('"user:1"', keys_out)

        # TTL 동작 검증
        self.assertEqual(r.execute("EXPIRE user:2 3"), "(integer) 1")
        # 즉시 조회 시 남은 초는 3
        self.assertEqual(r.execute("TTL user:2"), "(integer) 3")

        # 1초 경과
        clock.advance(1.0)
        self.assertEqual(r.execute("TTL user:2"), "(integer) 2")

        # 3초 경과 후 (총 4초)
        clock.advance(3.0)
        self.assertEqual(r.execute("GET user:2"), "(nil)")
        self.assertEqual(r.execute("TTL user:2"), "(integer) -2")

    def test_lru_order_updated_on_get(self):
        """GET 성공 시 LRU 갱신되어 다음 방출 대상에서 제외되는지 검증."""
        r = MiniRedisStore()
        r.execute("CONFIG SET maxmemory 6")  # 각 키+값 2바이트씩
        r.execute("SET a 1")  # len: 2
        r.execute("SET b 2")  # len: 2
        # used_memory = 4

        # a를 조회하여 LRU 상 맨 앞으로 갱신 (최근 사용)
        self.assertEqual(r.execute("GET a"), '"1"')

        # c를 추가하면 used_memory = 6
        r.execute("SET c 3")

        # d를 추가하면 used_memory가 8이 되어 초과 -> b가 가장 오래되었으므로 b 방출
        r.execute("SET d 4")

        self.assertEqual(r.execute("GET b"), "(nil)")
        self.assertEqual(r.execute("GET a"), '"1"')
        self.assertEqual(r.execute("GET c"), '"3"')
        self.assertEqual(r.execute("GET d"), '"4"')

    def test_single_entry_oom(self):
        """단일 엔트리 자체가 maxmemory를 초과하면 OOM 에러 출력 및 미저장."""
        r = MiniRedisStore()
        r.execute("CONFIG SET maxmemory 5")
        res = r.execute('SET toolong "123456"')
        self.assertEqual(res, "(error) OOM command not allowed when used_memory > 'maxmemory'")
        self.assertEqual(r.execute("DBSIZE"), "(integer) 0")
        self.assertEqual(r.execute("GET toolong"), "(nil)")

    def test_set_overwriting_clears_ttl(self):
        """기존 키를 덮어쓰는 경우 기존 TTL은 초기화(삭제)되어 영구 보관된다."""
        clock = MockClock(500.0)
        r = MiniRedisStore(now_func=clock)

        r.execute("SET key1 val1")
        r.execute("EXPIRE key1 5")
        self.assertEqual(r.execute("TTL key1"), "(integer) 5")

        # 덮어쓰기
        r.execute("SET key1 val2")
        self.assertEqual(r.execute("TTL key1"), "(integer) -1")

        # 10초 경과해도 여전히 유효
        clock.advance(10.0)
        self.assertEqual(r.execute("GET key1"), '"val2"')
        self.assertEqual(r.execute("TTL key1"), "(integer) -1")

    def test_expire_edge_cases(self):
        clock = MockClock(10.0)
        r = MiniRedisStore(now_func=clock)

        # 없는 키에 EXPIRE
        self.assertEqual(r.execute("EXPIRE no_such_key 10"), "(integer) 0")

        # 없는 키에 TTL
        self.assertEqual(r.execute("TTL no_such_key"), "(integer) -2")

        # TTL 없는 존재하는 키
        r.execute("SET persistent_key val")
        self.assertEqual(r.execute("TTL persistent_key"), "(integer) -1")

        # seconds <= 0 인 경우 즉시 만료 삭제
        self.assertEqual(r.execute("EXPIRE persistent_key 0"), "(integer) 1")
        self.assertEqual(r.execute("GET persistent_key"), "(nil)")
        self.assertEqual(r.execute("TTL persistent_key"), "(integer) -2")

    def test_error_standards(self):
        """명세서에 정의된 표준 에러 형식 검증."""
        r = MiniRedisStore()

        # 1. Unknown command
        self.assertEqual(r.execute("HELLO"), "(error) ERR unknown command 'HELLO'")
        self.assertEqual(r.execute("FOOBAR a b"), "(error) ERR unknown command 'FOOBAR'")

        # 2. Wrong number of arguments
        self.assertEqual(
            r.execute("GET"),
            "(error) ERR wrong number of arguments for 'GET' command",
        )
        self.assertEqual(
            r.execute("SET a"),
            "(error) ERR wrong number of arguments for 'SET' command",
        )
        self.assertEqual(
            r.execute("DEL"),
            "(error) ERR wrong number of arguments for 'DEL' command",
        )
        self.assertEqual(
            r.execute("DBSIZE extra_arg"),
            "(error) ERR wrong number of arguments for 'DBSIZE' command",
        )

        # 3. Integer parse failure
        self.assertEqual(
            r.execute("CONFIG SET maxmemory abc"),
            "(error) ERR value is not an integer or out of range",
        )
        self.assertEqual(
            r.execute("CONFIG SET maxmemory -10"),
            "(error) ERR value is not an integer or out of range",
        )
        r.execute("SET k v")
        self.assertEqual(
            r.execute("EXPIRE k not_a_number"),
            "(error) ERR value is not an integer or out of range",
        )


if __name__ == "__main__":
    unittest.main()
