#!/usr/bin/env python3
"""
SOP Data Extractor
==================
Stage 3 SOP/플로우차트 파일에서 구조화된 데이터를 추출합니다.

Stage 5 (Sales Report) Step 3 분석 전에 실행하여
LLM이 경로 목록과 볼륨 비율을 '자유 독해'가 아닌 구조화된 JSON으로 받을 수 있게 합니다.

추출 항목:
  - 플로우차트 케이스별 설명 → canonical path list (케이스명, 자동화율, 볼륨)
  - SOP 주요 패턴 → 패턴명, 빈도 레이블, 명시적 비율 (있을 경우)
  - SOP 자동화 가능성 별점 (★ 수)
  - metadata.json 샘플 수

출력:
  {output_dir}/{SOP_ID}_sop_data.json (SOP별)
  {output_dir}/all_sops_data.json (전체 통합)

Usage:
    python3 scripts/extract_sop_data.py \\
        --sop_dir results/assacom/03_sop \\
        --output_dir results/assacom/05_sales_report/sop_data

    # metadata.json에서 샘플 수 함께 추출
    python3 scripts/extract_sop_data.py \\
        --sop_dir results/assacom/03_sop \\
        --output_dir results/assacom/05_sales_report/sop_data \\
        --metadata results/assacom/03_sop/metadata.json
"""

import re
import json
import argparse
from pathlib import Path


# ─────────────────────── 공통 프로세스 단계 패턴 (경로로 오인하기 쉬운 것들) ────── #

class ProcessStep:
    KEYWORDS = [
        "정보_확인_요청",
        "고객_정보_확인",
        "에스컬레이션",
        "as_에스컬레이션",
    ]
    EXTRA_KEYWORDS = ["에스컬", "escalat", "전달", "공지"]


class FrequencyRate:
    TO_PCT = {
        "very high": 85,
        "high":      45,
        "medium":    25,
        "low":       10,
    }


class PatternClass:
    INQUIRY_PATH = "inquiry_path"
    PROCESS_STEP = "process_step"
    UNKNOWN      = "unknown"


# ──────────────────────────────── Flowchart parser ────────────────────────── #

