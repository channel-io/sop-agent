---
name: userchat-to-sop-pipeline
description: Complete end-to-end pipeline for transforming Excel customer support data into production-ready Agent SOP documents and flowcharts through Clustering, Pattern Extraction, SOP Generation, and Flowchart Generation stages.
---

# Userchat-to-SOP Complete Pipeline

## Overview
This SOP orchestrates the complete end-to-end pipeline for transforming Excel customer support data into production-ready Agent SOP documents with visual flowcharts. It integrates all four stages: Clustering (Python), Pattern Extraction (LLM), SOP Generation (LLM), and Flowchart Generation (LLM + Mermaid).

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

**Pipeline Flow:**
```
Excel Input (고객 상담 데이터)
    ↓
Stage 1: Clustering (Python) [~3 min]
    → clustered_data.xlsx, cluster_tags.xlsx, analysis_report.md
    ↓
Stage 2: Pattern Extraction (LLM) [5-10 min]
    → patterns.json, faq.json, response_strategies.json, keywords.json
    ↓
Stage 3: SOP Generation (LLM) [~5 min]
    → TS_*.sop.md, HT_*.sop.md, metadata.json
    ↓
Stage 4: Flowchart Generation (LLM) [~4 min, (기본 활성화)]
    → *_FLOWCHART.md (Mermaid markdown, SVG 선택)
    ↓
Output: Ready-to-deploy Agent SOP + Visual Flowcharts
```

**Total Time**: ~20-30 minutes (Stage 1-4 full pipeline)

## Parameters

### Required Parameters
- **language** (default: "ko"): Output language for clustering labels and LLM prompts
  - `"ko"`: Korean (한국어)
  - `"ja"`: Japanese (日本語)

### Stage 1 Parameters (자동 수집)
Stage 1은 `/stage1-clustering` 스킬을 호출하여 파라미터를 자동 수집합니다.
- `input_file`: data/ 디렉토리에서 자동 감지 (파일 1개면 자동 선택)
- `company`: 파일명에서 자동 추출
- `output_dir`: `results/{company}`로 자동 설정
- `sample_size`: 기본값 3000 (데이터가 3000건 미만이면 전체)
- `tagging_mode`: 기본값 "agent" (변경 불필요)
- `k`: 기본값 "auto"

**Note:** 파라미터를 묻지 않고 기본값으로 진행합니다. 파일이 여러 개일 때만 선택을 요청합니다.

---

### Optional Parameters (Stage 4)
- **generate_flowcharts** (default: true): Generate flowcharts in Stage 4 (기본 활성화 — 옵션으로 비활성화 가능)
  - `true`: Generate Mermaid flowcharts after SOP generation (recommended)
  - `false`: Skip Stage 4 (flowchart generation)

Note: Stage 4 (Flowchart Generation)은 기본적으로 활성화되어 있으나 옵션으로 비활성화할 수 있습니다. 플로우차트 생성을 건너뛰려면 `generate_flowcharts=false`로 설정하거나 검토 단계에서 생성 여부를 거부하세요.

- **flowchart_target** (default: "all"): Which SOPs to generate flowcharts for
  - `"all"`: Generate for all SOPs (both TS and HT, recommended)
  - `"ts_only"`: Only Troubleshooting SOPs
  - `"ht_only"`: Only How-To SOPs

- **flowchart_format** (default: "markdown"): Flowchart output format
  - `"markdown"`: Mermaid markdown only (recommended, no CLI needed)
  - `"svg"`: SVG images only (requires Mermaid CLI)
  - `"both"`: Both markdown and SVG

- **auto_proceed** (default: true): Automatic stage progression
  - `true`: Auto-proceed through stages without manual review (recommended)
  - `false`: Pause after each stage for review

## Steps

### 1. Initialize Pipeline

Validate environment and prepare for execution.

**Actions:**
- Ask user to select language (Korean / Japanese) using AskUserQuestion if not already specified
- Set `language` variable (`"ko"` or `"ja"`) — all subsequent Python script executions MUST be prefixed with `LANGUAGE={language}`
- Validate Python clustering package is installed
- Check .env file with UPSTAGE_API_KEY: `grep -s "UPSTAGE_API_KEY" .env`
  - If key is missing or is the placeholder `up_YOUR_API_KEY_HERE`:
    1. You MUST run the full `request-api-key` skill flow inline (send Channel.io message to groupId "531940", `sleep 10`, check thread, write key to .env)
    2. You MUST NOT proceed to Stage 1 until the key is confirmed valid
