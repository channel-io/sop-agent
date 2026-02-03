# Clustering UserChat Data

## Overview
This SOP guides the automated clustering and tagging of customer support chat data. It processes Korean customer service conversations through a complete pipeline: data preprocessing, text enhancement, embedding generation (Upstage Solar), K-Means clustering, LLM-based tagging, and structured output generation.

**Use Cases:**
- Analyzing large volumes (1000+) of customer support chat logs
- Automatically categorizing customer inquiries by topic
- Identifying common patterns in customer service interactions
- Generating industry-specific category taxonomies
- Preparing data for SOP (Standard Operating Procedure) extraction

**Key Features:**
- 3-level text enhancement fallback strategy
- Automatic embedding caching (4096-dimensional vectors)
- Silhouette score-based optimal cluster selection
- Two tagging modes: API (fast) or Claude manual (high-quality)
- Industry-adaptive category generation

## Parameters

### Required
- **input_file**: Path to Excel file containing UserChat data
  - Must have "UserChat data" sheet with chat metadata
  - Must have "Message data" sheet with conversation messages
  - Format: `.xlsx` file

### Optional
- **sample_size** (default: 1000): Number of records to process
  - Use 1000 for standard analysis (recommended default)
  - Use "all" for complete dataset (only if explicitly needed)
  - Note: 1000 records is sufficient for most clustering tasks

- **tagging_mode** (default: "agent"): Cluster tagging method
  - `"agent"`: Fast Solar-pro unified tagging (5-15 sec, industry-adaptive, recommended)
  - `"api"`: Solar-mini independent tagging (30 sec, hardcoded categories)
  - `"skip"`: Skip tagging, use `/tag-clusters-manual` skill for highest quality
  
- **k** (default: "auto"): Number of clusters
  - `"auto"`: Automatically select optimal K via silhouette score
  - Integer value: Use fixed cluster count
  
- **k_range** (default: "8,10,12,15,20,25"): K values to test when k="auto"
  - Comma-separated list of integers
  - Only used when k="auto"

- **output_dir** (default: "results"): Output directory path
- **prefix** (default: "output"): Filename prefix for outputs
- **cache_dir** (default: "cache"): Embedding cache directory

## Steps

### 1. Data Loading & Validation

Load Excel data and validate structure.

**Constraints:**
- You MUST validate presence of "UserChat data" and "Message data" sheets
- You MUST check for required columns: `id`, `summarizedMessage` (if available), messages
- You SHOULD report data statistics (total records, date range, companies)
- You MAY skip records with missing critical data
- You MUST NOT proceed if sheets are missing

**Tools Required:**
- `pandas` for Excel reading
- `openpyxl` engine for .xlsx files

**Expected Output:**
```
Loaded 1,645 records from Meliens
Date range: 2024-01-01 to 2024-12-31
Columns found: id, userId, summarizedMessage, ...
```

### 2. Text Enhancement

Enhance text quality using 3-level fallback strategy.

**Constraints:**
- You MUST apply the following priority:
  1. If `summarizedMessage` exists and ≥ 50 chars → Use it
  2. Else if `first_message` ≥ 20 chars → Use first message
  3. Else → Combine 3 turns (6 messages total)
- You MUST track which strategy was used per record (store in `text_strategy` column)
- You SHOULD clean text: remove extra whitespace, handle NaN values
- You MAY apply additional preprocessing (lowercasing, normalization) if needed
- You MUST NOT use empty strings (mark as NaN instead)

**Text Enhancement Logic:**
```python
def enhance_text(row, messages_df):
    # Strategy 1: summarizedMessage
    if row['summarizedMessage'] and len(row['summarizedMessage']) >= 50:
        return row['summarizedMessage'], 'summary'
    
    # Strategy 2: first_message
    user_messages = messages_df[messages_df['chatId'] == row['id']]
    if not user_messages.empty:
        first_msg = user_messages.iloc[0]['content']
        if len(first_msg) >= 20:
            return first_msg, 'first_message'
    
    # Strategy 3: combine 3 turns (6 messages)
    combined = ' '.join(user_messages['content'].head(6).tolist())
    return combined, 'combined_turns'
```

