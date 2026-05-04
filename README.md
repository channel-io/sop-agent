# Userchat-to-SOP Pipeline

Excel 고객 상담 데이터를 Agent SOP 문서 및 ALF 구축 패키지로 자동 변환하는 7단계 AI 파이프라인

## 프로젝트 개요

- **목적**: Excel 고객 상담 데이터 → 재사용 가능한 Agent SOP 문서 + ALF(AI 챗봇) 도입 패키지 + 고객사 공유용 배포 시나리오 자동 생성
- **방법**: 7단계 파이프라인 (Clustering → Extraction → SOP Generation → Flowchart Generation → ALF 구축 패키지 → ALF 문서 분리 → 배포 시나리오)
- **소요 시간**: Stage 1-4 Quick ~15분 / Standard ~25분 / Comprehensive ~30분, Stage 5 ~20-35분, Stage 6-7 ~10분
- **다국어 지원**: 한국어 (한국어), 일본어 (日本語)
- **기술 스택**:
  - **Stage 1 (Python)**: 로컬 BGE-m3-ko 임베딩(기본) + Upstage Solar fallback / K-Means 클러스터링 / Prism Gateway Claude 태깅(기본) + Upstage Solar-mini fallback
  - **Stage 2 (LLM)**: 패턴 추출 + FAQ 생성 + HT/TS 분류
  - **Stage 3 (LLM)**: Agent SOP 문서 생성 (병렬 처리 가능)
  - **Stage 4 (LLM + Mermaid)**: 플로우차트 자동 생성 (필수, SVG 선택)
  - **Stage 5 (LLM + Python)**: ALF 구축 패키지 — 규칙 초안(페르소나·말투·응대 가이드라인·공감 매핑), RAG 항목, 자동화 분석(4-Layer ALF 관여 모델), 앱함수 연동 분류(이지어드민/카페24/사방넷), ROI 계산, API 요건 정의서
  - **Stage 6 (LLM)**: ALF 등록용 개별 파일 분리 (규칙 9개 + RAG 토픽별 문서)
  - **Stage 7 (LLM)**: 고객사 공유용 배포 시나리오 & QA 세트 (HTML/Markdown, Notion 발행 선택)

## 빠른 시작

### 1. 사전 준비

- **Claude Code** — https://claude.ai/code
- **Upstage API 키** 또는 **Anthropic API 키**

### 2. 설치

#### 방법 1. 스크립트로 설치 (권장)

```bash
chmod +x setup.sh
./setup.sh
```

#### 방법 2. 수동 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 UPSTAGE_API_KEY 또는 ANTHROPIC_API_KEY 추가
```

#### 방법 3. Claude Code에게 설치 요청

이 폴더를 Claude Code로 열고 아래 메시지를 입력:

```
setup.sh 파일을 보고 환경 설정을 해줘. .env.example을 복사해서 .env 파일을 만들고, API 키 입력 위치를 안내해줘.
```

> **일본어 가이드**: [SETUP_GUIDE_JA.md](SETUP_GUIDE_JA.md) 참조

### 3. 파이프라인 실행

#### 통합 파이프라인 (권장)

```
/userchat-to-sop-pipeline
```

- 한 번에 Stage 1-7 자동 실행
- 각 단계별 리뷰 지점 제공
- Stage 간 자동 연결 및 검증

#### 개별 실행 (단계별 제어 필요 시)

```
/stage1-clustering              # Stage 1: 클러스터링
/stage2-extraction              # Stage 2: 패턴 추출
/stage3-sop-generation          # Stage 3: SOP 생성
/stage4-flowchart-generation    # Stage 4: 플로우차트 생성
/stage5-sop-to-guide            # Stage 5: ALF 구축 패키지 생성
/stage6-alf-document-export     # Stage 6: ALF 문서 개별 파일 분리
/stage7-deployment-scenario     # Stage 7: 배포 시나리오 & QA 세트
```

#### ALF 운영 보조 스킬

```
/upload-rules                   # 규칙 Markdown 일괄 업로드 (Channel.io)
/upload-documents               # RAG 문서 일괄 업로드 (Channel.io Desk API)
/settings-task                  # Task JSON 채널톡 업로드(생성/수정)
/evaluate-rag                   # 봇의 RAG 응답 품질 자동 테스트 (Playwright)
/evaluate-task                  # Task JSON 품질 평가
/analyze-bots                   # Non-ALF 봇 행동 분석 (커버리지/에스컬레이션)
```

#### CLI 직접 실행 (Stage 1)

```bash
# 기본 실행 (1000개 샘플)
python3 scripts/pipeline.py --input data/user_chat.xlsx

