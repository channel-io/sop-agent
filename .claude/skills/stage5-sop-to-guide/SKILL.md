---
name: stage5-sop-to-guide
description: Generate an ALF implementation package from all pipeline outputs. Produces rules draft, RAG knowledge items, dialog type cross-analysis heatmap, automation feasibility analysis, ROI calculation, task flowcharts (04_tasks/), API requirements doc, and final ALF implementation guide. **Language:** Auto-detects Korean (한국어) or Japanese (日本語) from user input.
---

# Stage 5: ALF 구축 패키지 생성

## Overview

Stage 1~3 산출물을 모두 활용하여 ALF(AI 챗봇) 도입을 위한 **구축 패키지**를 생성합니다.
단순 ROI 리포트를 넘어, 실제 챗봇 구축에 필요한 규칙 초안·RAG 항목·자동화 전략을 함께 제공합니다.

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

**입력 파일:**
```
01_classification/{company}_messages.csv   → 대화 원시 데이터 (cluster_id 포함)
01_classification/{company}_tags.xlsx      → 클러스터 메타 (라벨/크기)
02_extraction/patterns.json, faq.json      → 패턴/FAQ
03_sop/*.sop.md + *_FLOWCHART.md          → SOP/플로우차트
03_sop/metadata.json                       → SOP 커버리지 정보
```

**Stage Flow:**
```
입력 (Stage 1~3 산출물)
    ↓
Step 1: 파라미터 수집 (회사, 월 상담 건수, 시급 등 + ALF 세팅 현황)
    ↓
Step 2: LLM — SOP + patterns/faq 기반 분석
    → rules_draft.md          (규칙 초안)
    → rag_items.md            (RAG 필요 항목)
    ↓
Step 3: 대화유형 분류 + 교차분석 + 자동화 분석
    [Quick]    scripts/analyze_dialogs.py  (Solar-mini API 분류)
    [Standard] 에이전트 배치 분류 (서브에이전트 5개 병렬)
    → cross_analysis.json + heatmap.png
    에이전트 직접 작성 (API 호출 없음)
    → automation_analysis.md  (자동화 가능성)
    ↓
Step 4: Python — ROI 계산
    python3 scripts/generate_sales_report.py
    → sales_report_config.json + ROI 수치
    ↓
Step 5: LLM — 태스크 정의 + API 요건 정의서
    → 04_tasks/TASK{N}_{이름}.md   (태스크별 Mermaid 플로우차트 + 요약표)
    → {company}_api_requirements.md  (개발팀용 API 요건 정의서)
    ↓
Step 6: LLM — 최종 통합 보고서 (ALF 도입 가이드)
    → {company}_alf_implementation_guide.md
    ↓
Step 7: LLM — 최종 분석 리포트 (Rosa 프레임워크)
    → {company}_analysis_report.md
```

**산출물 디렉토리:**
```
results/{company}/
├── 04_tasks/                              ← (Stage 5에서 생성)
│   ├── TASK{N}_{이름}.md                  ← 태스크별 Mermaid 플로우차트 + 요약표
│   └── TASK{N}_{이름}.svg                 ← (선택, mmdc 설치 시)
├── {company}_api_requirements.md          ← API 요건 정의서 (개발팀용)
├── {company}_alf_implementation_guide.md  ← 최종 ALF 도입 가이드
└── 05_sales_report/
    ├── alf_setup/
    │   ├── rules_draft.md          ← 규칙 초안 (시스템 프롬프트)
    │   └── rag_items.md            ← RAG 지식 DB 등록 항목
    ├── analysis/
    │   ├── cross_analysis.json     ← 교차분석 원시 데이터
    │   ├── heatmap.png             ← 상담주제 × 대화유형 히트맵
    │   └── automation_analysis.md  ← 자동화 가능성 분석
    ├── sales_report_config.json
    └── {company}_analysis_report.md ← 최종 분석 리포트 (Rosa 프레임워크)
```

**Total Time**: ~20–35 minutes (데이터 크기에 따라)

---

## Parameters

### Required
- **company**: 회사 식별자 (예: `usimsa`, `meliens`)
- **monthly_volume**: 월 상담 건수 (실측값 또는 추산, 정수)

### Optional
- **hourly_wage** (기본값: `15100`): 상담사 시급 (원, 임금직업포털 중위값)
- **avg_handling_time_min** (기본값: `8`): 건당 평균 처리 시간 (분)
- **alf_chat_cost** (기본값: `500`): ALF 채팅 참여 비용 (원/건)
- **alf_task_cost** (기본값: `200`): ALF 태스크 실행 비용 (원/건)
- **phase2_min_krw** / **phase2_max_krw**: Phase 2 외주 개발비 범위 (원)
- **output_dir** (기본값: `results/{company}/05_sales_report`): 출력 디렉토리

---

## Steps

### 1. Gather Parameters

