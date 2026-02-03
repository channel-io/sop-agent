import numpy as np
import pickle
import hashlib
import os
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from ..config import (
    UPSTAGE_API_KEY,
    UPSTAGE_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE
)

def get_cache_key(texts, model_name):
    text_hash = hashlib.md5(''.join(texts).encode()).hexdigest()
    return f"{model_name}_{text_hash}_{len(texts)}"

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
    
    embeddings = []
    batch_size = EMBEDDING_BATCH_SIZE
    
    for i in tqdm(range(0, len(cleaned_texts), batch_size), desc="   Embedding"):
        batch = cleaned_texts[i:i+batch_size]
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
    
    embeddings = np.array(embeddings)
    
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'embeddings': embeddings,
            'model': EMBEDDING_MODEL,
            'n_samples': len(texts)
        }, f)
    
    return embeddings
