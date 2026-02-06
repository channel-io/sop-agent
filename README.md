# Userchat-to-SOP Pipeline

Userchat 고객 상담 데이터를 Agent SOP 문서로 자동 변환하는 4단계 AI 파이프라인

## 프로젝트 개요

- **목적**: Excel 고객 상담 데이터 → 재사용 가능한 Agent SOP 문서 자동 생성
- **방법**: 4단계 파이프라인 (Clustering → Extraction → SOP Generation → Flowchart Generation)
- **기술 스택**:
  - **Stage 1 (Python)**: Upstage Solar 임베딩 + K-Means 클러스터링 + LLM Fallback 자동화
  - **Stage 2 (LLM)**: 패턴 추출 + FAQ 생성 + HT/TS 분류
  - **Stage 3 (LLM)**: Agent SOP 문서 생성
  - **Stage 4 (LLM + Mermaid)**: 플로우차트 자동 생성 (선택)

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 UPSTAGE_API_KEY 추가
```

### 3. 파이프라인 실행

#### Stage 1: 클러스터링

**Claude Skill 사용 (권장)**:
```bash
/stage1-clustering
```

#### Stage 2: 패턴 추출

**Claude Skill**:
```bash
/stage2-extraction
```

#### Stage 3: SOP 생성

**Claude Skill**:
```bash
/stage3-sop-generation
```

#### Stage 4: 플로우차트 생성 (선택)

**Claude Skill**:
```bash
/stage4-flowchart-generation
```

**참고**: SVG 이미지 생성 시 Mermaid CLI 필요 (선택)
- CLI 없어도 Mermaid 마크다운 생성 가능
- SVG 필요 시:
```bash
npm install -g @mermaid-js/mermaid-cli
```

### 4. 결과 확인

```bash
# Stage 1: 클러스터링 결과
results/{company}/
├── {company}_clustered.xlsx    # 원본 데이터 + 클러스터 정보
├── {company}_tags.xlsx         # 클러스터 메타데이터
├── {company}_messages.csv      # 실제 대화 턴 (Stage 2용)
└── analysis_report.md          # 분석 리포트

# Stage 2: 패턴 추출 결과
results/{company}/02_extraction/
├── patterns.json               # 추출된 패턴 + HT/TS 분류
├── patterns_enriched.json      # 샘플 임베딩 (Stage 3 최적화)
├── faq.json                    # FAQ 쌍
├── response_strategies.json    # 응답 전략
├── keywords.json               # 키워드 분류체계
└── extraction_summary.md       # 추출 요약

# Stage 3: SOP 생성 결과
results/{company}/03_sop/
├── TS_001_*.sop.md            # Troubleshooting SOP
├── HT_001_*.sop.md            # How-To SOP
├── metadata.json              # SOP 메타데이터
└── generation_summary.md      # 생성 요약