# 전체 데이터 실행
python3 scripts/pipeline.py --input data/user_chat.xlsx --sample all

# K 값 지정
python3 scripts/pipeline.py --input data/user_chat.xlsx --k 20

# 최적 K 탐색
python3 scripts/pipeline.py --input data/user_chat.xlsx --k-range 10,15,20,25

# 태깅 건너뛰기 (수동 태깅용)
python3 scripts/pipeline.py --input data/user_chat.xlsx --skip-tagging

# 출력 경로 지정
python3 scripts/pipeline.py --input data/input.xlsx --output results/company --prefix company_v1
```

### 4. SVG 이미지 생성 (선택)

Mermaid CLI 없이도 마크다운 플로우차트는 생성됩니다. SVG가 필요한 경우:

```bash
npm install -g @mermaid-js/mermaid-cli
```

### 5. 결과 확인

```
results/{company}/
├── {company}_clustered.xlsx              # Stage 1: 원본 데이터 + 클러스터 정보
├── {company}_tags.xlsx                   # Stage 1: 클러스터 메타데이터
├── {company}_messages.csv                # Stage 1: 실제 대화 턴 (Stage 2용)
├── analysis_report.md                    # Stage 1: 분석 리포트
│
├── 02_extraction/                        # Stage 2
│   ├── patterns.json                     #   추출된 패턴 + HT/TS 분류
│   ├── patterns_enriched.json            #   샘플 임베딩 (Stage 3 최적화)
│   ├── faq.json                          #   FAQ 쌍
│   ├── response_strategies.json          #   응답 전략
│   ├── keywords.json                     #   키워드 분류체계
│   └── extraction_summary.md             #   추출 요약
│
├── 03_sop/                               # Stage 3 + 4
│   ├── TS_001_*.sop.md                   #   Troubleshooting SOP
│   ├── HT_001_*.sop.md                   #   How-To SOP
│   ├── TS_001_*_FLOWCHART.md             #   Mermaid 플로우차트 (TS)
│   ├── TS_001_*_flowchart.svg            #   SVG 이미지 (TS, 선택)
│   ├── HT_001_*_FLOWCHART.md             #   Mermaid 플로우차트 (HT)
│   ├── HT_001_*_flowchart.svg            #   SVG 이미지 (HT, 선택)
│   ├── metadata.json                     #   SOP 메타데이터
│   ├── generation_summary.md             #   생성 요약
│   └── flowchart_generation_summary.md   #   플로우차트 요약
│
├── 05_sales_report/                      # Stage 5: ALF 패키지 + 분석/보고서
│   ├── alf_setup/
│   │   ├── rules_draft.md                #   규칙 초안 (시스템 프롬프트)
│   │   └── rag_items.md                  #   RAG 지식 DB 등록 항목
│   ├── tasks/                            #   태스크 플로우차트
│   │   ├── TASK{N}_{이름}.md             #     태스크별 Mermaid 플로우차트
│   │   └── TASK{N}_{이름}.svg            #     SVG 이미지 (선택)
│   ├── analysis/
│   │   ├── cross_analysis.json           #   교차분석 원시 데이터
│   │   ├── heatmap.png                   #   상담주제 × 대화유형 히트맵
│   │   └── automation_analysis.md        #   자동화 가능성 분석
│   ├── sales_report_config.json          #   ROI 계산 설정
│   └── {company}_analysis_report.md      #   최종 분석 리포트 (Rosa 프레임워크)
│
├── 06_alf_documents/                     # Stage 6: ALF 등록용 개별 파일
│   ├── rules/                            #   개별 규칙 파일 9개 (≤2,000자)
│   │   ├── 01_tone_manner.md
│   │   └── ... (02~09)
│   └── rag/                              #   RAG 지식 문서 (토픽별)
│       └── {토픽}.md
│
├── 07_deployment/                        # Stage 7: 배포 시나리오 & QA
│   ├── deployment_qa_set.html            #   고객사 공유용
│   └── deployment_qa_set.md              #   로컬 보관용
│
├── {company}_api_requirements.md         # Stage 5: API 요건 정의서
└── {company}_alf_implementation_guide.md # Stage 5: 최종 ALF 도입 가이드
```

## 디렉토리 구조

```
.
├── .claude/                         # Claude Code 설정
│   ├── settings.json                # 기본 권한 설정
│   ├── settings.local.json          # 로컬 권한 오버라이드
│   └── skills/                      # Claude Code Skills
│       ├── stage1-clustering/       #   Stage 1 Skill
│       ├── stage2-extraction/       #   Stage 2 Skill
│       ├── stage3-sop-generation/   #   Stage 3 Skill
│       ├── stage4-flowchart-generation/ # Stage 4 Skill
│       ├── stage5-sop-to-guide/     #   Stage 5 Skill
│       └── userchat-to-sop-pipeline/ #  통합 파이프라인 Skill
├── agent-sops/                      # Agent SOP 정의서
│   ├── stage1-clustering.sop.md
│   ├── stage2-extraction.sop.md
│   ├── stage3-sop-generation.sop.md
│   ├── stage4-flowchart-generation.sop.md
│   └── userchat-to-sop-pipeline.sop.md
├── scripts/                         # Python 스크립트
│   ├── pipeline.py                  # Stage 1 진입점
│   ├── config.py                    # API 키, 기본 설정
│   ├── lang_config.py               # 다국어 설정 (한/일)
│   ├── enrich_patterns.py           # Stage 2.5: 샘플 임베딩
│   ├── analyze_dialogs.py           # Stage 5: 대화유형 분류
│   ├── generate_heatmap.py          # Stage 5: 교차분석 히트맵
│   ├── generate_sales_report.py     # Stage 5: 영업 보고서 생성
│   ├── extract_alf_setup_data.py    # Stage 5: ALF 세팅 데이터 추출
│   └── clustering/                  # 클러스터링 모듈
│       ├── data_loader.py           #   Excel 로딩 (first_msg 우선 샘플링)
│       ├── text_enhancer.py         #   텍스트 향상 (간소화)
│       ├── embeddings.py            #   임베딩 (병렬 + 캐싱)
│       ├── clustering.py            #   K-Means 클러스터링
│       ├── tagging.py               #   LLM 자동 태깅
│       └── output.py                #   Excel 저장
├── templates/                       # 출력 템플릿
│   ├── HT_template.md              #   How-To SOP 템플릿
│   ├── TS_template.md              #   Troubleshooting SOP 템플릿
│   ├── FLOWCHART_template.md       #   플로우차트 템플릿
│   ├── ALF_RULES_DRAFT_template.md #   규칙 초안 템플릿
│   ├── RAG_ITEMS_template.md       #   RAG 항목 템플릿
│   ├── AUTOMATION_ANALYSIS_template.md # 자동화 분석 템플릿
│   ├── TASK_template.md            #   태스크 플로우차트 템플릿
│   ├── API_REQUIREMENTS_template.md #  API 요건 정의서 템플릿
│   ├── ALF_PACKAGE_template.md     #   ALF 도입 가이드 템플릿
│   ├── SALES_REPORT_template.md    #   분석 리포트 템플릿
│   └── examples/                   #   예시 SOP 파일
├── rules/                           # 형식 규격
│   └── agent-sop-format.md         #   Agent SOP 표준 형식
├── lang/                            # 다국어 설정
│   ├── ko.yaml                     #   한국어
│   └── ja.yaml                     #   일본어
├── docs/                            # 프로젝트 문서
├── data/                            # 입력 Excel 파일
├── results/                         # 출력 결과
└── cache/                           # 임베딩 캐시
```

## 파이프라인 아키텍처

```
Excel Input (고객 상담 데이터)
  ↓