- Print pipeline configuration
- Inform user that Stage 1 will be interactive

**Expected Output:**
```
✅ Pipeline initialized
  - Python package validated
  - API key confirmed
  - Ready for Stage 1 (대화형 파일 선택)

📋 Stage 1 will prompt you to:
  1. Select Excel data file (from data/ directory scan)
  2. Choose company name (auto-extracted from filename)
  3. Confirm output directory (auto-suggested)
  4. (Optional) Adjust clustering parameters

Proceeding to Stage 1...
```

### 2. Execute Stage 1: Clustering

Run clustering via `/stage1-clustering` skill with auto-detected parameters.

**Documentation**: See [stage1-clustering SKILL.md](../stage1-clustering/SKILL.md)

**Execution:**
```bash
# Execute Stage 1 skill
/stage1-clustering

# Stage 1 will:
# 1. Scan data/ directory for Excel files (auto-select if single file)
# 2. Extract company name from filename
# 3. Set output_dir to results/{company}
# 4. Run clustering with defaults (sample_size=3000, k=auto, tagging_mode=agent)
# 5. Generate analysis report
```

**Outputs (Auto-detected for next stages):**
- `results/{company}/01_clustering/{company}_clustered.xlsx` - Full dataset with cluster assignments
- `results/{company}/01_clustering/{company}_tags.xlsx` - Cluster summary
- `results/{company}/01_clustering/analysis_report.md` - Comprehensive analysis for Stage 2

**After Stage 1 Completion:**
Pipeline automatically detects `company` and `output_base_dir` from Stage 1 outputs:
```bash
# Auto-detection logic
output_base_dir="results/{company}"  # From Stage 1 output path
company="{company}"                   # From Stage 1 output prefix

# Validate Stage 1 outputs exist
✓ {output_base_dir}/01_clustering/{company}_clustered.xlsx
✓ {output_base_dir}/01_clustering/{company}_tags.xlsx
✓ {output_base_dir}/01_clustering/analysis_report.md
```

**Quality Checks:**
- [ ] Clustering completed successfully
- [ ] Analysis report generated and readable
- [ ] Cluster distribution is balanced (no single cluster >50%)
- [ ] Silhouette score is reasonable (>0.05)
- [ ] Category labels are meaningful
- [ ] No critical data quality issues

**Stage Transition:**

**IF auto_proceed=true (기본값):**
- You MUST automatically proceed to Stage 2 WITHOUT asking user
- You MUST display: "✅ Stage 1 complete. Auto-proceeding to Stage 2..."
- You MUST NOT use read -p or AskUserQuestion
- You MUST skip to Step 3 immediately

**IF auto_proceed=false:**
- You MUST display: "📋 Review analysis report: $output_base_dir/01_clustering/analysis_report.md"
- You MUST ask via AskUserQuestion: "Stage 1 완료. Stage 2 (Pattern Extraction)로 진행할까요?"
- You MUST wait for user confirmation before proceeding

### 3. Execute Stage 2: Pattern Extraction

Use LLM to extract patterns, FAQs, and response strategies from clusters.

**Documentation**: See [stage2-extraction SKILL.md](../stage2-extraction/SKILL.md)

**Execution:**
```bash
# In Claude Code:
/stage2-extraction

# Parameters (auto-detected from Stage 1):
# - clustering_output_dir: $output_base_dir/01_clustering
# - company: $company
# - n_samples_per_cluster: 20
```

**Inputs:**
- Stage 1 outputs (in `$output_base_dir/01_clustering/`): `{company}_clustered.xlsx`, `{company}_tags.xlsx`, `analysis_report.md`

**Outputs:**
- `patterns.json` - Extracted patterns per cluster
- `faq.json` - FAQ pairs for common inquiries
- `response_strategies.json` - Response strategies and escalation rules
- `keywords.json` - Keyword taxonomy
- `extraction_summary.md` - Summary and recommendations

**Expected Duration**: ~5-10 minutes

**Quality Checks:**
- [ ] All JSON files generated and valid
- [ ] Patterns extracted for top 10 clusters
- [ ] FAQ pairs are specific and actionable
- [ ] Response strategies include escalation rules
- [ ] Keyword taxonomy is comprehensive
- [ ] Extraction summary highlights automation opportunities

**Stage Transition:**

