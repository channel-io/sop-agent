---
name: stage4-flowchart-generation
description: Generate Mermaid flowcharts from Stage 3 SOP documents and convert to SVG images. Visualizes customer support processes with color-coded decision trees. **Language:** Auto-detects Korean (한국어) or Japanese (日本語) from user input.
type: anthropic-skill
version: "1.0"
---

# Stage 4: Flowchart Generation

## Overview
This SOP guides the automatic generation of Mermaid flowcharts from SOP documents created in Stage 3. This is **Stage 4** (optional enhancement stage) of the Excel-to-SOP pipeline, performed by the AI agent using natural language analysis and Mermaid diagram generation.

**Language:** Detect the language from the user's first message and respond in that language throughout. Support Korean (한국어) and Japanese (日本語). Default to Korean if language is unclear.

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

**Total Time**: ~4 minutes (typical, depends on number of SOPs)

## Parameters

### Required
- **sop_dir**: Directory containing Stage 3 SOP files
  - Example: `results/{company}/03_sop`
  - Must contain `.sop.md` files

### Optional
- **output_dir** (default: derived from sop_dir as `{sop_dir}/../04_flowcharts`): Directory to save flowchart files. Defaults to a sibling `04_flowcharts/` directory next to `03_sop/`.
- **mode** (default: "standard"): Flowchart generation depth mode
  - `"quick"`: Simple flowcharts (5-10 nodes), basic decision tree only
  - `"standard"`: Balanced flowcharts (15-30 nodes), main process flows (default)
  - `"deep"`: Detailed flowcharts (30+ nodes), full process with all edge cases

- **target_sops** (default: "all"): Which SOPs to generate flowcharts for
  - `"all"`: Generate for all SOPs (both TS and HT)
  - `"ts_only"`: Only Troubleshooting SOPs (recommended for complex processes)
  - `"ht_only"`: Only How-To SOPs
  - List: `["TS_001", "HT_002"]` - Specific SOP IDs

- **output_format** (default: "both"): Output file format
  - `"markdown"`: Mermaid markdown only
  - `"svg"`: SVG image only
  - `"both"`: Both markdown and SVG (recommended)

- **color_scheme** (default: "status"): Color coding strategy
  - `"status"`: Success (green), Warning (yellow), Error (red), Info (blue)
  - `"priority"`: High/Medium/Low priority
  - `"none"`: No color coding

## Steps

### 1. Validate Inputs

Verify Stage 3 SOP files and Mermaid CLI installation.

**Actions:**
- Check `sop_dir` exists and contains `.sop.md` files
- Derive `output_dir` if not provided: `{sop_dir}/../04_flowcharts` (e.g., `results/{company}/04_flowcharts`)
- Create output directory: `mkdir -p {output_dir}`
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
  - 출력 디렉토리: results/{company}/04_flowcharts (생성됨)
  - 발견된 SOP: 7개 (TS: 4개, HT: 3개)
  - 처리 대상: 7개 (전체) 또는 4개 (TS만) 또는 3개 (HT만)
  - Mermaid CLI: 설치됨 (v11.12.0)
  - 출력 형식: Markdown + SVG
```

**Expected Output (CLI not installed):**
```
✅ Stage 4 준비 완료
  - SOP 디렉토리: results/{company}/03_sop
  - 출력 디렉토리: results/{company}/04_flowcharts (생성됨)
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

**You MUST read `templates/FLOWCHART_template.md` before generating any flowchart.**
This template defines the official color scheme (`classDef`), node shapes, naming conventions, and quality checklist.

**Key rules from the template:**
- Use `classDef` for color coding (NOT inline `style` per node):
  ```
  classDef successClass fill:#d4edda,stroke:#28a745,stroke-width:2px
  classDef warningClass fill:#fff3cd,stroke:#ffc107,stroke-width:2px
  classDef dangerClass  fill:#f8d7da,stroke:#dc3545,stroke-width:2px
  classDef infoClass    fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px
  classDef processClass fill:#e7f3ff,stroke:#0056b3,stroke-width:2px
  classDef apiClass     fill:#fff0c0,stroke:#e6a817,stroke-width:2px,stroke-dasharray:5 5
  ```
