#!/usr/bin/env python3
"""
SOP Analysis Validator
======================
Stage 5에서 생성된 sop_analysis/*.md 파일의 구조적 정합성을 검증합니다.

검증 항목:
  1. 경로 수 vs 플로우차트 케이스 수 일치 여부
  2. 경로 볼륨 합계가 ~100%인지 (±5% 허용)
  3. 가중 해결율 계산이 명시된 값과 일치하는지
  4. 공통 프로세스 패턴이 경로명으로 사용되었는지 (경고)

Usage:
    python3 scripts/validate_sop_analysis.py \\
        --sop_dir results/assacom/03_sop \\
        --analysis_dir results/assacom/05_sales_report/sop_analysis
"""

import re
import argparse
from pathlib import Path


# ─────────────────────── 공통 프로세스 패턴 (경로로 오인하기 쉬운 키워드) ──────────── #

PROCESS_STEP_PATTERNS = [
    "정보_확인_요청",
    "고객_정보_확인",
    "에스컬레이션",
    "as_에스컬레이션",
    "정보 확인",
    "에스컬레이션",
]


# ──────────────────────────────── Parsers ─────────────────────────────────── #

def parse_flowchart_cases(flowchart_path: Path):
    """_FLOWCHART.md의 케이스별 설명 섹션에서 케이스 목록을 추출.
    '케이스 1~4' 형태의 범위 표기도 처리."""
    text = flowchart_path.read_text(encoding="utf-8")

    # 케이스별 설명 섹션 추출
    section_match = re.search(r'##\s+케이스별 설명(.*?)(?=^##|\Z)', text, re.DOTALL | re.MULTILINE)
    if not section_match:
        return []

    section = section_match.group(1)

    cases = []
    # 범위 표기: 케이스 N~M
    for m in re.finditer(r'\*\*케이스\s+(\d+)~(\d+)\*\*', section):
        cases.extend(range(int(m.group(1)), int(m.group(2)) + 1))
    # 단일 케이스: 케이스 N (정상 처리 섹션만 카운트)
    for m in re.finditer(r'\*\*케이스\s+(\d+)\*\*(?!~)', section):
        n = int(m.group(1))
        if n not in cases:
            cases.append(n)

    return sorted(set(cases))


def parse_analysis_paths(analysis_path: Path):
    """분석 파일에서 경로 목록, 비율, 해결율 추출."""
    text = analysis_path.read_text(encoding="utf-8")
    paths = []

    # ### 경로 N: {name} (~{ratio}%, ...) 패턴
    # greedy 매칭으로 경로명 내 괄호(예: "주문 취소 (조립 전)")를 올바르게 처리
    for m in re.finditer(
        r'###\s+경로\s+(\d+)[:\s]+(.+)\(~?(\d+)%',
        text
    ):
        path_num = int(m.group(1))
        path_name = m.group(2).strip()
        ratio = int(m.group(3))

        # 해당 경로의 해결율: **경로 해결율**: ✅/❌ **{N}%** 패턴
        # 경로 헤더 이후 다음 경로 헤더 전까지의 텍스트에서 찾기
        path_start = m.end()
        next_path = re.search(r'###\s+경로\s+\d+', text[path_start:])
        path_text = text[path_start: path_start + next_path.start()] if next_path else text[path_start:]

        res_match = re.search(r'\*\*경로 해결율\*\*[^\*]*\*\*(\d+)%\*\*', path_text)
        resolution = int(res_match.group(1)) if res_match else None

        paths.append({
            "num": path_num,
            "name": path_name,
            "ratio": ratio,
            "resolution": resolution,
        })

    return paths


def parse_stated_resolution(analysis_path: Path):
    """분석 파일 기본 정보 테이블에서 명시된 전체 해결율 추출."""
    text = analysis_path.read_text(encoding="utf-8")
    m = re.search(r'\|\s*\*\*해결율\*\*\s*\|\s*\*\*(\d+)%\*\*', text)
    return int(m.group(1)) if m else None


def check_process_step_misuse(analysis_path: Path):
    """공통 프로세스 패턴이 경로명으로 사용된 경우 탐지."""
    text = analysis_path.read_text(encoding="utf-8").lower()
    hits = []
    for pat in PROCESS_STEP_PATTERNS:
        # 경로 헤더(### 경로 N:) 안에 해당 패턴이 있는지 확인
        if re.search(r'###\s+경로\s+\d+.*' + pat.lower(), text):
            hits.append(pat)
    return hits