def parse_flowchart(flowchart_path: Path) -> list[dict]:
    """
    _FLOWCHART.md의 '## 케이스별 설명' 섹션에서 케이스 목록 추출.

    반환 형식:
    [
        {
            "case_num": 1,
            "name": "TPM 2.0 설정 완료",
            "automation_rate": 80,          # 자동화 가능 % (없으면 null)
            "volume_pct": 50,               # 볼륨 % (없으면 null)
            "volume_source": "flowchart",   # 또는 "unknown"
            "tech_note": "RAG: BIOS 설정 가이드 자동"
        },
        ...
    ]
    """
    text = flowchart_path.read_text(encoding="utf-8")

    # 케이스별 설명 섹션만 추출 (## 로 시작하는 다음 섹션 또는 EOF까지)
    section_m = re.search(
        r'##\s+케이스별 설명\n(.*?)(?=\n##\s|\Z)',
        text, re.DOTALL
    )
    if not section_m:
        return []

    section = section_m.group(1)
    cases = []

    def parse_case_line(full_desc: str, case_num: int, name: str) -> dict:
        """케이스 항목 1줄에서 자동화율·볼륨·기술 노트 추출."""
        auto_m = re.search(r'\*\*자동화 가능\*\*[:\s]+(\d+)%', full_desc)
        automation_rate = int(auto_m.group(1)) if auto_m else None

        tech_m = re.search(r'\(([A-Za-z가-힣][^)]+)\)\s*$', full_desc)
        tech_note = tech_m.group(1).strip() if tech_m else None

        # 볼륨 비율: "게임 오류 (30%)", "가장 흔한 케이스 (50%)" 등
        vol_m = re.search(r'\((\d+)%\)', full_desc)
        volume_pct    = int(vol_m.group(1)) if vol_m else None
        volume_source = "flowchart" if volume_pct else "unknown"

        return {
            "case_num":        case_num,
            "name":            name,
            "automation_rate": automation_rate,
            "volume_pct":      volume_pct,
            "volume_source":   volume_source,
            "tech_note":       tech_note,
        }

    # ── 형식 A: **케이스 N~M**: ... (범위 표기) ──────────────────────── #
    for m in re.finditer(r'-\s+\*\*케이스\s+(\d+)~(\d+)\*\*[:\s]+([^\n]+)', section):
        start, end    = int(m.group(1)), int(m.group(2))
        full_desc     = m.group(3).strip()
        auto_m        = re.search(r'\*\*자동화 가능\*\*[:\s]+(\d+)%', full_desc)
        automation_rate = int(auto_m.group(1)) if auto_m else None
        for n in range(start, end + 1):
            if not any(c["case_num"] == n for c in cases):
                cases.append({
                    "case_num": n,
                    "name": f"케이스 {n} (범위 {start}~{end}에 포함)",
                    "automation_rate": automation_rate,
                    "volume_pct": None, "volume_source": "unknown", "tech_note": None,
                })

    # ── 형식 B: **케이스 N**: {desc} ─────────────────────────────────── #
    for m in re.finditer(r'-\s+\*\*케이스\s+(\d+)\*\*(?!~)[:\s]+([^\n]+)', section):
        case_num = int(m.group(1))
        full_desc = m.group(2).strip()
        if any(c["case_num"] == case_num for c in cases):
            continue
        name_m = re.match(r'^([^—]+?)(?:\s*—|\s*,\s*\*\*자동화)', full_desc)
        name   = name_m.group(1).strip() if name_m else full_desc[:40].strip()
        cases.append(parse_case_line(full_desc, case_num, name))

    # ── 형식 C: **{경로명}: {desc} (HT SOP 스타일) ──────────────────── #
    # 케이스 번호가 없는 경로명 항목 (정상 처리 섹션 내부만)
    if not cases:
        success_m = re.search(
            r'###\s+🟢\s+정상 처리.+?\n((?:-[^\n]+\n?)+)',
            section, re.DOTALL
        )
        if success_m:
            for idx, m in enumerate(
                re.finditer(r'-\s+\*\*([^*:]+)\*\*[:\s]+([^\n]+)', success_m.group(1)),
                start=1
            ):
                name      = m.group(1).strip()
                full_desc = m.group(2).strip()
                cases.append(parse_case_line(full_desc, idx, name))

    return sorted(cases, key=lambda c: c["case_num"])


# ──────────────────────────────── SOP parser ──────────────────────────────── #

def classify_pattern(pattern_name: str) -> str:
    """
    패턴명이 '독립 문의 경로'인지 '공통 프로세스 단계'인지 분류.
    Returns: PatternClass.INQUIRY_PATH | PatternClass.PROCESS_STEP
    """
    lower = pattern_name.lower()
    for kw in ProcessStep.KEYWORDS:
        if kw.lower() in lower:
            return PatternClass.PROCESS_STEP
    if any(k in lower for k in ProcessStep.EXTRA_KEYWORDS):
        return PatternClass.PROCESS_STEP
    return PatternClass.INQUIRY_PATH


