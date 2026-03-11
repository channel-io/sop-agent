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

**Output format**: `templates/ALF_RULES_DRAFT_template.md` 구조를 따릅니다.

#### 2-B. rag_items.md — RAG Knowledge Items

List all items that the client needs to register in the vector knowledge DB.

Include:
1. **Priority 1 (immediate)**: FAQs, policies, guides — covering 지식응답/정책확인 dialog types
2. **Priority 2 (supplementary)**: Fallback info for Task failures, error code solutions
3. **고객사 추가 권장 항목**: Items expected to be needed but not found in the sample data

Each item MUST show two things separately:
- **등록해야 할 내용**: The ideal/complete scope the knowledge entry should cover
- **발견된 자료**: The specific content actually confirmed from the sample data

**Output format**: `templates/RAG_ITEMS_template.md` 구조를 따릅니다.

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

> **Ask the user to select a mode.** Default is quick.

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

Without using the Python script, the agent reads the message data directly and classifies in batches.

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
- 5 batch Tasks MUST be launched simultaneously in a single message
- Force the prompt to return classification results in JSON format only

#### 3-B. automation_analysis.md 생성 (에이전트 직접 작성)

Read `cross_analysis.json` and **Stage 2's `response_strategies.json` together** using the Read tool, then
**the agent directly writes** all 5 sections to `analysis/automation_analysis.md`. (No external API calls)

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
- Do NOT directly equate dialog type ratios from `cross_analysis.json` to automation rates — always combine with `decision_flow` and `automation_opportunity` from Stage 2 `response_strategies.json`
- Reflect both the per-cluster `automation_opportunity` value (high/medium/low) and the number of `decision_flow` steps
- **Always report "intent ceiling" and "actual automation rate" separately** — both numbers MUST appear in the output
- Calculate the final overall automation rate as a cluster-count **weighted average** (simple average is not allowed)
- Include all 7 dialog types without omission

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

Based on the SOP and automation_analysis.md analysis results, generate two documents.

#### 5-A. 04_tasks/ — Task Flowchart Files

Separate scenarios that include API calls into individual task files, one file per task.

**태스크 선정 기준:**
- API 호출 노드가 1개 이상 포함된 시나리오
- 고객 응답 기반 분기가 3단계 이상인 복잡한 플로우
- 상담사 연결 조건이 명확하게 정의된 시나리오

**각 태스크 파일 형식**: `templates/TASK_template.md` 구조를 따릅니다.

SVG 생성 (mmdc 설치 시):
```bash
mmdc -i results/{company}/04_tasks/TASK{N}_{이름}.md -o results/{company}/04_tasks/TASK{N}_{이름}.svg -b transparent
```

#### 5-B. {company}_api_requirements.md — API Requirements Document

Define the APIs used in tasks so that the development team can review them.

**포함 섹션:**
1. API 필요 태스크: 각 API별 호출 시점, 필요 입력/응답, 챗봇 처리 결과, 비고
2. 처리 방식 선택 항목: API 없이도 처리 가능한 케이스 (방식 A/B 선택지)
3. API 불필요 태스크: 지식 응답만으로 처리 가능한 태스크 + 사유
4. 전체 요약 표: API명, 필수/선택, 핵심 응답값, 연결 태스크
5. 공통 전제 사항: 고객 식별자, 응답 속도, 오류 fallback

**각 API 항목 형식**: `templates/API_REQUIREMENTS_template.md` 구조를 따릅니다.

**Constraints:**
- Extract API requirements only from the SOPs and task flowcharts — no guessing
- Write APIs (POST/PUT/DELETE) MUST be separately marked as "optional" or "secondary review"

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
- ALF participation rate MUST NOT be a single figure — always express as a **min~max range**
- Use the setup completion status exactly as confirmed in Step 1
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

**Output format**: `templates/최종 분석 리포트 템플릿.md` 구조를 따릅니다.

**Constraints:**
- Fields with no data MUST be marked `(데이터 미제공)` or `(확인 필요)` — never fill by guessing
- Numbers in sections 2, 3, and 4 MUST use only actual values read from `cross_analysis.json`
- **Section 3 automation summary**: Intent ceiling and actual automation rate MUST always be displayed separately — refer to `automation_analysis.md`
- **Section 5 Phase figures**: Use the actual automation rate from section 4 of `automation_analysis.md`, not dialog type ratios
- **Section 8 summary**: A single "automatable ratio" figure is not allowed — show intent ceiling and actual full-automation rate as separate rows
- Section 6 (additional findings) is LLM-written but MUST cite evidence from the data — unsupported statements like "generally…" are not allowed
- Heatmap image MUST be referenced by file path, not inline embedded: `![히트맵](../analysis/heatmap.png)`

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
