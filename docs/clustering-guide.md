# 고객 상담 데이터 클러스터링 가이드

## 개요

이 SOP는 고객 상담 채팅 데이터의 자동 클러스터링 및 태깅을 안내합니다. 한국어 고객 서비스 대화를 완전한 파이프라인으로 처리합니다: 데이터 전처리, 텍스트 향상, 임베딩 생성(Upstage Solar), K-Means 클러스터링, LLM 기반 태깅, 구조화된 출력 생성.

**활용 사례:**
- 대량(1000건 이상)의 고객 상담 채팅 로그 분석
- 고객 문의를 주제별로 자동 분류
- 고객 서비스 상호작용의 일반적인 패턴 식별
- 업종별 카테고리 분류 체계 생성
- SOP(표준 운영 절차) 추출을 위한 데이터 준비

**주요 기능:**
- 3단계 텍스트 향상 폴백 전략
- 자동 임베딩 캐싱 (4096차원 벡터)
- Silhouette 점수 기반 최적 클러스터 수 선택
- 두 가지 태깅 모드: API(빠름) 또는 Claude 수동(고품질)
- 업종 적응형 카테고리 생성

## 파라미터

### 필수
- **input_file**: UserChat 데이터가 포함된 Excel 파일 경로
  - "UserChat data" 시트(채팅 메타데이터 포함) 필수
  - "Message data" 시트(대화 메시지 포함) 필수
  - 형식: `.xlsx` 파일

### 선택
- **sample_size** (기본값: 1000): 처리할 레코드 수
  - 표준 분석에는 1000 사용 (권장 기본값)
  - 전체 데이터셋이 명시적으로 필요한 경우에만 "all" 사용
  - 참고: 대부분의 클러스터링 작업에는 1000개 레코드로 충분

- **tagging_mode** (기본값: "agent"): 클러스터 태깅 방법
  - `"agent"`: 빠른 Solar-pro 통합 태깅 (5-15초, 업종 적응형, 권장)
  - `"api"`: Solar-mini 독립 태깅 (30초, 하드코딩된 카테고리)
  - `"skip"`: 태깅 건너뛰기, 최고 품질을 위해 `/tag-clusters-manual` 스킬 사용

- **k** (기본값: "auto"): 클러스터 수
  - `"auto"`: Silhouette 점수를 통해 최적 K 자동 선택
  - 정수 값: 고정 클러스터 수 사용

- **k_range** (기본값: "8,10,12,15,20,25"): k="auto"일 때 테스트할 K 값들
  - 쉼표로 구분된 정수 목록
  - k="auto"일 때만 사용됨

- **output_dir** (기본값: "results"): 출력 디렉토리 경로
- **prefix** (기본값: "output"): 출력 파일명 접두사
- **cache_dir** (기본값: "cache"): 임베딩 캐시 디렉토리

## 단계별 프로세스

### 1. 데이터 로딩 및 검증

Excel 데이터를 로드하고 구조를 검증합니다.

**제약 조건:**
- "UserChat data" 및 "Message data" 시트 존재 여부 반드시 검증
- 필수 컬럼 확인: `id`, `summarizedMessage` (있는 경우), messages
- 데이터 통계 보고 권장 (총 레코드 수, 날짜 범위, 회사)
- 필수 데이터가 누락된 레코드는 건너뛸 수 있음
- 시트가 누락되면 진행 불가

**필요 도구:**
- Excel 읽기용 `pandas`
- .xlsx 파일용 `openpyxl` 엔진

**예상 출력:**
```
Meliens에서 1,645개 레코드 로드됨
날짜 범위: 2024-01-01 ~ 2024-12-31
발견된 컬럼: id, userId, summarizedMessage, ...
```

### 2. 텍스트 향상

3단계 폴백 전략을 사용하여 텍스트 품질을 향상시킵니다.