def parse_sop_patterns(sop_path: Path) -> dict:
    """
    .sop.md의 📊 데이터 분석 정보 블록에서 패턴 추출.

    반환 형식:
    {
        "automation_stars": 4,          # ★ 수 (없으면 null)
        "patterns": [
            {
                "name":           "BIOS_진입_설정",
                "frequency":      "high",
                "explicit_pct":   45,     # 명시된 % (없으면 null)
                "estimated_pct":  45,     # explicit 또는 frequency→추산
                "classification": "inquiry_path"
            },
            ...
        ]
    }
    """
    text = sop_path.read_text(encoding="utf-8")

    # 📊 데이터 분석 정보 섹션 추출
    section_m = re.search(
        r'📊\s+데이터 분석 정보(.*?)(?=^---|\Z)',
        text, re.DOTALL | re.MULTILINE
    )
    if not section_m:
        return {"automation_stars": None, "patterns": []}

    section = section_m.group(1)

    # 자동화 가능성 별점 추출
    stars_m = re.search(r'자동화 가능성:\s*(★+)', section)
    automation_stars = len(stars_m.group(1)) if stars_m else None

    # 주요 패턴 블록 추출
    patterns_block_m = re.search(
        r'주요 패턴:\s*\n((?:\s+-[^\n]+\n?)+)',
        section
    )
    if not patterns_block_m:
        return {"automation_stars": automation_stars, "patterns": []}

    patterns = []
    for line in patterns_block_m.group(1).splitlines():
        line = line.strip()
        if not line.startswith('-'):
            continue

        # 형식: - {pattern_name}: {frequency} ({N}%) 또는 - {name}: {frequency}
        line_m = re.match(
            r'-\s+([^:]+):\s+(\w[\w\s]+?)(?:\s+\((\d+)%\))?$',
            line
        )
        if not line_m:
            continue

        name      = line_m.group(1).strip()
        frequency = line_m.group(2).strip().lower()
        explicit_pct = int(line_m.group(3)) if line_m.group(3) else None
        estimated_pct = explicit_pct if explicit_pct else FrequencyRate.TO_PCT.get(frequency)

        patterns.append({
            "name":           name,
            "frequency":      frequency,
            "explicit_pct":   explicit_pct,
            "estimated_pct":  estimated_pct,
            "classification": classify_pattern(name),
        })

    return {"automation_stars": automation_stars, "patterns": patterns}


# ──────────────────────────────── Volume mapper ───────────────────────────── #

def map_volumes(cases: list[dict], patterns: list[dict]) -> list[dict]:
    """
    플로우차트 케이스와 SOP 패턴을 매핑하여 볼륨 비율을 채웁니다.
    매핑 전략: 케이스명 키워드 ↔ 패턴명 키워드 fuzzy match
    매핑 실패 시 null 유지 (LLM이 추산 처리).
    """
    inquiry_patterns = [p for p in patterns if p["classification"] == PatternClass.INQUIRY_PATH]

    for case in cases:
        if case["volume_pct"] is not None:
            continue  # 이미 플로우차트에서 확인됨

        case_words = set(re.sub(r'[_\s]+', ' ', case["name"]).lower().split())
        best_match = None
        best_score = 0

        for pat in inquiry_patterns:
            pat_words = set(re.sub(r'[_\s]+', ' ', pat["name"]).lower().split())
            # 공통 단어 수로 스코어 계산
            score = len(case_words & pat_words)
            if score > best_score:
                best_score = score
                best_match = pat

        if best_match and best_score >= 1 and best_match.get("estimated_pct"):
            case["volume_pct"]    = best_match["estimated_pct"]
            case["volume_source"] = f"sop_pattern:{best_match['name']}"

    return cases


# ──────────────────────────────── Main extractor ──────────────────────────── #

