---
name: stage3-sop-generation
description: This SOP guides the generation of a production-ready Agent SOP document from extracted patterns and FAQs. This is **Stage 3** (final stage) of the Userchat-to-SOP pipeline, performed entirely by the AI agent using natural language composition.  **Language:** Auto-detects Korean (한국어) or Japanese (日本語) from user input.  **Stage Flow:** - **Input**: Stage 2 extraction results (JSON files with patterns, FAQs, strategies) - **Process**: LLM composition of Agent SOP following standard format - **Output**: Agent SOP document (.sop.md) ready for deployment  **Key Capabilities:** - Generate Agent SOP in standardized format (RFC 2119 compliant) - Transform extracted patterns into parameterized workflows - Create constraint-based steps with MUST/SHOULD/MAY keywords - Include examples and troubleshooting sections - Ensure reusability across different customer support scenarios
---

# Stage 3: Agent SOP Generation

## Overview
This SOP guides the generation of a production-ready Agent SOP document from extracted patterns and FAQs. This is **Stage 3** (final stage) of the Userchat-to-SOP pipeline, performed entirely by the AI agent using natural language composition.

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

**Stage Flow:**
- **Input**: Stage 2 extraction results (JSON files with patterns, FAQs, strategies)
- **Process**: LLM composition of Agent SOP following standard format
- **Output**: Agent SOP document (.sop.md) ready for deployment

**Key Capabilities:**
- Generate Agent SOP in standardized format (RFC 2119 compliant)
- Transform extracted patterns into parameterized workflows
- Create constraint-based steps with MUST/SHOULD/MAY keywords
- Include examples and troubleshooting sections
- Ensure reusability across different customer support scenarios

## Parameters

### Required
- **extraction_output_dir**: Directory containing Stage 2 results
  - Example: `results/{company}/02_extraction`
  - Must contain: `patterns.json`, `faq.json`, `response_strategies.json`

- **company**: Company name
  - Example: "Channel Corp."
  - Used in SOP title and context

- **sop_title**: Title of the generated SOP
  - Example: "Channel Corp. Customer Support Assistant"
  - Should be descriptive and specific

### Optional
- **sop_type** (default: "customer_support"): Type of SOP to generate
  - `"customer_support"`: General support agent SOP
  - `"troubleshooting"`: Technical troubleshooting focus
  - `"sales"`: Sales inquiry handling

- **include_sections** (default: "all"): Which sections to include
  - `"all"`: Full SOP (Overview, Parameters, Steps, Examples, Troubleshooting)
  - `"essential"`: Core sections only (Overview, Parameters, Steps)
  - Custom list: e.g., `"overview,parameters,steps,examples"`

## Steps

### 1. Load and Analyze Extraction Results

Read all Stage 2 outputs to understand extracted patterns and strategies.

**Constraints:**
- You MUST read the SOP templates BEFORE generating any SOP file:
  - `templates/HT_template.md`: HT SOP 구조 기준 (목적/주의사항/내용/톤앤매너/에스컬레이션)
  - `templates/TS_template.md`: TS SOP 구조 기준 (목적/주의사항/문제해결프로세스/톤앤매너/에스컬레이션)
  - 생성하는 모든 SOP는 반드시 이 템플릿 구조를 따라야 한다
- You MUST read all JSON files from Stage 2:
  1. `patterns.json`: Patterns per cluster + **`sop_topic_map`** (authoritative SOP plan from Stage 2)
  2. `faq.json`: FAQ pairs (organized by SOP topic)
  3. `response_strategies.json`: Response strategies per SOP topic
  4. `keywords.json`: Keyword taxonomy
  5. `extraction_summary.md`: Summary and automation opportunities
- You MUST read enriched patterns (required, not optional):
  6. `patterns_enriched.json`: Patterns with **20 real conversation transcripts per cluster**
  - Contains full conversation `turns` (not summaries)
  - Contains tone-and-manner samples per cluster
  - **Read the actual `turns` in each conversation** to extract real customer expressions, agent response templates, and troubleshooting steps
