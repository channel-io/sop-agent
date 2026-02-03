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

def tag_clusters(df, mode='agent', llm_model=None, samples_per_cluster=None):
    if mode == 'agent':
        return _tag_with_agent(df, llm_model, samples_per_cluster)
    else:
        return _tag_with_api(df, llm_model, samples_per_cluster)

def _tag_with_api(df, llm_model=None, samples_per_cluster=None):
    if llm_model is None:
        llm_model = LLM_MODEL
    if samples_per_cluster is None:
        samples_per_cluster = LLM_SAMPLES_PER_CLUSTER
    
    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url=UPSTAGE_BASE_URL)
    
    cluster_tags = []
    
    for cluster_id in sorted(df['cluster_id'].unique()):
        cluster_df = df[df['cluster_id'] == cluster_id]
        samples = cluster_df['enhanced_text'].dropna().head(samples_per_cluster).tolist()
        
        sample_text = "\n".join([f"{i+1}. {text[:200]}" for i, text in enumerate(samples)])
        
        prompt = f"""다음은 고객 상담 내용들입니다. 이 클러스터를 대표하는 라벨을 생성하세요.

클러스터 크기: {len(cluster_df)}건

샘플 (상위 {len(samples)}개):
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
    
    tags_df = pd.DataFrame(cluster_tags)
    return tags_df

def _tag_with_agent(df, llm_model=None, samples_per_cluster=None):
    if llm_model is None:
        llm_model = LLM_MODEL
    if samples_per_cluster is None:
        samples_per_cluster = LLM_SAMPLES_PER_CLUSTER
    
    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url=UPSTAGE_BASE_URL)
    
    cluster_summaries = []
    for cluster_id in sorted(df['cluster_id'].unique()):
        cluster_df = df[df['cluster_id'] == cluster_id]
        samples = cluster_df['enhanced_text'].dropna().head(samples_per_cluster).tolist()
        
        samples_text = "\n".join([f"  - {text[:150]}" for text in samples[:10]])
        
        cluster_summaries.append(f"""
[클러스터 {cluster_id}] (n={len(cluster_df)}건)
{samples_text}
""")
    
    all_clusters_text = "\n".join(cluster_summaries)
    
    prompt = f"""다음은 고객 상담 데이터를 클러스터링한 결과입니다.

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
        response = client.chat.completions.create(
            model="solar-pro",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        result_json = json.loads(result_text)
        
        tags_df = pd.DataFrame(result_json)
        return tags_df
    
    except Exception as e:
        print(f"\n⚠️  Agent 태깅 실패 (에러: {e}), API 방식으로 폴백...")
        return _tag_with_api(df, llm_model, samples_per_cluster)
