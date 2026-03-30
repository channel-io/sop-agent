---
name: stage2-extraction
description: This SOP guides the real sample-based LLM extraction of patterns, FAQs, and response strategies from clustered customer support data. This is Stage 2 of the Userchat-to-SOP pipeline, combining Python sample extraction with AI agent natural language analysis. **Language:** Auto-detects Korean (한국어) or Japanese (日本語) from user input.
---

# Stage 2: Pattern & FAQ Extraction

## Overview
This SOP guides the **real sample-based LLM extraction** of patterns, FAQs, and response strategies from clustered customer support data. This is **Stage 2** of the Userchat-to-SOP pipeline, combining Python sample extraction with AI agent natural language analysis.

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

**Stage Flow:**
- **Input**: Stage 1 clustering results (Excel files + analysis report)
- **Process**:
  1. Load Stage 1 results and run enrichment (extract full conversation transcripts)
  2. LLM reads **full conversation transcripts** (NOT summaries) per cluster
  3. LLM extracts patterns, classifies HT vs TS
  4. **LLM defines SOP topics and re-classifies clusters → topics**
  5. LLM generates FAQs, response strategies, keywords
- **Output**: Structured JSON files with patterns, FAQ pairs, **SOP topic map**, enriched conversations

**Critical Philosophy:**
- ❌ DO NOT analyze `enhanced_text` (summaries) — they lose customer expressions and agent responses
- ✅ DO read **full conversation transcripts** (`turns` from enriched data) for all analysis
- ✅ DO extract verbatim customer expressions from actual conversations
- ✅ DO preserve company tone from actual agent responses
- ✅ DO re-classify clusters into SOP topics based on what you actually read

## Parameters

### Required
- **clustering_output_dir**: Directory containing Stage 1 results
  - Example: `results/meliens`
  - Must contain: `{prefix}_clustered.xlsx`, `{prefix}_tags.xlsx`, `{prefix}_messages.csv`, `analysis_report.md`

- **company**: Company name for context
  - Example: "Meliens", "Assacom", "Usimsa"

### Optional
- **min_total_samples** (default: 300): Minimum total conversation samples across all clusters
  - Dynamically adjusts `n_samples_per_cluster` based on cluster count (K)
  - Formula: `n_samples_per_cluster = max(20, ceil(min_total_samples / K))`
  - Examples: K=8 → 38/cluster (304 total), K=10 → 30/cluster (300 total), K=15 → 20/cluster (300 total), K=25 → 20/cluster (500 total)
- **n_samples_per_cluster** (default: dynamically calculated): Number of conversation samples to extract per cluster
  - If explicitly set by user, overrides dynamic calculation
  - If not set, calculated from `min_total_samples` and K
- **focus_clusters** (default: "all"): Which clusters to analyze
  - `"all"`: All clusters
  - `"top_10"`: Top 10 by size
  - List: `"0,2,5,7"`

## Steps

### 1. Load Stage 1 Results and Run Enrichment

Read clustering results, then **immediately run enrichment** to extract full conversation transcripts. All subsequent steps use these transcripts, not summaries.

**Constraints:**
- You MUST read Stage 1 files first:
  1. `{prefix}_tags.xlsx`: Cluster summary (ID, label, category, keywords, count)
  2. `analysis_report.md`: Analysis insights and recommendations
  3. (DO NOT read `{prefix}_clustered.xlsx` for samples — enrichment will provide better data)
- You MUST calculate `n_samples_per_cluster` dynamically (unless user explicitly set it):
  ```python
  import math
  K = len(tags)  # number of clusters from tags.xlsx
  min_total = 300  # min_total_samples parameter
  n_samples = max(20, math.ceil(min_total / K))
  ```
- You MUST create a bootstrap patterns.json from tags.xlsx, then run enrichment:
  ```bash
  mkdir -p results/{company}/02_extraction

  # 1. Create minimal patterns.json from tags (cluster IDs only)
  python3 -c "
  import pandas as pd, json
  tags = pd.read_excel('results/{company}/01_clustering/{prefix}_tags.xlsx')
  data = {'metadata': {'company': '{company}', 'bootstrap': True}, 'clusters': []}
  for _, r in tags.iterrows():
      data['clusters'].append({'cluster_id': int(r['cluster_id']), 'label': r['label'], 'category': r['category'], 'cluster_size': int(r['cluster_size'])})
  with open('results/{company}/02_extraction/patterns.json', 'w') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
  "

  # 2. Run enrichment to extract full conversation transcripts
  #    n_samples is dynamically calculated: max(20, ceil(300 / K))
  python3 scripts/enrich_patterns.py \
    --patterns results/{company}/02_extraction/patterns.json \
    --messages results/{company}/01_clustering/{prefix}_messages.csv \
    --output results/{company}/02_extraction/conversations_by_cluster.json \
    --n-samples {n_samples}
  ```