- You MUST verify JSON structure is valid
- You MUST follow `sop_topic_map` from `patterns.json` — this is the **authoritative plan** from Stage 2
  - DO NOT re-classify clusters or redefine SOP topics
  - DO NOT add or remove topics beyond what the map specifies
  - Each topic in the map becomes exactly one SOP file
- You SHOULD identify which patterns will become SOP steps
- You MAY skip low-frequency patterns within a topic (< 2%), but NOT the topic itself

**Reading Process:**
```bash
# In Claude Code - Stage 2 outputs
Read results/{company}/02_extraction/patterns.json      # includes sop_topic_map
Read results/{company}/02_extraction/faq.json
Read results/{company}/02_extraction/response_strategies.json
Read results/{company}/02_extraction/keywords.json
Read results/{company}/02_extraction/extraction_summary.md
Read results/{company}/02_extraction/patterns_enriched.json  # full conversations
```

**Analysis Checklist:**
- [ ] `sop_topic_map` present in patterns.json? (required — defines what SOPs to generate)
- [ ] How many SOP topics defined? (each becomes one SOP file)
- [ ] Which topics are HT vs TS?
- [ ] Which patterns map to which topic?
- [ ] Which conversations from enriched data correspond to each topic?

### 2. Design SOP Structure (from `sop_topic_map`)

Read the `sop_topic_map` from `patterns.json` and use it as the **definitive SOP plan**. Do NOT redesign the topic structure.

**Using `sop_topic_map` (필수):**

Stage 2 Step 3에서 이미 클러스터를 분석하고 SOP 토픽을 정의했다. Stage 3은 이 맵을 **그대로 따른다**.

```
sop_topic_map에서 가져올 정보:
- topic_id → SOP 파일명
- title → SOP 제목
- type (HT/TS) → 사용할 템플릿
- journey_stage → 파일명 접두사
- source_clusters → 어떤 클러스터/대화를 참고할지
- key_patterns → SOP 내용의 핵심 패턴
```

**SOP 파일명 규칙:**
```
HT_{여정단계}_{주제}.sop.md   → 정보 안내 중심
TS_{여정단계}_{주제}.sop.md   → 문제 해결 중심

예시:
HT_구매전_제품견적상담.sop.md
TS_사용중_하드웨어불량및수리.sop.md
```

**Constraints:**
- You MUST follow `sop_topic_map` exactly — one SOP per topic, no additions or removals
- You MUST follow `templates/HT_template.md` for HT SOPs and `templates/TS_template.md` for TS SOPs
- You MUST NOT use Overview/Parameters/Steps/Examples 구조 — 템플릿에 없는 섹션은 추가하지 말 것
- You MUST NOT redesign the topic structure or re-classify clusters (already done in Stage 2)
- You MUST read enriched conversations for each topic's `source_clusters` when writing that SOP
- You SHOULD include all sections defined in the template (목적, 주의사항, 내용/문제해결프로세스, 톤앤매너, 에스컬레이션, 관련SOP)
- You SHOULD add cross-references between related SOPs (관련 SOP 섹션)
- You MAY merge similar patterns into single 케이스 under 해결책 안내
- You MUST ensure each SOP has a clear, single responsibility

**Design Decisions:**

1. **Step Granularity:**
   - Group related patterns: "충전_AS", "배터리_AS" → single Case under 해결책 안내
   - Keep distinct scenarios separate: each Case should represent a clearly different customer situation

2. **Constraint Levels:**
   - MUST: Critical business rules (warranty verification, PII handling)
   - SHOULD: Best practices (check history first)
   - MAY: Optional enhancements (offer related products)

### 3. Extract Concrete Details from Enriched Conversations

Before writing any SOP, mine the enriched conversation data for concrete, actionable details.

