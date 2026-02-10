---
name: stage4-flowchart-generation
description: Generate Mermaid flowcharts from Stage 3 SOP documents and convert to SVG images. Visualizes customer support processes with color-coded decision trees. **Language:** All user interactions MUST be conducted in Korean (한국어).
type: anthropic-skill
version: "1.0"
---

# Stage 4: Flowchart Generation

## Overview
This SOP guides the automatic generation of Mermaid flowcharts from SOP documents created in Stage 3. This is **Stage 4** (optional enhancement stage) of the Excel-to-SOP pipeline, performed by the AI agent using natural language analysis and Mermaid diagram generation.

**Language:** All user interactions MUST be conducted in Korean (한국어). Questions, confirmations, and outputs should be in Korean unless the user explicitly requests English.

**Stage Flow:**
```
Input: Stage 3 SOP documents (03_sop/*.sop.md)
    ↓
Process: AI analysis of SOP structure
    ↓
Generate: Mermaid flowchart syntax
    ↓
Convert: SVG image generation (mmdc CLI)
    ↓
Output: Flowchart Markdown + SVG files
```

**Total Time**: 5-15 minutes (depends on number of SOPs)

## Parameters

### Required
- **sop_dir**: Directory containing Stage 3 SOP files
  - Example: `results/{company}/03_sop`
  - Must contain `.sop.md` files

### Optional
- **target_sops** (default: "all"): Which SOPs to generate flowcharts for
  - `"all"`: Generate for all SOPs (both TS and HT)
  - `"ts_only"`: Only Troubleshooting SOPs (recommended for complex processes)
  - `"ht_only"`: Only How-To SOPs
  - List: `["TS_001", "HT_002"]` - Specific SOP IDs

- **output_format** (default: "both"): Output file format
  - `"markdown"`: Mermaid markdown only
  - `"svg"`: SVG image only
  - `"both"`: Both markdown and SVG (recommended)

- **diagram_style** (default: "standard"): Flowchart complexity
  - `"simple"`: Basic decision tree (5-10 nodes)
  - `"standard"`: Balanced detail (15-30 nodes)
  - `"detailed"`: Full process with all cases (30+ nodes)

- **color_scheme** (default: "status"): Color coding strategy
  - `"status"`: Success (green), Warning (yellow), Error (red), Info (blue)
  - `"priority"`: High/Medium/Low priority
  - `"none"`: No color coding

## Steps

### 1. Validate Inputs

Verify Stage 3 SOP files and Mermaid CLI installation.

**Actions:**
- Check `sop_dir` exists and contains `.sop.md` files
- Verify Mermaid CLI is installed: `mmdc --version`
- If CLI not installed:
  - ⚠️ Warn user that SVG generation will be skipped
  - Automatically adjust output_format to "markdown" only
  - Continue with Mermaid markdown generation
- Count number of SOPs to process
- Filter by target_sops parameter

**Expected Output (CLI installed):**
```
✅ Stage 4 준비 완료
  - SOP 디렉토리: results/{company}/03_sop
  - 발견된 SOP: 7개 (TS: 4개, HT: 3개)
  - 처리 대상: 7개 (전체) 또는 4개 (TS만) 또는 3개 (HT만)
  - Mermaid CLI: 설치됨 (v11.12.0)
  - 출력 형식: Markdown + SVG
```

**Expected Output (CLI not installed):**
```
✅ Stage 4 준비 완료
  - SOP 디렉토리: results/{company}/03_sop
  - 발견된 SOP: 7개 (TS: 4개, HT: 3개)
  - 처리 대상: 7개 (전체) 또는 4개 (TS만) 또는 3개 (HT만)
  - Mermaid CLI: ❌ 미설치
  - 출력 형식: Markdown만 (SVG 생성 건너뜀)

⚠️ SVG 이미지가 필요하면 나중에 설치 후 변환 가능:
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i TS_001_FLOWCHART.md -o TS_001_flowchart.svg -b transparent
```

### 2. Analyze SOP Structure

For each target SOP, analyze structure to extract flowchart components.

**Actions:**
- Read SOP file
- Identify SOP type (TS or HT)
  - **TS (Troubleshooting)**: Focus on decision trees and problem resolution paths
  - **HT (How-To)**: Focus on sequential steps and process flows
- Extract "케이스 1, 2, 3..." sections or step sequences
- Parse decision logic and branches
- Identify escalation criteria

**Expected Duration:** 1-2 minutes per SOP

### 3. Generate Mermaid Flowchart

Convert analyzed structure into Mermaid flowchart syntax.

**Actions:**
- Create flowchart nodes (Start, Decision, Process, End)
- Define edges and conditions
- Apply color coding (Success, Warning, Danger, Info)
- Add legend and case descriptions

**Expected Duration:** 2-3 minutes per SOP

### 4. Create Flowchart Markdown File

Write complete flowchart documentation.