**제약 조건:**
- 다음 우선순위를 반드시 적용:
  1. `summarizedMessage`가 존재하고 50자 이상이면 → 사용
  2. 그렇지 않고 `first_message`가 20자 이상이면 → 첫 메시지 사용
  3. 그 외 → 3턴(총 6개 메시지) 결합
- 레코드별로 어떤 전략을 사용했는지 추적 (`text_strategy` 컬럼에 저장)
- 텍스트 정리 권장: 여분의 공백 제거, NaN 값 처리
- 필요시 추가 전처리 적용 가능 (소문자화, 정규화)
- 빈 문자열 사용 금지 (대신 NaN으로 표시)

**텍스트 향상 로직:**
```python
def enhance_text(row, messages_df):
    # 전략 1: summarizedMessage
    if row['summarizedMessage'] and len(row['summarizedMessage']) >= 50:
        return row['summarizedMessage'], 'summary'

    # 전략 2: first_message
    user_messages = messages_df[messages_df['chatId'] == row['id']]
    if not user_messages.empty:
        first_msg = user_messages.iloc[0]['content']
        if len(first_msg) >= 20:
            return first_msg, 'first_message'

    # 전략 3: 3턴(6개 메시지) 결합
    combined = ' '.join(user_messages['content'].head(6).tolist())
    return combined, 'combined_turns'
```

**예상 출력:**
- 새 컬럼: `enhanced_text` (향상된 텍스트)
- 새 컬럼: `text_strategy` (사용된 전략)
- 통계: "93.9%가 summary 사용, 2.5%가 first_message 사용, 3.6%가 결합 턴 사용"

### 3. 임베딩 생성

자동 캐싱과 함께 Upstage Solar API를 사용하여 4096차원 임베딩을 생성합니다.

**제약 조건:**
- Upstage Solar `embedding-passage` 모델 반드시 사용
- 임베딩 생성 전 캐시 확인 필수 (캐시 키: model_texthash_samplesize)
- API 호출 배치 처리 필수 (권장: 배치당 100개 텍스트)
- 진행 상황 표시 권장 (예: "임베딩 배치 1/10...")
- 실패한 API 호출은 최대 3회까지 재시도 가능
- 생성 후 임베딩을 캐시에 저장 필수
- 빈 텍스트나 NaN 텍스트는 임베딩 금지 (먼저 필터링)

**API 설정:**
```python
import requests

UPSTAGE_API_KEY = "up_..."  # config.py에서 로드
EMBEDDING_MODEL = "embedding-passage"
API_URL = "https://api.upstage.ai/v1/solar/embeddings"

headers = {
    "Authorization": f"Bearer {UPSTAGE_API_KEY}",
    "Content-Type": "application/json"
}
```

**캐싱 메커니즘:**
```python
import pickle
import hashlib

def get_cache_key(texts, model):
    text_hash = hashlib.md5(''.join(texts).encode()).hexdigest()[:10]
    return f"embeddings_{model}_{text_hash}_{len(texts)}.pkl"

def load_embeddings_cache(cache_key, cache_dir="cache"):
    cache_path = f"{cache_dir}/{cache_key}"
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None
```

**예상 출력:**
- 형태가 (N, 4096)인 Numpy 배열
- 저장된 캐시 파일: `cache/embeddings_embedding-passage_abc123_1000.pkl`
- 시간 보고: "45초 만에 1000개 임베딩 생성" 또는 "2초 만에 캐시에서 로드"

### 4. K-Means 클러스터링

최적 K 선택과 함께 K-Means 클러스터링을 수행합니다.

**제약 조건:**
- 클러스터링 전 임베딩 정규화 필수 (아직 정규화되지 않은 경우)
- k="auto"인 경우: k_range의 모든 K 값을 테스트하고 Silhouette 점수로 최적값 선택 필수
- k가 정수인 경우: 해당 K를 직접 사용 필수
- 모든 레코드에 클러스터 ID (0부터 K-1) 할당 필수
- 클러스터 크기 계산 및 분포 보고 권장
- 더 나은 수렴을 위해 k-means++로 초기화 가능
- K-Means 이외의 클러스터링 알고리즘 사용 금지 (분석 요구사항)

