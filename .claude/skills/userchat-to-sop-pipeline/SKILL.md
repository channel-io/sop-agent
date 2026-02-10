---
name: userchat-to-sop-pipeline
description: Complete end-to-end pipeline for transforming Excel customer support data into production-ready Agent SOP documents and flowcharts through Clustering, Pattern Extraction, SOP Generation, and Flowchart Generation stages.
type: anthropic-skill
version: "1.0"
---

# Userchat-to-SOP Complete Pipeline

## Overview
This SOP orchestrates the complete end-to-end pipeline for transforming Excel customer support data into production-ready Agent SOP documents with visual flowcharts. It integrates all four stages: Clustering (Python), Pattern Extraction (LLM), SOP Generation (LLM), and Flowchart Generation (LLM + Mermaid).

**Language:** All user interactions MUST be conducted in Korean (한국어). Questions, confirmations, and outputs should be in Korean unless the user explicitly requests English.

**Pipeline Flow:**
```
Excel Input (고객 상담 데이터)
    ↓
Stage 1: Clustering (Python) [5-10 min]
    → clustered_data.xlsx, cluster_tags.xlsx, analysis_report.md
    ↓
Stage 2: Pattern Extraction (LLM) [10-35 min]
    → patterns.json, faq.json, response_strategies.json, keywords.json
    ↓
Stage 3: SOP Generation (LLM) [10-25 min]
    → TS_*.sop.md, HT_*.sop.md, metadata.json
    ↓
Stage 4: Flowchart Generation (LLM) [5-10 min, (기본 활성화)]
    → *_FLOWCHART.md (Mermaid markdown, SVG 선택)
    ↓
Output: Ready-to-deploy Agent SOP + Visual Flowcharts
```

**Total Time**: 30-80 minutes (Stage 1-4 full pipeline)
- Quick mode: ~40 minutes
- Standard mode: ~55 minutes
- Comprehensive mode: ~70-80 minutes

## Parameters

### Required
- **input_file**: Path to Excel file with customer support chat data
  - Example: `data/raw/user_chat_{company}.xlsx`
  - Must have "UserChat data" and "Message data" sheets

- **company**: Company name
  - Example: "Channel Corp."
  - Used throughout all stages for context

- **output_base_dir**: Base output directory
  - Example: `results/{company}`
  - Structure: `{output_base_dir}/{01_clustering,02_extraction,03_sop}/`

### Optional
- **sample_size** (default: 1000): Data sampling for Stage 1
  - 1000: Standard analysis (recommended default)
  - `"all"`: Full dataset (only if explicitly needed)

- **tagging_mode** (default: "agent"): Clustering tagging method (Stage 1)
  - `"agent"`: Fast unified tagging (5-15 sec, industry-adaptive, recommended)
  - `"api"`: Independent tagging (30 sec, hardcoded categories)

- **k** (default: "auto"): Number of clusters (Stage 1)
  - `"auto"`: Automatic optimal K selection
  - Integer: Fixed K value

- **extraction_depth** (default: "standard"): Pattern extraction detail (Stage 2)
  - `"quick"`: Patterns + Keywords + FAQ + Strategies (간소화, ~5-8분)
    - FAQ 10-15개, Strategies 핵심만, 빠른 분석
  - `"standard"`: Patterns + Keywords + FAQ + Strategies (상세, ~8-12분)
    - FAQ 30-50개, Strategies 전체, 균형잡힌 분석
  - `"deep"`: Standard + patterns_enriched.json + 예시/edge cases (~15-20분)
    - 샘플 임베딩, 더 많은 예시, 심층 분석

- **sop_detail_level** (default: "standard"): SOP detail level (Stage 3)
  - `"concise"`: Minimal SOP (~500 lines)
  - `"standard"`: Balanced (~1000 lines)
  - `"comprehensive"`: Full detail (~2000 lines)

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