- You MUST verify enrichment succeeded: each cluster has `{n_samples}` conversation transcripts with full `turns`
- You MUST display the calculated n_samples_per_cluster and total sample count

**Why enrichment first?**
- All subsequent analysis (patterns, HT/TS, topic mapping, FAQ, strategies) benefits from reading **actual agent-customer dialog**, not summaries
- Summaries (`enhanced_text`) lose: customer tone, agent response style, conversation flow, escalation moments, resolution steps

**Fallback if enrichment fails:**
- If `enrich_patterns.py` fails or `messages.csv` is missing, fall back to extracting samples from `clustered.xlsx` using `enhanced_text`
- Mark analysis as `"data_source": "summary_fallback"` in metadata

**Expected Output:**
```
✅ Enrichment 완료
  - 클러스터: 12개 (K=12)
  - 클러스터당 대화: 25건 (= max(20, ceil(300/12)))
  - 총 분석 대화: 300건
  - 파일: conversations_by_cluster.json
```

---

### 2. Analyze Full Conversations per Cluster

For each cluster, read the **full conversation transcripts** and extract patterns, classify HT vs TS.

**Constraints:**
- You MUST read actual conversation `turns` from enrichment output (NOT `enhanced_text`)
- You MUST process clusters **sequentially** in main agent (no subagents)
- You MUST identify 3-8 distinct patterns per cluster
- You MUST extract actual customer phrases **verbatim** from conversations
- You MUST categorize patterns by: `정보_요청`, `문제_신고`, `프로세스_문의`, `불만_제기`
- You MUST classify each cluster as HT or TS based on conversation content
- You MUST note if a cluster contains **mixed topics** (e.g., both hardware AS and Windows issues)
- You SHOULD measure frequency by counting pattern occurrences across `{n_samples}` conversations

**Per-Cluster Analysis Process:**

For each cluster, read `{n_samples}` conversations and extract:

1. **Patterns** (3-8 per cluster):
   - Pattern name, type, common phrases (verbatim from conversations), intent, frequency

2. **HT vs TS Classification**:
   - HT (How-To): 주요 목적이 정보 제공/안내
   - TS (Troubleshooting): 주요 목적이 문제 해결
   - If mixed: note which conversations belong to which type

3. **Mislabel Detection**:
   - Compare cluster label with actual conversation content
   - Flag if >30% of conversations don't match the label
   - Record `actual_content` description

4. **Company Tone** (from agent messages in conversations):
   - Greeting style, emoji usage, brand messaging
   - Response structure (numbered steps, bullet points)
   - Closing style

**Reading Conversations (important):**
```
For Cluster X, read each conversation's turns:
  Turn 1 (customer): "블루스크린이 계속 떠요. 어제부터 갑자기..."
  Turn 2 (agent): "안녕하세요, 고객님! ... 먼저 메모리 재장착을 시도해주세요"
  Turn 3 (customer): "재장착 했는데 아직도 같아요"
  Turn 4 (agent): "그렇다면 택배 AS 접수를 도와드리겠습니다..."

→ Pattern: 블루스크린 → 자가조치 → AS 접수 (TS, 문제 해결 프로세스)
→ Agent tone: emoji 사용, 공감 표현 먼저, 단계별 안내
→ Real phrase: "블루스크린이 계속 떠요" (not "블루스크린 문제 발생")
```

**Output per cluster:**
```json
{
  "cluster_id": 0,
  "original_label": "오류 해결 문의",
  "actual_content": "A/S 접수 + 하드웨어 불량 + 윈도우 설치 (혼합)",
  "is_mixed": true,
  "mixed_topics": ["하드웨어_AS", "윈도우_소프트웨어", "케이블_연결"],
  "sop_type": "TS",
  "patterns": [...],
  "tone_observations": {...}
}
```

---

### 3. Define SOP Topics and Map Clusters (Re-classification)

After analyzing ALL clusters, define the **actual SOP topic list** independent of cluster boundaries. This is the **authoritative plan** that Stage 3 must follow.

**Constraints:**
- You MUST execute this step AFTER completing Step 2 for ALL clusters
- You MUST define SOP topics based on **what you actually read in conversations**, not cluster labels
- You MUST handle these cases:
  - **Mixed cluster** (1 cluster → 2+ topics): Split. Record which conversations belong to which topic
  - **Duplicate clusters** (2+ clusters → 1 topic): Merge
  - **Mislabeled cluster**: Use actual content, ignore label
  - **Noise cluster** (mostly greetings/empty): Absorb into "초기 응대" or exclude
- You MUST produce a `sop_topic_map` — Stage 3 MUST follow this map
- You SHOULD aim for 8-15 SOP topics
- You SHOULD organize by customer journey (구매 전 → 구매/결제 → 수령/설치 → 사용 중 → AS → 기타)