**Silhouette 점수 계산:**
```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def find_optimal_k(embeddings, k_range=[8, 10, 12, 15, 20, 25]):
    best_k = k_range[0]
    best_score = -1

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels, sample_size=min(10000, len(embeddings)))

        print(f"K={k}: Silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k

    return best_k, best_score
```

**예상 출력:**
- 새 컬럼: `cluster_id` (0부터 K-1)
- 새 컬럼: `cluster_size` (클러스터 내 레코드 수)
- 보고: "최적 K=20, Silhouette 점수=0.064"
- 클러스터 분포 테이블

### 5. 클러스터 태깅

LLM을 사용하여 각 클러스터에 라벨, 카테고리, 키워드를 태깅합니다.

**제약 조건:**
- `tagging_mode` 파라미터에 따라 두 가지 태깅 모드 중 하나를 반드시 선택
- 두 모드 모두: 각 클러스터에 대해 라벨, 카테고리, 키워드 생성 필수
- **모든 출력 필드(라벨, 카테고리, 키워드, 설명)는 반드시 한국어로 생성**
- 모든 텍스트 필드는 한국어 사용 (예: "AS_접수", "일반_상담", "충전기", "보풀제거기")
- 분석을 위해 클러스터당 대표 샘플 5개 추출 권장
- 매우 긴 텍스트(200자 이상)는 표시용으로 잘라낼 수 있음
- 정말 필요한 경우가 아니면 "기타" 카테고리 생성 금지

#### 모드 A: API 태깅 (tagging_mode="api")

**제약 조건:**
- 빠른 태깅을 위해 Solar-mini API 반드시 사용
- 각 클러스터를 독립적으로 태깅 필수
- **API 프롬프트의 모든 출력 필드에 한국어 반드시 사용**
- 하드코딩된 카테고리 사용 권장: ["구매", "배송", "AS", "취소", "견적", "기타"]
- 예상 시간: 20개 클러스터에 약 30초
- 예상 비용: 1000개 레코드당 약 $0.01

**API 프롬프트 템플릿:**
```python
prompt = f"""
다음은 고객 상담 채팅 클러스터의 샘플입니다:

{samples}

이 클러스터를 분석하여 JSON으로 응답하세요. 모든 필드는 한국어로 작성하세요:
{{
  "label": "클러스터 라벨 (예: AS_접수, 배송_조회)",
  "category": "구매|배송|AS|취소|견적|기타 중 하나",
  "keywords": ["키워드1", "키워드2", "키워드3"]
}}
"""
```

#### 모드 B: Claude 수동 태깅 (tagging_mode="claude_manual")

**제약 조건:**
- 모든 클러스터를 전체적으로 분석 필수 (독립적으로 아님)
- 업종별 카테고리 자동 생성 필수 (하드코딩 아님)
- **모든 태그(라벨, 카테고리, 키워드, 설명)를 반드시 한국어로 생성**
- 모든 출력 필드는 한국어 필수 (예: label="충전_AS", category="A/S", keywords=["충전기", "케이블"])
- 특수 케이스(빈 데이터, 내부 티켓) 식별 필수
- 각 클러스터에 대한 상세 설명 제공 권장
- 표준 카테고리 외에 사용자 정의 카테고리 생성 가능
- 예상 시간: 10개 클러스터당 약 2-3분
- 예상 비용: 더 높음 (Claude API 토큰)