**Constraints:**
- You MUST read `patterns_enriched.json` → each cluster's `sample_conversations` → `turns`
- You MUST extract the following from actual manager (agent) messages in turns:
  1. **Internal tool URLs/paths** — e.g., `biz-crm.dmz.channel.io/accounts/{accountId}?tab=settings`
  2. **Step-by-step instructions agents actually gave** — copy near-verbatim, don't paraphrase
  3. **Warning messages agents sent** — e.g., "구글 로그인 버튼으로 다시 접속하시면 재연동됩니다"
  4. **Specific UI navigation paths** — e.g., "좌측 하단 프로필 이미지 클릭 > [계정 설정]"
  5. **Conditional branches agents used** — e.g., "비밀번호를 설정한 적 없는 경우 → 비밀번호 찾기 안내"
- You MUST also extract from user messages:
  1. **Common customer expressions** — how customers describe the problem in their own words
  2. **Frequently asked follow-up questions**
- You MUST use `tone_and_manner_samples` for the 톤앤매너 section
- You SHOULD create a per-topic extraction note before writing each SOP:

```
Topic: Setting_Account_구글연동해제
Source clusters: [3, 7]
Extracted from conversations:
  - Admin URL: biz-crm.dmz.channel.io/accounts/{accountId}?tab=settings
  - Agent instruction: "로그인 화면에서 '구글 로그인' 버튼이 아닌, 이메일 입력란에 기존 이메일 주소를 직접 입력"
  - Warning: "구글 로그인 버튼으로 다시 접속하면 재연동됨"
  - UI path: "좌측 하단 프로필 이미지 클릭 > [계정 설정] > '로그인 계정'"
  - Customer expression: "이메일 변경이 안 돼요", "구글 로그인 해제해주세요"
  - Condition: "비밀번호 미설정 → 비밀번호 찾기 안내"
```

**Why this matters:**
- Without concrete details, SOPs become generic (e.g., "내부 어드민에서 확인" instead of actual URL)
- The enriched data contains real agent responses — use them as the foundation, not as mere reference

**⚠️ Extraction Guardrails (반드시 준수):**

1. **예외 조치 vs 표준 절차 구분**: 대화에서 상담원이 수행한 조치가 **표준 절차**인지 **비상/예외 조치**인지 판단해야 한다. 다음 패턴은 예외 조치일 가능성이 높으므로 SOP의 표준 Step으로 포함하지 않는다:
   - 보안 인증 정보(인증코드, OTP 등)를 채팅/문자로 직접 전달하는 행위
   - 내부 시스템을 우회하는 임시 조치 (예: 수동 차단 해제 후 재차단 발생)
   - 상담원이 "한 번만 더 시도해보고" 등의 시행착오를 반복하는 구간
   - 에스컬레이션 후 Tier2가 처리한 특수 조치
   → 이런 조치가 대화에 있더라도 SOP에는 **에스컬레이션 조건**으로만 기재한다.

2. **FAQ 문구의 과잉 일반화 금지**: FAQ에 "세일즈팀에 문의", "기술팀에 확인" 등의 표현이 있다고 해서 해당 토픽의 **모든 Case를 에스컬레이션으로** 처리하지 않는다.
   - FAQ의 에스컬레이션 문구는 **해당 FAQ 질문의 맥락**에만 적용한다.
   - 같은 토픽 내에서도 CX팀이 직접 처리 가능한 Case와 에스컬레이션이 필요한 Case를 분리한다.
   - 에스컬레이션 기준이 불명확한 경우, `<!-- TODO: 에스컬레이션 기준 확인 필요 -->` 주석을 남긴다.

3. **문의 유형 혼재 방지**: 하나의 Case 안에 서로 다른 문의 유형의 Step이 섞이지 않도록 한다.
   - 각 Case는 **하나의 고객 시나리오**만 다뤄야 한다.
   - 대화 원문에서 여러 이슈가 연속으로 발생한 경우, 각 이슈를 별도 Case로 분리한다.
   - Case 간 참조("Case N 참조")로 연결하되, Step을 혼합하지 않는다.

