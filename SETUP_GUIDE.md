# 설치 가이드

Excel 고객 상담 데이터를 Agent SOP 문서 + 플로우차트로 자동 변환하는 AI 파이프라인 설치 가이드입니다.

---

## 사전 준비

1. **Claude Code 설치** — https://claude.ai/code
2. **Upstage API 키 발급** — DM 주시면 전달드리겠습니다!

---

## 설치 방법

### 방법 1. 터미널에서 직접 설치

```bash
# 1. 설치 스크립트 실행 (Python 가상환경 + 패키지 자동 설치)
chmod +x setup.sh
./setup.sh

# 2. API 키 입력
# .env 파일에 UPSTAGE_API_KEY 입력
```

### 방법 2. Claude Code에게 설치 요청 (터미널 없이)

1. 이 폴더를 Claude Code로 열기
2. 채팅창에 아래 메시지를 그대로 붙여넣기:

```
setup.sh 파일을 보고 환경 설정을 해줘. 그리고 .env.example 파일을 복사해서 .env 파일을 만들고, UPSTAGE_API_KEY 값을 알려줘서 내가 직접 입력할 수 있게 안내해줘.
```

3. Claude Code가 자동으로 설치를 진행하고, API 키 입력 위치를 안내해줍니다.

---

## 실행 방법

`data/` 폴더에 고객 상담 Excel 파일을 넣고, 해당 폴더를 Claude Code로 연 뒤 명령어 실행:

```
/userchat-to-sop-pipeline    # SOP 문서 + 플로우차트 생성 (약 15~30분)
```

단계별로 실행하려면:

```
/stage1-clustering              # 클러스터링
/stage2-extraction              # 패턴 추출
/stage3-sop-generation          # SOP 문서 생성
/stage4-flowchart-generation    # 플로우차트 생성
/stage5-sop-to-guide            # ALF 구축 패키지 생성
```

---

## 문제 해결

### "pip3: command not found"

```bash
python3 -m ensurepip --upgrade
```

### "Permission denied" 또는 "Externally managed environment"