# Stage 4: 플로우차트 생성 결과 (선택)
results/{company}/03_sop/
├── TS_001_*_FLOWCHART.md      # Mermaid 플로우차트 (TS)
├── TS_001_*_flowchart.svg     # SVG 이미지 (TS)
├── HT_001_*_FLOWCHART.md      # Mermaid 플로우차트 (HT)
├── HT_001_*_flowchart.svg     # SVG 이미지 (HT)
└── flowchart_generation_summary.md  # 플로우차트 요약
```

## 디렉토리 구조

```
.
├── .claude/                    # Claude Code Skills
│   └── skills/
│       ├── stage1-clustering/  # Stage 1 Skill
│       ├── stage2-extraction/  # Stage 2 Skill
│       ├── stage3-sop-generation/ # Stage 3 Skill
│       └── stage4-flowchart-generation/ # Stage 4 Skill
├── agent-sops/                 # Agent SOP 파일들
│   ├── stage1-clustering.sop.md
│   ├── stage2-extraction.sop.md
│   ├── stage3-sop-generation.sop.md
│   └── stage4-flowchart-generation.sop.md
├── scripts/                    # Python 스크립트
│   ├── pipeline.py            # Stage 1 진입점
│   ├── enrich_patterns.py     # Stage 2.5: 샘플 임베딩
│   ├── generate_sops.py       # Stage 3: SOP 생성
│   ├── config.py              # API 키, 기본 설정
│   └── clustering/            # 클러스터링 모듈
│       ├── data_loader.py     # Excel 로딩 (first_msg 우선 샘플링)
│       ├── text_enhancer.py   # 텍스트 향상 (간소화)
│       ├── embeddings.py      # 임베딩 (병렬 + 캐싱)
│       ├── clustering.py      # K-Means 클러스터링
│       ├── tagging.py         # LLM 자동 태깅
│       └── output.py          # Excel 저장
├── templates/                 # SOP 템플릿
│   ├── HT_template.md         # How-To 템플릿
│   └── TS_template.md         # Troubleshooting 템플릿
├── data/                      # 입력 Excel 파일
├── results/{company}/         # 출력 결과
│   ├── {company}_clustered.xlsx    # Stage 1
│   ├── {company}_tags.xlsx
│   ├── {company}_messages.csv
│   ├── 02_extraction/              # Stage 2
│   │   ├── patterns.json
│   │   ├── patterns_enriched.json
│   │   └── ...
│   └── 03_sop/                     # Stage 3
│       ├── *.sop.md
│       ├── *_FLOWCHART.md          # Stage 4: Mermaid 플로우차트
│       ├── *_flowchart.svg         # Stage 4: SVG 이미지
│       ├── metadata.json
│       ├── generation_summary.md
│       └── flowchart_generation_summary.md  # Stage 4
├── cache/                     # 임베딩 캐시
└── docs/                      # 프로젝트 문서
```

## 개발 로드맵

### Phase 1: 초기 설정 ✅
- [x] 프로젝트 구조 설정
- [x] 기본 디렉토리 생성
- [x] README 작성

### Phase 2: Stage 1 구현 ✅
- [x] 클러스터링 파이프라인 구현
- [x] 임베딩 캐싱 시스템
- [x] LLM 자동 태깅 (Agent/API/Skip 모드)
- [x] 분석 리포트 자동 생성
- [x] Claude Code Skill 통합

### Phase 3: Stage 2 구현 ✅
- [x] 실제 샘플 기반 패턴 추출 (20개/클러스터)
- [x] FAQ 자동 생성
- [x] HT/TS 자동 분류
- [x] 키워드 추출
- [x] enrich_patterns.py (샘플 임베딩)
- [x] first_message 우선 샘플링 (형식 통일)

### Phase 4: Stage 3 구현 ✅
- [x] Agent SOP 문서 자동 생성 (LLM)
- [x] HT/TS 템플릿 기반 생성
- [x] 실제 고객 표현 포함
- [x] 메타데이터 및 요약 리포트 생성
- [x] 플레이스홀더 사용 ({company})
- [x] 민감 정보 일반화 (Channel Corp. 예시)

### Phase 5: Stage 4 구현 ✅
- [x] Mermaid 플로우차트 자동 생성
- [x] TS/HT 모두 지원
- [x] SVG 이미지 변환 (mmdc CLI)
- [x] 색상 코딩 (Success/Warning/Error/Info)
- [x] 플로우차트 요약 리포트 생성

### Phase 6: 통합 (예정)
- [ ] 전체 파이프라인 연결
- [ ] 문서화 완성

## Claude Code Skills

### `/stage1-clustering`
대화형 Stage 1 실행 - 파라미터 선택 가이드 제공
- 데이터 파일 자동 스캔 및 선택
- 회사명 자동 추출
- LLM Fallback 자동 감지 (≥20%)
- 배치 처리 (50개씩, 25배 속도 향상)
- Interactive/Auto 모드 지원
- RFC 2119 키워드 사용 (MUST/SHOULD/MAY)

### `/stage2-extraction`
실제 샘플 기반 패턴 추출 + HT/TS 분류
- 추측 금지, 20개 샘플 직접 분석
- FAQ, 응답 전략, 키워드 자동 생성
- patterns_enriched.json 생성 (Stage 3 최적화용)
- RFC 2119 키워드 사용 (MUST/SHOULD/MAY)

### `/stage3-sop-generation`
Agent SOP 문서 자동 생성
- HT/TS 템플릿 기반 생성
- 실제 고객 표현, 응답 예시 포함
- 톤앤매너, 담당팀 전달 기준 명시
- 플레이스홀더 사용 (results/{company}/03_sop/{company}_*.sop.md)
- 민감 정보 일반화 (예시: Channel Corp., 1234-5678)
- RFC 2119 키워드 사용 (MUST/SHOULD/MAY)

### `/stage4-flowchart-generation`
Mermaid 플로우차트 자동 생성 (선택)
- TS/HT 모두 지원 (all, ts_only, ht_only 옵션)
- Mermaid 다이어그램 + SVG 이미지 생성
- 색상 코딩 (Success/Warning/Error/Info)
- TS: 의사결정 트리, 조건 분기, 에스컬레이션 강조
- HT: 순차적 단계, 체크포인트, 병렬 작업 강조
- VSCode 내 SVG 자동 렌더링 지원

## 기술 스택

### Stage 1 (Python)
- **임베딩**: Upstage Solar `embedding-passage` (4096차원)
- **클러스터링**: scikit-learn K-Means
- **LLM**: Upstage Solar `solar-mini` (태깅 + LLM fallback)
- **최적화**: 병렬 처리 (임베딩), 배치 처리 (요약 50개), 캐싱

### Stage 2 (LLM)
- **모델**: Claude Sonnet 4.5 (1M context)
- **작업**: 패턴 추출, FAQ 생성, HT/TS 분류
- **출력**: patterns.json, patterns_enriched.json, faq.json, strategies.json

### Stage 3 (LLM)
- **모델**: Claude Sonnet 4.5 (1M context)
- **작업**: SOP 문서 작성, 케이스별 응답 템플릿 생성
- **출력**: TS/HT SOP 문서, metadata.json, generation_summary.md
- **보안**: 플레이스홀더 사용, 민감 정보 일반화

### Stage 4 (LLM + Mermaid)
- **모델**: Claude Sonnet 4.5 (플로우차트 구조 분석)
- **다이어그램**: Mermaid.js (flowchart syntax)
- **변환**: @mermaid-js/mermaid-cli (SVG 생성)
- **작업**: SOP 구조 분석 → Mermaid 생성 → SVG 변환
- **출력**: *_FLOWCHART.md, *_flowchart.svg, flowchart_generation_summary.md

### 공통
- **데이터 처리**: pandas, numpy, openpyxl
- **병렬/배치**: ThreadPoolExecutor (임베딩), 배치 처리 (요약)

## 기여하기

이슈와 PR은 언제든 환영합니다!