**Expected Output:**
- New column: `enhanced_text` (enhanced text)
- New column: `text_strategy` (strategy used)
- Statistics: "93.9% used summary, 2.5% used first_message, 3.6% combined turns"

### 3. Embedding Generation

Generate 4096-dimensional embeddings using Upstage Solar API with automatic caching.

**Constraints:**
- You MUST use Upstage Solar `embedding-passage` model
- You MUST check cache before generating embeddings (cache key: model_texthash_samplesize)
- You MUST batch API calls (recommended: 100 texts per batch)
- You SHOULD show progress (e.g., "Embedding batch 1/10...")
- You MAY retry failed API calls up to 3 times
- You MUST save embeddings to cache after generation
- You MUST NOT embed empty or NaN texts (filter them out first)

**API Configuration:**
```python
import requests

UPSTAGE_API_KEY = "up_..."  # Load from config.py
EMBEDDING_MODEL = "embedding-passage"
API_URL = "https://api.upstage.ai/v1/solar/embeddings"

headers = {
    "Authorization": f"Bearer {UPSTAGE_API_KEY}",
    "Content-Type": "application/json"
}
```

**Caching Mechanism:**
```python
import pickle
import hashlib

def get_cache_key(texts, model):
    text_hash = hashlib.md5(''.join(texts).encode()).hexdigest()[:10]
    return f"embeddings_{model}_{text_hash}_{len(texts)}.pkl"

def load_embeddings_cache(cache_key, cache_dir="cache"):
    cache_path = f"{cache_dir}/{cache_key}"
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None
```

**Expected Output:**
- Numpy array of shape (N, 4096)
- Cache file saved: `cache/embeddings_embedding-passage_abc123_1000.pkl`
- Time report: "Generated 1000 embeddings in 45 seconds" or "Loaded from cache in 2 seconds"

### 4. K-Means Clustering

Perform K-Means clustering with optimal K selection.

**Constraints:**
- You MUST normalize embeddings before clustering (if not already normalized)
- If k="auto": You MUST test all K values in k_range and select best via silhouette score
- If k is integer: You MUST use that K directly
- You MUST assign cluster IDs (0 to K-1) to all records
- You SHOULD calculate cluster sizes and report distribution
- You MAY initialize with k-means++ for better convergence
- You MUST NOT use clustering algorithms other than K-Means (requirement from analysis)

**Silhouette Score Calculation:**
```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def find_optimal_k(embeddings, k_range=[8, 10, 12, 15, 20, 25]):
    best_k = k_range[0]
    best_score = -1
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels, sample_size=min(10000, len(embeddings)))
        
        print(f"K={k}: Silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k
    
    return best_k, best_score
```

**Expected Output:**
- New column: `cluster_id` (0 to K-1)
- New column: `cluster_size` (number of records in cluster)
- Report: "Optimal K=20, Silhouette Score=0.064"
- Cluster distribution table

### 5. Cluster Tagging

Tag each cluster with label, category, and keywords using LLM.

**Constraints:**
- You MUST choose ONE of two tagging modes based on `tagging_mode` parameter
- For BOTH modes: You MUST generate label, category, keywords for each cluster
- **You MUST generate all output fields (label, category, keywords, description) in KOREAN**
- Use Korean for all text fields (e.g., "AS_접수", "일반_상담", "충전기", "보풀제거기")
- You SHOULD extract 5 representative samples per cluster for analysis
- You MAY truncate very long texts (>200 chars) for display
- You MUST NOT create "기타" (other) category unless truly necessary

#### Mode A: API Tagging (tagging_mode="api")

**Constraints:**
- You MUST use Solar-mini API for fast tagging
- You MUST tag each cluster independently
- **You MUST use Korean for all output fields in the API prompt**
- You SHOULD use hardcoded categories: ["구매", "배송", "AS", "취소", "견적", "기타"]
- Expected time: ~30 seconds for 20 clusters
- Expected cost: ~$0.01 per 1000 records