**Actions:**
1. Scan `results/` for company directories that contain both `01_classification/` and `03_sop/`
2. Use `AskUserQuestion` to collect all required inputs at once:
   - Target company (select from detected list or enter manually)
   - `monthly_volume` (required — do not assume)
   - `hourly_wage` (show default 15,100원, confirm or update)
   - `phase2_min_krw` / `phase2_max_krw` (outsourcing dev cost range)
3. Auto-resolve file paths:
   - `messages_csv` = `results/{company}/01_classification/{company}_messages.csv`
   - `tags_xlsx` = `results/{company}/01_classification/{company}_tags.xlsx`
   - `sop_dir` = `results/{company}/03_sop`
   - `patterns_json` = `results/{company}/02_extraction/patterns.json`
   - `faq_json` = `results/{company}/02_extraction/faq.json`

**Constraints:**
- You MUST collect ALL inputs in Step 1 — no further questions after this step
- You MUST NOT assume `monthly_volume` — always confirm with the user
- If using defaults, mark them as `(기본값)` in the final report
- **ALF 세팅 현황**: 규칙·지식·태스크 중 이미 완료된 항목을 확인 → Step 6 ALF 가이드의 ✅/🔧 표시에 반영

**Expected Output:**
```
✅ Stage 5 파라미터 확인
  - Company: usimsa
  - messages.csv: results/usimsa/01_classification/usimsa_messages.csv ✅
  - tags.xlsx:    results/usimsa/01_classification/usimsa_tags.xlsx ✅
  - SOP dir:      results/usimsa/03_sop ✅ (8 SOPs)
  - Monthly volume: 3,000건
  - Hourly wage: 15,100원 (기본값)
  - Handling time: 8분 (기본값)
  - Phase 2 dev cost: 100~300만원
  - Output: results/usimsa/05_sales_report/
```

---

### 2. Rules Draft + RAG Items (Python + LLM)

#### 2-A. Python: Run extract_alf_setup_data.py

```bash
python3 scripts/extract_alf_setup_data.py \
    --sop_dir   results/{company}/03_sop \
    --patterns  results/{company}/02_extraction/patterns.json \
    --faq       results/{company}/02_extraction/faq.json \
    --output    results/{company}/05_sales_report/alf_setup
```

Produces `alf_setup/alf_setup_data.json` containing:
- `tone_rules.examples` — tone & manner examples from all SOP tone sections
- `tone_rules.forbidden` — forbidden phrases (❌) from all SOPs
- `escalation_conditions` — parsed escalation tables from all SOPs (with source SOP)
- `faq_pairs` — all FAQ Q/A pairs from faq.json
- `high_freq_patterns` — high/very-high frequency patterns from patterns.json

#### 2-B. LLM: Write rules_draft.md and rag_items.md

Read `alf_setup/alf_setup_data.json` (single structured file) to produce two output files.

#### 2-A. rules_draft.md — Rules Draft

**No hallucination**: Only include content explicitly stated in the SOPs.

Include:
1. **Tone & manner** — extracted from SOP tone sections. For recommended expressions, do NOT just list examples — synthesize them into **behavioral guidelines** (원칙), then provide supporting examples under each guideline. Aim for 5–7 guidelines that cover the full range of expression patterns found (e.g., concreteness principle, empathy-first principle, step-by-step resolution, closing completeness, etc.). Do NOT include a forbidden expressions section.
2. **Escalation conditions** — extracted from each SOP's escalation table. ALF cannot route to specific internal teams — frame all escalation as **"상담사 연결"**. Group cases by situation pattern and synthesize into **decision principles** (e.g., "상담사 연결 기준: 위약금 정확 금액 산정이 필요한 경우"). List representative examples under each principle. End with an "즉시 상담사 연결 트리거 키워드" block.
3. **Non-automatable situations** — extracted from flowchart 🔴 escalation cases

Output format:
```markdown
# {Company} ALF Rules Draft

## Tone & Manner

### ✅ 권장 표현 가이드라인

**[가이드라인 1: {원칙명}]**
{이 원칙의 의미와 적용 기준을 1~2문장으로 설명}
- 예: "..."
- 예: "..."

**[가이드라인 2: {원칙명}]**
{설명}
- 예: "..."

*(가이드라인 5~7개)*

## Escalation Conditions (상담사 연결 기준)

**[상담사 연결 기준 1: {상황 패턴명}]**
{이 상황에서 상담사 연결이 필요한 이유를 1~2문장으로 설명}
- 예: {상황 설명}
- 예: ...

**[상담사 연결 기준 2: {상황 패턴명}]**
{설명}
- 예: ...

*(상황 패턴별로 그룹화, 긴급도 높은 케이스는 맨 위)*

### 🚨 즉시 상담사 연결 트리거 키워드
아래 키워드 감지 시 즉시 상담사 연결:
- `키워드1`, `키워드2`, ...

## Non-automatable Situations
| # | 상황 | 이유 |
|---|------|------|
| ... | ... | ... |
```

#### 2-B. rag_items.md — RAG Knowledge Items

List all items that the client needs to register in the vector knowledge DB.

