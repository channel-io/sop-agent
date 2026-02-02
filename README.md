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

### 3. 기본 실행

```bash
python3 scripts/pipeline.py --input data/input.xlsx --output results
```

## 디렉토리 구조

```
.
├── .claude/        # Claude Code Skills
├── agent-sops/     # Agent SOP 파일들 (.sop.md)
├── scripts/        # Python 스크립트
├── data/          # 입력 Excel 파일
├── results/       # 출력 결과
├── templates/     # SOP 템플릿
└── docs/          # 프로젝트 문서
```

## 개발 로드맵

### Phase 1: 초기 설정 ✅
- [x] 프로젝트 구조 설정
- [x] 기본 디렉토리 생성
- [x] README 작성

### Phase 2: Stage 1 구현 (예정)
- [ ] 클러스터링 파이프라인 구현
- [ ] 임베딩 캐싱 시스템
- [ ] LLM 자동 태깅

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
- [ ] Claude Code Skills 통합
- [ ] 문서화 완성

## 기술 스택

- **임베딩**: Upstage Solar `embedding-passage` (4096차원)
- **클러스터링**: scikit-learn K-Means
- **LLM**: Upstage Solar `solar-mini`
- **데이터 처리**: pandas, numpy

## 기여하기

이슈와 PR은 언제든 환영합니다!