### 4. Write SOP Content (해결책 안내 — Case-by-Case)

This is the most critical step. Each SOP's 해결책 안내 section must contain **Case-by-Case breakdowns** with production-ready detail.

**Constraints:**
- You MUST follow the template structure exactly:
  - HT SOPs → `templates/HT_template.md` (목적 → 주의사항 → 내용 → 톤앤매너 → 에스컬레이션)
  - TS SOPs → `templates/TS_template.md` (목적 → 주의사항 → 문제해결프로세스 → 톤앤매너 → 에스컬레이션)
- You MUST NOT use Overview/Parameters/Steps/Examples structure — that is for Agent Skills, not SOP documents
- **For TS SOPs**: You MUST follow the **비파괴적 순서 (Non-Destructive Order)** principle
  - Order troubleshooting steps from least to most invasive
  - Include "✅ 해결되었는지 확인" checkpoint after each troubleshooting step
  - Reference: See `templates/TS_template.md` for detailed guidance

#### Case Quality Requirements (MUST follow for every Case)

Each Case under 해결책 안내 MUST include ALL of the following elements:

| # | Required Element | Bad Example (generic) | Good Example (production-ready) |
|---|-----------------|----------------------|-------------------------------|
| 1 | **Case 헤더 with 빈도** | `Case 1: 인증코드 미수신 (빈도: 높음)` | `Case 1: 로그인 이메일/계정 변경을 위한 해제 (빈도: 높음 — 전체의 66.7%)` |
| 2 | **주요 상황 서술** | `주요 원인: 이메일 수신거부` | `주요 상황: 고객이 계정 설정에서 로그인 이메일을 변경하려 하나, 구글 연동 상태라 이메일이 잠겨있어 수정이 불가한 경우` |
| 3 | **Step별 안내 멘트 (블록 인용)** | `"이메일을 확인해 주세요"` | 3줄 이상의 구체적 안내 + 번호 매긴 절차 (아래 예시 참조) |
| 4 | **내부 도구 경로** | `내부 어드민에서 확인` | `**경로:** biz-crm.dmz.channel.io/accounts/{accountId}?tab=settings` |
| 5 | **UI 네비게이션 경로** | `설정에서 변경` | `좌측 하단 프로필 이미지 클릭 > **[계정 설정]** > **'로그인 계정'** 항목` |
| 6 | **조건 분기 (IF/THEN)** | (없음) | `변경이 안 되는 경우, 구글 재연동 여부를 확인하고 Step 2부터 다시 진행` |
| 7 | **⚠️ 경고/주의 문구** | (없음) | `⚠️ **중요:** '구글 로그인' 버튼으로 다시 로그인하시면 구글 연동이 재설정됩니다` |
| 8 | **완료 확인 Step** | (없음) | `"이메일 변경이 정상적으로 완료되셨나요? 확인 한 번만 부탁드립니다."` |
| 9 | **Case 간 참조** | (없음) | `Case 1의 Step 2~4와 동일하게 처리한다` |

#### Step 안내 멘트 작성 기준

각 Step의 안내 멘트는 블록 인용(>) 형식으로, **고객에게 보내는 실제 메시지** 수준으로 작성한다:

```markdown
**Step 3. 재로그인 안내**

> "구글 연동 해제가 완료되었습니다. 아래 순서대로 진행해 주세요.
>
> 1. 현재 채널톡에서 **로그아웃**해 주세요.
> 2. 로그인 화면에서 **'구글 로그인' 버튼이 아닌**, 이메일 입력란에 기존 이메일 주소를 직접 입력하여 로그인해 주세요.
> 3. 로그인 후 좌측 하단 프로필 이미지 클릭 > **[계정 설정]** > **'로그인 계정'** 항목에서 원하시는 이메일로 변경해 주세요.
>
> ⚠️ **중요:** '구글 로그인' 버튼으로 다시 로그인하시면 구글 연동이 재설정되어 이메일 변경이 다시 불가능해집니다. 반드시 이메일을 직접 입력하는 방식으로 로그인해 주세요."
```