Include:
1. **Priority 1 (immediate)**: FAQs, policies, guides — covering 지식응답/정책확인 dialog types
2. **Priority 2 (supplementary)**: Fallback info for Task failures, error code solutions
3. **고객사 추가 권장 항목**: Items expected to be needed but not found in the sample data

Each item MUST show two things separately:
- **등록해야 할 내용**: The ideal/complete scope the knowledge entry should cover
- **발견된 자료**: The specific content actually confirmed from the sample data

Output format:
```markdown
# {Company} RAG 지식 DB 등록 항목

> 이 문서는 ALF(AI 챗봇) 도입 시 벡터 지식 DB에 등록해야 할 항목 목록입니다.
>
> **주의**: 아래 "발견된 자료"는 분석 샘플(전체 상담 중 일부)에서 추출된 내용으로,
> 실제 등록 시에는 고객사가 전체 정책/매뉴얼 기준으로 내용을 보완해야 합니다.
>
> 각 항목 형식: **등록해야 할 내용** (이상적 범위) / **발견된 자료** (샘플에서 확인된 내용)

---

## Priority 1: 즉시 등록 (Phase 1 구축 필수)

*지식응답(1) + 정책확인(4) 대화 유형 커버 — 개발 없이 즉시 적용 가능*

| # | 항목 | 등록해야 할 내용 | 발견된 자료 (샘플 기반) | 출처 |
|---|------|----------------|----------------------|------|
| 1 | ... | {이상적으로 포함해야 할 범위 — 조건, 예외, 전체 절차} | {샘플에서 확인된 구체적 내용} | faq.json / HT_001.sop.md |

---

## Priority 2: 보완 등록 (Phase 2 이후 추가)

*정보조회(2) + 단순실행(3) Task 실패 시 폴백 정보*

| # | 항목 | 등록해야 할 내용 | 발견된 자료 (샘플 기반) | 출처 |
|---|------|----------------|----------------------|------|

---

## 고객사 추가 권장 항목 (샘플 데이터 미발견)

> 아래 항목은 분석 샘플에서 직접적인 근거를 확인하지 못했으나,
> 유사 서비스 기준으로 **반드시 구축이 필요한 지식**입니다.
> 고객사가 내부 정책 문서를 기반으로 직접 작성하여 등록해야 합니다.

| # | 항목 | 등록해야 할 내용 | 필요 이유 |
|---|------|----------------|---------|
| 1 | ... | {포함해야 할 내용 범위} | {이 항목이 없으면 발생할 문제 또는 필요 이유} |

---

## 등록 우선순위 판단 기준

| 기준 | Priority 1 | Priority 2 | 고객사 추가 권장 |
|-----|-----------|-----------|--------------|
| 자동화 가능성 | 높음 (RAG만으로 답변 가능) | 중간 (Task 실패 폴백) | 미정 (내용 구축 후 판단) |
| 발생 빈도 | high 패턴 기반 | medium/low 패턴 | 샘플 미발견 (예상 기반) |
| 대화 유형 | 지식응답(1), 정책확인(4) | 정보조회(2), 단순실행(3) | 사전 문의, 이용 안내 |
| 데이터 근거 | 샘플에서 확인됨 | 샘플에서 확인됨 | **고객사 직접 작성 필요** |
| 적용 시점 | Phase 1 즉시 | Phase 2 이후 | Phase 1~2 병행 권장 |

---

> **총 항목**: Priority 1: {N}개 / Priority 2: {N}개 / 고객사 추가 권장: {N}개 = 총 {N}개
> **생성일**: {YYYY-MM-DD}
> **소스**: faq.json ({N}쌍) + SOP {N}개 + patterns.json
> **주의**: Priority 1·2는 샘플 기반 추출이므로, 고객사 전체 정책과 대조 후 내용 보완 필요
```

**Constraints:**
- Do NOT fabricate content not present in the SOPs — only use confirmed data for "발견된 자료"
- Prioritize Q/A pairs from faq.json for "발견된 자료"
- Only include patterns classified as 지식응답/정책확인 from patterns.json in Priority 1
- For "등록해야 할 내용", describe the FULL scope the entry should ideally cover (even if sample only shows part of it)
- For "고객사 추가 권장 항목", add items that are typical for this industry/service type but were not found in the sample — minimum 5 items, clearly marked as requiring the client to write from scratch

**Expected Output:**
```
✅ Step 2 complete
  - alf_setup/rules_draft.md: X escalation conditions extracted
  - alf_setup/rag_items.md: Priority 1: X items / Priority 2: X items / 고객사 추가 권장: X items
```

---

### 3. Dialog Type Classification + Cross-Analysis + Automation Feasibility

#### 3-A. 대화유형 분류 + 교차분석 — Quick / Standard 모드 선택

> **사용자에게 모드를 확인하세요.** 기본값은 quick입니다.