**API Prompt Template:**
```python
prompt = f"""
다음은 고객 상담 채팅 클러스터의 샘플입니다:

{samples}

이 클러스터를 분석하여 JSON으로 응답하세요. 모든 필드는 한국어로 작성하세요:
{{
  "label": "클러스터 라벨 (예: AS_접수, 배송_조회)",
  "category": "구매|배송|AS|취소|견적|기타 중 하나",
  "keywords": ["키워드1", "키워드2", "키워드3"]
}}
"""
```

#### Mode B: Claude Manual Tagging (tagging_mode="claude_manual")

**Constraints:**
- You MUST analyze all clusters holistically (not independently)
- You MUST auto-generate industry-specific categories (not hardcoded)
- **You MUST generate all tags (label, category, keywords, description) in KOREAN**
- All output fields MUST be in Korean (e.g., label="충전_AS", category="A/S", keywords=["충전기", "케이블"])
- You MUST identify special cases (empty data, internal tickets)
- You SHOULD provide detailed descriptions for each cluster
- You MAY create custom categories beyond standard ones
- Expected time: ~2-3 minutes per 10 clusters
- Expected cost: Higher (Claude API tokens)

**Manual Analysis Process:**
```python
# 1. Extract samples from all clusters
for cluster_id in range(K):
    samples = df[df['cluster_id'] == cluster_id]['enhanced_text'].dropna().head(5)
    print(f"Cluster {cluster_id}: {samples}")

# 2. Claude analyzes patterns and creates tags (in Korean)
manual_tags = {
    0: {
        'label': '제품_문의',
        'category': '일반_상담',
        'keywords': ['보풀제거기', '칼날', '쿠폰', '사용법'],
        'description': '보풀제거기 제품 기능, 사용법, 구매 옵션 문의'
    },
    3: {
        'label': '데이터_오류',
        'category': '시스템',
        'keywords': ['빈_데이터', 'NaN', '누락'],
        'description': '모든 레코드가 빈 데이터 - 시스템 오류'
    },
    # ... 각 클러스터에 대해
}

# 3. Apply tags to dataframe
for cluster_id, tags in manual_tags.items():
    mask = df['cluster_id'] == cluster_id
    df.loc[mask, 'label'] = tags['label']
    df.loc[mask, 'category'] = tags['category']
    df.loc[mask, 'keywords'] = str(tags['keywords'])
```

**Quality Checks:**
- Verify 0% "기타" rate for well-defined industries
- Check for system anomalies (empty data, internal tickets)
- Ensure categories are industry-specific
- Verify all output fields are in Korean

**Expected Output:**
- New column: `label` (cluster label)
- New column: `category` (high-level category)
- New column: `keywords` (list of keywords as string)
- Tag summary table showing distribution

### 6. Output Generation

Save results in two Excel files with comprehensive data.

**Constraints:**
- You MUST generate two output files:
  1. `{prefix}_clustered.xlsx`: Full dataset with all columns + cluster data
  2. `{prefix}_tags.xlsx`: Cluster summary with metadata
- You MUST include all original columns in clustered file
- You MUST use `openpyxl` engine for Excel writing
- You SHOULD create output directory if it doesn't exist
- You MAY add timestamp to filenames for versioning
- You MUST NOT overwrite existing files without warning

**Output File 1: `{prefix}_clustered.xlsx`**

Columns:
- All original columns from input Excel
- `enhanced_text`: Enhanced text used for clustering
- `text_strategy`: Strategy used (summary|first_message|combined_turns)
- `cluster_id`: Cluster ID (0 to K-1)
- `cluster_size`: Number of records in this cluster
- `label`: Cluster label (e.g., "AS_접수")
- `category`: High-level category (e.g., "A/S")
- `keywords`: Comma-separated keywords

**Output File 2: `{prefix}_tags.xlsx`**

