---
name: userchat-to-sop-pipeline
description: Complete end-to-end pipeline for transforming Excel customer support data into production-ready Agent SOP documents and flowcharts through Clustering, Pattern Extraction, SOP Generation (with verification), and Flowchart Generation stages.
---

# Userchat-to-SOP Complete Pipeline

## Overview

Orchestrates the complete pipeline: Excel data → Clustering → Pattern Extraction → SOP Generation (with verification) → Flowcharts.

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

**Pipeline Flow:**
```
Excel Input (고객 상담 데이터)
    ↓
Stage 1: Clustering (Python) [~3 min]
    → clustered_data.xlsx, cluster_tags.xlsx, analysis_report.md
    ↓
Stage 2: Pattern Extraction (LLM) [~8 min]
    → patterns.json (with sop_topic_map), faq.json, patterns_enriched.json
    ↓
Stage 3: SOP Generation + Verification (LLM) [~12 min]
    → TS_*.sop.md, HT_*.sop.md (verified against real conversations)
    ↓
Stage 4: Flowchart Generation (LLM) [~4 min, optional]
    → *_FLOWCHART.md (Mermaid markdown)
```

**Total Time**: ~25-30 minutes

## Parameters

### Required
- **language** (default: "ko"): `"ko"` (Korean) or `"ja"` (Japanese)

### Stage 1 Parameters (자동 수집)
- `input_file`: data/ 디렉토리에서 자동 감지
- `company`: 파일명에서 자동 추출
- `output_dir`: `results/{company}`로 자동 설정
- `sample_size`: 기본값 3000
- `k`: 기본값 "auto"

### Optional
- **auto_proceed** (default: true): `true` = 단계 간 자동 진행, `false` = 단계마다 확인
- **generate_flowcharts** (default: true): Stage 4 실행 여부
- **flowchart_target** (default: "all"): `"all"`, `"ts_only"`, `"ht_only"`
- **flowchart_format** (default: "markdown"): `"markdown"`, `"svg"`, `"both"`

## Steps

### 1. Initialize Pipeline

**Actions:**
- Detect language from user's first message
- Set `LANGUAGE={language}` for all Python script executions
- Check `.env` for `UPSTAGE_API_KEY`:
  - If missing: run `/request-api-key` flow inline (send Channel.io message, wait for reply, write to .env)
  - MUST NOT proceed until key is confirmed valid
- Validate: `pip install -r requirements.txt`

---

### 2. Execute Stage 1: Clustering

Run `/stage1-clustering` with auto-detected parameters.

**Outputs:**
- `results/{company}/01_clustering/{company}_clustered.xlsx`
- `results/{company}/01_clustering/{company}_tags.xlsx`
- `results/{company}/01_clustering/{company}_messages.csv`
- `results/{company}/01_clustering/analysis_report.md`

**Quality Checks:** Clustering succeeded, no single cluster >50%, silhouette score >0.05

**Transition:** If `auto_proceed=true`, proceed immediately. Otherwise ask user.

---

### 3. Execute Stage 2: Pattern Extraction

Run `/stage2-extraction` with auto-detected parameters.

**Key defaults (updated):**
- `min_total_samples`: **500** (increased from 300)
- `n_samples_per_cluster`: `max(25, ceil(500 / K))`

**Outputs:** `patterns.json` (with `sop_topic_map`), `faq.json`, `keywords.json`, `patterns_enriched.json`

**Quality Checks:** All JSON valid, patterns extracted, FAQ pairs are specific

**Transition:** If `auto_proceed=true`, proceed immediately. Otherwise ask user.

---

### 4. Execute Stage 3: SOP Generation + Verification

Run `/stage3-sop-generation` with auto-detected parameters.

**Key change:** Stage 3 now includes a **verification loop** — each SOP is tested against 3-5 real conversations from enriched data, and gaps are fixed before finalizing.

**Outputs:**
- `results/{company}/03_sop/HT_*.sop.md` (multiple files)
- `results/{company}/03_sop/TS_*.sop.md` (multiple files)
- `results/{company}/03_sop/metadata.json`

**Quality Checks:** Template structure followed, Cases include concrete details, verification coverage >70%

**Transition:** If `auto_proceed=true`, proceed immediately. Otherwise ask user.

---

### 5. Execute Stage 4: Flowchart Generation (optional, default enabled)

Run `/stage4-flowchart-generation`.

**Skip if:** `generate_flowcharts=false` or user declines during review.

**Outputs:** `*_FLOWCHART.md`, optionally `*_flowchart.svg`

---

### 6. Validate and Summarize

**Verify all outputs exist:**
```
results/{company}/
├── 01_clustering/  (clustered.xlsx, tags.xlsx, messages.csv, analysis_report.md)
├── 02_extraction/  (patterns.json, faq.json, keywords.json, patterns_enriched.json)
├── 03_sop/         (HT_*.sop.md, TS_*.sop.md, metadata.json, *_FLOWCHART.md)
└── pipeline_summary.md
```

**Generate `pipeline_summary.md`** with execution info, statistics per stage, verification results, key insights, and next steps.

**Communicate results:**
```
✅ Userchat-to-SOP Pipeline Complete: {Company}

📊 Results
  - Records: {N}, Clusters: {K}
  - Patterns: {P}, FAQ Pairs: {F}
  - SOP Files: {count} (TS: {ts}, HT: {ht})
  - Verification Coverage: {X}%
  - Flowcharts: {fc_count} (if Stage 4)

📁 Output: results/{company}/
```

---

## Pipeline Defaults

| Stage | Parameter | Default |
|-------|-----------|---------|
| 1 | sample_size | 3000 |
| 1 | k_range | 8,10,12,15,20,25 |
| 2 | min_total_samples | **500** |
| 2 | n_samples_per_cluster | max(25, ceil(500/K)) |
| 3 | verification | **enabled** (3-5 conversations per SOP) |
| 4 | flowchart_target | all |
| 4 | flowchart_format | markdown |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Stage 1 fails | `pip install -r requirements.txt`, check UPSTAGE_API_KEY |
| Stage 2 too slow | Reduce `min_total_samples` to 300, or `focus_clusters="top_10"` |
| SOPs too generic | Stage 3 verification should catch this; if not, increase Stage 2 samples |
| Need to resume | Each stage runs independently: `/stage2-extraction`, `/stage3-sop-generation`, etc. |
| Flowchart fails | Use `flowchart_format="markdown"` (no CLI needed) |

## Notes

- **Hybrid approach**: Python for clustering (fast, deterministic), LLM for extraction and composition (language understanding)
- **Stage 2: sequential processing in main agent** — no subagents (causes hanging)
- **Stage 3 verification loop** is the key quality improvement — invests tokens in checking rather than elaborate prompts
- Cost: ~$0.60-2.50 per 1000 records (Upstage + Claude)
- Each stage is independent and can be resumed separately