**수동 분석 프로세스:**
```python
# 1. 모든 클러스터에서 샘플 추출
for cluster_id in range(K):
    samples = df[df['cluster_id'] == cluster_id]['enhanced_text'].dropna().head(5)
    print(f"클러스터 {cluster_id}: {samples}")

# 2. Claude가 패턴을 분석하고 태그 생성 (한국어로)
manual_tags = {
    0: {
        'label': '제품_문의',
        'category': '일반_상담',
        'keywords': ['보풀제거기', '칼날', '쿠폰', '사용법'],
        'description': '보풀제거기 제품 기능, 사용법, 구매 옵션 문의'
    },
    3: {
        'label': '데이터_오류',
        'category': '시스템',
        'keywords': ['빈_데이터', 'NaN', '누락'],
        'description': '모든 레코드가 빈 데이터 - 시스템 오류'
    },
    # ... 각 클러스터에 대해
}

# 3. 데이터프레임에 태그 적용
for cluster_id, tags in manual_tags.items():
    mask = df['cluster_id'] == cluster_id
    df.loc[mask, 'label'] = tags['label']
    df.loc[mask, 'category'] = tags['category']
    df.loc[mask, 'keywords'] = str(tags['keywords'])
```

**품질 검사:**
- 잘 정의된 업종에서 0% "기타" 비율 확인
- 시스템 이상 확인 (빈 데이터, 내부 티켓)
- 카테고리가 업종별로 적합한지 확인
- 모든 출력 필드가 한국어인지 확인

**예상 출력:**
- 새 컬럼: `label` (클러스터 라벨)
- 새 컬럼: `category` (상위 카테고리)
- 새 컬럼: `keywords` (문자열로 된 키워드 목록)
- 분포를 보여주는 태그 요약 테이블

### 6. 출력 생성

포괄적인 데이터와 함께 두 개의 Excel 파일로 결과를 저장합니다.

**제약 조건:**
- 두 개의 출력 파일 생성 필수:
  1. `{prefix}_clustered.xlsx`: 모든 컬럼 + 클러스터 데이터가 포함된 전체 데이터셋
  2. `{prefix}_tags.xlsx`: 메타데이터가 포함된 클러스터 요약
- 클러스터링된 파일에 모든 원본 컬럼 포함 필수
- Excel 쓰기에 `openpyxl` 엔진 사용 필수
- 출력 디렉토리가 없으면 생성 권장
- 버전 관리를 위해 파일명에 타임스탬프 추가 가능
- 경고 없이 기존 파일 덮어쓰기 금지

**출력 파일 1: `{prefix}_clustered.xlsx`**

컬럼:
- 입력 Excel의 모든 원본 컬럼
- `enhanced_text`: 클러스터링에 사용된 향상된 텍스트
- `text_strategy`: 사용된 전략 (summary|first_message|combined_turns)
- `cluster_id`: 클러스터 ID (0부터 K-1)
- `cluster_size`: 이 클러스터의 레코드 수
- `label`: 클러스터 라벨 (예: "AS_접수")
- `category`: 상위 카테고리 (예: "A/S")
- `keywords`: 쉼표로 구분된 키워드

**출력 파일 2: `{prefix}_tags.xlsx`**

컬럼:
- `cluster_id`: 클러스터 ID
- `label`: 클러스터 라벨
- `category`: 상위 카테고리
- `keywords`: 쉼표로 구분된 키워드
- `description`: 상세 설명 (있는 경우)
- `count`: 클러스터 내 레코드 수
- `percentage`: 전체 레코드 중 비율
- `representative_samples`: 상위 3개 샘플 (선택사항)

**파일 저장:**
```python
import os
import pandas as pd

# 출력 디렉토리 생성
os.makedirs(output_dir, exist_ok=True)

# 클러스터링된 데이터 저장
output_path_clustered = f"{output_dir}/{prefix}_clustered.xlsx"
df.to_excel(output_path_clustered, index=False, engine='openpyxl')

# 태그 요약 저장
output_path_tags = f"{output_dir}/{prefix}_tags.xlsx"
tag_summary_df.to_excel(output_path_tags, index=False, engine='openpyxl')

print(f"✅ 결과 저장 완료:")
print(f"  - {output_path_clustered}")
print(f"  - {output_path_tags}")
```

