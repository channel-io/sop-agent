---
name: bot-analysis
description: Analyze existing bot performance in customer support data. Preprocesses Excel chat data via Python script to classify bot conversations as resolved/unresolved, then generates a comprehensive bot performance report with topic-level insights. **Language:** Auto-detects Korean (한국어) or Japanese (日本語) from user input.
---

# Bot Performance Analysis

## Overview

Analyzes the existing bot's performance in customer support chat data. Identifies which topics the bot handles well vs. poorly by classifying conversations as resolved (bot-only) or unresolved (handed off to manager with 2+ manager turns).

**Pipeline:**
```
Excel Input (고객 상담 데이터)
  ↓
Step 1: Parameter gathering (input file, company, clustering results)
  ↓
Step 2: Python preprocessing (scripts/analyze_bot.py)
  → bot_classified.xlsx    (전체 분류 데이터)
  → bot_resolved.xlsx      (Bot 해결 건)
  → bot_unresolved.xlsx    (Bot 미해결 건)
  → bot_analysis_summary.json (통계 요약)
  ↓
Step 3: Agent analysis — topic-level bot performance report
  → bot_performance_report.md
```

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

## Parameters

- **input_file** (required): Path to Excel file containing UserChat and Message data sheets
- **output_dir** (required): Output directory for bot analysis results
- **company** (required): Company name for context and file naming
- **clustered_path** (optional): Path to Stage 1 clustered Excel for topic mapping (e.g., `results/{company}/01_clustering/{company}_clustered.xlsx`)
- **tags_path** (optional): Path to Stage 1 tags Excel (e.g., `results/{company}/01_clustering/{company}_tags.xlsx`)
- **threshold** (optional, default: 2): Minimum manager turns after bot to classify as "unresolved"

**Constraints for parameter acquisition:**
- You MUST scan `data/` directory for Excel files and auto-select if only one exists
- You MUST extract company name from filename (e.g., "구하다 상담데이터 raw 90일_.xlsx" → "guhada")
- You MUST auto-detect clustering results at `results/{company}/01_clustering/` if they exist
- You MUST auto-set output_dir to `results/{company}/bot_analysis` unless user specifies otherwise
- You MUST NOT ask the user about threshold or other optional parameters — use defaults
- You SHOULD only ask the user to confirm input_file and company name if ambiguous (multiple files)

## Steps

### 1. Gather Parameters and Setup

Scan available files and detect clustering results.

**Constraints:**
- You MUST scan `data/` directory for Excel files: `ls -lh data/*.xlsx`
- You MUST check if Stage 1 clustering results exist: `ls results/{company}/01_clustering/`
- If clustering results exist, you MUST use them for topic mapping (set `--clustered` and `--tags`)
- You MUST create output directory: `mkdir -p {output_dir}`
- You MUST NOT proceed if input file doesn't exist

**Expected Output:**
```
✅ 파라미터 수집 완료:
  - 입력 파일: data/구하다 상담데이터 raw 90일_.xlsx
  - 출력 경로: results/guhada/bot_analysis
  - 회사명: guhada
  - 클러스터 태그: results/guhada/01_clustering/guhada_clustered.xlsx ✅
  - Manager 전환 기준: 2턴
```

### 2. Execute Bot Classification Script

Run the Python preprocessing script to classify all conversations.

**Constraints:**
- You MUST execute the bot analysis script:
  ```bash
  python3 scripts/analyze_bot.py \
    --input {input_file} \
    --output {output_dir} \
    --company {company} \
    --clustered {clustered_path} \
    --tags {tags_path} \
    --threshold {threshold}
  ```
- Omit `--clustered` and `--tags` flags if clustering results don't exist
- You MUST capture and display all output from the script
- You MUST detect and report errors immediately if script fails
- You MUST NOT proceed to next step if classification fails
- You MUST verify output files exist after script completes

**Expected Output:**
```
Bot Performance Analyzer — guhada
============================================================
[1/4] 데이터 로딩...
[2/4] 대화 분류 중...
   📊 분류 결과:
   ├─ Bot 참여 대화: 857건 (98.5%)
   │  └─ Bot 해결: 573건
   │  └─ Bot 미해결 (→Manager): 284건
   └─ Bot 해결률: 66.9%
[3/4] 클러스터 태그 매핑 중...
[4/4] 결과 저장 중...
✅ Bot 분석 완료
```

### 3. Generate Bot Performance Report

Read the preprocessed data and generate a comprehensive analysis report.

**Constraints:**
- You MUST read `bot_analysis_summary.json` for overall statistics
- You MUST read `bot_unresolved.xlsx` to analyze failure patterns (sample 30-50 unresolved conversations)
- You MUST read `bot_resolved.xlsx` to analyze success patterns (sample 20-30 resolved conversations)
- You MUST generate the report at `{output_dir}/bot_performance_report.md`
- If topic breakdown is available (from clustering), you MUST analyze per-topic resolution rates
- You MUST identify the top 3 topics the bot handles well and top 3 it struggles with
- You MUST include representative conversation examples for both resolved and unresolved cases
- You MUST analyze bot message patterns (what the bot says, how it responds)
- You SHOULD identify common handoff triggers (what causes bot→manager transfer)
- You SHOULD suggest improvement areas for bot configuration

