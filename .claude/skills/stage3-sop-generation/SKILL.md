---
name: stage3-sop-generation
description: This SOP guides the generation of a production-ready Agent SOP document from extracted patterns and FAQs. This is **Stage 3** (final stage) of the Excel-to-SOP pipeline, performed entirely by the AI agent using natural language composition.  **Language:** All user interactions MUST be conducted in Korean (한국어). Questions, confirmations, and outputs should be in Korean unless the user explicitly requests English.  **Stage Flow:** - **Input**: Stage 2 extraction results (JSON files with patterns, FAQs, strategies) - **Process**: LLM composition of Agent SOP following standard format - **Output**: Agent SOP document (.sop.md) ready for deployment  **Key Capabilities:** - Generate Agent SOP in standardized format (RFC 2119 compliant) - Transform extracted patterns into parameterized workflows - Create constraint-based steps with MUST/SHOULD/MAY keywords - Include examples and troubleshooting sections - Ensure reusability across different customer support scenarios
type: anthropic-skill
version: "1.0"
---

# Stage 3: Agent SOP Generation

## Overview
This SOP guides the generation of a production-ready Agent SOP document from extracted patterns and FAQs. This is **Stage 3** (final stage) of the Excel-to-SOP pipeline, performed entirely by the AI agent using natural language composition.

**Language:** All user interactions MUST be conducted in Korean (한국어). Questions, confirmations, and outputs should be in Korean unless the user explicitly requests English.

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
- **mode** (default: "standard"): SOP generation depth mode
  - `"quick"`: Concise SOP (~500 lines), all standard sections
  - `"standard"`: Balanced SOP (~1000 lines), all standard sections (default)
  - `"deep"`: Comprehensive SOP (~2000 lines), full detail with extensive examples

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
- You MUST read all JSON files from Stage 2:
  1. `patterns.json`: All patterns per cluster
  2. `faq.json`: FAQ pairs
  3. `response_strategies.json`: Response strategies and escalation rules
  4. `keywords.json`: Keyword taxonomy
  5. `extraction_summary.md`: Summary and automation opportunities
- You SHOULD read enriched patterns if available (recommended):
  6. `patterns_enriched.json`: Patterns with embedded conversation samples (from Stage 2 Step 7)
  - Contains 10 representative conversations per cluster
  - Contains 20 tone-and-manner samples per cluster
  - If this file exists, use it instead of clustered.xlsx
- You MAY fallback to Stage 1 clustered data if patterns_enriched.json doesn't exist:
  6b. `{company}_clustered.xlsx`: Full dataset with cluster assignments (from Stage 1 output)
  - Read 10 sample conversations per cluster for realistic examples
- You MUST verify JSON structure is valid
- You MUST generate SOP for EVERY cluster in patterns.json (do NOT select only "representative" clusters)
- You MUST create one SOP file per cluster (total = number of clusters)
- You SHOULD identify which patterns will become SOP steps
- You SHOULD group related patterns for workflow design
- You MAY skip low-frequency patterns within a cluster (< 2% of cluster), but NOT the cluster itself

**Reading Process:**
```bash
# In Claude Code - Stage 2 outputs
Read results/{company}/02_extraction/patterns.json
Read results/{company}/02_extraction/faq.json
Read results/{company}/02_extraction/response_strategies.json
Read results/{company}/02_extraction/keywords.json
Read results/{company}/02_extraction/extraction_summary.md

# RECOMMENDED: Stage 2 enriched patterns (if available)
Read results/{company}/02_extraction/patterns_enriched.json  # 샘플 이미 포함됨 (권장)

# FALLBACK: Stage 1 output (if patterns_enriched.json doesn't exist)
# Read results/{company}/{company}_clustered.xlsx  # 클러스터별 샘플 직접 추출
```

**Analysis Checklist:**
- [ ] How many distinct inquiry types? (will become Parameters)
- [ ] What are common workflows? (will become Steps)
- [ ] Which patterns need escalation? (will become Constraints)
- [ ] What automation opportunities exist? (will inform Step design)
- [ ] Are there industry-specific terms? (will need definitions)

### 2. Design SOP Structure

Plan the Agent SOP structure based on extracted patterns.

**Constraints:**
- You MUST follow the Agent SOP format standard (see `rules/agent-sop-format.md`)
- You MUST include sections: Overview, Parameters, Steps, Examples
- You SHOULD include Troubleshooting section if multiple failure modes exist
- You SHOULD design Parameters that cover all major inquiry types
- You MAY merge similar patterns into single parameterized Steps
- You MUST ensure Steps flow logically (inquiry → analysis → response)