# ──────────────────────────── Validation logic ────────────────────────────── #

def validate_one(analysis_path: Path, sop_dir: Path) -> dict:
    """분석 파일 1개를 검증하고 결과 dict 반환."""
    result = {
        "file": analysis_path.name,
        "errors": [],
        "warnings": [],
        "ok": True,
    }

    # 대응하는 플로우차트 파일 찾기
    sop_id = re.sub(r'^[A-Z]+_\d+_', '', analysis_path.stem).replace('_분석', '')
    flowchart_candidates = list(sop_dir.glob(f"*{sop_id}*FLOWCHART.md"))
    if not flowchart_candidates:
        result["warnings"].append(f"플로우차트 파일 없음 — 케이스 수 검증 건너뜀")
    else:
        fc_path = flowchart_candidates[0]
        fc_cases = parse_flowchart_cases(fc_path)
        analysis_paths = parse_analysis_paths(analysis_path)

        # ① 경로 수 vs 케이스 수 일치 확인 (경고 수준 — 1:1 매핑이 아닐 수 있음)
        if fc_cases and abs(len(fc_cases) - len(analysis_paths)) > 1:
            result["warnings"].append(
                f"경로 수 차이: 플로우차트 케이스 {len(fc_cases)}개 vs 분석 경로 {len(analysis_paths)}개 — 의도적 분리인지 확인"
            )

    # 분석 경로 파싱 (플로우차트 없어도 내부 검증은 진행)
    analysis_paths = parse_analysis_paths(analysis_path)

    if not analysis_paths:
        result["warnings"].append("경로가 발견되지 않음 — 포맷 확인 필요")
        return result

    # ② 볼륨 합계 ~100% 확인
    total_ratio = sum(p["ratio"] for p in analysis_paths)
    if abs(total_ratio - 100) > 5:
        result["errors"].append(
            f"경로 볼륨 합계 오류: {total_ratio}% (기대값 95~105%)"
        )
        result["ok"] = False

    # ③ 가중 해결율 재계산 vs 명시값 비교
    stated = parse_stated_resolution(analysis_path)
    if stated is not None:
        resolvable_paths = [p for p in analysis_paths if p["resolution"] is not None]
        if resolvable_paths:
            weighted = sum(
                p["ratio"] / 100 * p["resolution"]
                for p in resolvable_paths
            )
            diff = abs(weighted - stated)
            if diff > 5:
                result["errors"].append(
                    f"해결율 계산 오차: 재계산={weighted:.0f}% vs 명시={stated}% (차이 {diff:.0f}%p)"
                )
                result["ok"] = False

    # ④ 공통 프로세스 패턴 오용 경고
    misuse = check_process_step_misuse(analysis_path)
    if misuse:
        result["warnings"].append(
            f"프로세스 단계 패턴이 경로명에 포함될 수 있음: {', '.join(misuse)}"
        )

    return result


# ────────────────────────────── Entry point ───────────────────────────────── #

def main():
    parser = argparse.ArgumentParser(description="Validate Stage 5 sop_analysis files")
    parser.add_argument("--sop_dir",      required=True, help="Stage 3 SOP 디렉토리 (플로우차트 위치)")
    parser.add_argument("--analysis_dir", required=True, help="Stage 5 sop_analysis 디렉토리")
    args = parser.parse_args()

    sop_dir      = Path(args.sop_dir)
    analysis_dir = Path(args.analysis_dir)

    analysis_files = sorted(
        f for f in analysis_dir.glob("*_분석.md")
        if not f.name.startswith("00_")
    )

    if not analysis_files:
        print("❌ 분석 파일이 없습니다.")
        return

    print(f"\n🔍 SOP Analysis 검증 — {len(analysis_files)}개 파일\n{'─'*55}")

    all_ok = True
    for af in analysis_files:
        r = validate_one(af, sop_dir)
        status = "✅" if r["ok"] and not r["warnings"] else ("⚠️ " if r["ok"] else "❌")
        print(f"{status} {r['file']}")
        for e in r["errors"]:
            print(f"     ERROR  : {e}")
        for w in r["warnings"]:
            print(f"     WARNING: {w}")
        if r["errors"]:
            all_ok = False

    print(f"\n{'─'*55}")
    if all_ok:
        print("✅ 모든 파일 검증 통과\n")
    else:
        print("❌ 오류가 있는 파일이 있습니다. 위 목록을 확인해 수정하세요.\n")


if __name__ == "__main__":
    main()
