# Mini Redis CLI — 정보를 엄청 빠르게 찾아주는 작은 저장소

> **분야**: AI/SW 기초 | **구분**: 자료구조와 알고리즘 (80시간 미션)  
> **핵심 원칙**: 파이썬 내장 `dict`, `set`, `collections` 일절 사용 금지!  
> 해시맵, 이중 연결 리스트, 최소 힙 등 핵심 자료구조를 밑바닥부터 직접 구현하여 완성한 CLI 기반 Mini Redis 엔진입니다.

---

## 1. 프로젝트 개요

Redis는 전 세계에서 가장 널리 쓰이는 In-Memory Key-Value 데이터베이스입니다. Redis가 극도로 빠른 이유는 단순히 메모리에 데이터를 올리기 때문이 아니라, **해시맵(HashMap)**, **이중 연결 리스트(Doubly Linked List)**, **힙(Min-Heap)**을 목적에 맞게 $O(1)$ 및 $O(\log n)$으로 유기적으로 결합했기 때문입니다.

본 프로젝트는 내장 컬렉션 라이브러리에 의존하지 않고 기초 자료구조를 바닥부터 구현하여, 메모리 제한 환경에서의 LRU(Least Recently Used) 방출 정책과 힙 기반 TTL(Time-To-Live) 만료 메커니즘을 완벽하게 재현합니다.

```mermaid
flowchart TD
    CLI["CLI REPL (mini-redis>)"] --> Parser["Command Parser (shlex / tokenizer)"]
    Parser --> Engine["MiniRedis Store Engine"]

    subgraph Storage["저장소 & 알고리즘 조합"]
        Engine -->|Key -> Entry Lookup| HM["HashMap (Separate Chaining)\n- DJB2 Hash Function\n- DoublyLinkedList Buckets\n- 0.75 Load Factor Resizing"]
        Engine -->|O(1) Access Order Tracking| DLL["Doubly Linked List (LRU)\n- Head (MRU) <-> Tail (LRU)\n- Sentinel Nodes for O(1) ops"]
        Engine -->|O(1) Peek / O(log n) Expiration| Heap["Min-Heap (TTL)\n- (expire_at, key, version)\n- Active & Lazy Deletion"]
    end

    subgraph MemoryMgr["메모리 & 수명 관리"]
        Engine -->|used_memory = Σ(len(k) + len(v))| Mem["Memory Tracker\n- CONFIG SET maxmemory\n- INFO memory"]
        Mem -->|used_memory > maxmemory| Evict["LRU Eviction (Tail Drop)"]
    end
```

---

## 2. 4대 과제 목표 및 상세 기술 분석

### ① 해시맵의 해시 함수와 충돌 해결 방식(체이닝)
- **해시 함수 (DJB2)**:
  문자열의 각 UTF-8 바이트를 순회하며 33배수를 누적하고 32비트 마스킹을 적용합니다.
  $$h = ((h \ll 5) + h) + \text{byte}$$
  단순한 나눗셈이나 합산 방식보다 비트 분산도가 뛰어나 해시 충돌을 최소화합니다.
- **충돌 해결 (Separate Chaining)**:
  동일한 버킷 인덱스로 매핑되는 충돌이 발생하면, 각 버킷 슬롯에 할당된 `DoublyLinkedList`에 `HashEntry(key, value)` 노드를 체이닝하여 충돌을 해결합니다.
- **동적 리사이징 (Rehashing)**:
  로드 팩터($\alpha = \frac{\text{size}}{\text{capacity}}$)가 `0.75`를 초과하면 버킷 용량을 2배로 확장하고, 기존 모든 엔트리를 새로운 버킷 테이블에 재해싱하여 평균 $O(1)$의 탐색 시간을 항시 유지합니다.