| 모드 | 분류 방법 | 소요시간 |
|------|---------|---------|
| **quick** | `analyze_dialogs.py` → Solar-mini API (건당 1호출) | ~5분 |
| **standard** | Claude Code 에이전트가 배치로 직접 분류 | ~3분 |

---

**[Quick 모드] Python 스크립트 실행**

```bash
python3 scripts/analyze_dialogs.py \
    --messages results/{company}/01_classification/{company}_messages.csv \
    --tags     results/{company}/01_classification/{company}_tags.xlsx \
    --output   results/{company}/05_sales_report/analysis
```

Script produces:
- `analysis/cross_analysis.json` — cluster × dialog_type 교차표 + 통계
- `analysis/heatmap.png` — 히트맵 PNG

**Expected Output:**
```
✅ analyze_dialogs.py complete
  - Classified: 865 chats
  - heatmap.png saved
  - Top types: 4.정책확인 36.4% / 3.단순실행 28.9% / 1.지식응답 16.3%
```

---

**[Standard 모드] Claude Code 에이전트 배치 분류**

Python 스크립트를 사용하지 않고, 에이전트가 직접 메시지 데이터를 읽어 배치로 분류합니다.

1. `_messages.csv`를 Read 툴로 읽어 chatId별 첫 6턴 텍스트 추출
2. **Task 툴로 5개 서브에이전트를 단일 메시지에서 동시에** 실행:
   - 각 서브에이전트: ~200건 배치를 받아 7가지 유형으로 분류 후 JSON 반환
   - prompt 예시: `아래 대화 목록을 읽고 각 chatId를 7가지 유형 중 하나로 분류하세요. 결과를 {"chatId": "유형"} JSON으로만 반환하세요. [대화 목록]`
3. 5개 결과 합산 → 교차표 계산 → `cross_analysis.json` Write
4. `generate_heatmap()` 직접 호출하여 `heatmap.png` 생성:
   ```python
   python3 -c "
   import json, sys
   sys.path.insert(0, 'scripts')
   from analyze_dialogs import generate_heatmap
   from pathlib import Path
   data = json.loads(Path('results/{company}/05_sales_report/analysis/cross_analysis.json').read_text())
   generate_heatmap(data, Path('results/{company}/05_sales_report/analysis/heatmap.png'))
   "
   ```

**Constraints:**
- 5개 배치 Task는 반드시 단일 메시지에서 동시 실행
- 분류 결과는 JSON 형식만 반환하도록 프롬프트 강제

#### 3-B. automation_analysis.md 생성 (에이전트 직접 작성)

`cross_analysis.json`과 **Stage 2의 `response_strategies.json`을 함께** Read 툴로 읽은 후
**에이전트가 직접** 5개 섹션을 작성하여 `analysis/automation_analysis.md`에 Write합니다. (외부 API 호출 없음)

**두 데이터의 역할:**

| 데이터 | 역할 | 알 수 있는 것 |
|--------|------|-------------|
| `cross_analysis.json` | 의도 상한선 | 고객이 무엇을 원했나 (대화유형 분포) |
| `response_strategies.json` (Stage 2) | 실제 해결 복잡도 | 해결하려면 실제로 무엇이 필요한가 (decision_flow, automation_opportunity) |
| **결합** | **실질 자동화율** | 의도 상한선에서 해결 복잡도를 반영하여 현실적으로 조정 |

> `response_strategies.json` 경로: `results/{company}/02_extraction/response_strategies.json`

Include:
1. **히트맵 해석** — 전체 대비 ≥10% 고빈도 셀의 의미 분석
2. **클러스터별 2요소 결합 분석** (핵심 섹션) — 각 클러스터마다:
   - 대화유형 분포에서 도출한 **의도 상한선**
   - Stage 2 `decision_flow` 단계 수 + `automation_opportunity`에서 도출한 **실제 해결 복잡도**
   - 두 요소를 결합한 **실질 자동화율** (완전자동화 / 부분자동화 / 자동화불가)
   - 조정 근거 한 줄 (예: "단순실행 60%이지만 사진 증빙 + 구매일 분기가 필수이므로 하향")
   - 전체 클러스터 건수 가중 평균으로 최종 실질 자동화율 산출
3. **대화유형별 ALF 처리 전략** — 7가지 유형 전부 커버 (비율%, 처리방법). 이 비율은 **"의도 상한선"** 임을 명시
4. **Phase 우선순위** — 결합 분석 기반 실질 자동화율로 계산
5. **클러스터별 인사이트** — 각 클러스터의 지배 유형 + 권장 ALF 전략

**Constraints:**
- `cross_analysis.json`의 대화유형 비율을 자동화율로 **직접 등치하지 말 것** — 반드시 Stage 2 `response_strategies.json`의 `decision_flow` 및 `automation_opportunity`와 결합
- 클러스터별 `automation_opportunity` 값(high/medium/low)과 `decision_flow` 단계 수를 함께 반영할 것
- **"의도 상한선"과 "실질 자동화율"을 항상 분리하여 기재** — 두 숫자 모두 출력에 포함
- 최종 전체 자동화율은 클러스터 건수 **가중 평균**으로 계산 (단순 평균 금지)
- 7가지 대화유형 누락 없이 전부 포함

