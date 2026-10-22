"""Pub/Sub 발행/구독 기능 단위 테스트."""

import unittest
from mini_redis.store import MiniRedisStore
from mini_redis.pubsub import PubSubBroker, Subscriber


class TestPubSub(unittest.TestCase):
    def test_broker_direct(self):
        broker = PubSubBroker()
        sub1 = Subscriber("client1")
        sub2 = Subscriber("client2")

        # 아무도 구독하지 않은 채널 발행
        self.assertEqual(broker.publish("news", "Hello World"), 0)

        # 구독자 등록
        self.assertEqual(broker.subscribe("news", sub1), 1)
        self.assertEqual(broker.subscribe("news", sub2), 2)

        # 메시지 발행
        count = broker.publish("news", "Breaking News!")
        self.assertEqual(count, 2)

        # 각 구독자가 메시지를 받았는지 검증
        self.assertEqual(sub1.poll_messages(), [("news", "Breaking News!")])
        self.assertEqual(sub2.poll_messages(), [("news", "Breaking News!")])
        # 인박스를 비운 뒤 재조회 시 비어있음
        self.assertEqual(sub1.poll_messages(), [])

        # 구독 해제
        self.assertEqual(broker.unsubscribe("news", "client1"), 1)
        self.assertEqual(broker.publish("news", "Second News"), 1)
        self.assertEqual(sub1.poll_messages(), [])
        self.assertEqual(sub2.poll_messages(), [("news", "Second News")])

    def test_store_command_integration(self):
        store = MiniRedisStore()
        res_sub = store.execute("SUBSCRIBE sports user1")
        self.assertIn('"sports"', res_sub)
        self.assertIn("(integer) 1", res_sub)

        res_pub = store.execute("PUBLISH sports \"Go Team!\"")
        self.assertEqual(res_pub, "(integer) 1")


if __name__ == "__main__":
    unittest.main()