**IF auto_proceed=true (기본값):**
- You MUST automatically proceed to Stage 3 WITHOUT asking user
- You MUST display: "✅ Stage 2 complete. Auto-proceeding to Stage 3..."
- You MUST NOT use read -p or AskUserQuestion
- You MUST skip to Step 4 immediately

**IF auto_proceed=false:**
- You MUST display: "📋 Review extraction summary: $output_base_dir/02_extraction/extraction_summary.md"
- You MUST ask via AskUserQuestion: "Stage 2 완료. Stage 3 (SOP Generation)로 진행할까요?"
- You MUST wait for user confirmation before proceeding

### 4. Execute Stage 3: SOP Generation

Use LLM to generate Agent SOP documents from extracted patterns, organized by customer journey stages.

**Documentation**: See [stage3-sop-generation SKILL.md](../stage3-sop-generation/SKILL.md)

**Execution:**
```bash
# In Claude Code:
/stage3-sop-generation

# Parameters (auto-detected from Stage 2):
# - extraction_output_dir: $output_base_dir/02_extraction
# - company: $company
```

**Inputs:**
- Stage 2 outputs: `patterns_enriched.json`, `faq.json`, `response_strategies.json`, `keywords.json`

**Outputs:**
- `03_sop/HT_*.sop.md` - 10-15개 SOP 파일 (고객 여정 기반)
- `03_sop/TS_*.sop.md`
- `metadata.json` - SOP metadata

**Expected Duration**: ~5-10 minutes

**Quality Checks:**
- [ ] Multiple SOP files generated (TS_*.sop.md, HT_*.sop.md)
- [ ] 템플릿 구조 준수 (목적, 주의사항, 내용/문제해결프로세스, 톤앤매너, 에스컬레이션)
- [ ] Steps reference extracted patterns and FAQs
- [ ] Examples are concrete and realistic
- [ ] Troubleshooting section addresses common issues
- [ ] Text is natural and professional in the detected language
- [ ] `metadata.json` is complete and accurate

**Stage Transition:**

**IF auto_proceed=true (기본값):**
- You MUST automatically proceed to Stage 4 WITHOUT asking user
- You MUST display: "✅ Stage 3 complete. Auto-proceeding to Stage 4..."
- You MUST NOT use read -p or AskUserQuestion
- You MUST skip to Step 5 immediately

**IF auto_proceed=false:**
- You MUST display: "📋 Review generated SOPs: $output_base_dir/03_sop/"
- You MUST ask via AskUserQuestion: "Stage 3 완료. Stage 4 (Flowchart Generation)로 진행할까요?"
- You MUST wait for user confirmation before proceeding

### 5. Execute Stage 4: Flowchart Generation (Required)

Generate Mermaid flowcharts from SOP documents.

**Documentation**: See [stage4-flowchart-generation SKILL.md](../stage4-flowchart-generation/SKILL.md)

**Execution:**
```bash
# In Claude Code:
/stage4-flowchart-generation

# Parameters:
# - sop_dir: $output_base_dir/03_sop
# - target_sops: "all"
# - output_format: "markdown"
```

**Inputs:**
- Stage 3 outputs: `TS_*.sop.md`, `HT_*.sop.md`

**Outputs:**
- `*_FLOWCHART.md` - Mermaid flowchart markdown (required)
- `*_flowchart.svg` - SVG images (optional, only if user has Mermaid CLI)
- `flowchart_generation_summary.md` - Summary report

**Expected Duration**: ~3-5 minutes

**Quality Checks:**
- [ ] Flowchart markdown files generated for all target SOPs
- [ ] Flowcharts render correctly in VSCode/GitHub (markdown preview)
- [ ] Decision trees are clear and logical
- [ ] Color coding is applied correctly
- [ ] Escalation paths are visible
- [ ] SVG images generated (optional, if CLI available)

**Skip Conditions (Stage 4 is optional; default: enabled):**
- `generate_flowcharts=false` (사용자가 명시적으로 비활성화)
- User declines during review pause (검토 단계에서 생성 거부)

설명: Stage 4은 기본적으로 활성화되어 있으나 필요에 따라 건너뛸 수 있습니다. 위 두 조건 중 하나가 충족되면 플로우차트 생성은 수행되지 않습니다.

### 6. Validate Complete Pipeline

Perform final validation of all outputs.