**Expected Output:**
```
✅ automation_analysis.md complete
  - 의도 상한선 (대화유형 기준): XX.X%
  - 실질 완전자동화율 (2요소 결합): X.X% (XXX건)
  - 실질 부분자동화율 (ALF 관여→상담사 마무리): X.X% (XXX건)
  - 자동화 불가: X.X% (XXX건)
  - 주요 하향 조정 클러스터: {클러스터명} (사유)
```

---

### 4. ROI Calculation (Python)

#### 4-A. Write sales_report_config.json

Compile results from Step 2 (SOP analysis) and Step 3 (automation analysis) into the config JSON.

**Required config fields:**
```json
{
  "company": "lowercase_id",
  "company_name": "공식 회사명",
  "report_date": "YYYY-MM-DD",
  "base_params": {
    "monthly_volume": 0,
    "sample_size": 0,
    "agent_hourly_wage": 15100,
    "avg_handling_time_min": 8,
    "alf_chat_cost_per_conversation": 500,
    "alf_task_cost_per_execution": 200
  },
  "development_cost": {
    "phase1_cost_krw": 0,
    "phase2_min_krw": 0,
    "phase2_max_krw": 0,
    "phase2_duration": "약 X~Y개월"
  },
  "sop_groups": [...],
  "resource_table": [...],
  "non_automatable": [...],
  "phase1_notes": [...],
  "phase2_notes": [...],
  "phase2_description": "..."
}
```

#### 4-B. Run generate_sales_report.py

```bash
python3 scripts/generate_sales_report.py \
    --config results/{company}/05_sales_report/sales_report_config.json
```

**Constraints:**
- You MUST run this script — never manually calculate ROI figures
- `sample_size` MUST come from `metadata.json`

**Expected Output:**
```
✅ ROI calculation complete
  Phase 1: monthly net savings ~XXX만원 | annual ~X,XXX만원 | breakeven: immediate
  Full:    monthly net savings ~XXX만원 | annual ~X,XXX만원 | breakeven: ~X~X months
```

---

### 5. Task Definitions + API Requirements (LLM)

SOP와 automation_analysis.md 분석 결과를 바탕으로 두 문서를 생성합니다.

#### 5-A. 04_tasks/ — 태스크 플로우차트 파일

API 호출이 포함된 시나리오를 태스크 단위로 분리하여 각각 파일로 생성합니다.

**태스크 선정 기준:**
- API 호출 노드가 1개 이상 포함된 시나리오
- 고객 응답 기반 분기가 3단계 이상인 복잡한 플로우
- 상담사 연결 조건이 명확하게 정의된 시나리오

**각 태스크 파일 형식 (`TASK{N}_{이름}.md`):**
- Mermaid 플로우차트 (apiClass 적용)
- 구분선(`---`)
- 태스크 요약 표

태스크 요약표 형식:
```markdown
**태스크 {영문자} — {이름}**

| 항목 | 내용 |
|------|------|
| 커버 범위 | {처리하는 상담 유형 설명} |
| 진단 순서 | {분기 조건 순서} |
| API 호출 | `{API 이름}` — {호출 조건} / 없음 |
| ALF 종결 | {자동 완결 케이스 목록} |
| 상담사 연결 | {연결 필요 조건} |
| 상담사 전달 정보 | {전달 정보 목록} |
```

SVG 생성 (mmdc 설치 시):
```bash
mmdc -i results/{company}/04_tasks/TASK{N}_{이름}.md -o results/{company}/04_tasks/TASK{N}_{이름}.svg -b transparent
```

#### 5-B. {company}_api_requirements.md — API 요건 정의서

태스크에서 사용하는 API를 개발팀이 검토할 수 있도록 정의합니다.

**포함 섹션:**
1. API 필요 태스크: 각 API별 호출 시점, 필요 입력/응답, 챗봇 처리 결과, 비고
2. 처리 방식 선택 항목: API 없이도 처리 가능한 케이스 (방식 A/B 선택지)
3. API 불필요 태스크: 지식 응답만으로 처리 가능한 태스크 + 사유
4. 전체 요약 표: API명, 필수/선택, 핵심 응답값, 연결 태스크
5. 공통 전제 사항: 고객 식별자, 응답 속도, 오류 fallback

**각 API 항목 형식:**
```markdown
### API-{N}. {API 이름}
**연결 태스크**: TASK{N} — {태스크 이름}

| 항목 | 내용 |
|------|------|
| 호출 시점 | {분기 조건 충족 시} |
| 필요 입력 | {전달값} |
| 필요 응답 | {응답 필드 및 가능한 값} |
| 챗봇 처리 결과 | {응답값별 챗봇 동작} |
| 비고 | {예외 케이스} |
```

**Constraints:**
- API 요건은 SOP와 태스크 플로우차트에서만 추출 — 추측 금지
- 쓰기 API(POST/PUT/DELETE)는 "선택" 또는 "2차 검토"로 별도 표기