**SOP Structure Template:**
```markdown
# {sop_title}

## Overview
[What this SOP does, when to use it, key features]

## Parameters
### Required
- **inquiry_type**: Type of customer inquiry
- **customer_tier**: Customer service level (if applicable)

### Optional
- **escalation_needed**: Pre-identified escalation flag
- **language**: Response language (default: Korean)

## Steps
### 1. Classify Inquiry
[Identify inquiry type using keywords]

### 2. [Pattern-Based Step]
[Handle specific pattern, e.g., "Check Warranty Status"]

### 3. Provide Response
[Generate appropriate response based on inquiry type]

### 4. Escalate if Needed
[Escalation logic]

## Examples
[Concrete usage scenarios]

## Troubleshooting
[Common issues and solutions]
```

**Design Decisions:**

1. **Parameters vs. Dynamic Classification:**
   - If 5-10 clear inquiry types: Use `inquiry_type` parameter
   - If 20+ overlapping types: Use keyword-based dynamic classification in Step 1

2. **Step Granularity:**
   - Group related patterns: "충전_AS", "배터리_AS" → "Handle A/S Inquiries"
   - Keep complex processes separate: "배송_조회" as standalone step

3. **Constraint Levels:**
   - MUST: Critical business rules (warranty verification, PII handling)
   - SHOULD: Best practices (check history first)
   - MAY: Optional enhancements (offer related products)

### 3. Write Overview Section

Create a clear, concise overview of the SOP's purpose and capabilities.

**Mode-Specific Behavior:**
- **Quick Mode**: Brief overview (50-100 words), essential info only
- **Standard Mode**: Standard overview (100-200 words) with key features
- **Deep Mode**: Comprehensive overview (200-300 words) with detailed context and benefits

**Constraints:**
- You MUST describe what the SOP accomplishes
- You MUST specify when to use this SOP
- You MUST adjust length and detail based on mode
- You SHOULD list key features or capabilities (3-5 bullets)
- You SHOULD mention the company and industry context
- You MAY include expected outcomes or benefits

**Overview Template:**
```markdown
## Overview
This SOP guides {company} customer support agents in handling customer inquiries
across {N} major categories: {categories}. It provides step-by-step workflows for
common inquiry types, automated response generation, and escalation rules.

**Use Cases:**
- Handling customer inquiries via chat, email, or phone
- Providing product information and troubleshooting
- Processing A/S requests and tracking status
- Managing order and delivery inquiries

**Key Features:**
- Keyword-based inquiry classification
- Pattern-matched response templates
- Escalation triggers for complex cases
- Integration with {systems} (e.g., AS system, order tracking)

**Expected Outcomes:**
- Reduced response time (target: <2 minutes for common inquiries)
- Consistent response quality across agents
- Higher first-contact resolution rate (target: >80%)
```

**Example (Channel Corp.):**
```markdown
## Overview
This SOP guides Channel Corp. customer support agents in handling customer inquiries
for consumer electronic products. It covers
5 major categories: A/S (48%), General Inquiries (19%), Delivery (12%),
Order Management (10%), and System Issues (10%).

**Use Cases:**
- Responding to customer chat inquiries (primary channel)
- Handling product questions, troubleshooting, and A/S requests
- Processing order changes, returns, and delivery tracking
- Escalating complex technical or policy issues

**Key Features:**
- Automated inquiry classification using keyword matching
- Pre-built response templates for 52 common inquiry patterns
- Decision trees for A/S troubleshooting (charging, defects)
- Escalation rules to specialized teams (AS center, logistics)

**Expected Outcomes:**
- <2 min response time for 80% of inquiries
- >85% first-contact resolution for common patterns
- Consistent brand voice and service quality
```

### 4. Define Parameters

Define SOP parameters that control workflow behavior.

**Constraints:**
- You MUST include at least one Required parameter
- You MUST define `inquiry_type` parameter if <15 distinct types
- You SHOULD include `customer_tier` if service levels exist
- You SHOULD use enums for categorical parameters
- You MAY include optional parameters for advanced features
- You MUST provide clear descriptions and examples for each parameter

**Parameter Types:**

1. **inquiry_type** (if applicable):
```markdown
### Required
- **inquiry_type** (required): Type of customer inquiry
  - Format: enum
  - Values: `a_s_request`, `delivery_inquiry`, `product_question`, `order_change`, `complaint`
  - Example: `a_s_request`
  - Description: Determines which workflow path to follow
```

