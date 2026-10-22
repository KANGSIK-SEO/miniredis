"""CLI REPL 파싱 및 통합 테스트."""

import unittest
from mini_redis.parser import tokenize
from mini_redis.store import MiniRedisStore


class TestCli(unittest.TestCase):
    def test_tokenize(self):
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize("   "), [])
        self.assertEqual(tokenize('SET user:1 "Alice"'), ["SET", "user:1", "Alice"])
        self.assertEqual(
            tokenize('SET greeting "Hello World"'),
            ["SET", "greeting", "Hello World"],
        )
        self.assertEqual(tokenize("DEL k1"), ["DEL", "k1"])

    def test_tokenize_syntax_error(self):
        with self.assertRaises(ValueError):
            tokenize('SET user:1 "Alice unclosed')

    def test_execute_empty_and_whitespace(self):
        store = MiniRedisStore()
        self.assertIsNone(store.execute(""))
        self.assertIsNone(store.execute("    "))

    def test_syntax_error_handling_in_execute(self):
        store = MiniRedisStore()
        result = store.execute('SET user:1 "Unclosed')
        self.assertTrue(result.startswith("(error) ERR syntax error"))


if __name__ == "__main__":
    unittest.main()