Columns:
- `cluster_id`: Cluster ID
- `label`: Cluster label
- `category`: High-level category
- `keywords`: Comma-separated keywords
- `description`: Detailed description (if available)
- `count`: Number of records in cluster
- `percentage`: Percentage of total records
- `representative_samples`: Top 3 samples (optional)

**File Saving:**
```python
import os
import pandas as pd

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Save clustered data
output_path_clustered = f"{output_dir}/{prefix}_clustered.xlsx"
df.to_excel(output_path_clustered, index=False, engine='openpyxl')

# Save tag summary
output_path_tags = f"{output_dir}/{prefix}_tags.xlsx"
tag_summary_df.to_excel(output_path_tags, index=False, engine='openpyxl')

print(f"✅ Results saved:")
print(f"  - {output_path_clustered}")
print(f"  - {output_path_tags}")
```

**Expected Output:**
```
✅ Results saved:
  - results/meliens_claude_manual/meliens_claude_manual_clustered.xlsx
  - results/meliens_claude_manual/meliens_claude_manual_tags.xlsx

Category Distribution:
  A/S: 790건 (48.0%)
  일반_상담: 318건 (19.3%)
  배송: 196건 (11.9%)
  시스템: 171건 (10.4%)
  주문관리: 170건 (10.3%)
```

**Note:** See `sops/examples/` directory for actual example files:
- `text_enhancement_example.xlsx` - Text preprocessing demonstration (15 records)
- `meliens_claude_manual_clustered.xlsx` - Full pipeline result (1,645 records)
- `meliens_claude_manual_tags.xlsx` - Cluster summary (10 clusters)
- `README.md` - Detailed explanation of each file

## Examples

### Example 1: Quick Analysis with Sampling

**Input:**
```bash
python3 scripts/pipeline.py \
  --input data/user_chat_assacom.xlsx \
  --sample 1000 \
  --tagging-mode api \
  --output results/assacom_sample \
  --prefix assacom_test
```

**Expected Execution:**
1. Load 1000 sampled records from Assacom
2. Enhance text (3-level fallback)
3. Generate embeddings (cached if available)
4. Auto-select optimal K (test 8,10,12,15,20,25)
5. Tag clusters using Solar-mini API (~30 sec)
6. Save results

**Output Files:**
- `results/assacom_sample/assacom_test_clustered.xlsx` (1000 rows)
- `results/assacom_sample/assacom_test_tags.xlsx` (K rows, e.g., 20)

**Performance:**
- Time: ~2 minutes (1 min embedding + 30 sec tagging + 30 sec processing)
- Cost: ~$0.06 ($0.05 embedding + $0.01 tagging)

### Example 2: Production Run with Claude Manual Tagging

**Input:**
```bash
python3 scripts/pipeline.py \
  --input "data/raw data_meliens.xlsx" \
  --k 10 \
  --tagging-mode claude_manual \
  --output results/meliens_production \
  --prefix meliens_v1
```

**Expected Execution:**
1. Load full dataset (1,645 records)
2. Enhance text
3. Generate embeddings (or load from cache)
4. Cluster with K=10 (fixed)
5. Claude manually analyzes and tags 10 clusters (~2-3 min)
6. Save results

**Output Files:**
- `results/meliens_production/meliens_v1_clustered.xlsx` (1,645 rows)
- `results/meliens_production/meliens_v1_tags.xlsx` (10 rows)

**Tag Quality:**
- 0% "기타" category
- Industry-specific categories: A/S (48.0%), 일반_상담 (19.3%), 배송 (11.9%)
- Special cases detected: 데이터_오류 (7.1%), 내부_티켓 (3.3%)

**Performance:**
- Time: ~4 minutes (1 min embedding + 3 min manual tagging)
- Cost: ~$0.10 ($0.08 embedding + $0.02 Claude tokens)

### Example 3: Multi-Company Batch Processing

