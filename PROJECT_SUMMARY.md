# SOP Agent 프로젝트 요약

**최종 업데이트**: 2026-02-06

---

## 요약

**분석 보고서만 쓰던 에이전트가 이제 실제 사용 가능한 SOP + 플로우차트까지 자동 생성합니다.**

기존 EDA 에이전트의 소요시간, 상호작용, 일관성 문제를 해결하고, **SOP 자동 생성 + 플로우차트 시각화** 기능을 추가했습니다.

---

## 기존 문제 (EDA 에이전트)

**분석 보고서만 생성:**
- 소요 시간: 30분 ~ 2시간 (CSM 팀 사용 기준)
- 사용자 상호작용: 매번 검증 필요
- 일관성: 낮음 (추측 기반)
- **실사용 불가**: SOP 문서 별도 작성 필요

---

## 주요 의사결정

### 1. 추측 금지 → 실제 샘플 필수
클러스터 라벨만 보고 추측 ❌
→ **20개 실제 샘플을 LLM이 직접 읽고 분석** ✅

### 2. 기계적 분류 → LLM 맥락 판단
pattern_type 개수로 계산 ❌
→ **LLM이 실제 샘플 보고 맥락 파악** ✅

### 3. 요약본만 → 실제 대화 활용
요약본만 사용 ❌
→ **Stage 1에서 실제 대화 턴 CSV 저장** (+10초) ✅

### 4. 텍스트만 → 시각화 추가 ⭐ NEW!
SOP 텍스트 문서만 ❌
→ **Mermaid 플로우차트 + SVG 이미지** ✅
(이유: 신입 교육, 프로세스 검토, 의사결정 트리 시각화)

### 5. 외래어 → 로컬라이제이션 ⭐ NEW!
"에스컬레이션" (외래어) ❌
→ **"담당팀 전달"** (직관적 한국어) ✅
(이유: 고객 서비스 실무자 이해도 향상)

---

## 구현된 내용

### Stage 1: 클러스터링 ✅ 완료
**구현 날짜**: 2026-02-01

- k-means 기반 자동 클러스터링
- **Message CSV 저장 기능 추가** (output.py, pipeline.py 수정)
- Upstage Solar 임베딩 + LLM 태깅
- 실행 시간: ~ 3분 (+10초)

**출력**:
- `{company}_clustered.xlsx` - 클러스터 할당 데이터
- `{company}_tags.xlsx` - 클러스터 요약
- `{company}_messages.csv` - 실제 대화 턴
- `analysis_report.md` - 분석 리포트

### Stage 2: 패턴 추출 + HT/TS 분류 ✅ 완료
**구현 날짜**: 2026-02-04

- **실제 샘플 20개 기반 LLM 분석** (추측 금지)
- **HT/TS 분류 자동화** (LLM 맥락 판단)
- Task agent 처리로 **5분 완료** (예상 5 - 10분)
- 실제 고객 표현 샘플 추출

**출력**:
- `patterns.json` - 56개 패턴 + HT/TS 분류
- `faq.json` - 39개 FAQ 쌍
- `response_strategies.json` - 응답 전략
- `keywords.json` - 키워드 분류체계
- `extraction_summary.md` - 추출 요약

### Stage 3: SOP 문서 생성 ✅ 완료

**구현 날짜**: 2026-02-05

- **HT/TS 템플릿 기반 자동 생성**
- 실제 고객 표현, 응답 예시 포함
- RFC 2119 키워드 사용 (MUST/SHOULD/MAY)
- 톤앤매너, 담당팀 전달 기준 포함

**출력 (회사별)**:
- **Assacom**: 7개 SOP (TS: 4개, HT: 3개) - 1,000건 중 645건 커버 (64.5%)
- **Usimsa**: 7개 SOP (TS: 2개, HT: 5개) - 985건 분석
- **Meliens**: 8개 SOP (TS: 4개, HT: 4개) - 1,000건 분석
- `metadata.json` - SOP 메타데이터
- `generation_summary.md` - 생성 요약

**총 22개 프로덕션 SOP 생성** 🎉

### Stage 4: 플로우차트 생성 ✅ 완료 ⭐ NEW!

**구현 날짜**: 2026-02-05

- **Mermaid 플로우차트 자동 생성**
- **SVG 이미지 변환** (mmdc CLI)
- 5가지 색상 코딩 (성공/주의/담당팀전달/의사결정/정보확인)
- 케이스별 설명, 체크포인트 테이블 포함

**출력**:
- **Assacom**: 1개 플로우차트 (TS_001)
- **Usimsa**: 2개 플로우차트 (TS_001, TS_002)
- **Meliens**: 3개 플로우차트 (TS_001, TS_002, TS_004)
- 각 플로우차트: Markdown + SVG (100-200KB)


### 템플릿 시스템
**SOP 템플릿**:
- `templates/HT_template.md` - How-To 타입
- `templates/TS_template.md` - Troubleshooting 타입