**Process:**

1. Review all cluster analyses from Step 2
2. List all **actual topics** observed across all conversations (ignore cluster boundaries)
3. For mixed clusters: assign each of the 20 conversations to a topic
4. Map clusters (or portions) → topics
5. Assign HT or TS to each topic
6. Validate: every cluster mapped, total records ≈ input total

**Output Structure (`sop_topic_map` in patterns.json):**

```json
{
  "sop_topic_map": {
    "description": "Authoritative SOP topic list. Stage 3 MUST follow this map.",
    "topics": [
      {
        "topic_id": "TS_HARDWARE_AS",
        "title": "A/S 접수 및 하드웨어 불량 처리",
        "type": "TS",
        "journey_stage": "사용 중",
        "source_clusters": [
          {"cluster_id": 0, "portion": "partial", "conversation_ids": [1,3,5,6,8,10,12,14,15,17,19], "reason": "하드웨어 불량/AS 접수 관련 대화만"},
          {"cluster_id": 6, "portion": "full", "reason": "전체가 AS 문의"}
        ],
        "estimated_records": 500,
        "key_patterns": ["블루스크린", "쿨러_소음", "택배_AS_접수"]
      },
      {
        "topic_id": "TS_WINDOWS_SW",
        "title": "윈도우/소프트웨어 문제 해결",
        "type": "TS",
        "journey_stage": "설치",
        "source_clusters": [
          {"cluster_id": 0, "portion": "partial", "conversation_ids": [2,4,7,9,11,13,16,18,20], "reason": "윈도우 설치/드라이버 관련 대화만"}
        ],
        "estimated_records": 300,
        "key_patterns": ["윈도우_설치", "정품_인증", "드라이버_문제"]
      }
    ],
    "merge_log": [
      "Clusters 2+5+6 merged → HT_INITIAL_INTAKE (모두 초기 인사 메시지)"
    ],
    "label_corrections": [
      {"cluster_id": 7, "original_label": "현금영수증 문의", "actual_content": "80% 취소/환불 + 20% 서류 발행", "action": "split into TS_CANCEL + HT_DOCUMENTS"}
    ]
  }
}
```

**Validation Checklist:**
- [ ] All clusters assigned to at least one topic
- [ ] Mixed clusters split with `conversation_ids` assigned per topic
- [ ] Label corrections documented
- [ ] Total estimated records ≈ total input records
- [ ] Each topic has HT or TS
- [ ] Topic count is 8-15

---

### 4. Generate FAQ Pairs

Create question-answer pairs based on **actual conversations read in Step 2**.

**Constraints:**
- You MUST generate 3-5 FAQ pairs per **SOP topic** (from Step 3 topic map)
- You MUST write questions using actual customer language from conversations (verbatim!)
- You MUST write answers following the company's actual agent tone from conversations
- You MUST ensure answers include specific steps, timeframes, contact info observed in conversations
- You MUST NOT create generic FAQ pairs

**Critical Requirement:**
- ❌ "AS 접수는 어떻게 하나요?" (generic)
- ✅ "블루스크린이 계속 떠요. 어제부터 갑자기..." (from actual conversation)
- ✅ Answer includes actual agent response pattern observed: "먼저 메모리 재장착을 시도해주세요 → 안 되면 택배 AS 접수"

---

### 5. Identify Response Strategies

Define response strategies and escalation rules per **SOP topic**.

**Constraints:**
- You MUST define strategy per SOP topic (not per cluster)
- You MUST extract escalation triggers from actual conversations (when did agents escalate?)
- You MUST identify automation opportunities
- You SHOULD document standard response patterns observed in conversations

---

### 6. Build Keyword Taxonomy

Create keyword taxonomy from all analyzed conversations.

**Constraints:**
- You MUST extract keywords from actual conversations (not summaries)
- You MUST group hierarchically (category → subcategory → keywords)
- You SHOULD include synonyms and common typos observed

---

### 7. Save All Results

Save extraction results and run final enrichment.

**Constraints:**
- You MUST save these files to `results/{company}/02_extraction/`:
  1. `patterns.json` — patterns + `sop_topic_map` + HT/TS classification
  2. `faq.json` — FAQ pairs organized by SOP topic
  3. `response_strategies.json` — strategies per SOP topic
  4. `keywords.json` — keyword taxonomy
  5. `extraction_summary.md` — human-readable summary
- You MUST run enrichment on the final patterns.json (using the same `{n_samples}` calculated in Step 1):
  ```bash
  python3 scripts/enrich_patterns.py \
    --patterns results/{company}/02_extraction/patterns.json \
    --messages results/{company}/01_clustering/{company}_messages.csv \
    --output results/{company}/02_extraction/patterns_enriched.json \
    --n-samples {n_samples}
  ```
