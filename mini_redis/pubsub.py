"""채널 기반 Pub/Sub 브로커 모듈 (보너스 과제 5).

이중 연결 리스트(DoublyLinkedList)를
1. 채널별 구독자 목록 관리
2. 각 구독자의 메시지 수신함(Inbox) 큐
로 재활용하여 실시간 메시지 발행/구독 패턴을 구현합니다.
"""

from typing import Any, List, Optional
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datastructures.doubly_linked_list import DoublyLinkedList
from datastructures.hash_map import HashMap


class Subscriber:
    """메시지를 수신하는 구독자 클라이언트 모델.

    각 구독자는 자신만의 전용 메시지 큐(inbox: DoublyLinkedList)를 가집니다.
    """

    def __init__(self, client_id: str):
        self.client_id: str = client_id
        # 메시지가 발행되면 이 큐의 뒤(insert_back)로 차곡차곡 쌓입니다.
        self.inbox: DoublyLinkedList = DoublyLinkedList()

    def receive(self, channel: str, message: str) -> None:
        """새 메시지를 받아 인박스 큐의 맨 뒤에 넣습니다. (Enqueue, O(1))"""
        self.inbox.insert_back((channel, message))

    def poll_messages(self) -> List[tuple]:
        """인박스 큐의 앞에서부터 메시지를 하나씩 꺼내옵니다. (Dequeue, O(1))"""
        msgs = []
        while not self.inbox.is_empty():
            msgs.append(self.inbox.remove_front())
        return msgs


class PubSubBroker:
    """채널별 구독자 등록 및 브로드캐스트 브로커."""

    def __init__(self):
        # 자체 구현 HashMap 사용: 채널명(str) -> 해당 채널을 구독한 Subscriber들의 DoublyLinkedList
        self._channels: HashMap = HashMap()

    def subscribe(self, channel: str, subscriber: Subscriber) -> int:
        """클라이언트를 특정 채널의 구독자로 등록하고 현재 해당 채널의 총 구독자 수를 반환합니다."""
        subscribers_list: Optional[DoublyLinkedList] = self._channels.get(channel)
        if subscribers_list is None:
            subscribers_list = DoublyLinkedList()
            self._channels.put(channel, subscribers_list)

        # 중복 등록 방지
        for node in subscribers_list.iter_nodes():
            sub: Subscriber = node.data
            if sub.client_id == subscriber.client_id:
                return subscribers_list.size()

        subscribers_list.insert_back(subscriber)
        return subscribers_list.size()

    def unsubscribe(self, channel: str, client_id: str) -> int:
        """채널에서 특정 클라이언트를 구독 해제하고 남은 구독자 수를 반환합니다."""
        subscribers_list: Optional[DoublyLinkedList] = self._channels.get(channel)
        if subscribers_list is None:
            return 0

        for node in subscribers_list.iter_nodes():
            sub: Subscriber = node.data
            if sub.client_id == client_id:
                subscribers_list.remove_node(node)
                break

        return subscribers_list.size()

    def publish(self, channel: str, message: str) -> int:
        """채널에 연결된 모든 구독자에게 메시지를 복제 배달(Fan-out)하고, 수신한 구독자 수를 반환합니다."""
        subscribers_list: Optional[DoublyLinkedList] = self._channels.get(channel)
        if subscribers_list is None or subscribers_list.is_empty():
            return 0

        count = 0
        for node in subscribers_list.iter_nodes():
            sub: Subscriber = node.data
            sub.receive(channel, message)
            count += 1

        return count

    def channel_count(self) -> int:
        """현재 개설된 총 채널 개수."""
        return self._channels.size()