**Actions:**
- Verify all output files exist
- Validate file sizes are reasonable (not empty)
- Check JSON files are valid JSON
- Verify markdown files render correctly
- Generate pipeline summary report

**Files to Check:**
```
$output_base_dir/
├── 01_clustering/
│   ├── {company}_clustered.xlsx
│   ├── {company}_tags.xlsx
│   └── analysis_report.md
├── 02_extraction/
│   ├── patterns.json
│   ├── faq.json
│   ├── response_strategies.json
│   ├── keywords.json
│   └── extraction_summary.md
├── 03_sop/
│   ├── TS_*.sop.md (multiple files)
│   ├── HT_*.sop.md (multiple files)
│   ├── *_FLOWCHART.md (if Stage 4 executed)
│   ├── *_flowchart.svg (if Stage 4 executed with CLI)
│   ├── metadata.json
│   └── generation_summary.md
└── pipeline_summary.md (generated in next step)
```

**Expected Output (without Stage 4):**
```
✅ All output files validated
  - Stage 1: 3 files
  - Stage 2: 5 files
  - Stage 3: 10+ files (multiple SOPs)
Total: 18+ files, pipeline complete (Stage 1-3)
```

**Expected Output (with Stage 4):**
```
✅ All output files validated
  - Stage 1: 3 files
  - Stage 2: 5 files
  - Stage 3: 10+ files (multiple SOPs)
  - Stage 4: 14+ files (7 FLOWCHART.md + 7 SVG)
Total: 32+ files, full pipeline complete (Stage 1-4)
```

### 7. Generate Pipeline Summary

Create comprehensive summary of pipeline execution and results.

**Summary Contents:**
- Execution information (date, duration, parameters)
- Stage 1 statistics (records, clusters, silhouette score, top category)
- Stage 2 statistics (patterns, FAQs, automation opportunities)
- Stage 3 statistics (SOP files, types, total lines)
- Stage 4 statistics (flowcharts generated, SVG status) - if executed
- Key insights from all stages
- Next steps for deployment
- Quality metrics

**Output:** `{output_base_dir}/pipeline_summary.md`

**Template:**
```markdown
# Userchat-to-SOP Pipeline Summary

## Execution Information
- Company: {company}
- Execution Date: {timestamp}
- Total Duration: {duration}
- Stages Executed: {stages} (1-3 or 1-4)

## Stage Results

### Stage 1: Clustering
- Records: {N}, Clusters: {K}, Score: {score}

### Stage 2: Pattern Extraction
- Patterns: {P}, FAQs: {F}, Strategies: {S}

### Stage 3: SOP Generation
- TS SOPs: {TS_count} files
- HT SOPs: {HT_count} files
- Total Lines: {total_lines}

### Stage 4: Flowchart Generation (if executed)
- Flowcharts: {flowchart_count} (TS: {ts_fc}, HT: {ht_fc})
- SVG Images: {svg_count} (CLI: {cli_status})

## Key Insights
1. {insight_1}
2. {insight_2}
3. {insight_3}

## Next Steps
1. Review SOPs: {sop_dir}
2. Review flowcharts (if generated): {flowchart_dir}
3. Test with sample inquiries
4. Deploy to Claude Skills
5. Monitor metrics
```

### 8. Communicate Results

Present pipeline results to stakeholders.

**Communication Template:**
```
✅ Userchat-to-SOP Pipeline Complete: {Company}

📊 Pipeline Results
  - Total Records: {N:,}
  - Clusters: {K}
  - Patterns: {P}
  - FAQ Pairs: {F}
  - SOP Files: {sop_count} (TS: {ts_count}, HT: {ht_count})
  - Flowcharts: {flowchart_count} (if Stage 4 executed)

💡 Key Insights
  1. {insight from analysis report}
  2. {insight from extraction}
  3. {automation opportunity}

📁 Output Files
  - Analysis Report: {path}/01_clustering/analysis_report.md
  - Extraction Summary: {path}/02_extraction/extraction_summary.md
  - SOP Documents: {path}/03_sop/TS_*.sop.md, HT_*.sop.md
  - Flowcharts: {path}/03_sop/*_FLOWCHART.md (if generated)

🚀 Next Steps
  1. Review analysis report and SOPs
  2. Review flowcharts (if generated)
  3. Test SOPs with sample inquiries
  4. Deploy via Claude Skills
  5. Monitor key metrics
```

## Examples

### Example 1: Standard Production Run (Full 4-Stage Pipeline)