**Expected Output:**
```
✅ Step 5 complete
  - 04_tasks/: TASK 파일 {X}개 생성
  - {company}_api_requirements.md: 필수 API {X}개 / 선택 API {X}개
```

---

### 6. Final Integrated Report (LLM)

Compose `{company}_alf_implementation_guide.md` using all outputs.

**Source files:**
- `rules_draft.md`, `rag_items.md` (Step 2)
- `cross_analysis.json`, `heatmap.png`, `automation_analysis.md` (Step 3)
- ROI figures from Step 4 script output
- `04_tasks/*.md`, `{company}_api_requirements.md` (Step 5)

**Report sections:**

| Section | Content | Source |
|---------|---------|--------|
| **요약** | ALF 참여율 최저~최고 범위 + ALF 설정 현황 (✅/🔧) | Step 3, 4 |
| **현황: 상담 유형 분포** | 카테고리별 월 건수·비율·주요 처리 방식 | cross_analysis.json |
| **유형별 하위 흐름 → ALF 처리 매핑** | 세부 흐름을 지식/태스크/상담사로 매핑 | SOPs + Step 5 |
| **ALF 세팅 구성** | 규칙·지식·태스크 현황 + 태스크 목록 + API 개발 목록 | Step 2, 5 |
| **예상 커버리지** | 카테고리별 최저→최고 ALF 참여율 + 기여 분해 | Step 3, 5 |
| **준비 사항** | CS팀·개발팀·채널톡 역할별 작업 목록 | LLM composition |

**ALF 참여율 표기 (요약 섹션):**
- 단일 수치가 아닌 **최저(1차 조회 API)~최고(2차 쓰기 API 포함) 범위**로 표기
- ALF 설정 구성 테이블: `상태` 열에 `✅ 세팅 완료` 또는 `🔧 구축 필요` 표시
  - 세팅 완료 여부는 Step 1에서 사용자에게 확인하여 반영

**카테고리별 예상 처리 결과 표기:**
- `ALF 참여 최저→최고`, `최고 추가 자동화 근거`, `직접 상담사 최저→최고` 열 포함
- 최저 = 1차 조회 API만 / 최고 = 2차 쓰기 API(접수·해제·설정) 추가 시

**Constraints:**
- ALF 참여율은 단일 수치 금지 — 반드시 **최저~최고 범위**로 표기
- 세팅 완료 상태는 Step 1에서 확인한 값 그대로 사용
- Use ONLY Step 4 script values for ROI figures

**Expected Output:**
```
✅ Final report complete
  - File: results/{company}/{company}_alf_implementation_guide.md
  - Sections: 6
  - ALF 참여율: 최저 {X}% → 최고 {Y}~{Z}%
```

---

### 7. Final Analysis Report — Rosa Framework (LLM)

**목적**: `templates/최종 분석 리포트 템플릿.md` 구조를 따르는 상세 분석 리포트 생성.
ALF 패키지(`_alf_package.md`)가 영업/배포 중심이라면, 이 보고서는 **데이터 분석 중심**으로
고객사 내부 팀이 현황을 이해하고 개선 우선순위를 파악하는 용도입니다.

**Source files:**
- `cross_analysis.json` (Step 3) → 섹션 2, 3, 4
- `automation_analysis.md` (Step 3) → 섹션 5, 7
- `tags.xlsx` → 섹션 2 (클러스터 라벨/크기)
- `metadata.json` → 섹션 1 (데이터 규모)
- `patterns.json` → 섹션 6 (추가 인사이트)
- `heatmap.png` → 섹션 4-1

**Report sections** (템플릿 구조 그대로 따름):

| 섹션 | 내용 | 소스 | 데이터 없을 때 |
|------|------|------|--------------|
| **1. 데이터 개요** | 원천 데이터 수치, 운영 현황, 특이사항 | metadata.json, messages.csv | 확인된 수치만 기재, 나머지 `(데이터 미제공)` |
| **2. 상담주제 분포** | 클러스터별 건수·비율·키워드 + 핵심 인사이트 | cross_analysis.json + tags.xlsx | — |
| **3. 대화유형 분포** | 7가지 유형 건수·비율·AI 처리방식 + **의도 상한선 vs 실질 자동화율 비교** | cross_analysis.json + automation_analysis.md | — |
| **4. 교차분석** | 히트맵 + Top 10 조합 + 셀 해석 | cross_analysis.json + heatmap.png | — |
| **5. 자동화 전략** | **클러스터별 2요소 결합 분석** 기반 Phase 로드맵 + 예측 효과 (의도 상한선이 아닌 실질 자동화율 사용) | automation_analysis.md | — |
| **6. 추가 발견사항** | 데이터에서 발견된 특이 패턴 및 운영 인사이트 | patterns.json + SOPs | 최소 3개 이상 |
| **7. 우선순위 권고** | ROI 기준 순위 테이블 | cross_analysis.json + automation_analysis.md | — |
| **8. 요약** | 핵심 지표 요약 테이블 + 핵심 메시지 | 전체 | — |