**Where do these details come from?**
- **내부 도구 경로, UI 경로**: `patterns_enriched.json` → `sample_conversations` → manager turns에서 추출
- **안내 멘트**: 실제 상담원이 보낸 메시지를 기반으로 재구성 (near-verbatim, not paraphrased)
- **조건 분기**: 대화에서 상담원이 "~인 경우", "~하셨다면" 등으로 분기한 패턴 추출
- **경고 문구**: 상담원이 "주의", "중요", "꼭" 등의 키워드와 함께 보낸 메시지에서 추출
- **빈도 데이터**: `patterns.json`의 cluster_size와 패턴 비율에서 계산

#### Enriched Data 미보유 시 (내부 도구 경로 등이 대화에 없는 경우)

대화 데이터에서 구체적인 내부 도구 경로나 어드민 URL이 발견되지 않는 경우:
- `{내부_도구_경로}` 같은 플레이스홀더를 사용하고 주석으로 표시: `<!-- TODO: 내부 어드민 경로 확인 필요 -->`
- 절대로 임의의 URL이나 경로를 지어내지 않는다
- 안내 멘트, 조건 분기, 경고 문구는 대화 데이터에서 항상 추출 가능하므로 반드시 포함한다

### 5. Write 톤앤매너 Section

Extract tone and manner from enriched data and write the section.

**Constraints:**
- You MUST use `tone_and_manner_samples` from `patterns_enriched.json` as the foundation
- You MUST include: 인사말, 공감 표현, 마무리 인사, 금지 표현
- You MUST use actual agent messages from the data, not generic templates
- You SHOULD include 금지 표현 with 대체 표현 pairs (table format)

**Process:**
1. Read `tone_and_manner_samples` for the topic's source clusters
2. Group by category: greeting, empathy, closing, proactive, informative
3. Select 2-3 best examples per category
4. Identify negative patterns from conversations (agent responses that caused re-inquiry or escalation)
5. Create 금지/대체 표현 pairs

### 6. Write 에스컬레이션 Section

**Constraints:**
- You MUST include an escalation table with: 상황, 에스컬레이션 대상, 전달 정보, 예상 응답 시간
- You MUST include 에스컬레이션 시 고객 안내 멘트 (from actual agent messages)
- You SHOULD include 에스컬레이션 요청 양식 (내부용) if internal tool paths are available
- Escalation targets MUST be extracted from actual conversations (not invented)

### 8. Save Agent SOP Documents

Write all SOP files to the output directory. Each SOP is a separate file.

**Constraints:**
- You MUST name files using the customer journey convention:
  - HT SOP: `HT_{여정단계}_{주제}.sop.md`
  - TS SOP: `TS_{여정단계}_{주제}.sop.md`
- You MUST use `.sop.md` extension (Agent SOP convention)
- You MUST save all generated SOPs to the same output directory
- You MUST use versioned directory if previous SOPs exist:
  - First run: `results/{company}/03_sop/`
  - Second run (if 03_sop/ exists): `results/{company}/03_sop_v2/`
  - Third run: `results/{company}/03_sop_v3/` (etc.)
- You MUST NOT overwrite existing SOP files — use versioned directory
- You SHOULD validate each SOP after saving
- You MUST create output directory if needed

**File Creation (multiple SOPs):**
```bash
# In Claude Code — save each SOP as a separate file
Write results/{company}/03_sop/HT_{topic1}.sop.md
Write results/{company}/03_sop/TS_{topic2}.sop.md
Write results/{company}/03_sop/HT_{topic3}.sop.md
# ... (약 10-15개 파일)
```

**Post-Save Validation (per file):**

**구조 체크:**
- [ ] 템플릿 섹션 모두 포함 (목적, 주의사항, 내용 or 문제해결프로세스, 톤앤매너, 에스컬레이션)
- [ ] Overview/Parameters/Steps/Examples 구조를 사용하지 않았는가
- [ ] 파일명이 내용을 잘 반영
- [ ] File size reasonable (100-500 lines per SOP)