### ② 이중 연결 리스트 + 해시맵 조합으로 O(1) LRU 추적이 가능한 이유
- 일반적인 리스트나 배열에서 특정 원소를 찾아 맨 앞으로 옮기거나 삭제하려면 $O(n)$의 순차 탐색이 필요합니다.
- 본 Mini Redis에서는 해시맵의 값으로 `RedisEntry`를 보관하며, 이 엔트리가 **LRU 이중 연결 리스트의 노드(`Node`) 참조를 직접 가리킵니다**.
- 따라서 `GET` 또는 `SET` 호출 시:
  1. 해시맵 조회를 통해 $O(1)$에 `RedisEntry` 획득
  2. 엔트리에 저장된 `lru_node` 참조를 통해 탐색 없이 즉시 리스트의 해당 노드 접근
  3. 센티넬 노드를 둔 이중 연결 리스트에서 해당 노드를 언링크한 뒤 헤드 바로 뒤로 연결(`move_to_front`)하는 작업이 **순수 $O(1)$**에 수행됩니다.
- 메모리 방출 시에는 리스트의 끝단(`tail.prev`) 노드를 조회하여 $O(1)$에 방출할 키(LRU Victim)를 특정할 수 있습니다.

### ③ 힙(Min-Heap)이 TTL 만료 시간 관리에 적합한 이유
- 모든 키의 만료 시각을 매초 순차 탐색($O(n)$)하는 것은 데이터가 많아질수록 시스템에 심각한 병목을 유발합니다.
- `MinHeap`은 완전 이진 트리 배열 구조로, **가장 이른 만료 시각(최솟값)을 갖는 루트 노드를 $O(1)$ 시간에 `peek`**할 수 있습니다.
- 상위 노드가 아직 만료되지 않았다면 그보다 뒤에 만료될 하위 노드들은 검사할 필요조차 없으므로 검사 비용이 극적으로 절감됩니다.
- 만료 시에는 루트 노드를 꺼내고($O(\log n)$), `expire_version` 및 `expire_at` 일치 여부를 검증하는 **Lazy Deletion 전략**을 병행하여 불필요한 힙 재구성을 방지합니다.

### ④ 메모리 제한 환경에서 LRU 방출 전체 흐름
1. **메모리 계산 공식**:
   $$\text{used\_memory} = \sum (\text{len}(\text{utf8}(\text{key})) + \text{len}(\text{utf8}(\text{value})))$$
   자료구조 노드/포인터 오버헤드는 제외한 순수 바이트 합계를 유지합니다.
2. **단일 엔트리 검사**:
   신규 저장하려는 (키+값)의 바이트 크기가 `maxmemory`를 단독으로 초과하면 저장을 거부하고 `(error) OOM command not allowed when used_memory > 'maxmemory'`를 반환합니다.
3. **증분 갱신 및 방출**:
   - 기존 키 덮어쓰기 시: 기존 크기 차감 후 신규 크기 가산, TTL 초기화, LRU 최신화
   - 신규 키 추가 시: 신규 크기 가산 및 LRU 헤드 삽입
   - `used_memory > maxmemory`인 동안: LRU 리스트의 `tail.prev`(가장 오래 참조되지 않은 키)를 꺼내어 해시맵과 LRU 리스트에서 제거하고, 메모리를 반환하며 `evicted_keys` 카운터를 1 증가시킵니다.

---

## 3. 지원 명령어 명세