2. **customer_tier** (if service levels exist):
```markdown
- **customer_tier** (optional, default: "standard"): Customer service level
  - Format: enum
  - Values: `standard`, `premium`, `vip`
  - Example: `premium`
  - Description: Affects response priority and escalation rules
```

3. **Dynamic Classification Alternative** (if too many types):
```markdown
### Required
- **customer_message** (required): Customer's inquiry message
  - Format: string
  - Example: "충전이 안 되는데 어떻게 해야 하나요?"
  - Description: Full customer message for keyword-based classification

### Optional
- **customer_history** (optional): Previous interaction history
  - Format: array of messages
  - Example: `["3개월 전 AS 접수", "충전기 교체 완료"]`
  - Description: Used to provide context-aware responses
```

**Parameter Selection Guide:**
- **Few clear types (5-10)**: Use `inquiry_type` enum
- **Many types (15+)**: Use `customer_message` with dynamic classification
- **Service tiers**: Always include `customer_tier`
- **Multi-language**: Include `language` parameter

### 5. Write Step-by-Step Workflow

Create detailed steps using extracted patterns and response strategies.

**Constraints:**
- You MUST include at least 3 steps
- You MUST use RFC 2119 keywords (MUST, SHOULD, MAY, MUST NOT)
- You MUST write each step with clear sub-tasks
- You SHOULD include decision logic (IF/THEN) where applicable
- You SHOULD reference FAQ answers in response steps
- You MAY include code snippets or pseudo-code for complex logic
- You MUST ensure steps flow logically (classify → analyze → respond → escalate)
- **For Troubleshooting (TS) workflows**: You MUST follow the **비파괴적 순서 (Non-Destructive Order)** principle
  - Order troubleshooting steps from least to most invasive (최소 침습 → 최대 침습)
  - Minimize data loss risk and action scope at each step
  - Include "✅ 해결되었는지 확인" checkpoint after each troubleshooting step
  - Example order: Connection check → Refresh → Update → Restart app → Restart device → Reinstall
  - Reference: See `templates/TS_template.md` for detailed guidance

**Step Structure Template:**
```markdown
### {N}. {Step Title}

{Brief description of what this step accomplishes}

**Constraints:**
- You MUST {critical requirement}
- You SHOULD {recommended practice}
- You MAY {optional enhancement}
- You MUST NOT {prohibited action}

**Process:**
1. {Sub-task 1}
2. {Sub-task 2}
   - IF {condition}: {action}
   - ELSE: {alternative action}
3. {Sub-task 3}

**Tools Required:**
- {Tool 1}
- {Tool 2}

**Expected Output:**
{What this step produces}
```

**Example Steps (Channel Corp. Customer Support):**

