import pandas as pd
import json
from openai import OpenAI
from ..config import (
    UPSTAGE_API_KEY,
    UPSTAGE_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_SAMPLES_PER_CLUSTER
)

# ───────────────────────────────────────────────────────────── #
# 실제 대화 메시지 추출
# ───────────────────────────────────────────────────────────── #

def _get_conversation_samples(df_chat_cluster, df_msg, samples_per_cluster, max_turns=8, max_chars=150):
    """
    클러스터 내 샘플 상담건의 실제 대화를 추출한다.

    Args:
        df_chat_cluster: 해당 클러스터의 df_chat 슬라이스
        df_msg: 전체 Message 데이터프레임 (chatId, plainText, createdAt)
        samples_per_cluster: 샘플 상담 건수
        max_turns: 상담 1건당 최대 메시지 수
        max_chars: 메시지 1개당 최대 문자수

    Returns:
        list[str]: 포맷된 대화 문자열 목록
    """
    sampled_ids = df_chat_cluster['id'].dropna().head(samples_per_cluster).tolist()
    conversations = []

    for chat_id in sampled_ids:
        msgs = df_msg[df_msg['chatId'] == chat_id].sort_values('createdAt')
        if msgs.empty:
            continue

        lines = []
        for _, row in msgs.head(max_turns).iterrows():
            text = str(row.get('plainText', '')).strip()
            if not text or text.lower() in ('nan', 'none', ''):
                continue
            lines.append(f"  - {text[:max_chars]}")

        if lines:
            conversations.append("\n".join(lines))

    return conversations


# ───────────────────────────────────────────────────────────── #
# 공개 인터페이스
# ───────────────────────────────────────────────────────────── #

def tag_clusters(df, df_msg=None, mode='agent', llm_model=None, samples_per_cluster=None):
    """
    Args:
        df: cluster_id 컬럼이 포함된 df_chat
        df_msg: Message 데이터프레임 (제공 시 실제 대화 내용으로 태깅, 미제공 시 enhanced_text 사용)
        mode: 'agent' (Solar-pro 통합 분석) | 'api' (Solar-mini 개별 분석)
    """
    if mode == 'agent':
        return _tag_with_agent(df, df_msg, llm_model, samples_per_cluster)
    else:
        return _tag_with_api(df, df_msg, llm_model, samples_per_cluster)


# ───────────────────────────────────────────────────────────── #
# API 방식 (개별 클러스터 순차 호출)
# ───────────────────────────────────────────────────────────── #

def _tag_with_api(df, df_msg=None, llm_model=None, samples_per_cluster=None):
    if llm_model is None:
        llm_model = LLM_MODEL
    if samples_per_cluster is None:
        samples_per_cluster = LLM_SAMPLES_PER_CLUSTER

    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url=UPSTAGE_BASE_URL)
    cluster_tags = []

    for cluster_id in sorted(df['cluster_id'].unique()):
        cluster_df = df[df['cluster_id'] == cluster_id]

        # 실제 대화 또는 enhanced_text 중 선택
        if df_msg is not None:
            samples = _get_conversation_samples(cluster_df, df_msg, samples_per_cluster)
        else:
            samples = cluster_df['enhanced_text'].dropna().head(samples_per_cluster).tolist()

        if len(samples) == 0:
            cluster_tags.append({
                'cluster_id': cluster_id,
                'cluster_size': len(cluster_df),
                'label': '빈 데이터',
                'category': '시스템',
                'keywords': 'empty, 텍스트없음, 자동분류',
            })
            print(f"  ℹ️  클러스터 {cluster_id} ({len(cluster_df)}건): 빈 데이터 → 자동 분류")
            continue

        sample_text = "\n\n".join([f"[상담 {i+1}]\n{conv}" for i, conv in enumerate(samples)])
        source_label = "실제 대화" if df_msg is not None else "요약 텍스트"

        prompt = f"""다음은 고객 상담 {source_label}입니다. 이 클러스터를 대표하는 라벨을 생성하세요.

클러스터 크기: {len(cluster_df)}건

샘플 ({len(samples)}건):
{sample_text}

다음 형식으로 JSON 응답:
{{
  "label": "간결한 한글 라벨 (3-8자)",
  "category": "적절한 카테고리 (자유롭게)",
  "keywords": ["키워드1", "키워드2", "키워드3"]
}}"""

        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE
            )
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            cluster_tags.append({
                'cluster_id': cluster_id,
                'cluster_size': len(cluster_df),
                'label': result_json.get('label', f'클러스터 {cluster_id}'),
                'category': result_json.get('category', '기타'),
                'keywords': ', '.join(result_json.get('keywords', [])),
            })
        except Exception:
            cluster_tags.append({
                'cluster_id': cluster_id,
                'cluster_size': len(cluster_df),
                'label': f'클러스터 {cluster_id}',
                'category': '기타',
                'keywords': '',
            })

    return pd.DataFrame(cluster_tags)