**Scenario**: Complete pipeline with flowcharts (default configuration)

**Execution:**
```bash
/userchat-to-sop-pipeline
```

**Stage 1 (대화형 파라미터 수집):**
- 📁 File selection: `data/user_chat_channelcorp.xlsx` (선택)
- 🏢 Company: "channelcorp" (자동 추출)
- 📂 Output: `results/channelcorp` (자동 제안)
- ⚙️ Clustering: sample_size=all, k=auto, tagging_mode=agent (기본값)

**Optional Parameters (Stage 2-4):**
```bash
min_total_samples=300            # Stage 2 (default, dynamically adjusts per-cluster count)
sop_detail_level="standard"     # Stage 3 (default)
generate_flowcharts=true        # Stage 4 (default)
flowchart_target="all"          # Stage 4 (default)
auto_proceed=false              # Pause for review
```

**Timeline:**
- Stage 1 (Clustering): 3 minutes (대화형 포함)
- Review & Approve: 2 minutes
- Stage 2 (Extraction): 7 minutes
- Review & Approve: 3 minutes
- Stage 3 (SOP Generation): 5 minutes
- Review & Approve: 2 minutes
- Stage 4 (Flowcharts): 4 minutes
- Validation & Summary: 1 minute
- **Total**: 27 minutes

**Results:**
- 10 clusters, 37 patterns, 52 FAQ pairs
- 7 SOP files (TS: 4, HT: 3), ~5,000 total lines
- 7 flowchart markdowns
- Key insight: A/S inquiries dominate (48%)

### Example 2: Quick Production Run (Auto-proceed Mode)

**Scenario**: Fast pipeline execution without manual review pauses

**Execution:**
```bash
/userchat-to-sop-pipeline
```

**Stage 1 (대화형):**
- 파일, 회사명, 출력 경로 선택 (대화형)
- Clustering 파라미터는 기본값 사용

**Optional Parameters:**
```bash
auto_proceed=true  # No pauses (자동 진행)
```

**Timeline:**
- Stage 1: 3 minutes (대화형 포함)
- Stage 2: 7 minutes (auto-proceed)
- Stage 3: 5 minutes (auto-proceed)
- Stage 4: 4 minutes (auto-proceed)
- Validation: 1 minute
- **Total**: 20 minutes

**Results:**
- 10 clusters, 37 patterns, 52 FAQ pairs
- 7 SOP files (TS: 4, HT: 3)
- 7 flowchart markdowns

### Example 3: Quick Test Run

**Scenario**: Quick validation before full run

**Execution:**
```bash
/userchat-to-sop-pipeline
```

**Stage 1 (대화형):**
- 📁 File: `data/user_chat_test.xlsx` (선택)
- 🏢 Company: "testco" (자동)
- 📂 Output: `results/testco` (자동)
- ⚙️ **Clustering 조정**: sample_size=1000, k=15 (대화형에서 조정)

**Optional Parameters:**
```bash
n_samples_per_cluster=10        # Stage 2 (빠른 분석)
sop_detail_level="concise"      # Stage 3 (간소화)
flowchart_target="ts_only"      # Stage 4 (TS만)
auto_proceed=true               # 자동 진행
```

**Timeline:**
- Stage 1: 2 minutes (1000개, K=15)
- Stage 2: 4 minutes (10 samples/cluster)
- Stage 3: 3 minutes (concise)
- Stage 4: 2 minutes (TS only)
- **Total**: 11 minutes

**Results:**
- 15 clusters, 25 patterns
- 5 SOP files, ~2,500 total lines
- 3 TS flowcharts

## Troubleshooting

### Issue: Stage 1 Clustering Fails

**Solution:**
1. Verify Python package: `pip install -r requirements.txt`
2. Check input file format (required sheets present)
3. Verify environment variables (UPSTAGE_API_KEY)
4. Run Stage 1 independently: `/stage1-clustering`
5. Check logs for specific error messages

### Issue: Stage 2 Takes Too Long

**Solution:**
1. Reduce `n_samples_per_cluster` to 10 or 20 (standard)
2. Use `focus_clusters="top_10"` to analyze only top clusters
3. Consider re-running Stage 1 with lower K value

### Issue: Generated SOP is Too Generic

**Solution:**
1. Review Stage 2 extraction quality
2. Re-run Stage 2 with `n_samples_per_cluster=30`
3. Manually enhance Stage 3 output with company-specific details
4. Include more sample messages in extraction