Stage 1: Clustering (Python)
  → 임베딩: 로컬 BGE-m3-ko 우선 → Upstage Solar fallback
  → K-Means 클러스터링 (silhouette 기반 최적 K 자동 선택)
  → 태깅: Prism Gateway Claude 우선 → Upstage Solar-mini fallback
  → clustered.xlsx, tags.xlsx, messages.csv, analysis_report.md
  ↓
Stage 2: Pattern Extraction (LLM)
  → 실제 샘플 기반 패턴/FAQ/키워드 추출 + HT/TS 자동 분류
  → patterns.json, faq.json, keywords.json, response_strategies.json
  ↓
Stage 3: SOP Generation (LLM)
  → HT/TS 템플릿 기반 Agent SOP 문서 생성
  → *.sop.md, metadata.json
  ↓
Stage 4: Flowchart Generation (LLM + Mermaid)
  → SOP 구조 분석 → Mermaid 다이어그램 + SVG 변환
  → *_FLOWCHART.md, *_flowchart.svg
  ↓
Stage 5: ALF Implementation Package (LLM + Python)
  → 규칙 초안, RAG 항목, 교차분석 히트맵, 자동화 분석
  → ROI 계산, 태스크 플로우차트, API 요건, ALF 도입 가이드
  ↓
Stage 6: ALF Document Export (LLM)
  → rules_draft.md → 개별 규칙 파일 9개 (≤2,000자)
  → rag_items.md → 토픽별 RAG 지식 문서 (ALF 등록 직행)
  ↓
