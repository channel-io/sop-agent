import numpy as np
import pickle
import hashlib
import os
import time
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI # pyright: ignore[reportMissingImports]
from ..config import (
    UPSTAGE_API_KEY,
    UPSTAGE_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE
)

# 캐시 키 생성
def get_cache_key(texts, model_name):
    text_hash = hashlib.md5(''.join(texts).encode()).hexdigest()
    return f"{model_name}_{text_hash}_{len(texts)}"

# 임베딩 생성 및 캐싱
def generate_embeddings(texts, cache_dir='cache'):
    os.makedirs(cache_dir, exist_ok=True)
    cache_key = get_cache_key(texts, EMBEDDING_MODEL)
    cache_file = Path(cache_dir) / f"embeddings_{cache_key}.pkl"
    
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
            return cache_data['embeddings']
    
    cleaned_texts = []
    for text in texts:
        text = str(text).strip()
        if len(text) < 3:
            text = "빈 텍스트"
        cleaned_texts.append(text)
    
    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url=UPSTAGE_BASE_URL)

    def embed_batch_with_retry(batch, max_retries=3):
        """배치 임베딩 생성 (재시도 로직 포함)"""
        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"\n   ⚠️  배치 임베딩 실패 (시도 {attempt + 1}/{max_retries}), {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"\n   ❌ 배치 임베딩 최종 실패: {e}")
                    raise

    # 배치 준비
    batch_size = EMBEDDING_BATCH_SIZE
    batches = [cleaned_texts[i:i+batch_size] for i in range(0, len(cleaned_texts), batch_size)]

    # 병렬 처리 (최대 3개 동시 요청)
    embeddings = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(embed_batch_with_retry, batch): idx
                   for idx, batch in enumerate(batches)}

        # 진행상황 표시
        results = {}
        for future in tqdm(as_completed(futures), total=len(futures), desc="   Embedding"):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                raise RuntimeError(f"배치 {idx} 임베딩 실패 - 전체 작업 중단") from e

        # 순서대로 병합
        for idx in sorted(results.keys()):
            embeddings.extend(results[idx])

    embeddings = np.array(embeddings)
    
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'embeddings': embeddings,
            'model': EMBEDDING_MODEL,
            'n_samples': len(texts)
        }, f)
    
    return embeddings