**Case 품질 체크 (해결책 안내의 각 Case별):**
- [ ] Case 헤더에 정량적 빈도 포함 (e.g., "전체의 66.7%")
- [ ] `주요 상황` 서술이 고객 시나리오 기반인가 (not 기술적 원인 나열)
- [ ] 각 Step에 블록 인용(>) 형식의 안내 멘트가 있는가
- [ ] 안내 멘트가 3줄 이상이고 번호 매긴 절차를 포함하는가
- [ ] 내부 도구 경로 or `{placeholder}` + TODO 주석이 있는가
- [ ] UI 네비게이션 경로가 구체적인가 (e.g., "좌측 하단 > [설정]")
- [ ] 조건 분기(IF/THEN)가 최소 1개 있는가
- [ ] ⚠️ 경고/주의 문구가 해당되는 Case에 포함되어 있는가
- [ ] 완료 확인 Step이 있는가 ("~되셨나요?")
- [ ] Case 간 참조가 적절히 사용되었는가 (중복 방지)

**데이터 기반 체크:**
- [ ] 구체적인 내용이 enriched 대화에서 추출된 것인가 (임의 생성 아님)
- [ ] 톤앤매너의 예시가 실제 상담원 메시지 기반인가
- [ ] No placeholder text (e.g., "[TODO]", "[내용 추가]") — `{내부_도구_경로}` + TODO 주석은 허용

**Output Summary (완료 후 출력):**
```
✅ Stage 3 완료: {N}개 SOP 생성
저장 위치: results/{company}/03_sop/

생성된 파일:
  HT_구매후_바우처수신.sop.md
  HT_USIM배송_일반문의.sop.md
  TS_현지_데이터연결불량.sop.md
  ...
```

### 9. Generate Metadata

Create metadata file with SOP information.

**Constraints:**
- You MUST create `metadata.json` alongside SOP file
- You MUST include: version, generated date, source files, statistics
- You SHOULD include: author, review status, deployment target
- You MAY include: quality score, test results

**Metadata Structure:**
```json
{
  "sop_title": "Channel Corp. Customer Support Assistant",
  "company": "Channel Corp.",
  "version": "1.0.0",
  "generated_at": "2024-01-28T19:00:00Z",
  "last_updated_at": "2024-01-28T19:00:00Z",
  "generated_by": "Claude Sonnet 4.5 (Stage 3 Pipeline)",
  "source_files": [
    "results/{company}/01_clustering/{company}_clustered.xlsx",
    "results/{company}/01_clustering/{company}_tags.xlsx",
    "results/{company}/02_extraction/patterns.json",
    "results/{company}/02_extraction/faq.json"
  ],
  "statistics": {
    "total_clusters": 10,
    "patterns_extracted": 37,
    "faq_pairs": 52,
    "sop_steps": 5,
    "sop_examples": 3,
    "word_count": 4250
  },
  "coverage": {
    "inquiry_types": ["a_s_request", "delivery_inquiry", "product_question", "order_change", "complaint"],
    "top_categories": ["A/S", "배송", "일반_상담"],
    "automation_ready": ["delivery_inquiry", "product_question"]
  },
  "quality": {
    "rfc_2119_compliant": true,
    "all_sections_present": true,
    "examples_validated": true
  },
  "deployment": {
    "status": "ready",
    "target_platform": "Claude Skills / MCP Server",
    "review_required": true,
    "reviewer": "Customer Support Manager"
  },
  "notes": "Generated from 1,645 customer support chat records. Covers 5 major inquiry categories with 52 pre-built response templates."
}
```

**File Creation:**
```bash
Write results/{company}/03_sop/metadata.json
```

## Examples

### Example 1: SOP Generation (Channel Corp.)

**Input:**
- extraction_output_dir: `results/{company}/02_extraction`
- company: "Channel Corp."
- sop_title: "Channel Corp. Customer Support Assistant"
- sop_type: "customer_support"