Stage 7: Deployment Scenario (LLM)
  → 상담 카테고리 × 해결 방식(RAG/Task) 매핑 + 카테고리별 테스트 쿼리
  → deployment_qa_set.html / .md (+ Notion 발행 선택)
```

## Claude Code Skills

### `/userchat-to-sop-pipeline`
**통합 파이프라인 (Stage 1-7 자동 실행, 권장)**
- 한 번에 전체 7단계 파이프라인 실행
- Stage 간 자동 연결 및 검증
- 각 단계별 리뷰 지점 제공 (auto_proceed 옵션)
- 파라미터 커스터마이제이션 (Quick/Standard/Comprehensive)

### `/stage1-clustering`
대화형 Stage 1 실행 - 파라미터 선택 가이드 제공
- 데이터 파일 자동 스캔 및 선택
- 회사명 자동 추출
- 임베딩: **로컬 BGE-m3-ko 우선 → Upstage Solar fallback** (MPS/CUDA/CPU 자동 선택)
- 태깅: **Prism Gateway Claude 우선 → Upstage Solar-mini fallback**
- LLM Fallback 자동 감지 (≥20%)
- 배치 처리 (50개씩)

### `/stage2-extraction`
실제 샘플 기반 패턴 추출 + HT/TS 분류
- 추측 금지, 20개 샘플 직접 분석
- FAQ, 응답 전략, 키워드 자동 생성
- patterns_enriched.json 생성 (Stage 3 최적화용)

### `/stage3-sop-generation`
Agent SOP 문서 자동 생성
- HT/TS 템플릿 기반 생성
- 실제 고객 표현, 응답 예시 포함
- 민감 정보 일반화 (플레이스홀더 사용)

### `/stage4-flowchart-generation`
Mermaid 플로우차트 자동 생성
- TS/HT 모두 지원 (all, ts_only, ht_only 옵션)
- 색상 코딩 (Success/Warning/Error/Info)
- VSCode 내 SVG 자동 렌더링 지원

### `/stage5-sop-to-guide`
ALF 구축 패키지 생성 (Stage 1-4 산출물 기반)
- 규칙 초안 — 페르소나 / 말투 규칙 / 응대 가이드라인 8개 / 감정별 공감 매핑
- RAG 지식 DB 항목
- 대화유형 교차분석 히트맵
- 자동화 가능성 분석 — **4-Layer ALF 관여 모델** (완전 해결 / 승인노드 / 초벌 상담 / 주제 분류)
- ROI 계산 — `monthly_volume`은 Stage 1 데이터(원본 건수 ÷ 날짜 범위)에서 자동 추정
- 태스크 플로우차트 — `app_functions=true` 시 **앱함수 연동 분류**(이지어드민/카페24/사방넷 함수 스펙 기반, 앱함수/코드노드/혼합)
- API 요건 정의서 + 최종 ALF 도입 가이드

### `/stage6-alf-document-export`
ALF 등록용 개별 파일 분리
- `rules_draft.md` → 9개 규칙 파일 (각 ≤2,000자, 페르소나·말투·응대·공감 등 카테고리별)
- `rag_items.md` → 토픽별 RAG 지식 문서

### `/stage7-deployment-scenario`
고객사 공유용 배포 시나리오 & QA 세트
- 상담 카테고리 ↔ 해결 방식(RAG/Task) ↔ 배포 단계 매핑
- 카테고리별 테스트 쿼리 자동 생성
- HTML + Markdown 출력, Notion 발행 선택

## SOP 템플릿

### Troubleshooting (TS)
문제 해결 프로세스 — 케이스별 분기, 의사결정 트리, 에스컬레이션
- A/S 요청, 제품 불량, 배송 문제, 환불/교환 처리

### How-To (HT)
절차 안내 프로세스 — 순차적 단계, 정보 전달, 셀프서비스
- 사용법 안내, 주문/배송 조회, 회원가입, 적립금/쿠폰 안내

Stage 2에서 각 클러스터를 자동으로 HT/TS로 분류하고, Stage 3에서 해당 템플릿을 적용합니다.

## 기술 스택

| 구분 | 기술 | 용도 |
|------|------|------|
| **임베딩** | `dragonkue/BGE-m3-ko` (로컬, 기본) / Upstage Solar `embedding-passage` (fallback) | 텍스트 벡터화 |
| **클러스터링** | scikit-learn K-Means | 상담 데이터 분류 |
| **LLM** | Claude (Prism Gateway 우선, Anthropic API 직접 호출 가능) / Upstage Solar-mini (fallback) | 태깅, 패턴 추출, SOP 생성, 분석 |
| **플로우차트** | Mermaid.js + @mermaid-js/mermaid-cli | 시각화 |
| **데이터 처리** | pandas, numpy, openpyxl | Excel I/O |
| **시각화** | matplotlib | 히트맵 생성 |
| **병렬 처리** | ThreadPoolExecutor | 임베딩, 배치 처리 |
| **캐싱** | pickle (파일 기반) | 임베딩 재사용 |

## 환경 변수

```bash
# 임베딩 (Stage 1) — 둘 다 선택
#   - 로컬 BGE-m3-ko가 기본 (sentence-transformers 설치 시 자동 사용)
#   - 미설치 시 아래 키로 Upstage Solar API fallback
UPSTAGE_API_KEY=up_...                                # Solar 임베딩 + Solar-mini 태깅 fallback