**Actions:**
- Create file: `{SOP_ID}_FLOWCHART.md`
- Include Mermaid chart, case explanations, checkpoints
- Add cross-reference to original SOP

**Expected Duration:** 1 minute per SOP

### 5. Convert to SVG Image (CLI Required)

Use Mermaid CLI to generate SVG images if installed.

**Actions:**
- Check if Mermaid CLI is installed
- **If installed:**
  ```bash
  mmdc -i {SOP_ID}_FLOWCHART.md -o {SOP_ID}_flowchart.svg -b transparent
  ```
- **If not installed:**
  - Skip SVG generation
  - Note in summary that markdown files can be viewed in VSCode or GitHub

**Expected Duration:** 10-20 seconds per SOP (if CLI installed)

**Troubleshooting:**
- Parse error: Remove quotes and emoticons from node text
- Retry: Re-run mmdc command
- CLI not found: Skip SVG, continue with markdown only

### 6. Generate Summary Report

Create summary of flowchart generation results.

**Actions:**
- Count generated files
- List all flowcharts with file sizes
- Provide viewing instructions
- Save to `flowchart_generation_summary.md`

### 7. Update Metadata

Update `metadata.json` with flowchart references.

**Actions:**
- Add flowchart info to each SOP entry
- Save updated metadata

## Examples

### Example 1: Full Run (All SOPs)

**Input:**
```
sop_dir: results/{company}/03_sop
target_sops: all
output_format: both
```

**Output:**
- 7 Markdown files (TS_001~004_FLOWCHART.md, HT_001~003_FLOWCHART.md)
- 7 SVG images (~170KB each)
- 1 Summary report
- Updated metadata.json

**Time:** ~12 minutes

### Example 2: TS Only Run

**Input:**
```
sop_dir: results/{company}/03_sop
target_sops: ts_only
output_format: both
```

**Output:**
- 4 Markdown files (TS_001~004_FLOWCHART.md)
- 4 SVG images (~170KB each)
- 1 Summary report
- Updated metadata.json

**Time:** ~8 minutes

### Example 3: Specific SOPs

**Input:**
```
sop_dir: results/{company}/03_sop
target_sops: ["TS_001", "HT_001"]
```

**Output:**
- 2 Flowcharts (1 TS, 1 HT)
- 2 SVG images

**Time:** ~4 minutes

### Example 4: Markdown Only (CLI 없음)

**Input:**
```
sop_dir: results/{company}/03_sop
target_sops: all
```

**Detected:** Mermaid CLI not installed

**Output:**
- 7 Markdown files only (TS_001~004_FLOWCHART.md, HT_001~003_FLOWCHART.md)
- ⚠️ SVG 생성 건너뜀
- 1 Summary report

**Time:** ~8 minutes (SVG 변환 시간 제외)

**Note:** Markdown 파일은 VSCode Mermaid 확장 또는 GitHub에서 바로 렌더링됨

## Viewing Flowcharts

### VSCode에서 SVG 보기
1. SVG 파일 클릭 → 자동 렌더링

### Markdown 프리뷰 (확장 필요)
1. 확장 설치: "Markdown Preview Mermaid Support"
2. `Cmd + Shift + V`

### 브라우저
- SVG 파일을 브라우저로 드래그

## Related Documentation

- **Stage 3 SOP Generation**: [stage3-sop-generation.sop.md](../agent-sops/stage3-sop-generation.sop.md)
- **Full Pipeline**: [excel-to-sop-pipeline.sop.md](../agent-sops/excel-to-sop-pipeline.sop.md)
- **Mermaid Documentation**: https://mermaid.js.org/

## Notes

### When to Use Stage 4

**추천 상황**:
- 복잡한 Troubleshooting SOP (5개 이상 케이스, 의사결정 분기 많음)
- 다단계 How-To SOP (순차적 프로세스 시각화 필요)
- 신입 교육용 자료 필요
- 프로세스 검토 및 최적화
- 고객사 프레젠테이션

**생략 가능 상황**:
- 매우 간단한 SOP (3단계 이하)
- 텍스트 SOP만으로 충분
- 시간 제약

**TS vs HT 플로우차트 특징**:
- **TS**: 의사결정 트리, 조건 분기, 에스컬레이션 경로 강조
- **HT**: 순차적 단계, 체크포인트, 병렬 작업 흐름 강조

### Flowchart Quality Criteria

**Good Flowchart**:
- ✅ 한 화면에 전체 프로세스 표시
- ✅ 색상으로 케이스 구분 명확
- ✅ 의사결정 포인트 명확
- ✅ 에스컬레이션 경로 표시

**Bad Flowchart**:
- ❌ 너무 많은 노드 (50개 이상)
- ❌ 화살표 교차 많음
- ❌ 텍스트 너무 김 (노드 안)
- ❌ 색상 없이 흑백만

---

**This is an optional Stage 4**. Use when visual process documentation adds value beyond text-based SOP.