**Report Structure:**
```markdown
# Bot Performance Analysis Report: {Company}

## Executive Summary
[3-5 sentences: overall bot resolution rate, key strengths, key weaknesses]

## 1. Overall Statistics
| 지표 | 수치 |
|------|------|
| 전체 유저챗 | {N}건 |
| Bot 참여 | {N}건 ({%}) |
| Bot 해결 | {N}건 ({%}) |
| Bot 미해결 | {N}건 ({%}) |
| Bot 해결률 | {%} |

## 2. Topic-Level Analysis
### 2.1 Bot이 잘 처리하는 토픽 (Top 3)
[For each: topic name, resolution rate, conversation count, bot behavior pattern, examples]

### 2.2 Bot이 잘 못 처리하는 토픽 (Top 3)
[For each: topic name, resolution rate, conversation count, failure pattern, examples]

### 2.3 Topic Resolution Rate Table
[Full table: category, total, resolved, unresolved, rate — sorted by rate desc]

## 3. Bot Behavior Pattern Analysis
### 3.1 Bot 응답 패턴
[What messages does the bot send? Categorize bot responses]

### 3.2 핸드오프 트리거 분석
[What causes the bot to hand off to manager? Common patterns in unresolved conversations]

### 3.3 해결 패턴
[How does the bot successfully resolve? Common patterns in resolved conversations]

## 4. Unresolved Conversation Deep Dive
### 4.1 미해결 대화 유형 분류
[Categorize unresolved conversations: bot couldn't answer, bot gave wrong info, customer insisted on human, etc.]

### 4.2 대표 미해결 대화 예시 (5-10건)
[Show conversation flow: user asks → bot responds → manager takes over]

## 5. Recommendations
### 5.1 즉시 개선 가능 항목
[Quick wins: FAQ additions, response template improvements]

### 5.2 중기 개선 항목
[Medium-term: new automation flows, API integrations]

### 5.3 상담사 전용 유지 항목
[Topics that should remain human-handled]

## Metadata
- Generated: {timestamp}
- Source: {input_file}
- Manager turn threshold: {threshold}
```

**Expected Output:**
```
✅ Bot 성능 분석 보고서 생성:
   results/guhada/bot_analysis/bot_performance_report.md

📋 주요 발견:
  - Bot 해결률: 66.9%
  - 잘 처리하는 토픽: 배송 (77.7%), 기타 (81.2%)
  - 잘 못 처리하는 토픽: 주문관리 (55.4%), 반품교환 (56.8%)
```

### 4. Review and Communicate Results

Present results and suggest next steps.

**Constraints:**
- You MUST display summary of key findings
- You MUST provide file paths for all outputs
- You MUST highlight actionable insights
- You SHOULD suggest how this data can inform ALF (AI chatbot) setup

**Communication Template:**
```
✅ Bot 성능 분석 완료: {Company}

📊 Results Summary:
  - Bot 해결률: {rate}%
  - 강점 토픽: {topics}
  - 약점 토픽: {topics}

📁 Output Files:
  1. 분류 데이터: {output_dir}/bot_classified.xlsx
  2. 해결 건: {output_dir}/bot_resolved.xlsx
  3. 미해결 건: {output_dir}/bot_unresolved.xlsx
  4. 통계 요약: {output_dir}/bot_analysis_summary.json
  5. 분석 보고서: {output_dir}/bot_performance_report.md

💡 Key Insights:
  - {insight_1}
  - {insight_2}
  - {insight_3}
```

## Examples

### Example 1: With Clustering Results

```
input_file: data/구하다 상담데이터 raw 90일_.xlsx
output_dir: results/guhada/bot_analysis
company: guhada
clustered_path: results/guhada/01_clustering/guhada_clustered.xlsx
tags_path: results/guhada/01_clustering/guhada_tags.xlsx
```

Results:
- Topic-level resolution rates available
- Bot handles 배송 well (77.7%), struggles with 반품교환 (56.8%)

### Example 2: Without Clustering Results

```
input_file: data/user_chat_newclient.xlsx
output_dir: results/newclient/bot_analysis
company: newclient
```

Results:
- Overall statistics only (no topic breakdown)
- Agent analyzes conversation content directly to identify patterns

## Troubleshooting

### Issue: No Bot Messages Found

**Symptom:** All conversations classified as `no_bot`

**Solution:**
- Check the `personType` column in Message data sheet
- Bot personType may differ (check for 'bot', 'Bot', 'BOT', 'workflow')
- If the channel uses workflows instead of bots, the analysis approach may need adjustment

### Issue: Clustering Results Not Found

**Symptom:** Topic breakdown unavailable

**Solution:**
- Run Stage 1 clustering first: `/stage1-clustering`
- Or proceed without clustering — the agent will analyze conversation content directly

## Notes

### Classification Logic

- **bot_resolved**: Bot participated AND (no manager involved OR manager had < threshold turns after bot's last message)
- **bot_unresolved**: Bot participated AND manager had >= threshold turns after bot's last message
- **no_bot**: No bot messages in the conversation

### Output for ALF Setup

The bot performance report directly informs ALF configuration:
- Topics with high bot resolution → Keep similar automation, add to ALF rules
- Topics with low bot resolution → Design new ALF workflows with better logic
- Handoff patterns → Define ALF escalation rules

### Performance

- 1,000 conversations: ~10-20 seconds
- No API calls required (pure data processing)
- Clustering merge adds ~5 seconds
