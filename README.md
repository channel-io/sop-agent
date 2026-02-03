# Userchat-to-SOP Pipeline

Userchat 고객 상담 데이터를 Agent SOP 문서로 자동 변환하는 3단계 AI 파이프라인

## 프로젝트 개요

- **목적**: Excel 고객 상담 데이터 → 재사용 가능한 Agent SOP 문서 자동 생성
- **방법**: 3단계 파이프라인 (Clustering → Extraction → SOP Generation)
- **기술 스택**:
  - **Stage 1 (Python)**: Upstage Solar 임베딩 + K-Means 클러스터링
  - **Stage 2 (LLM)**: 패턴 추출 + FAQ 생성
  - **Stage 3 (LLM)**: Agent SOP 문서 생성

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

### 3. Stage 1: 클러스터링 실행

#### Python 스크립트 직접 실행

```bash
# 기본 실행 (1000개 샘플, 자동 K 선택, Agent 태깅)
python3 scripts/pipeline.py --input data/user_chat.xlsx --output results/company --prefix company

# 전체 데이터 실행
python3 scripts/pipeline.py --input data/user_chat.xlsx --output results/company --prefix company --sample all

# K 값 지정
python3 scripts/pipeline.py --input data/user_chat.xlsx --output results/company --prefix company --k 20

# 최적 K 탐색
python3 scripts/pipeline.py --input data/user_chat.xlsx --output results/company --prefix company --k-range 10,15,20,25
```

#### Claude Code Skill 사용 (권장)

```bash
# 대화형 실행 - 파라미터 선택 가이드와 함께
/stage1-clustering
```

### 4. 결과 확인

```bash
# 클러스터링 결과
results/{company}/{company}_clustered.xlsx   # 원본 데이터 + 클러스터 정보
results/{company}/{company}_tags.xlsx        # 클러스터 메타데이터
results/{company}/analysis_report.md         # 분석 리포트
```

## 디렉토리 구조

```
.
├── .claude/                    # Claude Code Skills
│   └── skills/
│       └── stage1-clustering/  # Stage 1 Skill
├── agent-sops/                 # Agent SOP 파일들 (.sop.md)
├── scripts/                    # Python 스크립트
│   ├── pipeline.py            # Stage 1 진입점
│   ├── config.py              # API 키, 기본 설정
│   └── clustering/            # 클러스터링 모듈
│       ├── data_loader.py     # Excel 로딩
│       ├── text_enhancer.py   # 텍스트 향상 (3-level fallback)
│       ├── embeddings.py      # 임베딩 생성 (병렬 처리 + 캐싱)
│       ├── clustering.py      # K-Means 클러스터링
│       ├── tagging.py         # LLM 자동 태깅
│       └── output.py          # Excel 저장
├── data/                      # 입력 Excel 파일
├── results/                   # 출력 결과
│   └── {company}/
│       ├── {company}_clustered.xlsx  # 클러스터링 결과
│       ├── {company}_tags.xlsx       # 클러스터 메타데이터
│       └── analysis_report.md        # 분석 리포트
├── cache/                     # 임베딩 캐시
├── templates/                 # SOP 템플릿
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

### Phase 3: Stage 2 구현 (예정)
- [ ] 패턴 추출 로직
- [ ] FAQ 자동 생성
- [ ] 키워드 추출

### Phase 4: Stage 3 구현 (예정)
- [ ] Agent SOP 생성
- [ ] 템플릿 시스템
- [ ] 메타데이터 생성

### Phase 5: 통합 (예정)
- [ ] 전체 파이프라인 연결
- [ ] 문서화 완성

## Claude Code Skills

### `/stage1-clustering`
대화형 Stage 1 실행 - 파라미터 선택 가이드 제공
- 데이터 파일 자동 스캔 및 선택
- 회사명 자동 추출
- Interactive/Auto 모드 지원

## 기술 스택

- **임베딩**: Upstage Solar `embedding-passage`
- **클러스터링**: scikit-learn K-Means
- **LLM**: Upstage Solar `solar-mini`, `solar-pro`
- **데이터 처리**: pandas, numpy
- **병렬 처리**: ThreadPoolExecutor

## 기여하기

이슈와 PR은 언제든 환영합니다!