**Execution Time**: ~5 minutes

**Output:**
- `03_sop/` 디렉토리에 10-15개 SOP 파일
- `metadata.json`

### Example 2: Concise Troubleshooting SOP (Channel Corp.)

**Input:**
- extraction_output_dir: `results/{company}/02_extraction`
- company: "Channel Corp."
- sop_title: "Channel Corp. Hardware Troubleshooting Guide"
- sop_type: "troubleshooting"
- detail_level: "concise"

**Execution Time**: ~3-4 minutes

**Output:**
- `{company}_troubleshooting.sop.md` (600 lines)
- Focus on A/S and technical issues only
- Minimal examples, core workflows only

## Output Format

### File 1: `{company}_support.sop.md`

SOP document following HT/TS template structure.

**TS SOP Structure (문제 해결):**
```markdown
# {SOP Title}

## 메타데이터
| 항목 | 내용 |
|------|------|
| SOP ID | {ID} |
| 분류 | {분류} |
...

## 1. 목적
## 2. 주의사항
## 3. 문제 해결 프로세스
### 3-1. 처리 흐름 개요
### 3-2. 문제 상황 확인
### 3-3. 해결책 안내
#### Case 1: {시나리오} (빈도: 높음 — 전체의 XX%)
  **Step 1~N** with 블록 인용 안내 멘트, 내부 도구 경로, 조건 분기, 완료 확인
#### Case 2: ...
## 4. 톤앤매너
## 5. 해결이 안되면 (에스컬레이션)
## 6. 관련 SOP
## 7. 데이터 분석 정보
```

**HT SOP Structure (정보 안내):**
```markdown
# {SOP Title}

## 메타데이터
## 1. 목적
## 2. 주의사항
## 3. 내용
### (주제별 Case 구조 — 동일한 디테일 요구사항 적용)
## 4. 톤앤매너
## 5. 해결이 안되면 (에스컬레이션)
## 6. 관련 SOP
## 7. 데이터 분석 정보
```

### File 2: `metadata.json`

SOP metadata and statistics.

**Fields:**
- sop_title, company, version
- generated_at, generated_by
- source_files
- statistics (clusters, patterns, FAQ count, steps, examples)
- coverage (inquiry types, categories, automation ready)
- quality (RFC compliance, section completeness)
- deployment (status, target platform, review status)

## Troubleshooting

### Issue 1: Generated SOP Cases are too generic

**Symptom**: Cases lack specificity — "내부 어드민에서 확인", no UI paths, no concrete agent messages

**Solution:**
- Re-read `patterns_enriched.json` → `sample_conversations` → manager turns
- Extract actual URLs, UI paths, agent response templates from the conversations
- If not found in data, use `{placeholder}` + `<!-- TODO -->` — never invent details

### Issue 2: Cases use "주요 원인" instead of "주요 상황"

**Symptom**: Case descriptions list technical causes rather than customer scenarios

**Solution:**
- Rewrite from customer's perspective: "고객이 [X]를 하려 하나, [Y] 상태라 [Z]가 불가한 경우"
- Extract customer expressions from user turns in enriched data
- Technical causes go into the Step's internal notes, not the Case header

### Issue 3: Missing validation steps and conditional branches

**Symptom**: Cases are linear (Step 1 → 2 → 3 → done) without confirmation or branching

**Solution:**
- Add "완료 확인" step after each major action: "~되셨나요?"
- Add conditional branches: "안 되는 경우 → [다른 조치]" or "→ Step N부터 다시 진행"
- Add ⚠️ warnings where re-occurrence is likely (e.g., 재연동, 재발 가능성)

## Related Documentation

- **Agent SOP Format**: `rules/agent-sop-format.md`
- **HT/TS Templates**: `templates/HT_template.md`, `templates/TS_template.md` (SOP structure reference)
- **Stage 2**: `agent-sops/stage2-extraction.sop.md` (Prerequisite)
- **RFC 2119**: https://datatracker.ietf.org/doc/html/rfc2119