**예상 출력:**
```
✅ 결과 저장 완료:
  - results/meliens_claude_manual/meliens_claude_manual_clustered.xlsx
  - results/meliens_claude_manual/meliens_claude_manual_tags.xlsx

카테고리 분포:
  A/S: 790건 (48.0%)
  일반_상담: 318건 (19.3%)
  배송: 196건 (11.9%)
  시스템: 171건 (10.4%)
  주문관리: 170건 (10.3%)
```

## 사용 예시

### 예시 1: 샘플링을 통한 빠른 분석

**입력:**
```bash
python3 scripts/pipeline.py \
  --input data/user_chat_assacom.xlsx \
  --sample 1000 \
  --tagging-mode api \
  --output results/assacom_sample \
  --prefix assacom_test
```

**예상 실행:**
1. Assacom에서 1000개 샘플 레코드 로드
2. 텍스트 향상 (3단계 폴백)
3. 임베딩 생성 (캐시 있으면 로드)
4. 최적 K 자동 선택 (8,10,12,15,20,25 테스트)
5. Solar-mini API로 클러스터 태깅 (약 30초)
6. 결과 저장

**출력 파일:**
- `results/assacom_sample/assacom_test_clustered.xlsx` (1000행)
- `results/assacom_sample/assacom_test_tags.xlsx` (K행, 예: 20)

**성능:**
- 시간: 약 2분 (임베딩 1분 + 태깅 30초 + 처리 30초)
- 비용: 약 $0.06 (임베딩 $0.05 + 태깅 $0.01)

### 예시 2: Claude 수동 태깅을 통한 프로덕션 실행

**입력:**
```bash
python3 scripts/pipeline.py \
  --input "data/raw data_meliens.xlsx" \
  --k 10 \
  --tagging-mode claude_manual \
  --output results/meliens_production \
  --prefix meliens_v1
```

**예상 실행:**
1. 전체 데이터셋 로드 (1,645개 레코드)
2. 텍스트 향상
3. 임베딩 생성 (또는 캐시에서 로드)
4. K=10으로 클러스터링 (고정)
5. Claude가 10개 클러스터를 수동으로 분석하고 태깅 (약 2-3분)
6. 결과 저장

**출력 파일:**
- `results/meliens_production/meliens_v1_clustered.xlsx` (1,645행)
- `results/meliens_production/meliens_v1_tags.xlsx` (10행)

**태그 품질:**
- 0% "기타" 카테고리
- 업종별 카테고리: A/S (48.0%), 일반_상담 (19.3%), 배송 (11.9%)
- 특수 케이스 감지: 데이터_오류 (7.1%), 내부_티켓 (3.3%)

### 예시 3: 다중 회사 배치 처리

**입력:**
```bash
# Assacom (PC/하드웨어)
python3 scripts/pipeline.py --input data/user_chat_assacom.xlsx --sample 1000 \
  --k 20 --prefix assacom --output results/assacom_agent

# Usimsa (통신)
python3 scripts/pipeline.py --input data/user_chat_usimsa.xlsx --sample 1000 \
  --k 10 --prefix usimsa --output results/usimsa_agent

# Meliens (전자제품)
python3 scripts/pipeline.py --input "data/raw data_meliens.xlsx" \
  --k 10 --prefix meliens --output results/meliens_agent
```

**예상 결과:**

| 회사 | 업종 | K | Silhouette | 주요 카테고리 |
|------|------|---|------------|--------------|
| Assacom | PC/하드웨어 | 20 | 0.064 | AS (33.8%), 일반문의 (28.5%) |
| Usimsa | 통신 | 10 | 0.041 | 활성화, 기기설정, 사용량관리 |
| Meliens | 전자제품 | 10 | 0.132 | A/S (48.0%), 일반_상담 (19.3%) |

## 문제 해결

### 문제 1: "KeyError: 'summarizedMessage'"

**원인:** 입력 Excel에 `summarizedMessage` 컬럼이 없음 (예: Meliens 데이터셋)