```markdown
## Steps

### 1. Classify Inquiry Type

Analyze the customer message to determine inquiry type using keyword matching.

**Constraints:**
- You MUST scan the message for keywords from `keywords.json` taxonomy
- You SHOULD check multiple keyword categories (A/S, 배송, 제품)
- You SHOULD assign primary and secondary types if multiple matches
- You MAY use customer history to disambiguate unclear inquiries
- You MUST assign "general_inquiry" if no keywords match

**Process:**
1. Extract keywords from customer message (Korean NLP or simple matching)
2. Match against keyword taxonomy:
   - A/S keywords: 충전, 수리, 고장, AS, 교체 → `a_s_request`
   - 배송 keywords: 배송, 조회, 송장, 언제도착 → `delivery_inquiry`
   - 제품 keywords: 사용법, 스펙, 기능, 구매 → `product_question`
   - 주문 keywords: 취소, 변경, 반품, 주소 → `order_change`
3. Assign inquiry_type based on highest keyword match score
4. Flag `escalation_needed = true` if keywords include: 환불, 불만, 화남, 법적조치

**Tools Required:**
- Keyword taxonomy from `keywords.json`
- (Optional) Korean tokenizer for better keyword extraction

**Expected Output:**
- `inquiry_type`: one of [a_s_request, delivery_inquiry, product_question, order_change, complaint]
- `matched_keywords`: list of matched keywords
- `confidence`: high/medium/low

---

### 2. Handle A/S Requests

Process A/S (after-sales service) inquiries using troubleshooting patterns.

**Constraints:**
- You MUST execute this step only if `inquiry_type == a_s_request`
- You MUST determine A/S sub-type: 충전, 수리, 교체
- You MUST provide troubleshooting steps before escalating to AS center
- You SHOULD check warranty status if customer provides purchase date
- You MAY offer immediate replacement if within 7-day exchange period
- You MUST NOT promise repair time without checking AS center capacity

**Process:**
1. Determine A/S sub-type from keywords:
   - 충전 keywords → Charging issue workflow
   - 고장, 작동안함 → General defect workflow
   - 교체, 새제품 → Replacement workflow

2. **IF charging issue (비파괴적 순서):**
   a. Provide troubleshooting steps (from FAQ faq_2_1):
      - Step 1: Check cable and adapter connection → ✅ Ask customer to test and report
      - Step 2: Clean charging port → ✅ Ask customer to test and report
      - Step 3: Test with different cable → ✅ Ask customer to test and report
   b. After each step, ask customer to confirm if issue is resolved
   c. IF still failing after all steps → Escalate to AS center
   d. **Important**: Follow non-destructive order (최소 침습 → 최대 침습)

3. **IF general defect:**
   a. Ask for symptom details (noise, no power, etc.)
   b. Check warranty status:
      - IF <1 year: Offer free repair
      - IF >1 year: Inform of paid repair (10,000 KRW)
   c. Escalate to AS center for inspection

4. **IF replacement request:**
   a. Check purchase date:
      - IF <7 days: Direct exchange via customer center
      - IF 7-30 days: AS center inspection required
      - IF >30 days: Repair only (no replacement)
   b. Provide escalation contact info

**Tools Required:**
- FAQ database (faq.json)
- Warranty lookup system (customer purchase history)
- AS center contact info (1234-5678)

**Expected Output:**
- Troubleshooting guidance provided (charging checklist, symptom questions)
- Warranty status confirmed
- Escalation initiated if needed

---

### 3. Handle Delivery Inquiries

Provide delivery tracking information and resolve delivery issues.

**Constraints:**
- You MUST execute this step only if `inquiry_type == delivery_inquiry`
- You MUST retrieve tracking number from order system
- You SHOULD provide estimated delivery date if order is recent
- You MAY automate this entirely with tracking link
- You MUST escalate to logistics team if delivery is delayed >3 days

**Process:**
1. Retrieve order ID from customer (ask if not provided)
2. Look up tracking information in order system
3. Provide response based on delivery status:
   - **Shipped**: "운송장 번호는 {tracking_no}입니다. [조회 링크]로 확인하세요. 예상 도착: {eta}"
   - **Preparing**: "상품 준비 중입니다. {expected_ship_date}에 발송 예정입니다."
   - **Delivered**: "배송 완료되었습니다 ({delivery_date}). 수령하지 못하셨다면 배송 기사에게 연락하세요."
   - **Delayed**: Escalate to logistics team

**Tools Required:**
- Order management system
- Carrier tracking API (CJ, 로젠, 우체국)

**Expected Output:**
- Tracking number and link provided
- Delivery status and ETA communicated
- Escalation if delayed

---

### 4. Provide Response

Generate appropriate response using pattern-matched templates.

**Constraints:**
- You MUST use response strategy from `response_strategies.json` for the inquiry type
- You MUST personalize response with customer name (if available)
- You SHOULD use friendly, professional Korean tone
- You SHOULD include next steps or follow-up actions
- You MAY offer related information (FAQs, product links)
- You MUST NOT use overly formal or robotic language

**Process:**
1. Load response template for inquiry type from `response_strategies.json`
2. Fill in placeholders:
   - `[고객명]` → customer name or "고객님"
   - `[제품명]` → product name from order history
   - `[AS센터 번호]` → 1234-5678
   - `[예상기간]` → estimated timeframe (3-5일, etc.)
3. Add empathy statement if complaint or frustration detected
4. Include call-to-action or next steps
5. Append signature: "감사합니다. Channel Corp. 고객센터"

**Example Response (Charging A/S):**
```
안녕하세요, [고객명]님!

충전 문제로 불편을 드려 죄송합니다. 다음 단계를 먼저 확인해주세요:

1. 케이블과 어댑터가 제품과 전원에 제대로 연결되었는지 확인
2. 충전 포트에 이물질이나 먼지가 없는지 확인
3. 가능하면 다른 케이블로 교체 테스트

위 단계를 시도하신 후에도 문제가 계속되면 AS 접수를 도와드리겠습니다.
AS 센터: 1234-5678 (평일 09:00-18:00)

