---
name: evaluate-rag
description: Channel.io 봇의 RAG 응답 품질을 Playwright로 자동 테스트합니다.
args: "<channel-url> <company-or-questions-path> [count]"
args_description: |
  channel-url: 테스트 대상 Channel.io URL (예: qd713.channel.io, qd5l9.channel.io)
  company-or-questions-path: 회사명(kamoa, kmong 등) 또는 질문 JSON 파일 경로
    - 회사명 입력 시: data/{company}/test-questions.json 자동 탐색, 없으면 FAQ에서 생성
    - 파일 경로 입력 시: 해당 파일을 직접 사용 (예: ./my-questions.json)
  count (선택): 테스트할 질문 수 제한. 미지정 시 전체 실행
---

# RAG 응답 품질 평가

## 사용법

```
/evaluate-rag <channel-url> <company-or-questions-path> [count]
```

예시:
- `/evaluate-rag qd5l9.channel.io kmong` — 크몽 전체 FAQ 테스트
- `/evaluate-rag qd713.channel.io kamoa 10` — 카모아 10개만 테스트
- `/evaluate-rag qd713.channel.io ./data/kamoa/test-questions.json` — 질문 파일 직접 지정

## 작업 순서

### 1. 인자 파싱

두 번째 인자가 `.json`으로 끝나거나 `/`를 포함하면 → 질문 파일 경로로 처리.
그 외 → 회사명으로 처리.

URL이나 두 번째 인자가 없으면 물어본다:
- "테스트할 Channel.io URL을 알려주세요 (예: qd713.channel.io)"
- "회사명 또는 질문 파일 경로를 알려주세요 (예: kamoa, ./questions.json)"

### 2. 질문 파일 확인

**경로 직접 지정 시**: 해당 파일을 그대로 사용.

**회사명 지정 시**: `data/{company}/test-questions.json` 존재 여부 확인.
- **있으면**: 바로 3단계 진행.
- **없으면**: FAQ에서 자동 생성:
  1. `/Users/pete/Documents/sop-agent/results/{company}/02_extraction/faq.json` 읽기
  2. 질문+평가 기준(keywords, conditions, follow_up_info) 생성
  3. `data/{company}/test-questions.json`에 저장

**count 지정 시**: 질문 파일에서 상위 N개만 선별하여 임시 파일 생성 후 사용.

질문 생성 시 평가 기준:
- **keywords**: FAQ answer에서 핵심 키워드 추출, variants(동의어) 포함
- **conditions**: 답변에 조건 분기가 있으면 check_phrases로 검증
- **follow_up_info**: TS_ 토픽(문제해결형)은 `should_ask: true` (정보 수집 필요)
- **scoring weights**: keyword 0.4, condition 0.35, followup 0.25

### 3. 테스트 실행

```bash
node data/rag-tester.js --url {channel-url} --questions {questions-path}
```

- Playwright headless:false로 실행 (브라우저 표시)
- 질문별 새 채팅 생성 → 응답 수집 → 평가
- 결과 JSON: 질문 파일과 같은 디렉토리에 `test-rag-results.json`
- HTML 리포트: 같은 디렉토리에 `test-rag-report.html`

### 4. 결과 요약

테스트 완료 후:
1. HTML 리포트를 `open` 명령으로 브라우저에서 연다.
2. 결과를 간단히 요약한다:
   - 종합 점수, PASS/PARTIAL/FAIL 수
   - FAIL 항목별 원인 (RAG 미등록, 키워드 누락, 조건부 미충족 등)

### 5. 평가 규칙

- **정보수집 질문** (follow_up_info.should_ask=true): 봇이 추가 정보를 요청하면 → 자동 PASS
- **일반 안내 질문**: 키워드(40%) + 조건부(35%) + 후속질문(25%) 가중 평균
- 등급: PASS ≥ 85%, PARTIAL ≥ 60%, FAIL < 60%

## 파일 구조

```
data/
├── rag-tester.js              # 범용 테스트 러너
├── kmong/
│   ├── test-questions.json    # 크몽 질문 (25개)
│   ├── test-rag-results.json  # 결과
│   └── test-rag-report.html   # 리포트
├── kamoa/
│   ├── test-questions.json    # 카모아 질문 (46개)
│   ├── test-rag-results.json
│   └── test-rag-report.html
└── {company}/                 # 새 회사 추가 시 자동 생성
```

## FAQ 소스 경로

회사별 FAQ 데이터:
```
/Users/pete/Documents/sop-agent/results/{company}/02_extraction/faq.json
```

지원 구조:
- `{ "faq_pairs": [...] }` — kmong 형식 (faq_id, question, answer, keywords, frequency)
- `{ "faq_by_topic": { "TOPIC": [{ "q": "...", "a": "..." }] } }` — kamoa 형식