# ───────────────────────────────────────────────────────────── #
# Agent 방식 (전체 클러스터 일괄 분석)
# ───────────────────────────────────────────────────────────── #

def _tag_with_agent(df, df_msg=None, llm_model=None, samples_per_cluster=None):
    if llm_model is None:
        llm_model = LLM_MODEL
    if samples_per_cluster is None:
        samples_per_cluster = LLM_SAMPLES_PER_CLUSTER

    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url=UPSTAGE_BASE_URL)

    cluster_summaries = []
    empty_cluster_tags = []

    source_label = "실제 대화 메시지" if df_msg is not None else "요약 텍스트"

    for cluster_id in sorted(df['cluster_id'].unique()):
        cluster_df = df[df['cluster_id'] == cluster_id]

        # 실제 대화 또는 enhanced_text 중 선택
        if df_msg is not None:
            samples = _get_conversation_samples(cluster_df, df_msg, samples_per_cluster)
        else:
            raw = cluster_df['enhanced_text'].dropna().head(samples_per_cluster).tolist()
            samples = [f"  - {text[:150]}" for text in raw]

        if len(samples) == 0:
            empty_cluster_tags.append({
                'cluster_id': cluster_id,
                'cluster_size': len(cluster_df),
                'label': '빈 데이터',
                'category': '시스템',
                'keywords': ['empty', '텍스트없음', '자동분류'],
            })
            print(f"  ℹ️  클러스터 {cluster_id} ({len(cluster_df)}건): 빈 데이터 → 자동 분류")
            continue

        if df_msg is not None:
            # 실제 대화: 상담별 블록으로 포맷
            conv_blocks = "\n\n".join([
                f"  [상담 {i+1}]\n{conv}" for i, conv in enumerate(samples[:10])
            ])
        else:
            conv_blocks = "\n".join(samples[:10])

        cluster_summaries.append(f"""
[클러스터 {cluster_id}] (n={len(cluster_df)}건)
{conv_blocks}
""")

    if len(cluster_summaries) == 0:
        return pd.DataFrame(empty_cluster_tags)

    all_clusters_text = "\n".join(cluster_summaries)

    prompt = f"""다음은 고객 상담 데이터를 클러스터링한 결과입니다. 각 클러스터에는 {source_label}가 포함되어 있습니다.

{all_clusters_text}

당신의 임무:
1. 전체 클러스터를 분석하여 이 데이터셋의 특성(업종, 문의 유형)을 파악하세요
2. 데이터에 적합한 카테고리 체계를 생성하세요 (5-10개 정도)
3. 각 클러스터를 일관되게 분류하세요

요구사항:
- 카테고리는 상호 배타적이고 전체를 포괄해야 함
- 클러스터 간 비교하며 일관된 기준으로 분류
- "기타"는 최소화 (정말 분류 불가능한 경우만)
- 라벨은 간결하게 3-8자

다음 형식의 JSON 배열로 응답:
[
  {{
    "cluster_id": 0,
    "cluster_size": 100,
    "label": "배송 지연 문의",
    "category": "배송",
    "keywords": ["배송", "지연", "조회"]
  }},
  ...
]

JSON만 출력하세요 (추가 설명 없이)."""

    try:
        temp = LLM_TEMPERATURE if LLM_TEMPERATURE is not None else 0.0
        response = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )

        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result_json = json.loads(result_text)

        if empty_cluster_tags:
            result_json.extend(empty_cluster_tags)

        tags_df = pd.DataFrame(result_json)
        tags_df = tags_df.sort_values('cluster_id').reset_index(drop=True)
        return tags_df

    except Exception as e:
        print(f"\n⚠️  Agent 태깅 실패 (에러: {e}), API 방식으로 폴백...")
        return _tag_with_api(df, df_msg, llm_model, samples_per_cluster)