- **auto_proceed** (default: false): Automatic stage progression
  - `true`: Auto-proceed through stages without manual review
  - `false`: Pause after each stage for review

## Steps

### 1. Initialize Pipeline

Set up directory structure and validate inputs.

**Actions:**
- Verify input file exists and has correct format
- Create output directory structure: `{output_base_dir}/{01_clustering,02_extraction,03_sop}/`
- Validate Python clustering package is installed
- Print pipeline configuration
- Prompt user to confirm (if `auto_proceed=false`)

**Expected Output:**
```
✅ Pipeline initialized
  - Output directories created
  - Python package validated
  - Configuration confirmed

Ready to start Stage 1 (Clustering)...
```

### 2. Execute Stage 1: Clustering

Run Python clustering pipeline to analyze and cluster customer data.

**Documentation**: See [stage1-clustering.sop.md](stage1-clustering.sop.md)

**Execution:**
```bash
clustering-userchat \
  --input "$input_file" \
  --output "$output_base_dir/01_clustering" \
  --prefix "$company" \
  --sample "$sample_size" \
  --tagging-mode "$tagging_mode" \
  --k "$k"
```

**Outputs:**
- `{company}_clustered.xlsx` - Full dataset with cluster assignments
- `{company}_tags.xlsx` - Cluster summary
- `analysis_report.md` - Comprehensive analysis for Stage 2

**Quality Checks:**
- [ ] Clustering completed successfully
- [ ] Analysis report generated and readable
- [ ] Cluster distribution is balanced (no single cluster >50%)
- [ ] Silhouette score is reasonable (>0.05)
- [ ] Category labels are meaningful
- [ ] No critical data quality issues

**Pause for Review (if auto_proceed=false):**
```bash
echo "Review analysis report: $output_base_dir/01_clustering/analysis_report.md"
read -p "Proceed to Stage 2? (y/n) "
```

### 3. Execute Stage 2: Pattern Extraction

Use LLM to extract patterns, FAQs, and response strategies from clusters.

**Documentation**: See [stage2-extraction.sop.md](stage2-extraction.sop.md)

**Execution:**
```bash
# In Claude Code, execute:
/stage2-extraction

# With parameters:
# - clustering_output_dir: $output_base_dir/01_clustering
# - company: $company
# - extraction_depth: $extraction_depth
```

**Inputs:**
- Stage 1 outputs: `clustered_data.xlsx`, `tags.xlsx`, `analysis_report.md`

**Outputs:**
- `patterns.json` - Extracted patterns per cluster
- `faq.json` - FAQ pairs for common inquiries
- `response_strategies.json` - Response strategies and escalation rules
- `keywords.json` - Keyword taxonomy
- `extraction_summary.md` - Summary and recommendations

**Expected Duration:**
- Quick: ~10-15 minutes
- Standard: ~15-25 minutes
- Deep: ~25-35 minutes

**Quality Checks:**
- [ ] All JSON files generated and valid
- [ ] Patterns extracted for top 10 clusters
- [ ] FAQ pairs are specific and actionable
- [ ] Response strategies include escalation rules
- [ ] Keyword taxonomy is comprehensive
- [ ] Extraction summary highlights automation opportunities

**Pause for Review (if auto_proceed=false):**
```bash
echo "Review extraction summary: $output_base_dir/02_extraction/extraction_summary.md"
read -p "Proceed to Stage 3? (y/n) "
```

### 4. Execute Stage 3: SOP Generation

Use LLM to generate final Agent SOP document from extracted patterns.

**Documentation**: See [stage3-sop-generation.sop.md](stage3-sop-generation.sop.md)

**Execution:**
```bash
# In Claude Code, execute:
/stage3-sop-generation

# With parameters:
# - extraction_output_dir: $output_base_dir/02_extraction
# - company: $company
# - sop_title: "${company} Customer Support Assistant"
# - detail_level: $sop_detail_level
```

**Inputs:**
- Stage 2 outputs: `patterns.json`, `faq.json`, `response_strategies.json`, `keywords.json`

