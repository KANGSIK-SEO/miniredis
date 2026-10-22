"""
Mini Redis 프로젝트 완주 기술 보고서 PDF 생성 스크립트
ReportLab + AppleGothic 한국어 폰트 지원
출력: /Users/kangsikseo/Downloads/Mini_Redis_Report.pdf
"""

import os
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 폰트 등록
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
pdfmetrics.registerFont(TTFont("AppleGothic", FONT_PATH))

DEST_DOWNLOADS = "/Users/kangsikseo/Downloads/Mini_Redis_Report.pdf"
DEST_LOCAL = "/Users/kangsikseo/miniredis/Mini_Redis_Report.pdf"

def create_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # 커스텀 스타일 정의
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="AppleGothic",
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#C0392B"), # Redis Red
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        fontName="AppleGothic",
        fontSize=11.5,
        leading=16,
        textColor=colors.HexColor("#2C3E50"),
        alignment=1,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName="AppleGothic",
        fontSize=13.5,
        leading=18,
        textColor=colors.HexColor("#C0392B"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName="AppleGothic",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        fontName="AppleGothic",
        fontSize=8.5,
        leading=13.5,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=4
    )

    code_pre_style = ParagraphStyle(
        "Code_Pre",
        fontName="AppleGothic",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#1A252F")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="AppleGothic",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="AppleGothic",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2C3E50")
    )

    story = []

    # ---------------- 1. 제목 및 헤더 ----------------
    story.append(Spacer(1, 5))
    story.append(Paragraph("Mini Redis 기술 구현 및 완주 보고서", title_style))
    story.append(Paragraph("정보를 엄청 빠르게 찾아주는 작은 저장소 만들기 (자료구조와 알고리즘 80시간 미션)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#C0392B"), spaceAfter=12))

    # 프로젝트 메타데이터 테이블
    meta_data = [
        [Paragraph("<b>개발자 / GitHub</b>", table_cell_style), Paragraph("KANGSIK-SEO (<font color='#2980B9'>https://github.com/KANGSIK-SEO/miniredis</font>)", table_cell_style)],
        [Paragraph("<b>개발 환경</b>", table_cell_style), Paragraph("macOS (Apple Silicon M4 Max, 48GB) / Python 3.14 / Git", table_cell_style)],
        [Paragraph("<b>핵심 제약 사항</b>", table_cell_style), Paragraph("<font color='#C0392B'><b>dict, set, collections 사용 일절 금지</b></font> (기초 자료구조 직접 구현)", table_cell_style)],
        [Paragraph("<b>단위 테스트 결과</b>", table_cell_style), Paragraph("<b>34개 단위 테스트 100% 통과</b> (Ran 34 tests in 0.002s, OK)", table_cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[110, 410])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F6F7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # ---------------- 2. 프로젝트 개요 및 핵심 질문 ----------------
    story.append(Paragraph("1. 프로젝트 개요 및 본질 (Key-Value 관점)", h1_style))
    story.append(Paragraph(
        "Redis는 단순한 Key-Value 저장소처럼 보이지만, <b>'한정된 메모리 안에서 수천만 개의 데이터를 1번(O(1)) 만에 찾고, "
        "가장 오래된 데이터를 즉시 버리며(LRU), 유통기한 지난 데이터를 실시간 청소(TTL)'</b>하는 정밀 시스템입니다. "
        "본 프로젝트는 파이썬 내장 컬렉션에 의존하지 않고 기초 자료구조를 바닥부터 구현하여 Redis의 고성능 엔진 아키텍처를 증명했습니다.",
        body_style
    ))

    # 3대 자료구조 테이블
    ds_summary_data = [
        [Paragraph("자료구조", table_header_style), Paragraph("담당 역할 (Key-Value 관점)", table_header_style), Paragraph("시간 복잡도", table_header_style), Paragraph("설계 및 구현 원리", table_header_style)],
        [
            Paragraph("<b>HashMap</b><br/>(체이닝 방식)", table_cell_style),
            Paragraph("초고속 Key ──▶ Value 탐색 메인 저장소", table_cell_style),
            Paragraph("평균 <b>O(1)</b>", table_cell_style),
            Paragraph("DJB2 다항 롤링 해시 함수로 충돌 최소화. 버킷마다 이중 연결 리스트로 체이닝. 로드 팩터 0.75 초과 시 버킷 2배 확장(Rehashing).", table_cell_style)
        ],
        [
            Paragraph("<b>DoublyLinkedList</b><br/>(이중 연결 리스트)", table_cell_style),
            Paragraph("Key의 '최근 사용 순서' (LRU 큐) 추적", table_cell_style),
            Paragraph("모든 연산 <b>O(1)</b>", table_cell_style),
            Paragraph("prev, next 노드 포인터 기반. 해시맵 값에 노드 주소를 저장하여 get/set 시 O(1)로 Head로 이동. 용량 초과 시 Tail 노드를 O(1)로 퇴출.", table_cell_style)
        ],
        [
            Paragraph("<b>MinHeap</b><br/>(최소 힙)", table_cell_style),
            Paragraph("Key의 '유효기간' (TTL 만료) 감시", table_cell_style),
            Paragraph("확인 <b>O(1)</b><br/>삭제 <b>O(log N)</b>", table_cell_style),
            Paragraph("완전 이진 트리를 1차원 배열로 구현. (expire_at, key) 튜플 저장. 루트에 가장 이른 만료 시간이 오므로 100만 개 전수조사 없이 O(1)에 만료 감시.", table_cell_style)
        ]
    ]
    t_ds = Table(ds_summary_data, colWidths=[95, 120, 65, 240])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F9EBEA")),
        ('BACKGROUND', (0,3), (-1,3), colors.white),
    ]))
    story.append(t_ds)
    story.append(Spacer(1, 10))

    # ---------------- 3. 메모리 및 LRU / TTL 라이프사이클 ----------------
    story.append(Paragraph("2. 메모리 관리 및 LRU / TTL 라이프사이클", h1_style))
    story.append(Paragraph(
        "<b>• 메모리 계산 공식:</b> used_memory = Σ( len(utf8(key)) + len(utf8(value)) ) (자료구조 오버헤드 제외)<br/>"
        "<b>• 단일 엔트리 OOM:</b> 단일 key+value 크기가 maxmemory를 초과하면 기존 데이터를 지우지 않고 즉시 OOM 에러 출력<br/>"
        "<b>• LRU 자동 퇴출 알고리즘:</b> maxmemory > 0이고 새 데이터 추가로 한도를 초과하면, 한도 이하가 될 때까지 DLL의 Tail에서 가장 오래된 키를 꺼내 해시맵/리스트/힙에서 동시 삭제 및 evicted_keys 누적<br/>"
        "<b>• SET 덮어쓰기 정합성:</b> 기존 키가 존재할 경우 메모리 차감/가산 반영 및 기존 TTL 즉시 무효화(삭제)<br/>"
        "<b>• TTL 만료 처리:</b> 모든 키 기반 명령 실행 전 expire_at 검사 (Lazy Deletion). 만료 시 즉시 삭제 후 (nil) 반환 및 LRU 갱신 방지",
        body_style
    ))
    story.append(Spacer(1, 8))

    # ---------------- 4. Redis 10대 기본 명령어 명세 ----------------
    story.append(Paragraph("3. 지원 명령어 명세 및 Redis 표준 규격", h1_style))
    cmd_table_data = [
        [Paragraph("명령어", table_header_style), Paragraph("구분", table_header_style), Paragraph("표준 반환 규격", table_header_style), Paragraph("시간 복잡도", table_header_style), Paragraph("동작 및 엣지 케이스 처리", table_header_style)],
        [Paragraph("SET k v", table_cell_style), Paragraph("String", table_cell_style), Paragraph("OK / (error) OOM", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("LRU Head 승격. 메모리 초과 시 LRU 방출. 덮어쓰기 시 기존 TTL 제거.", table_cell_style)],
        [Paragraph("GET k", table_cell_style), Paragraph("String", table_cell_style), Paragraph("\"value\" / (nil)", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("만료된 키는 삭제 후 (nil) 반환 (LRU 갱신 안 함). 유효 시 LRU Head 승격.", table_cell_style)],
        [Paragraph("DEL k", table_cell_style), Paragraph("String", table_cell_style), Paragraph("(integer) 1 또는 0", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("해시맵, LRU 리스트, TTL 힙 모두에서 동시 제거 및 used_memory 차감.", table_cell_style)],
        [Paragraph("EXISTS k", table_cell_style), Paragraph("String", table_cell_style), Paragraph("(integer) 1 또는 0", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("실행 전 만료 여부 먼저 검사하여 만료 시 삭제 후 0 반환.", table_cell_style)],
        [Paragraph("DBSIZE", table_cell_style), Paragraph("String", table_cell_style), Paragraph("(integer) N", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("현재 유효한 활성 키 개수 반환.", table_cell_style)],
        [Paragraph("KEYS", table_cell_style), Paragraph("String", table_cell_style), Paragraph("1. \"k\" ... / (empty array)", table_cell_style), Paragraph("O(N)", table_cell_style), Paragraph("현재 존재하는 모든 유효 키 목록 배열 출력.", table_cell_style)],
        [Paragraph("CONFIG SET", table_cell_style), Paragraph("Memory", table_cell_style), Paragraph("OK / (error)", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("maxmemory 바이트 설정 (0=무제한). 잘못된 값 입력 시 에러 반환.", table_cell_style)],
        [Paragraph("INFO memory", table_cell_style), Paragraph("Memory", table_cell_style), Paragraph("포맷 텍스트", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("used_memory, maxmemory, evicted_keys 통계 출력.", table_cell_style)],
        [Paragraph("EXPIRE k s", table_cell_style), Paragraph("TTL", table_cell_style), Paragraph("(integer) 1 또는 0", table_cell_style), Paragraph("O(log N)", table_cell_style), Paragraph("초 단위 만료 등록. 없는 키는 0. 0 이하 초 입력 시 즉시 삭제 후 1 반환.", table_cell_style)],
        [Paragraph("TTL k", table_cell_style), Paragraph("TTL", table_cell_style), Paragraph("(integer) N / -1 / -2", table_cell_style), Paragraph("O(1)", table_cell_style), Paragraph("없는 키 -2, 만료 없는 키 -1, 만료 예정 키는 남은 초 정수 반환.", table_cell_style)]
    ]
    t_cmd = Table(cmd_table_data, colWidths=[70, 45, 105, 55, 245])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_cmd)

    story.append(PageBreak())

    # ---------------- 5. 실제 실행 및 검증 로그 ----------------
    story.append(Paragraph("4. 과제 요구사항 8번 결과 예시 100% 일치 검증 로그", h1_style))
    story.append(Paragraph("터미널에서 <code>python3 demo.py</code> 또는 <code>python3 main.py</code> 실행 시 출력되는 실제 실행 결과입니다:", body_style))

    demo_log = """mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
# maxmemory(30) 초과로 LRU(user:1) 제거 확인
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
(integer) 2
# (3초 경과 후)
mini-redis> GET user:2
(nil)
mini-redis> TTL user:2
(integer) -2

mini-redis> CONFIG SET maxmemory abc
(error) ERR value is not an integer or out of range
mini-redis> GET
(error) ERR wrong number of arguments for 'GET' command
mini-redis> HELLO
(error) ERR unknown command 'HELLO'"""

    t_code = Table([[Preformatted(demo_log, code_pre_style)]], colWidths=[520])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_code)
    story.append(Spacer(1, 10))

    # ---------------- 6. 단위 테스트 통과 결과 ----------------
    story.append(Paragraph("5. 단위 테스트 결과 (34개 테스트 100% 통과)", h1_style))
    test_log = """kangsikseo@KANGSIKs-MacBook-Pro miniredis % python3 -m unittest discover -s tests
..................................
----------------------------------------------------------------------
Ran 34 tests in 0.002s

OK"""
    t_test = Table([[Preformatted(test_log, code_pre_style)]], colWidths=[520])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#E8F8F5")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#A3E4D7")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 10))

    # ---------------- 7. 보너스 과제 완주 내역 ----------------
    story.append(Paragraph("6. 보너스 과제 완주 내역 (선택 과제 5종 전체 구현)", h1_style))
    story.append(Paragraph(
        "1. <b>동적 배열 직접 구현 (DynamicArray):</b> append, get, set, remove 구현 및 용량 초과 시 2배 자동 확장<br/>"
        "2. <b>스택/큐/덱 조사 문서화:</b> <code>STACK_QUEUE_DEQUE.md</code> 작성 (빅오 복잡도, 원리 및 활용 비교)<br/>"
        "3. <b>이진 트리 4대 순회:</b> <code>BinaryTree</code> 전위, 중위, 후위, 레벨 순회(BFS 큐) 구현<br/>"
        "4. <b>이진 탐색 트리 (BST):</b> <code>BinarySearchTree</code> O(log N) 삽입, 탐색 및 중위 순회 오름차순 정렬<br/>"
        "5. <b>Pub/Sub 기능:</b> <code>PubSubBroker</code> 발행/구독 패턴 및 채널별 메시지 큐 구현",
        body_style
    ))
    story.append(Spacer(1, 12))

    # ---------------- 8. 결론 및 깃허브 링크 ----------------
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))
    story.append(Paragraph("<b>✅ 결론 및 깃허브 저장소 확인:</b>", h2_style))
    story.append(Paragraph(
        "본 프로젝트의 모든 소스코드, 34개 단위 테스트, 상세 README 및 자동 데모 스크립트는 "
        "공식 GitHub 저장소에 안전하게 커밋 및 푸시되어 있습니다.<br/>"
        "👉 <b>GitHub Repository:</b> <font color='#2980B9'>https://github.com/KANGSIK-SEO/miniredis</font>",
        body_style
    ))

    doc.build(story)
    print(f"✅ PDF 생성 완료: {filename}")

if __name__ == "__main__":
    create_pdf(DEST_LOCAL)
    shutil.copyfile(DEST_LOCAL, DEST_DOWNLOADS)
    print(f"✅ Downloads 폴더로 복사 완료: {DEST_DOWNLOADS}")