**플로우차트 템플릿**:
- `templates/FLOWCHART_template.md` - 플로우차트 표준 구조
- 변수 가이드, 색상 코딩 규칙, Mermaid 작성법 포함

### Claude Skills 통합

**실행 가능한 스킬**:
1. `/stage1-clustering` - Python 클러스터링 실행
2. `/stage2-extraction` - LLM 패턴 추출
3. `/stage3-sop-generation` - SOP 문서 생성
4. `/stage4-flowchart-generation` - 플로우차트 생성 ⭐ NEW!
5. `/userchat-to-sop-pipeline` - 전체 파이프라인 오케스트레이션

**스킬 위치**:
- `agent-sops/*.sop.md` - 원본 SOP (Agent SOP 표준 준수)
- `.claude/skills/*/SKILL.md` - Claude Code 실행용 (YAML frontmatter 추가)

### 데이터 흐름
```
Excel (11MB) - 원본 고객 상담 데이터
  ↓ Stage 1 (3분)
clustered.xlsx (3MB) + tags.xlsx (50KB) + messages.csv (2MB)
  ↓ Stage 2 (5-10분)
patterns.json (56개) + faq.json (39개) + strategies.json + keywords.json
  ↓ Stage 3 (5-10분)
22개 SOP 문서 (.sop.md) + metadata.json
  ↓ Stage 4 (3분)
6개 플로우차트 (Markdown + SVG)
```

**총 소요 시간**: 15-20분 (Stage 1-4 포함)

---

## 결과 비교

### 개선 전 (EDA 에이전트)

| 항목 | 값 |
|------|-----|
| 산출물 | 분석 보고서 (텍스트) |
| 소요 시간 | 30분 ~ 2시간 |
| 일관성 | 낮음 |
| 실사용 | 불가 (추가 작업 필요) |
| 시각화 | 없음 |

### 개선 후 (SOP 생성 파이프라인)

| 항목 | 값 |
|------|-----|
| 산출물 | **SOP 문서 + 플로우차트** ✅ |
| 소요 시간 | **15-20분** (자동화) |
| 일관성 | **높음** (템플릿 기반) |
| 실사용 | **즉시 가능** ✅ |
| 시각화 | **Mermaid 플로우차트 + SVG** ✅ |

### ⇒ 시간 단축, 실사용 가능한 SOP 생성, pipeline 자동화

---

## 산출물 현황 (2026-02-04)

### 1. Assacom (PC 조립/판매)
**Stage 1-3 완료**:
- 클러스터: 20개 (1,000건 샘플링 분석)
- SOP: 7개 (645건 커버, 64.5%)
  - TS_001: AS접수 및 하드웨어 진단 (81건)
  - TS_002: 윈도우/소프트웨어 문제해결 (65건)
  - TS_003: 주문 취소/교환/반품 (51건)
  - TS_004: 컴퓨터 부품 문제진단 (51건)
  - HT_001: 배송 조회 및 방법 변경 (124건)
  - HT_002: 견적 상담 및 구매 안내 (144건)
  - HT_003: AS 진행상황 안내 (129건)

**Stage 4 완료** ⭐:
- 플로우차트: 1개 (TS_001)
- SVG: 167KB

### 2. Usimsa (eSIM 여행 통신)

**Stage 1-3 완료**:
- 클러스터: 20개 (985건 분석)
- SOP: 7개
  - TS_001: 이심 데이터 연결 문제해결 (258건, 26.2%)
  - TS_002: 취소 및 환불 처리 (59건, 6.0%)
  - HT_001: 이심 구매 및 설정 안내
  - HT_002: 사용량 조회 및 충전 안내
  - HT_003: 유심 등록 양도 정책 안내
  - HT_004: 이벤트 및 서비스 안내
  - HT_005: 결제 및 제휴 문의 안내

**Stage 4 완료** ⭐:
- 플로우차트: 2개 (TS_001, TS_002)
- SVG: 174KB, 180KB

### 3. Meliens (링홀더/생활용품)

**Stage 1-3 완료**:
- 클러스터: 20개 (1,000건 분석)
- SOP: 8개
  - TS_001: 교환/반품 처리 (125건, 12.5%)
  - TS_002: AS 접수 및 처리 (141건, 14.1%)
  - TS_003: 주문 취소/반품 처리
  - TS_004: 할인/쿠폰 문제 해결 (103건, 10.3%)
  - HT_001: 배송 및 출고 안내
  - HT_002: 링홀더 제품 안내
  - HT_003: 충전기/어댑터 안내
  - HT_004: 보풀제거기/클렌저 안내

**Stage 4 완료** ⭐:
- 플로우차트: 3개 (TS_001, TS_002, TS_004)
- SVG: 171KB, 148KB, 200KB

---

## 전체 산출물

| 항목 | 수량 |
|------|------|
| **처리 회사** | 3개 (Assacom, Usimsa, Meliens) |
| **분석 상담 건수** | 2,985건 (Assacom 1,000 + Usimsa 985 + Meliens 1,000) |
| **생성 클러스터** | 60개 (회사당 20개) |
| **생성 SOP** | **22개** (TS: 10개, HT: 12개) |
| **생성 플로우차트** | **6개** (Markdown + SVG) ⭐ |
| **총 파일** | 100+ (Excel, JSON, MD, SVG) |