**Input:**
```bash
# Assacom (PC/Hardware)
python3 scripts/pipeline.py --input data/user_chat_assacom.xlsx --sample 1000 \
  --k 20 --prefix assacom --output results/assacom_agent

# Usimsa (Telecom)
python3 scripts/pipeline.py --input data/user_chat_usimsa.xlsx --sample 1000 \
  --k 10 --prefix usimsa --output results/usimsa_agent

# Meliens (Electronics)
python3 scripts/pipeline.py --input "data/raw data_meliens.xlsx" \
  --k 10 --prefix meliens --output results/meliens_agent
```

**Expected Results:**

| Company | Industry | K | Silhouette | Top Categories |
|---------|----------|---|------------|----------------|
| Assacom | PC/Hardware | 20 | 0.064 | AS (33.8%), 일반문의 (28.5%) |
| Usimsa | Telecom | 10 | 0.041 | 활성화, 기기설정, 사용량관리 |
| Meliens | Electronics | 10 | 0.132 | A/S (48.0%), 일반_상담 (19.3%) |

### Example 4: Troubleshooting Empty Data

**Scenario:** Meliens dataset has 117 empty records (Cluster 3).

**Detection (Claude Manual Mode):**
```python
# Cluster 3 analysis output:
Cluster 3: 117건 (7.1%)
⚠️  모든 레코드가 NaN (빈 데이터)
```

**Tag Assignment:**
```python
{
    'label': '데이터_오류',
    'category': '시스템',
    'keywords': ['빈_데이터', 'NaN', '누락'],
    'description': '모든 레코드가 빈 데이터(NaN) - 시스템 오류 또는 데이터 수집 실패'
}
```

**Action:**
- Flag these records for data quality team
- Exclude from analysis or mark as system issue
- Investigate data collection pipeline

## Output Format

### File 1: `{prefix}_clustered.xlsx`

Sample rows (Meliens example):

| id | userId | summarizedMessage | enhanced_text | text_strategy | cluster_id | cluster_size | label | category | keywords |
|----|--------|-------------------|---------------|---------------|------------|--------------|-------|----------|----------|
| 68dc87... | usr_123 | 질문: 멜리언스... | 질문: 멜리언스 세탁소용 보풀제거기의... | summary | 0 | 92 | 제품_문의 | 일반_상담 | 보풀제거기, 칼날, 쿠폰 |
| 68ea4a... | usr_456 | 안녕하세요... | 안녕하세요 반품 신청한 건... | first_message | 1 | 170 | 주문_취소_변경 | 주문관리 | 반품철회, 주소변경 |
| 68ff0c... | usr_789 | NaN | 질문: 충전이 잘 되지 않음... | combined_turns | 2 | 120 | 충전_AS | A/S | 충전기, 케이블, 부식 |

### File 2: `{prefix}_tags.xlsx`

Sample rows:

| cluster_id | label | category | keywords | description | count | percentage |
|------------|-------|----------|----------|-------------|-------|------------|
| 0 | 제품_문의 | 일반_상담 | 보풀제거기, 칼날, 쿠폰, 사용법, 제품_스펙 | 보풀제거기 제품 기능, 사용법, 구매 옵션, 칼날 재고 등에 대한 일반 문의 | 92 | 5.6% |
| 1 | 주문_취소_변경 | 주문관리 | 반품철회, 주소변경, 취소, 재주문, 예약판매 | 주문 취소, 반품 철회, 배송지 변경 등 주문 내역 변경 요청 | 170 | 10.3% |
| 2 | 충전_AS | A/S | 충전기, 케이블, 어댑터, 부식, 교체 | 진동클렌저 충전기 관련 문제(부식, 충전 불량) 및 케이블 교체 요청 | 120 | 7.3% |

### Category Distribution Summary

**Meliens (Claude Manual) - 1,645 records:**
```
A/S:         790건 (48.0%)
일반_상담:    318건 (19.3%)
배송:        196건 (11.9%)
시스템:      171건 (10.4%)
주문관리:    170건 (10.3%)

Total: 5 categories, 10 labels
"기타" rate: 0%
```

## Troubleshooting

### Issue 1: "KeyError: 'summarizedMessage'"