**Outputs:**
- `{company}_support.sop.md` - Complete Agent SOP document
- `metadata.json` - SOP metadata

**Expected Duration:**
- Concise: ~4 minutes (병렬 에이전트)
- Standard: ~6 minutes (병렬 에이전트)
- Comprehensive: ~10 minutes

**Quality Checks:**
- [ ] Multiple SOP files generated (TS_*.sop.md, HT_*.sop.md)
- [ ] All required sections present (Overview, Parameters, Steps, Examples)
- [ ] RFC 2119 keywords used correctly
- [ ] Steps reference extracted patterns and FAQs
- [ ] Examples are concrete and realistic
- [ ] Troubleshooting section addresses common issues
- [ ] Korean text is natural and professional
- [ ] `metadata.json` is complete and accurate

**Pause for Review (if auto_proceed=false):**
```bash
echo "Review generated SOPs: $output_base_dir/03_sop/"
read -p "Continue to Stage 4 (Flowcharts)? (y/n) "
```

### 5. Execute Stage 4: Flowchart Generation (Required)

Generate Mermaid flowcharts from SOP documents for visual process documentation.

**Documentation**: See [stage4-flowchart-generation.sop.md](stage4-flowchart-generation.sop.md)

**Execution:**
```bash
# In Claude Code, execute:
/stage4-flowchart-generation

# With parameters:
# - sop_dir: $output_base_dir/03_sop
# - target_sops: $flowchart_target (default: "all")
# - output_format: "markdown" (SVG generation skipped by default)
```

**Inputs:**
- Stage 3 outputs: `TS_*.sop.md`, `HT_*.sop.md`

**Outputs:**
- `*_FLOWCHART.md` - Mermaid flowchart markdown (required)
- `*_flowchart.svg` - SVG images (optional, only if user has Mermaid CLI)
- `flowchart_generation_summary.md` - Summary report

**Expected Duration:**
- All SOPs markdown: ~5 minutes
- With SVG conversion: ~8 minutes (if CLI installed)

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

**Parameters:**
```bash
input_file="data/raw/user_chat_{company}.xlsx"
company="Channel Corp."
output_base_dir="results/channelcorp"
sample_size="all"  # Full dataset
tagging_mode="agent"
k="auto"
extraction_depth="standard"
sop_detail_level="standard"
generate_flowcharts=true  # Default: enabled
flowchart_target="all"  # Default: all SOPs
flowchart_format="markdown"  # Default: markdown only (no SVG)
auto_proceed=false  # Pause for review after each stage
```

**Timeline:**
- Stage 1 (Clustering): 6 minutes
- Review & Approve: 3 minutes
- Stage 2 (Extraction): 20 minutes
- Review & Approve: 5 minutes
- Stage 3 (SOP Generation): 15 minutes (병렬 생성)
- Review & Approve: 3 minutes
- Stage 4 (Flowcharts - Markdown): 8 minutes
- Validation & Summary: 2 minutes
- **Total**: 62 minutes

**Results:**
- 10 clusters, 37 patterns, 52 FAQ pairs
- 7 SOP files (TS: 4, HT: 3), ~5,000 total lines
- 7 flowchart markdowns (no SVG)
- Key insight: A/S inquiries dominate (48%)

### Example 2: Quick Production Run (Auto-proceed Mode)

**Scenario**: Fast pipeline execution without manual review pauses

**Parameters:**
```bash
input_file="data/raw/user_chat_{company}.xlsx"
company="Channel Corp."
output_base_dir="results/channelcorp"
sample_size="all"
tagging_mode="agent"
k="auto"
extraction_depth="standard"
sop_detail_level="standard"
generate_flowcharts=true  # Default: enabled
flowchart_target="all"  # Default: all SOPs
flowchart_format="markdown"  # Default: markdown only
auto_proceed=true  # No pauses
```