---

## 기술 스택

### Python (Stage 1)
- **임베딩**: Upstage Solar (`embedding-passage`, 4096차원)
- **클러스터링**: scikit-learn K-Means
- **LLM 태깅**: Upstage Solar Mini
- **병렬 처리**: ThreadPoolExecutor (max_workers=3)
- **캐싱**: pickle 기반 임베딩 캐시

### LLM (Stage 2-4)
- **모델**: Claude Sonnet 4.5 (1M context)
- **작업**:
  - Stage 2: 패턴 추출, FAQ 생성, HT/TS 분류
  - Stage 3: SOP 문서 작성
  - Stage 4: Mermaid 플로우차트 생성

### Visualization (Stage 4)
- **다이어그램**: Mermaid.js
- **변환**: @mermaid-js/mermaid-cli (mmdc)
- **출력**: SVG (투명 배경, 100-200KB)
- **색상**: 5가지 코딩 (성공/주의/담당팀전달/의사결정/정보확인)

### Templates
- **SOP**: HT_template.md, TS_template.md
- **Flowchart**: FLOWCHART_template.md
- **표준**: Agent SOP Specification 준수

---

## Claude Skills 시스템

### 개별 스테이지 스킬

| 스킬 | 기능 | 소요 시간 |
|------|------|----------|
| `/stage1-clustering` | Python 클러스터링 실행 | 3분 |
| `/stage2-extraction` | LLM 패턴 추출 | 5-10분 |
| `/stage3-sop-generation` | SOP 문서 생성 | 5-10분 |
| `/stage4-flowchart-generation` | 플로우차트 생성 ⭐ | 3분 |

### 통합 파이프라인 스킬

**`/userchat-to-sop-pipeline`**:
- 전체 Stage 1-4 자동 실행
- 단계별 검증 및 리뷰
- 최종 산출물: SOP + 플로우차트

---

## 파일 구조

```
sop-agent/
├── data/
│   └── raw data_{company}.xlsx          # 원본 데이터
├── scripts/
│   ├── pipeline.py                       # Stage 1 진입점
│   └── clustering/                       # 클러스터링 모듈
├── templates/
│   ├── HT_template.md                    # How-To SOP 템플릿
│   ├── TS_template.md                    # Troubleshooting SOP 템플릿
│   └── FLOWCHART_template.md             # 플로우차트 템플릿 
├── agent-sops/                           # claude skill 원본
│   ├── stage1-clustering.sop.md
│   ├── stage2-extraction.sop.md
│   ├── stage3-sop-generation.sop.md
│   ├── stage4-flowchart-generation.sop.md 
│   └── userchat-to-sop-pipeline.sop.md
├── .claude/
│   ├── settings.json                     # 권한 설정
│   └── skills/
│       ├── stage1-clustering/
│       ├── stage2-extraction/
│       ├── stage3-sop-generation/
│       ├── stage4-flowchart-generation/
│       └── userchat-to-sop-pipeline/
└── results/{company}/
    ├── 01_clustering/
    │   ├── {company}_clustered.xlsx
    │   ├── {company}_tags.xlsx
    │   ├── {company}_messages.csv        
    │   └── analysis_report.md
    ├── 02_extraction/
    │   ├── patterns.json
    │   ├── faq.json
    │   ├── response_strategies.json
    │   ├── keywords.json
    │   └── extraction_summary.md
    └── 03_sop/
        ├── TS_001_*.sop.md
        ├── TS_001_*_FLOWCHART.md         
        ├── TS_001_flowchart-1.svg       
        ├── HT_001_*.sop.md
        ├── metadata.json
        └── generation_summary.md
```

---

## 핵심 성과

### 시간 효율
- **EDA**: 30-120분 → **SOP 생성**: 15-20분
- **즉시 사용 가능한 SOP** 산출 ✅

### 품질 향상
- 일관성 낮음 → **템플릿 기반 일관성**
- 분석 보고서 → **상담 SOP** ⭐

### 확장성
- 수동 작업 → **스킬 기반 자동화**
- 재실행 어려움 → **즉시 재실행 가능**

---

## 프로젝트 상태

| Stage | 상태 | 산출물 |
|-------|------|--------|
| **Stage 1** | ✅ 완료 | 60개 클러스터, 11,985건 분석 |
| **Stage 2** | ✅ 완료 | 패턴, FAQ, 전략, 키워드 |
| **Stage 3** | ✅ 완료 | 22개 SOP 문서 |
| **Stage 4** | ✅ 완료 | 6개 플로우차트 ⭐ |
| **통합** | ✅ 완료 | 4단계 파이프라인 |

**진행률**: **100%** (모든 코어 스테이지 완료)

---

**최종 업데이트**: 2026-02-06
**버전**: v1.0 (Production Ready)
**제작자**: 🐱 Pete