**Cause:** Input Excel missing `summarizedMessage` column (e.g., Meliens dataset)

**Solution:**
- This is expected behavior - text enhancement will use fallback strategies
- Verify Step 2 logs show "Strategy: first_message" or "Strategy: combined_turns"
- No action needed if `enhanced_text` is populated

### Issue 2: Low Silhouette Score (<0.05)

**Cause:** High-dimensional embeddings (4096D) with limited samples create curse of dimensionality

**Context:** 
- Meliens: K=10, score=0.132 (good)
- Assacom: K=20, score=0.064 (acceptable)
- Usimsa: K=10, score=0.041 (low but expected)

**Solution:**
- Low score is expected for K-Means on high-dimensional data
- Focus on cluster distribution balance and tag quality
- Consider reducing K if clusters are too fragmented
- Do NOT switch to HDBSCAN (creates 70%+ noise - see docs/FINAL_REPORT.md)

### Issue 3: High "기타" (Other) Category Rate

**Scenario:** API mode tagged 57% as "기타" for Usimsa telecom data

**Cause:** Hardcoded categories don't match industry domain

**Solution:**
- Switch to `--tagging-mode claude_manual`
- Claude will auto-generate industry-specific categories
- Usimsa results: 0% "기타", with proper telecom categories (활성화, 기기설정)

### Issue 4: Empty Cache, Slow Re-runs

**Symptom:** Embeddings regenerated every run despite caching

**Cause:** Cache key mismatch due to:
- Different sample_size
- Data order changed (text hash differs)
- Cache directory deleted

**Solution:**
```bash
# Check cache
ls -lh cache/

# Embeddings cache format:
# embeddings_{model}_{texthash}_{count}.pkl

# If cache exists but not loading:
# - Verify text hash matches (same data order)
# - Check sample size matches
# - Ensure cache_dir parameter is correct
```

**Cache Management:**
```bash
# View cache size
du -sh cache/

# Clean old caches (manual)
rm cache/embeddings_*.pkl

# Keep specific cache
mv cache/embeddings_abc123_1000.pkl cache/KEEP_embeddings_abc123_1000.pkl
rm cache/embeddings_*.pkl
mv cache/KEEP_embeddings_abc123_1000.pkl cache/embeddings_abc123_1000.pkl
```

### Issue 5: LLM Tagging JSON Parse Error

**Symptom:** `JSONDecodeError` when tagging clusters (API mode)

**Cause:** LLM returned non-JSON response or malformed JSON

**Current Behavior:** 
- Pipeline assigns default label "클러스터 X"
- Continues processing

**Solution:**
- Check API logs for actual LLM response
- Verify prompt template includes clear JSON format requirement
- If frequent failures: switch to `claude_manual` mode
- Or improve prompt with few-shot examples

### Issue 6: Out of Memory (OOM) Error

**Symptom:** Python crashes during embedding or clustering on large datasets

**Cause:** Loading 10,000+ records with 4096D embeddings into memory

**Solution:**
```python
# Reduce sample size
python3 scripts/pipeline.py --input data.xlsx --sample 5000

# Or process in batches (modify pipeline.py):
def process_in_batches(df, batch_size=5000):
    results = []
    for i in range(0, len(df), batch_size):
        batch = df[i:i+batch_size]
        # Process batch...
        results.append(batch_result)
    return pd.concat(results)
```

### Issue 7: Cluster Size Imbalance

**Symptom:** One cluster has 800 records, others have 20-50

**Cause:** K-Means found dominant pattern in data

**Assessment:**
- Check if large cluster is meaningful (e.g., "일반_상담")
- Verify not a data quality issue (repeated text)

**Solutions:**
1. Increase K to split large cluster
2. Use hierarchical clustering on large cluster
3. Accept if semantically correct (some categories are naturally larger)

### Issue 8: API Rate Limiting

**Symptom:** `429 Too Many Requests` from Upstage API

**Cause:** Exceeded API rate limits during embedding generation