| 범주 | 명령어 | 설명 | 출력 형식 예시 |
|---|---|---|---|
| **String** | `SET key value` | 키에 값 저장 (LRU 최신화, TTL 초기화, OOM 방출) | `OK` |
| | `GET key` | 키 값 조회 (성공 시에만 LRU 갱신, 만료 시 (nil)) | `"value"` 또는 `(nil)` |
| | `DEL key` | 키 삭제 (Map, LRU, TTL 연계 제거) | `(integer) 1` 또는 `(integer) 0` |
| | `EXISTS key` | 키 존재 여부 확인 | `(integer) 1` 또는 `(integer) 0` |
| | `DBSIZE` | 유효 키 총 개수 반환 | `(integer) N` |
| | `KEYS` | 전체 유효 키 목록 출력 | `1. "key1"\n2. "key2"` 또는 `(empty array)` |
| **메모리** | `CONFIG SET maxmemory <bytes>` | 최대 메모리 바이트 설정 (0=무제한) | `OK` |
| | `INFO memory` | 메모리 사용량, 한도, 방출 수치 조회 | `used_memory:X\nmaxmemory:Y\nevicted_keys:Z` |
| **TTL** | `EXPIRE key <seconds>` | 키 만료 시간 설정 (<=0 초는 즉시 만료) | `(integer) 1` 또는 `(integer) 0` |
| | `TTL key` | 남은 만료 시간 초 조회 (-2: 없음/만료, -1: 영구) | `(integer) N` |
| **보너스** | `PUBLISH channel message` | 채널로 메시지 브로드캐스트 | `(integer) <수신자 수>` |
| | `SUBSCRIBE channel [id]` | 채널 구독 등록 | `1) "subscribe"\n...` |

---

## 4. 디렉토리 구조

```
uptriangle/
├── .gitignore
├── README.md                   # 프로젝트 종합 설명서
├── STACK_QUEUE_DEQUE.md        # [보너스 2] 스택/큐/덱 심층 개념 분석 문서
├── main.py                     # CLI 진입점 스크립트
├── datastructures/             # 순수 자체 구현 자료구조 패키지
│   ├── __init__.py
│   ├── doubly_linked_list.py   # 이중 연결 리스트 (센티넬 노드, O(1) 이동)
│   ├── hash_map.py             # 체이닝 해시맵 (DJB2, 로드팩터 0.75 리사이즈)
│   ├── min_heap.py             # 최소 힙 (우선순위 큐, heapify up/down)
│   ├── dynamic_array.py        # [보너스 1] 동적 배열 (배열 2배 확장 및 축소)
│   ├── binary_tree.py          # [보너스 3] 이진 트리 (전위/중위/후위/레벨 순회)
│   └── binary_search_tree.py   # [보너스 4] 이진 탐색 트리 (BST 탐색/삭제/정렬)
├── mini_redis/                 # Mini Redis 엔진 & 인터페이스
│   ├── __init__.py
│   ├── entry.py                # 키 엔트리 데이터 클래스
│   ├── parser.py               # 따옴표/공백 처리 명령어 토크나이저
│   ├── pubsub.py               # [보너스 5] 채널 기반 Pub/Sub 브로커
│   ├── store.py                # Mini Redis 핵심 저장소 및 명령어 실행기
│   └── cli.py                  # 대화형 REPL 인터페이스
└── tests/                      # 테스트 스위트 (100% 자체 통과)
    ├── __init__.py
    ├── test_doubly_linked_list.py
    ├── test_hash_map.py
    ├── test_min_heap.py
    ├── test_dynamic_array.py
    ├── test_binary_tree.py
    ├── test_bst.py
    ├── test_store.py
    ├── test_pubsub.py
    └── test_cli.py
```

---

## 5. 실행 및 테스트 방법

### 5.1 CLI 실행
```bash
python3 main.py
```

실행 화면 예시:
```
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
mini-redis> KEYS
1. "user:2"
2. "user:3"
mini-redis> EXPIRE user:2 3
(integer) 1
mini-redis> TTL user:2
(integer) 3
mini-redis> exit
```

### 5.2 전체 단위 테스트 실행
```bash
python3 -m unittest discover -s tests
```
결과:
```
..................................
----------------------------------------------------------------------
Ran 34 tests in 0.001s

OK
```
총 34개의 단위 테스트가 작성되어 있으며 자료구조, OOM 처리, LRU 교체, 만료 시각 검증이 100% 통과합니다.