추가 문의 사항이 있으시면 언제든지 말씀해주세요.
감사합니다.

Channel Corp. 고객센터
```

**Expected Output:**
- Complete, ready-to-send response message in Korean
- Personalized with customer and product details
- Includes actionable next steps

---

### 5. Escalate if Needed

Escalate to specialized teams when required.

**Constraints:**
- You MUST escalate if `escalation_triggers` from response strategy are met
- You MUST provide customer with escalation target contact info
- You MUST log escalation in CRM system
- You SHOULD set escalation priority based on customer tier and urgency
- You SHOULD provide customer with expected response time
- You MUST NOT close conversation until escalation is confirmed

**Escalation Triggers** (from `response_strategies.json`):
1. Customer attempted troubleshooting 3+ times
2. Warranty verification required
3. Delivery delayed >3 days
4. Customer uses complaint keywords (환불, 불만, 법적)
5. Technical issue beyond first-line support

**Process:**
1. Identify escalation target:
   - A/S issues → AS Center (1234-5678)
   - Delivery issues → Logistics team (internal)
   - Complaints → Customer service manager
   - Technical issues → Product team
2. Create escalation ticket in CRM
3. Provide customer with:
   - Escalation target contact info
   - Ticket number
   - Expected response time (AS: 1-2일, Complaints: 24시간)
4. Set follow-up reminder
5. Confirm escalation: "담당 팀에 전달했습니다. {expected_time} 내로 연락드리겠습니다."

**Expected Output:**
- Escalation ticket created
- Customer notified with ticket number and timeline
- Follow-up scheduled
```

### 6. Create Examples Section

Write concrete usage examples demonstrating the SOP in action.

**Mode-Specific Behavior:**
- **Quick Mode**: 1-2 basic examples only
- **Standard Mode**: 2-3 examples covering main scenarios (default)
- **Deep Mode**: 4-5 examples including edge cases and anti-examples

**Constraints:**
- You MUST adjust example count based on mode
- You MUST use realistic customer messages (from clustered.xlsx samples)
- You SHOULD cover different inquiry types
- You SHOULD show both simple and complex scenarios
- You MAY include "anti-examples" (what NOT to do) in Deep Mode
- You MUST format examples clearly with Input → Process → Output structure

**Example Structure:**
```markdown
## Examples

### Example 1: {Scenario Name}

**Scenario**: {Brief description}

**Input:**
- inquiry_type: {type}
- customer_message: "{actual customer message}"
- customer_tier: {tier}

**Process:**
1. [Step 1] {What happens}
2. [Step 2] {What happens}
3. [Step 3] {What happens}

**Output:**
```
{Final response to customer}
```

**Notes**: {Any special considerations or learnings}
```

**Example 1:**
```markdown
### Example 1: Charging Issue with Troubleshooting

**Scenario**: Customer reports charging problem for electronic product.

**Input:**
- customer_message: "충전이 안 되는데 어떻게 해야 하나요?"
- customer_tier: "standard"

**Process:**
1. [Classify Inquiry] Matched keywords: ["충전"] → inquiry_type = `a_s_request`
2. [Handle A/S] Sub-type: charging issue
   - Provide troubleshooting checklist (FAQ faq_2_1)
3. [Provide Response] Use charging troubleshooting template

**Output:**
```
안녕하세요, 고객님!

충전 문제로 불편을 드려 죄송합니다. 다음 단계를 먼저 확인해주세요:

1. 케이블과 어댑터가 제품과 전원에 제대로 연결되었는지 확인
2. 충전 포트에 이물질이나 먼지가 없는지 확인
3. 가능하면 다른 케이블로 교체 테스트

위 단계를 시도하신 후에도 문제가 계속되면 AS 접수를 도와드리겠습니다.
AS 센터: 1234-5678 (평일 09:00-18:00)

감사합니다.
Channel Corp. 고객센터
```

**Notes**: Most charging issues are resolved at Step 2 (troubleshooting). Only ~20% escalate to AS center.
```

### 7. Add Troubleshooting Section

Document common issues and failure modes.

**Mode-Specific Behavior:**
- **Quick Mode**: SKIP troubleshooting section or include 1-2 critical issues only
- **Standard Mode**: Include 3-4 common issues with solutions (default)
- **Deep Mode**: Comprehensive troubleshooting with 5+ issues, prevention tips, and external references