**Solution:**
```python
# Add rate limiting to embedding generation
import time

def generate_embeddings_with_backoff(texts, batch_size=100):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        try:
            response = requests.post(API_URL, json={"input": batch}, headers=headers)
            response.raise_for_status()
            embeddings.extend(response.json()['data'])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limited, waiting 10 seconds...")
                time.sleep(10)
                # Retry
                response = requests.post(API_URL, json={"input": batch}, headers=headers)
                embeddings.extend(response.json()['data'])
        
        time.sleep(0.5)  # Throttle requests
    
    return embeddings
```

## Related Documentation

- **Stage 1 SOP**: `/stage1-clustering` - AI workflow for executing clustering pipeline
- **Stage 2 Extraction**: `/stage2-extraction` - Pattern extraction workflow
- **Stage 3 SOP Generation**: `/stage3-sop-generation` - SOP generation workflow
- **Full Pipeline**: `/excel-to-sop-pipeline` - End-to-end orchestration
- **Project README**: `../README.md` - Project overview and quick start

## Notes

### Why K-Means over HDBSCAN?

HDBSCAN (density-based clustering) was tested but rejected due to:
- **72% noise** with default parameters (720/1000 records unassigned)
- **907/1000 in single cluster** with EOM (Excess of Mass)
- **Curse of dimensionality**: 4096D embeddings with 1000 samples = 1:4.1 ratio

K-Means succeeds because:
- Distance-based (not density-based) - works in high dimensions
- 0% noise (all records assigned)
- Balanced clusters with proper K selection

See `docs/FINAL_REPORT.md` for detailed analysis.

### Tagging Mode Comparison

| Aspect | API Mode | Claude Manual |
|--------|----------|---------------|
| Speed | ~30 sec | ~2-3 min per 10 clusters |
| Cost | $0.01/1000 | Higher (Claude tokens) |
| Categories | Hardcoded | Industry-adaptive |
| "기타" rate | 20-57% | 0% |
| Special cases | Missed | Detected (empty data, internal tickets) |
| Scalability | High | Medium |
| Quality | Good for standard domains | Excellent for all domains |

**Recommendation:**
- Use **API mode** for quick prototyping, standard domains (구매/배송/AS)
- Use **Claude manual** for production, industry-specific analysis, quality-critical work

### Cost Breakdown (per 1000 records)

**Embedding:**
- Upstage Solar embedding-passage: $0.05/1000 (1M tokens ≈ 1000 Korean sentences)

**Tagging:**
- API mode (Solar-mini): $0.01/1000
- Claude manual: $0.02-0.05/1000 (varies by complexity)

**Total per 1000 records:**
- API mode: ~$0.06
- Claude manual: ~$0.08-$0.10

**Full dataset (24,322 records):**
- API mode: ~$1.46
- Claude manual: ~$2.00

### Performance Benchmarks

Hardware: MacBook Pro M1, 16GB RAM

| Dataset Size | Embedding Time | Clustering Time | Tagging Time (API) | Tagging Time (Claude) | Total |
|--------------|----------------|-----------------|--------------------|-----------------------|-------|
| 100 records | 10 sec | 5 sec | 3 sec | 1 min | ~1.5 min |
| 1,000 records | 60 sec | 10 sec | 30 sec | 3 min | ~5 min |
| 10,000 records | 10 min | 60 sec | 5 min | 30 min | ~45 min |

*Note: Embedding time assumes no cache. With cache: ~2-5 seconds regardless of size.*

### Data Privacy Considerations

**Upstage API:**
- Data sent to external API for embedding generation
- Review Upstage privacy policy before processing sensitive data
- Consider on-premise embedding models for confidential data

**Claude API:**
- Chat data sent to Claude for manual tagging
- Anthropic's data retention policy applies
- For sensitive data: use API mode (Solar-mini) or local LLM

**Recommendation:**
- Anonymize PII (personally identifiable information) before processing
- Remove sensitive customer data (names, phone numbers, addresses)
- Redact confidential business information if needed