**Timeline:**
- Stage 1: 5 minutes
- Stage 2: 8 minutes (병렬 에이전트)
- Stage 3: 6 minutes (병렬 에이전트)
- Stage 4: 5 minutes
- Validation: 1 minute
- **Total**: 25 minutes

**Results:**
- 10 clusters, 37 patterns, 52 FAQ pairs
- 7 SOP files (TS: 4, HT: 3)
- 7 flowchart markdowns (Mermaid)

### Example 3: Quick Test Run

**Scenario**: Quick validation before full run

**Parameters:**
```bash
input_file="data/raw/user_chat_test.xlsx"
company="TestCo"
output_base_dir="results/test"
sample_size=1000
tagging_mode="agent"
k=15
extraction_depth="quick"
sop_detail_level="concise"
generate_flowcharts=true  # Default: enabled
flowchart_target="ts_only"  # Only TS for quick test
flowchart_format="markdown"  # Default: markdown only
auto_proceed=true  # Automatic, no pauses
```

**Timeline:**
- Stage 1: 3 minutes (K 고정)
- Stage 2: 5 minutes (병렬 에이전트, quick)
- Stage 3: 4 minutes (병렬 에이전트, concise)
- Stage 4: 3 minutes (TS only)
- **Total**: 15 minutes

**Results:**
- 15 clusters, 25 patterns
- 5 SOP files, ~2,500 total lines
- 3 TS flowcharts (Markdown)

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
1. Reduce `extraction_depth` to "quick" or "standard"
2. Use `focus_clusters="top_10"` to analyze only top clusters
3. Consider re-running Stage 1 with lower K value

### Issue: Generated SOP is Too Generic

**Solution:**
1. Review Stage 2 extraction quality
2. Re-run Stage 2 with `extraction_depth="deep"`
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

- **Stage 1 Clustering**: [stage1-clustering.sop.md](stage1-clustering.sop.md)
- **Stage 2 Extraction**: [stage2-extraction.sop.md](stage2-extraction.sop.md)
- **Stage 3 SOP Generation**: [stage3-sop-generation.sop.md](stage3-sop-generation.sop.md)
- **Stage 4 Flowchart Generation**: [stage4-flowchart-generation.sop.md](stage4-flowchart-generation.sop.md)
- **HT/TS Templates**: `templates/HT_template.md`, `templates/TS_template.md`
- **Detailed Clustering Guide**: `../docs/clustering-guide.md`

## Notes

### Why Hybrid Approach (Python + LLM)?

**Python (Stage 1):**
- Embedding generation: Computational, benefits from caching
- K-Means clustering: Statistical algorithm, fast and reliable
- Results in 3-5 minutes (vs 30+ min if done by LLM)

**LLM (Stage 2, 3):**
- Pattern extraction: Requires language understanding
- FAQ generation: Natural language composition
- SOP writing: Structured document creation with domain reasoning

**Hybrid = Best of Both Worlds**

### Pipeline Customization

Choose configuration based on use case:

**Quick Prototype** (~15 min, Stage 1-4):
- sample_size: 1000
- extraction_depth: "quick"
- sop_detail_level: "concise"
- generate_flowcharts: true
- flowchart_target: "ts_only"
- flowchart_format: "markdown"

**Standard Production** (~20 min, Stage 1-4, 기본값):
- sample_size: "all"
- extraction_depth: "standard"
- sop_detail_level: "standard"
- generate_flowcharts: true
- flowchart_target: "all"
- flowchart_format: "markdown"

**Comprehensive Analysis** (~30 min, Stage 1-4):
- sample_size: "all"
- extraction_depth: "deep"
- sop_detail_level: "comprehensive"
- generate_flowcharts: true
- flowchart_target: "all"
- flowchart_format: "markdown"

**Legacy Mode** (~15 min, Stage 1-3 only):
- sample_size: "all"
- extraction_depth: "standard"
- sop_detail_level: "standard"
- generate_flowcharts: false  # Skip Stage 4

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