**Output format** (섹션별 지침):

```markdown
# {Company명} 고객센터 최종 분석 리포트

> **분석 기간**: {available or "(데이터 미제공)"}
> **분석일**: {YYYY-MM-DD}
> **데이터 출처**: {source description}
> **프레임워크**: 상담주제 x 대화유형 2차원 교차분석 (ver. Rosa)

---

## 1. 데이터 개요

### 1-1. 원천 데이터
| 항목 | 수치 |
| --- | --- |
| 전체 케이스 | {N건 또는 "(데이터 미제공)"} |
| 분석 대상 | {N건} |
| 전체 메시지 | {N건 또는 "(데이터 미제공)"} |

### 1-2. 운영 현황
| 항목 | 내용 |
| --- | --- |
| 상담사 | {이름 목록 또는 "(데이터 미제공)"} |
| 채널 | {채널 분포 또는 "(데이터 미제공)"} |
| 주요 서비스 | {서비스 설명 — tags.xlsx 라벨에서 추론} |

### 1-3. 특이사항
- {messages.csv 패턴에서 발견된 특이점, 없으면 생략}

---

## 2. 상담주제 분포 (X축)

| # | 상담주제 | 건수 | 비율 | 주요 키워드 |
| --- | --- | --- | --- | --- |
{cross_analysis.json 클러스터 데이터 전체 나열, 비율 내림차순}

> **기타 비율**: X% — 품질 게이트 {통과/미통과} (기준: < 10%)

### 핵심 인사이트
> {상위 2~3개 클러스터 조합이 의미하는 업무 패턴을 1~2줄로 설명}

---

## 3. 대화유형 분포 (Y축)

| # | 대화유형 | 건수 | 비율 | 정의 | AI 처리 방식 |
| --- | --- | --- | --- | --- | --- |
{cross_analysis.json의 dialog_type_stats 전체 나열}

> **의도불명확 비율**: X% — 품질 게이트 {통과/미통과} (기준: < 25%)

### 자동화 가능성 요약 (의도 상한선 기준)

> ⚠️ 아래 비율은 **의도 상한선** (대화유형 분류 기반)입니다.
> 실질 자동화율은 `automation_analysis.md` 섹션 2의 클러스터별 결합 분석을 참고하세요.

| 구분 | 대화유형 | 의도 상한선 | 자동화 방식 |
| --- | --- | --- | --- |
| 🟢 즉시 자동화 | 지식응답 + 정보조회 + 단순실행 | X% | RAG + Task |
| 🟡 정책 정비 후 | 정책확인 + 조건부실행 | X% | RAG + Task + 분기 |
| ⚪ 명확화 | 의도불명확 | X% | 명확화 질문 시나리오 |
| 🔴 자동화 불가 | 상담사전환 | X% | 상담사 필수 |

### 의도 상한선 vs 실질 자동화율

| 지표 | 수치 | 설명 |
| --- | --- | --- |
| **의도 상한선** | {X}% | 대화유형 분류 기반 상한 |
| **실질 완전자동화율** | {X}% | Stage 2 해결 복잡도 반영 후 조정 (`automation_analysis.md` 참고) |
| **ALF 관여율** | {X}% | 완전자동화 + 부분자동화 합산 |

---

## 4. 상담주제 x 대화유형 교차분석

### 4-1. 히트맵
{heatmap.png 참조 — 파일 경로 명시: results/{company}/05_sales_report/analysis/heatmap.png}

### 4-2. Top 10 고빈도 조합
| 순위 | 상담주제 x 대화유형 | 건수 | 비율 | 자동화 방식 |
| --- | --- | --- | --- | --- |
{cross_analysis.json top_combinations에서 상위 10개}

### 4-3. 셀 해석
> **1위: {주제} x {유형} = X% ({N}건)**
> 대표 대화 패턴 및 자동화 접근 방식 설명

{Top 3~5개 셀만 선택적으로 해석}

---

## 5. 자동화 전략

> 이 섹션의 Phase별 수치는 `automation_analysis.md` 섹션 2의 **2요소 결합 분석** 결과 기반입니다.
> 의도 상한선이 아닌 **실질 자동화율**을 사용합니다.

### 5-1. 클러스터별 자동화 가능성
{automation_analysis.md 섹션 2 요약표 인용}

### 5-2. 자동화 로드맵

#### Phase 1: 즉시 자동화 — 실질 완전자동화 {X}%
> ※ 의도 상한선({Y}%)과 다름 — Stage 2 해결 복잡도 반영 조정
| 대상 | 방식 | 필요 작업 |

#### Phase 2: API 연동 후 — 완전자동화 추가 {X}%
| 대상 | 방식 | 필요 작업 |

#### Phase 3: 장기 과제 — 추가 {X}%
| 대상 | 방식 | 필요 작업 |

### 5-3. 자동화 효과 예측
| 지표 | 현재 | Phase 1 후 | Phase 1+2 후 |
| --- | --- | --- | --- |
| **실질 완전자동화율** | 0% | {X}% | {X}% |
| **ALF 관여율** | 0% | {X}% | {X}% |
| 월간 상담 건수 | {monthly_volume}건/월 | ~{N}건/월 | ~{N}건/월 |

---

## 6. 추가 발견사항

- {patterns.json 고빈도 패턴에서 발견된 운영 인사이트}
- {SOP 특이사항 — 예: 특정 문의가 복잡한 이유}
- {데이터 패턴에서 보이는 서비스 개선 포인트}

{최소 3개, 데이터 기반으로만 작성}

---

## 7. 우선순위 권고 (ROI 기준)

| 순위 | 시나리오 | 건수/월 | ROI 근거 | 난이도 |
| --- | --- | --- | --- | --- |
{cross_analysis.json + automation_analysis.md 기반으로 ROI 순서 정렬}

---

## 8. 요약

| 항목 | 값 |
| --- | --- |
| 분석 케이스 | {N}건 |
| 상담주제 | {N}개 카테고리 (기타 {X}%) |
| 대화유형 | 7개 유형 (의도불명확 {X}%) |
| **의도 상한선** | **{X}%** (1~5유형 합산) |
| **실질 완전자동화율** | **{X}%** (Stage 2 해결 복잡도 반영) |
| **ALF 관여율** | **{X}%** (완전 + 부분자동화) |
| **핵심 자동화 대상** | {상위 클러스터들} |
| **예상 인력 절감** | {예측값 또는 "(ROI 계산 결과 참조)"} |

> **핵심 메시지**: {회사명} CS의 핵심은 {상위 2개 주제}. {자동화 전략 한 줄 요약}.
> 의도 상한선({X}%) 대비 실질 완전자동화율({X}%)의 차이({갭}%p)는 {주요 장벽}에 기인합니다.

---

*분석 도구: Claude Code (CS EDA 프레임워크) | 분석 방법론: 상담주제 x 대화유형 2차원 교차분석 (ver. Rosa)*
```