def extract_one(flowchart_path: Path, sop_path: Path, sample_count) -> dict:
    """SOP 1개의 데이터 추출."""
    sop_id = sop_path.name.replace(".sop.md", "")

    cases   = parse_flowchart(flowchart_path)
    sop_data = parse_sop_patterns(sop_path)
    patterns = sop_data["patterns"]

    # 볼륨 매핑 시도
    cases = map_volumes(cases, patterns)

    # 볼륨 합계 확인 및 미할당 케이스 균등 배분
    assigned   = [c for c in cases if c["volume_pct"] is not None]
    unassigned = [c for c in cases if c["volume_pct"] is None]
    assigned_sum = sum(c["volume_pct"] for c in assigned)

    if unassigned and assigned_sum < 100:
        remaining = 100 - assigned_sum
        per_case  = round(remaining / len(unassigned))
        for c in unassigned:
            c["volume_pct"]    = per_case
            c["volume_source"] = "estimated_equal"

    return {
        "sop_id":            sop_id,
        "sample_count":      sample_count,
        "automation_stars":  sop_data["automation_stars"],
        "flowchart_cases":   cases,
        "data_patterns":     patterns,
        "process_step_patterns": [
            p["name"] for p in patterns if p["classification"] == PatternClass.PROCESS_STEP
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Extract structured data from Stage 3 SOP files")
    parser.add_argument("--sop_dir",    required=True,  help="Stage 3 SOP 디렉토리")
    parser.add_argument("--output_dir", required=True,  help="출력 디렉토리")
    parser.add_argument("--metadata",   default=None,   help="metadata.json 경로 (sample_count 추출용)")
    args = parser.parse_args()

    sop_dir    = Path(args.sop_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # metadata.json에서 sample_count 로드
    sample_counts: dict[str, int] = {}
    if args.metadata:
        meta = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
        for entry in meta.get("sop_files", []):
            fname = entry.get("filename") or entry.get("file", "")
            sop_name = Path(fname).name.replace(".sop.md", "")
            sample_counts[sop_name] = entry.get("cluster_size", 0)

    # SOP-FLOWCHART 쌍 수집
    sop_files = sorted(sop_dir.glob("*.sop.md"))
    results   = []

    print(f"\n📤 SOP 데이터 추출 — {len(sop_files)}개\n{'─'*50}")
    for sop_path in sop_files:
        # HT_AS접수안내.sop.md → HT_AS접수안내
        sop_id = sop_path.name.replace(".sop.md", "")
        fc_candidates = list(sop_dir.glob(f"{sop_id}_FLOWCHART.md"))

        if not fc_candidates:
            print(f"  ⚠️  {sop_id}: 플로우차트 없음 — SOP 패턴만 추출")
            fc_path = None
            cases   = []
        else:
            fc_path = fc_candidates[0]
            cases   = None  # extract_one 내부에서 처리

        sample_count = sample_counts.get(sop_id)
        if fc_path:
            data = extract_one(fc_path, sop_path, sample_count)
        else:
            sop_parsed = parse_sop_patterns(sop_path)
            data = {
                "sop_id":            sop_id,
                "sample_count":      sample_count,
                "automation_stars":  sop_parsed["automation_stars"],
                "flowchart_cases":   [],
                "data_patterns":     sop_parsed["patterns"],
                "process_step_patterns": [
                    p["name"] for p in sop_parsed["patterns"]
                    if p["classification"] == PatternClass.PROCESS_STEP
                ],
            }

        # 개별 JSON 저장
        out_path = output_dir / f"{sop_id}_sop_data.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        n_cases    = len(data["flowchart_cases"])
        n_patterns = len(data["data_patterns"])
        n_proc     = len(data["process_step_patterns"])
        print(f"  ✅ {sop_id}: {n_cases}개 케이스, {n_patterns}개 패턴 ({n_proc}개 프로세스단계)")

        results.append(data)

    # 전체 통합 JSON 저장
    all_path = output_dir / "all_sops_data.json"
    all_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'─'*50}")
    print(f"✅ 추출 완료")
    print(f"   개별: {output_dir}/*_sop_data.json")
    print(f"   통합: {all_path}\n")
    print("💡 Stage 5 Step 3에서 이 JSON을 FIRST INPUT으로 사용하세요.")
    print("   LLM은 flowchart_cases를 경로 목록의 기준으로, data_patterns를 볼륨 참조로 활용합니다.")
    print("   process_step_patterns에 나열된 항목은 경로명으로 사용하지 마세요.\n")


if __name__ == "__main__":
    main()