## Notes

### RFC 2119 Keywords

Use these keywords correctly in Constraints:

- **MUST** / **MUST NOT**: Absolute requirement or prohibition
- **SHOULD** / **SHOULD NOT**: Recommended but not required
- **MAY**: Optional, at discretion

**Example:**
```
**Constraints:**
- You MUST verify warranty before promising free repair (business critical)
- You SHOULD check customer history before responding (best practice)
- You MAY offer related product suggestions (optional enhancement)
- You MUST NOT promise specific repair timeframes (liability risk)
```

### SOP Reusability

The generated SOP should be reusable across:
- Different customer support agents (human)
- AI assistants (Claude Skills, MCP tools)
- Chatbots and automated systems
- Multi-channel support (chat, email, phone)

**Design for reusability:**
- Use parameterized workflows (not hardcoded values)
- Provide clear decision logic (IF/THEN)
- Include examples for common scenarios
- Document edge cases in Troubleshooting

### Execution Strategy

**메인 에이전트에서 순차 처리 (권장)**

재료(patterns, FAQ)가 이미 준비되어 있으므로, subagent 병렬 처리와 순차 처리의 시간 차이가 거의 없습니다. 순차 처리가 더 안정적이고 디버깅이 쉽습니다.

**Critical Constraints:**
- You MUST generate SOP documents using **LLM (Claude)** directly
- You MUST NOT use Python scripts to auto-generate SOP files
- You MUST NOT use automated template generators or boilerplate tools
- You MUST write each SOP through natural language composition
- You SHOULD process each SOP sequentially in main agent
- You MAY use subagent if needed, but sequential processing is preferred

**Why No Python Auto-generation:**
- ❌ Python cannot understand nuanced customer expressions
- ❌ Template-based generation produces generic, low-quality SOPs
- ✅ LLM composition ensures context-aware, company-specific content
- ✅ Natural language understanding captures tone and intent

**Recommended Approach:**
1. **순차 SOP 생성** - 메인 에이전트에서 하나씩 생성
2. **LLM 직접 작성** - Python 스크립트 없이 Claude가 직접 작성
3. **재료 활용** - patterns_enriched.json, faq.json에서 내용 추출
4. 각 SOP 완료 후 파일 저장 → 다음 SOP 진행

**Efficiency Tips:**
1. ✅ patterns_enriched.json 사용 (clustered.xlsx 재로드 불필요)
2. ✅ 순차 처리로 안정성 확보
3. ❌ Python 자동 생성 스크립트 사용 금지
4. 시간 차이 거의 없음 (재료가 준비되어 있으므로)

### Quality Checklist

Before finalizing each SOP:
- [ ] All patterns from extraction are covered in Cases
- [ ] FAQ answers are incorporated into Step 안내 멘트
- [ ] Response strategies reflected in 톤앤매너 section
- [ ] Escalation rules clearly defined with table format
- [ ] Each Case passes the 9-point Case Quality Requirements (Step 4)
- [ ] 안내 멘트 are based on actual agent messages (not generic)
- [ ] Text is natural and professional in the detected language
- [ ] No company-specific secrets or PII exposed
- [ ] Template structure followed (HT or TS) — no Overview/Parameters/Steps/Examples
- [ ] All sections complete (no empty TODOs except allowed `{placeholder}` patterns)

### Deployment Readiness

After SOP generation:
1. **Review**: Customer support manager validates accuracy
2. **Test**: Pilot with small team, collect feedback
3. **Refine**: Update based on testing results
4. **Deploy**: Roll out via Claude Skills, MCP server, or training docs
5. **Monitor**: Track usage metrics, identify gaps
6. **Iterate**: Update SOP based on new patterns (quarterly)

**Metrics to Track:**
- First-contact resolution rate
- Average response time
- Escalation rate
- Customer satisfaction score
- Agent feedback on SOP usability