- You MUST verify `patterns_enriched.json` contains conversation samples for each cluster

**Note:** If enrichment was already run in Step 1 for analysis, this second run updates the file with the final patterns structure. The conversations are re-selected based on the finalized cluster assignments.

---

## Examples

### Example 1: Standard Extraction (Assacom)

**Parameters:**
- clustering_output_dir: `results/assacom`
- company: "Assacom"
- min_total_samples: 300 (default)
- K=12 → n_samples_per_cluster = max(20, ceil(300/12)) = 25

**Execution:**
1. Load tags + analysis report, calculate n_samples = 25
2. Run enrichment → get 25 full conversations per cluster (total: 300)
3. Read conversations sequentially per cluster:
   - Cluster 0 (799건): Read 25 conversations → discover it's mixed (AS + 윈도우 + 케이블)
   - Cluster 1 (592건): Read 25 conversations → clean 견적/사양 topic
   - ...
4. Define topic map: 12 clusters → 8 SOP topics (split Cluster 0, merge Clusters 2+5+6)
5. Generate FAQs per SOP topic using actual customer expressions
6. Save all files + run final enrichment

**Time**: ~8-12 minutes
**Output**: 8 SOP topics, 47 patterns, 42 FAQ pairs, enriched conversations

### Example 2: Mixed Cluster Handling

**Scenario**: Cluster 0 has 799 records with hardware AS, Windows issues, and cable questions mixed together.

**What happens in Step 2:**
- Read 20 conversations
- Conv 1: customer reports blue screen → agent suggests memory reinstall → AS pickup → **하드웨어_AS**
- Conv 2: customer asks about Windows install USB → agent provides guide link → **윈도우_소프트웨어**
- Conv 3: customer can't connect dual monitor → agent explains D-SUB vs HDMI → **그래픽카드_모니터**
- ...

**What happens in Step 3:**
- Cluster 0 split into 3 topics with conversation_ids assigned
- Each topic gets its own SOP in Stage 3

## Troubleshooting

### Issue 1: Enrichment fails (messages.csv missing)

**Solution:**
- Fall back to reading `enhanced_text` from `clustered.xlsx`
- Mark `"data_source": "summary_fallback"` in metadata
- Quality will be lower but pipeline continues

### Issue 2: Patterns are too generic

**Root Cause**: LLM summarized instead of quoting verbatim
**Solution**: Re-read specific conversations and copy-paste exact customer phrases

### Issue 3: Too many SOP topics (>15)

**Solution**: Merge related topics. If "SSD 인식 문제" and "HDD 연결 문제" are separate, combine into "저장장치 문제"

## Notes

### Why Full Conversations Instead of Summaries?

| Aspect | Summary (`enhanced_text`) | Full Conversation (`turns`) |
|--------|--------------------------|----------------------------|
| Customer tone | Lost | "블루스크린이 계속 떠요 ㅠㅠ" |
| Agent response pattern | Lost | "먼저 ~해주세요 → 안 되면 ~" |
| Escalation moment | Lost | "3번 시도 후 AS 접수 전환" |
| Resolution steps | Lost | Step-by-step troubleshooting flow |
| Conversation length | Lost | Short (3 turns) vs Complex (15+ turns) |
| Mixed topic detection | Hard (summary blends topics) | Clear (each turn has context) |

### Execution Strategy

- ⚠️ **서브에이전트 사용 금지** — hanging 발생
- ✅ **메인 에이전트 순차 처리** — 클러스터 하나씩 대화 읽고 분석
- ✅ **컨텍스트 관리** — 클러스터 하나 분석 완료 후 결과 저장, 다음 클러스터 진행
- {n_samples}건 대화 × 평균 10턴 = ~{n_samples*10} 메시지/클러스터 → 컨텍스트에 충분히 들어감 (K=8일 때 38건도 ~380 메시지로 1M 컨텍스트 내 충분)

### Time Estimates

With `min_total_samples=300`, `n_samples_per_cluster = max(20, ceil(300/K))`:

| K (Clusters) | Samples/Cluster | Total Samples | Estimated Time |
|--------------|-----------------|---------------|----------------|
| 8 | 38 | 304 | ~12-18 min |
| 10 | 30 | 300 | ~12-16 min |
| 12 | 25 | 300 | ~12-16 min |
| 15 | 20 | 300 | ~12-16 min |
| 20 | 20 | 400 | ~15-20 min |
| 25 | 20 | 500 | ~18-25 min |

### Relationship with Stage 3

- Stage 3의 Customer Journey Mapping은 **이 단계의 `sop_topic_map`을 따라야 함**
- Stage 3은 토픽 맵을 재정의하지 않고, 주어진 토픽별로 SOP를 생성만 함
- `patterns_enriched.json`의 대화 샘플이 Stage 3의 주요 입력