# LLM (Stage 1 태깅 + Stage 2-7) — 아래 중 하나 선택, Prism 권장
PRISM_API_KEY=...                                     # Prism Gateway (Channel 내부)
PRISM_BASE_URL=https://prism.ch.dev
ANTHROPIC_MODEL=anthropic/claude-sonnet-4-20250514

ANTHROPIC_API_KEY=sk-ant_...                          # 또는 Claude API 직접 사용
```

> **Prism Gateway**: 사내 Channel 환경에서 Anthropic SDK를 `base_url`로 우회 호출하기 위한 게이트웨이. `PRISM_API_KEY`가 설정되어 있으면 자동으로 Prism 경유로 전환됩니다.
> **로컬 임베딩**: `pip install sentence-transformers` 시 BGE-m3-ko가 자동 활성화됩니다 (Mac MPS / CUDA / CPU 자동 선택). 미설치 환경에서는 `UPSTAGE_API_KEY`로 자동 fallback.

## 문제 해결

**임베딩 캐시 이슈:**
```bash
rm -rf cache/
```

**가상환경 문제:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Mermaid CLI 없을 때:** 마크다운 플로우차트는 정상 생성되며, SVG만 생략됩니다.

**그 외 에러:** 에러 메시지를 Claude Code에 붙여넣으면 자동으로 해결책을 제시합니다.

## 기여하기

이슈와 PR은 언제든 환영합니다!