**Constraints:**
- You MUST adjust based on mode (see above)
- You MUST include troubleshooting section in Standard/Deep modes if SOP has >3 potential failure points
- You SHOULD document issues encountered during testing or known edge cases
- You SHOULD provide clear solutions or workarounds
- You MAY reference external documentation
- You MUST format as Issue → Cause → Solution

**Troubleshooting Template:**
```markdown
## Troubleshooting

### Issue 1: {Issue Title}

**Symptom**: {What the user observes}

**Cause**: {Why this happens}

**Solution**:
1. {Step 1}
2. {Step 2}

**Prevention**: {How to avoid this issue}

---

### Issue 2: Cannot Classify Inquiry

**Symptom**: Step 1 classification returns "general_inquiry" for all messages

**Cause**: Customer message has no keywords matching the taxonomy

**Solution**:
1. Manually review message for intent
2. Use semantic search or LLM classification as fallback
3. Ask clarifying question: "AS, 배송, 또는 제품 문의 중 어느 것과 관련이 있나요?"

**Prevention**: Expand keyword taxonomy with more synonyms and variations
```

### 8. Save Agent SOP Document

Write the complete SOP to a markdown file.

**Constraints:**
- You MUST save as `{company}_support.sop.md`
- You MUST use `.sop.md` extension (Agent SOP convention)
- You MUST include all required sections (Overview, Parameters, Steps)
- You SHOULD validate RFC 2119 keyword usage (MUST, SHOULD, MAY)
- You SHOULD review for clarity and consistency
- You MUST create output directory if needed
- You MUST NOT overwrite existing SOP without confirmation

**File Creation:**
```bash
# In Claude Code
Write results/{company}/03_sop/{company}_support.sop.md
```

**Post-Save Validation:**
- [ ] All sections present (Overview, Parameters, Steps, Examples)
- [ ] RFC 2119 keywords used correctly
- [ ] No placeholder text (e.g., "[TODO]", "[Fill in]")
- [ ] Korean text is natural and professional
- [ ] Examples are concrete and realistic
- [ ] File size reasonable (500-2000 lines)

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

### Example 1: Standard SOP Generation (Channel Corp.)

**Input:**
- extraction_output_dir: `results/{company}/02_extraction`
- company: "Channel Corp."
- sop_title: "Channel Corp. Customer Support Assistant"
- sop_type: "customer_support"
- detail_level: "standard"

**Execution Time**: ~5 minutes

**Output:**
- `{company}_support.sop.md` (1,200 lines)
- `metadata.json`

**SOP Statistics:**
- Steps: 5
- Examples: 3
- Troubleshooting Issues: 4
- Total word count: ~4,000

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

Complete Agent SOP following standardized format.

**Structure:**
```markdown
# {SOP Title}

## Overview
[150-200 words]

## Parameters
### Required
- parameter1: description
### Optional
- parameter2: description

## Steps
### 1. Step Title
...

## Examples
### Example 1: ...
### Example 2: ...

## Troubleshooting
### Issue 1: ...

## Related Documentation
[Links to related docs]

## Notes
[Additional information]
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

### Issue 1: Generated SOP is too generic

**Symptom**: Steps lack specificity, could apply to any company

**Solution:**
- Include more company-specific details from extraction
- Use actual product names, contact numbers, internal systems
- Reference specific policies (warranty periods, refund rules)
- Incorporate brand voice from sample messages

### Issue 2: Steps are too granular

**Symptom**: 15+ steps, overwhelming to follow

**Solution:**
- Group related sub-tasks under fewer main steps (aim for 5-7)
- Use sub-sections within steps for detail
- Move edge cases to Troubleshooting section
- Consider splitting into multiple SOPs (e.g., A/S SOP, Delivery SOP)

### Issue 3: Parameters don't match workflow

**Symptom**: Steps don't reference defined parameters

**Solution:**
- Review Step 5 constraints: ensure steps check parameter values
- Add conditional logic: "IF inquiry_type == X, THEN..."
- Remove unused parameters
- Add missing parameters referenced in steps

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

Before finalizing SOP:
- [ ] All patterns from extraction are covered
- [ ] FAQ answers are incorporated into response templates
- [ ] Response strategies map to Steps
- [ ] Escalation rules are clearly defined
- [ ] Examples use real customer messages
- [ ] Korean text is natural and professional
- [ ] No company-specific secrets or PII exposed
- [ ] RFC 2119 keywords used correctly
- [ ] All sections are complete (no TODOs)
- [ ] Metadata is accurate

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