**Constraints:**
- 데이터 없는 필드는 `(데이터 미제공)` 또는 `(확인 필요)` 로 표시 — 절대 추측하여 채우지 않음
- 섹션 2·3·4의 수치는 반드시 `cross_analysis.json`에서 읽은 실제 값만 사용
- **섹션 3 자동화 요약**: 의도 상한선과 실질 자동화율을 반드시 분리하여 표시 — `automation_analysis.md` 참조
- **섹션 5 Phase 수치**: 대화유형 비율이 아닌 `automation_analysis.md` 섹션 4의 실질 자동화율 사용
- **섹션 8 요약**: "자동화 가능 비율" 단일 표기 금지 — 의도 상한선과 실질 완전자동화율을 별도 행으로 표기
- 섹션 6 (추가 발견사항)은 LLM 작성이지만 반드시 데이터에서 근거를 찾아 기술 — "일반적으로…" 같은 무근거 문장 금지
- 히트맵 이미지는 인라인 임베드 대신 파일 경로 참조로 명시: `![히트맵](../analysis/heatmap.png)`

**Expected Output:**
```
✅ Analysis report complete
  - File: results/{company}/05_sales_report/{company}_analysis_report.md
  - Sections: 8
  - 데이터 미제공 필드: X개 (운영 현황 일부 등)
```

---

## Related Documentation

- **Dialog Analysis Script**: [analyze_dialogs.py](../../../scripts/analyze_dialogs.py)
- **ROI Calculation Script**: [generate_sales_report.py](../../../scripts/generate_sales_report.py)
- **Rosa Analysis Framework**: [README_ver_rosa.md](../../../README_ver_rosa.md)
- **Analysis Report Template**: `templates/최종 분석 리포트 템플릿.md`

---

## Notes

### Dialog Type Definitions (7 types)

| # | Type | Definition | ALF Processing |
|---|------|------------|---------------|
| 1 | 지식응답 | FAQ, how-to, general info questions | RAG |
| 2 | 정보조회 | Personal order/delivery data lookup | Task (query API) |
| 3 | 단순실행 | Direct action requests (cancel, refund, resend) | Task (execution API) |
| 4 | 정책확인 | Conditional "is this possible?" questions | RAG + branching |
| 5 | 조건부실행 | Situation + action request combined | Task + policy logic |
| 6 | 의도불명확 | Too short or context-dependent utterances | Clarification question |
| 7 | 상담사전환 | Emotional escalation, legal mentions | Escalation |

### Filtering System Auto-Send Clusters

`messages.csv` may include bot/system auto-send clusters (e.g., QR code delivery notifications).
Identify and exclude before classification:
- Check tags.xlsx for clusters labeled "자동발송", "시스템 메시지", "결제 안내"
- Pass cluster IDs to exclude via `--exclude_clusters` option in analyze_dialogs.py
