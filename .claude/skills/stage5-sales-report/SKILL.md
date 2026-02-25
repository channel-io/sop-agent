---
name: stage5-sales-report
description: Generate an ALF implementation package from all pipeline outputs. Produces rules draft, RAG knowledge items, dialog type cross-analysis heatmap, automation feasibility analysis, ROI calculation, and final integrated report. **Language:** All user interactions MUST be conducted in Korean (한국어).
---

# Stage 5: ALF 구축 패키지 생성

## Overview

Stage 1~3 산출물을 모두 활용하여 ALF(AI 챗봇) 도입을 위한 **구축 패키지**를 생성합니다.
단순 ROI 리포트를 넘어, 실제 챗봇 구축에 필요한 규칙 초안·RAG 항목·자동화 전략을 함께 제공합니다.

**Language:** All user interactions MUST be conducted in Korean (한국어).

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
Step 1: 파라미터 수집 (회사, 월 상담 건수, 시급 등)
    ↓
Step 2: LLM — SOP + patterns/faq 기반 분석
    → rules_draft.md          (규칙 초안)
    → rag_items.md            (RAG 필요 항목)
    ↓
Step 3: Python — 대화유형 분류 + 교차분석
    python3 scripts/analyze_dialogs.py
    → cross_analysis.json + heatmap.png
    ↓ (이어서 LLM)
    → automation_analysis.md  (자동화 가능성)
    ↓
Step 4: Python — ROI 계산
    python3 scripts/generate_sales_report.py
    → sales_report_config.json + ROI 수치
    ↓
Step 5: LLM — 최종 통합 보고서
    → {company}_alf_package.md
```

**산출물 디렉토리:**
```
results/{company}/05_sales_report/
├── alf_setup/
│   ├── rules_draft.md          ← 규칙 초안 (시스템 프롬프트)
│   └── rag_items.md            ← RAG 지식 DB 등록 항목
├── analysis/
│   ├── cross_analysis.json     ← 교차분석 원시 데이터
│   ├── heatmap.png             ← 상담주제 × 대화유형 히트맵
│   └── automation_analysis.md  ← 자동화 가능성 분석
├── sales_report_config.json
└── {company}_alf_package.md    ← 최종 통합 보고서
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
1. **Tone & manner** — extracted from SOP tone sections (greeting style, empathy expressions, forbidden phrases)
2. **Escalation conditions** — extracted from each SOP's escalation table (situation → target team)
3. **Non-automatable situations** — extracted from flowchart 🔴 escalation cases

Output format:
```markdown
# {Company} ALF Rules Draft

## Tone & Manner
- Greeting: ...
- Empathy: ...
- Avoid: ...

## Escalation Conditions
| Situation | Target | Source SOP |
|-----------|--------|-----------|
| ... | ... | ... |

## Non-automatable Situations
- ...
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

### 3. Dialog Type Classification + Cross-Analysis + Automation Feasibility (Python + LLM)

#### 3-A. Python: Run analyze_dialogs.py

```bash
python3 scripts/analyze_dialogs.py \
    --messages results/{company}/01_classification/{company}_messages.csv \
    --tags     results/{company}/01_classification/{company}_tags.xlsx \
    --output   results/{company}/05_sales_report/analysis
```

> **Dialog type classification method (TBD)**: Default uses Upstage Solar-mini API (`--workers 5`).
> For cost reduction, Claude subagent parallel batch mode is available (~3 min for 5 batches × ~170 items each).

Script produces:
- `analysis/cross_analysis.json` — cluster × dialog_type cross-table + statistics
- `analysis/heatmap.png` — ratio% · count heatmap (rows/cols sorted by volume descending)

**Expected Output:**
```
✅ analyze_dialogs.py complete
  - Classified: 865 chats (system auto-send cluster excluded)
  - heatmap.png saved
  - Top types: 4.정책확인 36.4% / 3.단순실행 28.9% / 1.지식응답 16.3%
```

#### 3-B. LLM: Write automation_analysis.md

Read `cross_analysis.json` and write the automation strategy document.

Include:
1. **Heatmap interpretation** — meaning of high-frequency cells (≥10%)
2. **Automation strategy per dialog type** — ALF processing method for all 7 types
3. **Phase priorities**:
   - Phase 1: 지식응답 + 정책확인 → Rules+RAG (immediate, no development)
   - Phase 2: 정보조회 + 단순실행 → Task API (development required)
   - Phase 3: 조건부실행 → Complex scenarios (long-term)
4. **Per-cluster insights** — dominant dialog type and recommended ALF strategy per cluster

**Constraints:**
- Base all figures on actual values from cross_analysis.json — no guessing
- Cover all 7 dialog types

**Expected Output:**
```
✅ automation_analysis.md complete
  - Phase 1 target: X chats (Y%)
  - Phase 2 target: X chats (Y%)
  - Escalation only: X chats (Y%)
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

### 5. Final Integrated Report (LLM)

Compose `{company}_alf_package.md` using all outputs.

**Source files:**
- `rules_draft.md`, `rag_items.md` (Step 2)
- `cross_analysis.json`, `heatmap.png`, `automation_analysis.md` (Step 3)
- ROI figures from Step 4 script output

**Report sections:**

| Section | Content | Source |
|---------|---------|--------|
| **ROI Summary** | Phase-by-phase monthly & annual net savings | Step 4 |
| **Executive Summary** | Analysis scale, 3 key insights | LLM composition |
| **Cross-Analysis Results** | Heatmap + dialog type distribution | cross_analysis.json |
| **Automation Strategy** | Phase priorities | automation_analysis.md |
| **Rules Draft** | System prompt draft | rules_draft.md |
| **RAG Items** | Knowledge DB build list | rag_items.md |
| **ROI Detail** | Calculation breakdown | Step 4 |
| **Deployment Roadmap** | Phase-by-phase action items | LLM composition |

**Constraints:**
- Use ONLY Step 4 script values for all ROI figures
- 3 key insights MUST be derived from actual analysis (no generic statements)
- Always include at end of report:
  ```
  > ⚠️ ROI 수치는 alf_triggered, alf_handling_time 실측값으로 최종 검증 필요
  ```

**Expected Output:**
```
✅ Final report complete
  - File: results/{company}/05_sales_report/{company}_alf_package.md
  - Sections: 8
```

---

## Related Documentation

- **Dialog Analysis Script**: [analyze_dialogs.py](../../../scripts/analyze_dialogs.py)
- **ROI Calculation Script**: [generate_sales_report.py](../../../scripts/generate_sales_report.py)
- **Rosa Analysis Framework**: [README_ver_rosa.md](../../../README_ver_rosa.md)
- **Reference Outputs (usimsa)**: [results/usimsa/05_sales_report/](../../../results/usimsa/05_sales_report/)

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