**해결:**
- 이것은 예상된 동작입니다 - 텍스트 향상이 폴백 전략을 사용합니다
- 2단계 로그에서 "Strategy: first_message" 또는 "Strategy: combined_turns" 확인
- `enhanced_text`가 채워져 있으면 조치 불필요

### 문제 2: 낮은 Silhouette 점수 (<0.05)

**원인:** 고차원 임베딩(4096D)과 제한된 샘플이 차원의 저주를 일으킴

**맥락:**
- Meliens: K=10, 점수=0.132 (좋음)
- Assacom: K=20, 점수=0.064 (허용 가능)
- Usimsa: K=10, 점수=0.041 (낮지만 예상됨)

**해결:**
- 고차원 데이터에서 K-Means의 낮은 점수는 예상됨
- 클러스터 분포 균형과 태그 품질에 집중
- 클러스터가 너무 분산되면 K 줄이기 고려
- HDBSCAN으로 전환 금지 (70% 이상 노이즈 발생 - docs/FINAL_REPORT.md 참조)

### 문제 3: 높은 "기타" 카테고리 비율

**시나리오:** Usimsa 통신 데이터에서 API 모드가 57%를 "기타"로 태깅

**원인:** 하드코딩된 카테고리가 업종 도메인과 맞지 않음

**해결:**
- `--tagging-mode claude_manual`로 전환
- Claude가 업종별 카테고리를 자동 생성
- Usimsa 결과: 0% "기타", 적절한 통신 카테고리 (활성화, 기기설정)

### 문제 4: 빈 캐시, 느린 재실행

**증상:** 캐싱에도 불구하고 매 실행마다 임베딩 재생성

**원인:** 다음으로 인한 캐시 키 불일치:
- 다른 sample_size
- 데이터 순서 변경 (텍스트 해시 다름)
- 캐시 디렉토리 삭제

**해결:**
```bash
# 캐시 확인
ls -lh cache/

# 임베딩 캐시 형식:
# embeddings_{model}_{texthash}_{count}.pkl

# 캐시가 있지만 로드 안 되면:
# - 텍스트 해시가 일치하는지 확인 (같은 데이터 순서)
# - 샘플 크기가 일치하는지 확인
# - cache_dir 파라미터가 올바른지 확인
```

### 문제 5: LLM 태깅 JSON 파싱 오류

**증상:** 클러스터 태깅 시 `JSONDecodeError` (API 모드)

**원인:** LLM이 비-JSON 응답 또는 잘못된 JSON 반환

**현재 동작:**
- 파이프라인이 기본 라벨 "클러스터 X" 할당
- 처리 계속

**해결:**
- 실제 LLM 응답 확인을 위해 API 로그 확인
- 프롬프트 템플릿에 명확한 JSON 형식 요구사항 포함 확인
- 빈번한 실패 시: `claude_manual` 모드로 전환
- 또는 few-shot 예제로 프롬프트 개선

### 문제 6: 메모리 부족 (OOM) 오류

**증상:** 대용량 데이터셋에서 임베딩 또는 클러스터링 중 Python 충돌

**원인:** 10,000개 이상의 레코드와 4096D 임베딩을 메모리에 로드

**해결:**
```python
# 샘플 크기 줄이기
python3 scripts/pipeline.py --input data.xlsx --sample 5000

# 또는 배치로 처리 (pipeline.py 수정):
def process_in_batches(df, batch_size=5000):
    results = []
    for i in range(0, len(df), batch_size):
        batch = df[i:i+batch_size]
        # 배치 처리...
        results.append(batch_result)
    return pd.concat(results)
```

## 참고 사항

### K-Means를 HDBSCAN 대신 사용하는 이유

HDBSCAN(밀도 기반 클러스터링)을 테스트했지만 다음 이유로 기각:
- **기본 파라미터로 72% 노이즈** (1000개 레코드 중 720개 미할당)
- **EOM(Excess of Mass)으로 단일 클러스터에 907/1000**
- **차원의 저주**: 1000개 샘플에 4096D 임베딩 = 1:4.1 비율