### Issue: Pipeline Paused, Need to Resume

**Solution:**
Each stage is independent and can be resumed:

```bash
# Resume from Stage 2
/stage2-extraction
# (provide clustering_output_dir parameter)

# Resume from Stage 3
/stage3-sop-generation
# (provide extraction_output_dir parameter)

# Resume from Stage 4
/stage4-flowchart-generation
# (provide sop_dir parameter)
```

### Issue: Flowchart Generation Fails (Stage 4)

**Solution:**
1. Check if Mermaid CLI is installed: `mmdc --version`
2. If not installed and SVG needed: `npm install -g @mermaid-js/mermaid-cli`
3. If CLI not needed: Use `output_format="markdown"` for markdown-only
4. Verify SOP files exist and are valid markdown
5. Run Stage 4 independently: `/stage4-flowchart-generation`

## Related Documentation

- **Stage 1 Clustering**: [stage1-clustering SKILL.md](../stage1-clustering/SKILL.md)
- **Stage 2 Extraction**: [stage2-extraction SKILL.md](../stage2-extraction/SKILL.md)
- **Stage 3 SOP Generation**: [stage3-sop-generation SKILL.md](../stage3-sop-generation/SKILL.md)
- **Stage 4 Flowchart Generation**: [stage4-flowchart-generation SKILL.md](../stage4-flowchart-generation/SKILL.md)
- **HT/TS Templates**: `templates/HT_template.md`, `templates/TS_template.md`
- **Detailed Clustering Guide**: `../docs/clustering-guide.md`

## Notes

### Why Hybrid Approach (Python + LLM)?

**Python (Stage 1):**
- Embedding generation: Computational, benefits from caching
- K-Means clustering: Statistical algorithm, fast and reliable
- Results in 2-3 minutes (vs 30+ min if done by LLM)

**LLM (Stage 2, 3):**
- Pattern extraction: Requires language understanding
- FAQ generation: Natural language composition
- SOP writing: Structured document creation with domain reasoning

**Hybrid = Best of Both Worlds**

### Stage 2 Execution Strategy

**Important Implementation Details:**

⚠️ **Stage 2 uses sequential processing in main agent**
- Do NOT use subagent (Task agent) - causes performance degradation and hanging issues
- Sequential cluster analysis in main agent is faster and more stable
- Parallel processing attempts increase execution time and instability

✅ **Enrichment is always generated**
- `patterns_enriched.json` file is automatically generated in Stage 2 Step 7
- Includes 10 representative conversation samples + 20 tone-and-manner samples per cluster
- Stage 3 uses this file to generate richer SOPs

**See `/stage2-extraction` skill for detailed execution strategy**

### Pipeline Defaults

기본 설정 (파라미터 질문 없이 바로 실행):

| Stage | 파라미터 | 기본값 |
|-------|---------|--------|
| Stage 1 | sample_size | 3000 |
| Stage 1 | umap | true (4096D → 30D) |
| Stage 1 | k_range | 8,10,12,15,20,25 |
| Stage 1 | tagging_mode | agent |
| Stage 2 | min_total_samples | 300 |
| Stage 2 | n_samples_per_cluster | max(20, ceil(300/K)) |
| Stage 3 | SOP 구성 | 고객 여정 기반 ~10-15개 |
| Stage 4 | flowchart_target | all |
| Stage 4 | flowchart_format | markdown |

Stage 4를 건너뛰려면 `generate_flowcharts=false`로 설정.

### Cost Estimates (per 1000 records)

**Stage 1 (Upstage Solar):**
- Embeddings: $0.05
- Tagging: $0.01-0.02

**Stage 2 & 3 (Claude Sonnet 4.5):**
- Varies by depth
- Typical: $0.50-2.00 per full pipeline run

**Total**: ~$0.60-2.50 per 1000 records

### Monitoring & Iteration

After SOP deployment:

1. **Week 1-2**: Pilot with small team
2. **Week 3-4**: Refine based on feedback
3. **Month 2**: Full rollout, track metrics
4. **Quarterly**: Re-run pipeline with new data

**Metrics to Track:**
- First-contact resolution rate
- Average response time
- Escalation rate
- Customer satisfaction score
- Agent feedback on SOP usability

---

**This is an orchestration SOP**. For detailed implementation of each stage, refer to the stage-specific SOPs linked above.