```bash
# 가상환경 사용 (권장)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "ImportError: No module named 'pandas'"

```bash
pip3 install pandas numpy scikit-learn openpyxl openai tqdm --user
```

### 그 외 에러

에러 메시지를 Claude Code에 붙여넣으면 자동으로 해결책을 제시합니다.

---

## 분석 방법론

### Phase 분류 기준

파이프라인은 고객 상담을 **7가지 대화유형**으로 먼저 분류한 뒤, 대화유형에 따라 Phase를 결정합니다.

#### 대화유형 → Phase 매핑

| 대화유형 | 정의 | Phase | ALF 처리 방법 |
|---------|------|-------|-------------|
| 1.지식응답 | FAQ, 사용법, 일반 정보 질문 | **Phase 1** | RAG (지식 DB 검색) |
| 4.정책확인 | "이거 가능한가요?" 류 조건부 질문 | **Phase 1** | RAG + 분기 로직 |
| 2.정보조회 | 주문·배송·결제 등 개인 데이터 조회 | **Phase 2** | Task — 조회 API |
| 3.단순실행 | 취소·환불·재발송 등 직접 처리 요청 | **Phase 2** | Task — 실행 API |
| 5.조건부실행 | 정책 확인 + 처리 실행 복합 | **Phase 3** | RAG + Task 복합 |
| 6.의도불명확 | 맥락 부족, 단문 | 비자동화 | 명확화 질문 후 재분류 |
| 7.상담사전환 | 감정적 불만, 법적 이슈 | 비자동화 | 즉시 상담사 연결 |

- **Phase 1** (즉시 배포): 개발 불필요, 규칙+RAG만으로 2~3주 내 적용
- **Phase 2** (API 연동): Task API 개발 필요, 2~4개월
- **Phase 3** (장기 과제): RAG+Task 복합 워크플로우, Phase 2 완료 후 진행

#### 자주 묻는 엣지 케이스

| 케이스 | 분류 기준 |
|--------|---------|
| **단순 안내 + 일부 확인 필요** | 확인 내용이 지식 DB로 해결 가능하면 `1.지식응답`(Phase 1), 외부 시스템 조회가 필요하면 `2.정보조회`(Phase 2) |
| **"확인 후 안내드리겠습니다"** | 무조건 Phase 2가 아님. 상담사가 내부 시스템을 직접 조회해야 하는 경우만 `2.정보조회`(Phase 2). 정책·규정 확인이면 `4.정책확인`(Phase 1) |
| **복합 문의 (2개 이상 질문)** | 각 질문의 유형 중 가장 높은 Phase로 분류. 예: 지식응답+정보조회 → `2.정보조회`(Phase 2). 정책확인+단순실행 → `5.조건부실행`(Phase 3) |
| **고객 재질문 / 표현 변화** | 최초 의도 기준으로 분류. 고객이 같은 내용을 다르게 표현해도 유형 변경 없음 |

### 자동화 가능 비율 산정 방식

자동화 비율은 단일 수치가 아닌, **2단계 계산**으로 산출됩니다.

#### Step 1: 의도 상한선 (Intent Ceiling)

대화유형 분포만으로 계산한 이론적 최대치입니다.

```
의도 상한선 = (Phase 1 건수 + Phase 2 건수 + Phase 3 건수) / 전체 건수 × 100%
```

예시: 1000건 중 지식응답 300 + 정책확인 100 + 정보조회 200 + 단순실행 150 + 조건부실행 50 = 800건 → 의도 상한선 80%

#### Step 2: 실질 자동화율 (Actual Automation Rate)

의도 상한선에서 **해결 복잡도**를 반영하여 하향 조정합니다.

```
실질 자동화율 = 의도 상한선 - 복잡도 패널티
```

복잡도 패널티 요인:
- Stage 2 `response_strategies.json`의 `decision_flow` 단계 수 (많을수록 하향)
- `automation_opportunity` 레벨 (low → 큰 패널티)
- **중간 상담사 개입 필요 시**: 해당 경로 전체를 자동화 불가(0%)로 처리

#### 부분 자동화 처리 기준

| 상황 | 처리 방식 |
|------|---------|
| ALF가 전체 흐름을 완결 | **완전 자동화** (해결율에 포함) |
| ALF가 시작하고 상담사가 마무리 | **부분 자동화** (관여율에만 포함, 해결율 미포함) |
| 상담 중간에 상담사 개입 필요 | 해당 경로 **전체 비자동화** 처리 (보수적 기준) |

> 보수적 기준 적용 이유: 중간 개입 시 ALF↔상담사 간 컨텍스트 전달 손실이 발생하여, 실제 운영에서는 처음부터 상담사가 처리하는 것이 효율적이기 때문입니다.

### 상담 흐름 분석 범위

| 분석 요소 | 반영 여부 | 설명 |
|----------|---------|------|
| 대화 텍스트 내용 | ✅ 반영 | LLM이 실제 대화를 읽고 유형 분류 |
| 상담 턴 수 (왕복 횟수) | ✅ 반영 | `decision_flow` 단계 수로 복잡도 측정 |
| 응답 시간 / 지연 여부 | ❌ 미반영 | 현재 타임스탬프 기반 분석 미포함 |
| 상담사 개입 횟수 | ⚠️ 간접 반영 | 직접 카운트하지 않으나, 중간 개입 경로는 자동화 불가 처리 |
| 고객 감정 / 표현 변동성 | ❌ 미반영 | 정적 텍스트 분석 기반, 실시간 감정 변화 미추적 |
| 고객사 내부 승인 정책 | ❌ 미반영 | 상담 데이터에 포함되지 않는 내부 프로세스 |

> **참고**: 응답 시간·감정 변동성·내부 승인 정책은 실제 운영 단계에서 모니터링하여 Phase별 해결율을 조정하는 것을 권장합니다.

---

## Stage 4 플로우차트 SVG 생성 (선택)

Mermaid CLI가 없어도 마크다운 파일은 생성됩니다. SVG 이미지가 필요한 경우에만 설치하세요.

```bash
# Node.js 설치 확인
node --version

# Mermaid CLI 설치
npm install -g @mermaid-js/mermaid-cli

# SVG 변환
mmdc -i FLOWCHART.md -o flowchart.svg -b transparent
```