K-Means가 성공하는 이유:
- 거리 기반 (밀도 기반 아님) - 고차원에서 작동
- 0% 노이즈 (모든 레코드 할당)
- 적절한 K 선택으로 균형 잡힌 클러스터

자세한 분석은 `docs/FINAL_REPORT.md` 참조.

### 태깅 모드 비교

| 측면 | API 모드 | Claude 수동 |
|------|----------|------------|
| 속도 | 약 30초 | 10개 클러스터당 약 2-3분 |
| 비용 | $0.01/1000 | 더 높음 (Claude 토큰) |
| 카테고리 | 하드코딩 | 업종 적응형 |
| "기타" 비율 | 20-57% | 0% |
| 특수 케이스 | 놓침 | 감지 (빈 데이터, 내부 티켓) |
| 확장성 | 높음 | 중간 |
| 품질 | 표준 도메인에 좋음 | 모든 도메인에 우수 |

**권장:**
- **API 모드**: 빠른 프로토타이핑, 표준 도메인 (구매/배송/AS)에 사용
- **Claude 수동**: 프로덕션, 업종별 분석, 품질이 중요한 작업에 사용

### 비용 분석 (1000개 레코드당)

**임베딩:**
- Upstage Solar embedding-passage: $0.05/1000 (100만 토큰 ≈ 1000개 한국어 문장)

**태깅:**
- API 모드 (Solar-mini): $0.01/1000
- Claude 수동: $0.02-0.05/1000 (복잡도에 따라 다름)

**1000개 레코드당 총액:**
- API 모드: 약 $0.06
- Claude 수동: 약 $0.08-$0.10

**전체 데이터셋 (24,322개 레코드):**
- API 모드: 약 $1.46
- Claude 수동: 약 $2.00

### 성능 벤치마크

하드웨어: MacBook Pro M1, 16GB RAM

| 데이터셋 크기 | 임베딩 시간 | 클러스터링 시간 | 태깅 시간 (API) | 태깅 시간 (Claude) | 총합 |
|--------------|------------|----------------|----------------|-------------------|------|
| 100개 레코드 | 10초 | 5초 | 3초 | 1분 | 약 1.5분 |
| 1,000개 레코드 | 60초 | 10초 | 30초 | 3분 | 약 5분 |
| 10,000개 레코드 | 10분 | 60초 | 5분 | 30분 | 약 45분 |

*참고: 임베딩 시간은 캐시 없음 가정. 캐시 있으면: 크기와 관계없이 약 2-5초.*

### 데이터 프라이버시 고려사항

**Upstage API:**
- 임베딩 생성을 위해 데이터가 외부 API로 전송됨
- 민감한 데이터 처리 전 Upstage 개인정보 정책 검토
- 기밀 데이터의 경우 온프레미스 임베딩 모델 고려

**Claude API:**
- 수동 태깅을 위해 채팅 데이터가 Claude로 전송됨
- Anthropic의 데이터 보존 정책 적용
- 민감한 데이터의 경우: API 모드(Solar-mini) 또는 로컬 LLM 사용

**권장:**
- 처리 전 PII(개인 식별 정보) 익명화
- 민감한 고객 데이터 제거 (이름, 전화번호, 주소)
- 필요시 기밀 비즈니스 정보 수정

## 관련 문서

- **Stage 1 SOP**: `/stage1-clustering` - 클러스터링 파이프라인 실행 AI 워크플로우
- **Stage 2 추출**: `/stage2-extraction` - 패턴 추출 워크플로우
- **Stage 3 SOP 생성**: `/stage3-sop-generation` - SOP 생성 워크플로우
- **전체 파이프라인**: `/excel-to-sop-pipeline` - 엔드투엔드 오케스트레이션
- **프로젝트 README**: `../README.md` - 프로젝트 개요 및 빠른 시작