- Apply classes with `class NodeA,NodeB successClass` at the end of the diagram
- Node shapes: `([...])` start/end, `{...}` decision, `[...]` process, `[[...]]` API 호출 노드
- **API 호출 노드**: 외부 API를 실제로 호출하는 단계에 `[[API 이름<br>반환 필드 확인]]` 형태로 표현하고 `apiClass` 적용 (점선 노란 테두리)
- No double-quotes inside node labels — use `<br/>` for line breaks
- Keep node text ≤ 15 characters per line

**Mode-Specific Behavior:**
- **Quick Mode**: Simple (5-10 nodes), main paths only
- **Standard Mode**: Balanced (15-30 nodes), all standard cases (default)
- **Deep Mode**: Comprehensive (30+ nodes), all edge cases and escalation paths

**Expected Duration:**
- Quick: 1-2 minutes per SOP
- Standard: 2-3 minutes per SOP
- Deep: 3-5 minutes per SOP

### 4. Create Flowchart Markdown File

Write complete flowchart documentation following **`templates/FLOWCHART_template.md`** structure exactly.
Save each flowchart file to `{output_dir}/{SOP_ID}_FLOWCHART.md` (NOT inside the sop_dir).

**You MUST use this section order:**

```
# [{SOP 파일명}] Flowchart

## 상담 흐름도

```mermaid
flowchart TD
    ...
    classDef successClass ...
    classDef warningClass ...
    classDef dangerClass  ...
    classDef infoClass    ...
    classDef processClass ...
    class ... successClass
    class ... warningClass
    ...
```

## 케이스별 설명

### 🟢 정상 처리 (초록색)
- **케이스 N**: {설명} — **자동화 가능**: {X}% ({해결 기술: RAG/Action/Rules})

### 🟡 주의 필요 / 조건부 처리 (노란색)
- {설명}

### 🔴 담당팀 전달 / 에스컬레이션 (빨간색)
- {설명}

### 🔵 의사결정 포인트 (파란색)
- {설명}

### ⚙️ 정보 확인 단계 (연한 파란색)
- {설명}

## 주요 체크포인트

| 단계 | 확인 사항 | 도구/방법 |
|------|----------|----------|
| 1️⃣ ... | ... | ... |
...

## 담당팀 전달 기준  ← TS SOP에만 포함

| 조건 | 전달 대상 | 필수 정보 |
|------|----------|----------|
...

---

**생성 정보**:
- 원본 SOP: [{파일명}.sop.md](./{파일명}.sop.md)
- 생성일: {YYYY-MM-DD}
- 플로우차트 버전: v1.0
- 데이터: {N}건 ({%}%)
```

**케이스별 설명에 자동화 정보 필수 포함:**
- 각 케이스 설명에 **자동화 가능**: X% 와 사용 기술(RAG/Action/Rules) 을 반드시 기재
- 이 정보는 Stage 5 Sales Report의 관여율/해결율 산출 근거로 활용됨

**Expected Duration:** 1-2 minutes per SOP

### 5. Convert to SVG Image (CLI Required)

Use Mermaid CLI to generate SVG images if installed.

**Actions:**
- Check if Mermaid CLI is installed
- **If installed:**
  ```bash
  mmdc -i {output_dir}/{SOP_ID}_FLOWCHART.md -o {output_dir}/{SOP_ID}_flowchart.svg -b transparent
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
- 7 Markdown files in `04_flowcharts/` (TS_001~004_FLOWCHART.md, HT_001~003_FLOWCHART.md)
- 7 SVG images (~170KB each) in `04_flowcharts/`
- 1 Summary report
- Updated metadata.json

**Time:** ~4-5 minutes

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

**Time:** ~3-4 minutes

### Example 3: Specific SOPs

**Input:**
```
sop_dir: results/{company}/03_sop
target_sops: ["TS_001", "HT_001"]
```

**Output:**
- 2 Flowcharts (1 TS, 1 HT)
- 2 SVG images

**Time:** ~2 minutes

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

**Time:** ~3-4 minutes (SVG 변환 시간 제외)

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

- **Flowchart Template** ⭐: [FLOWCHART_template.md](../../../templates/FLOWCHART_template.md) — 반드시 이 템플릿을 기준으로 생성
- **Stage 3 SOP Generation**: [stage3-sop-generation.sop.md](../../../agent-sops/stage3-sop-generation.sop.md)
- **Full Pipeline**: [excel-to-sop-pipeline.sop.md](../../../agent-sops/excel-to-sop-pipeline.sop.md)
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
