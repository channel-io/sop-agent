import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from ..config import DEFAULT_K_RANGE

def find_optimal_k(embeddings, k_range=None):
    if k_range is None:
        k_range = DEFAULT_K_RANGE
    
    results = []
    for n_clusters in k_range:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        silhouette = silhouette_score(embeddings, labels)
        
        cluster_sizes = pd.Series(labels).value_counts()
        min_size = cluster_sizes.min()
        max_size = cluster_sizes.max()
        avg_size = cluster_sizes.mean()
        
        results.append({
            'n_clusters': n_clusters,
            'silhouette': silhouette,
            'min_size': min_size,
            'max_size': max_size,
            'avg_size': avg_size,
            'labels': labels
        })
    
    best = max(results, key=lambda x: x['silhouette'])
    
    return best['n_clusters'], best['labels'], results

def cluster_data(embeddings, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    silhouette = silhouette_score(embeddings, labels)
    
    return labels, silhouette
