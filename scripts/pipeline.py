#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.clustering import (
    load_data,
    enhance_text,
    generate_embeddings,
    find_optimal_k,
    cluster_data,
    tag_clusters,
    save_results,
    save_messages
)
from scripts.config import DEFAULT_K_RANGE, DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_PREFIX

def print_header(text):
    print("\n" + "="*70)
    print(text)
    print("="*70)

def print_stats(df_chat, df_msg):
    print(f"   UserChat: {len(df_chat):,}개")
    print(f"   Message: {len(df_msg):,}개")

def print_text_enhancement_stats(df_chat):
    original_len = df_chat['summarizedMessage'].astype(str).str.len().mean()
    enhanced_len = df_chat['enhanced_text'].astype(str).str.len().mean()
    
    print("\n   전략별 통계:")
    strategy_counts = df_chat['text_strategy'].value_counts()
    for strategy, count in strategy_counts.items():
        pct = count / len(df_chat) * 100
        print(f"     {strategy:12s}: {count:5d}건 ({pct:5.1f}%)")
    
    print("\n   텍스트 길이 비교:")
    print(f"     원본 평균: {original_len:.0f}자")
    print(f"     향상 평균: {enhanced_len:.0f}자")
    print(f"     증가율: {(enhanced_len / original_len - 1) * 100:.1f}%")

def print_clustering_results(best_k, results):
    print(f"\n   테스트 K 값: {[r['n_clusters'] for r in results]}")
    for result in results:
        print(f"   K={result['n_clusters']:2d} → Silhouette={result['silhouette']:.3f}, "
              f"크기:[{result['min_size']:3d}-{result['max_size']:3d}], 평균:{result['avg_size']:.0f}")
    
    best_result = next(r for r in results if r['n_clusters'] == best_k)
    print(f"\n   ✅ 선택: K={best_k} (Silhouette={best_result['silhouette']:.3f})")
    print(f"   클러스터 크기: 최소 {best_result['min_size']}건, 최대 {best_result['max_size']}건")

def print_tagging_results(tags_df, df_chat):
    print("\n" + "="*70)
    print("📊 클러스터 태깅 결과")
    print("="*70)
    print(tags_df[['cluster_id', 'cluster_size', 'label', 'category']].to_string(index=False))
    
    print("\n" + "="*70)
    print("📈 카테고리별 분포")
    print("="*70)
    category_dist = tags_df.groupby('category')['cluster_size'].sum().sort_values(ascending=False)
    for category, count in category_dist.items():
        pct = count / len(df_chat) * 100
        print(f"   {category:10s}: {count:3d}건 ({pct:5.1f}%)")

def main():
    parser = argparse.ArgumentParser(
        description='Customer Support Chat Clustering Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input', '-i', required=True, help='입력 Excel 파일')
    parser.add_argument('--sample', '-s', help='샘플링할 데이터 수 (기본: 1000, 예: 1000 또는 all)')
    parser.add_argument('--k', help='클러스터 개수 (기본: auto, 예: auto 또는 10)')
    parser.add_argument('--k-range', help='테스트할 K 값들 (쉼표 구분, 예: 10,15,20,25)')
    parser.add_argument('--tagging-mode', default='api', choices=['api', 'agent', 'skip'],
                        help='태깅 방식 (api: Solar-mini 개별, agent: Solar-pro 통합, skip: 건너뛰기, 기본: api)')
    parser.add_argument('--skip-tagging', action='store_true',
                        help='태깅을 건너뛰고 클러스터링만 수행 (Claude 수동 태깅용)')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_DIR, help=f'출력 디렉토리 (기본: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--prefix', '-p', default=DEFAULT_OUTPUT_PREFIX, help=f'출력 파일명 접두사 (기본: {DEFAULT_OUTPUT_PREFIX})')
    parser.add_argument('--cache-dir', default=DEFAULT_CACHE_DIR, help=f'캐시 디렉토리 (기본: {DEFAULT_CACHE_DIR})')
    
    args = parser.parse_args()

    # Handle skip-tagging flag
    if args.skip_tagging:
        args.tagging_mode = 'skip'

    # Parse sample size
    sample_size = None
    if args.sample:
        if args.sample == 'all':
            sample_size = None
        else:
            sample_size = int(args.sample)
    else:
        sample_size = 1000  # Default: 1000

    print_header("🎯 Customer Support Chat Clustering Pipeline")
    print(f"   입력: {args.input}")
    print(f"   샘플: {sample_size if sample_size else '전체'}")
    print(f"   출력: {args.output}/{args.prefix}_*.xlsx")

    print_header("1️⃣ 데이터 로딩")
    df_chat, df_msg = load_data(args.input, sample_size)
    print_stats(df_chat, df_msg)
    if sample_size:
        print(f"   샘플링: {sample_size:,}개")
    
    print_header("2️⃣ 텍스트 향상")
    df_chat = enhance_text(df_chat, df_msg)
    print_text_enhancement_stats(df_chat)
    
    print_header("3️⃣ 임베딩 생성")
    texts = df_chat['enhanced_text'].tolist()
    embeddings = generate_embeddings(texts, cache_dir=args.cache_dir)
    print(f"   생성 완료: {embeddings.shape}")
    
    print_header("4️⃣ K-Means 클러스터링")
    if args.k and args.k != 'auto':
        # Fixed K value
        k_value = int(args.k)
        print(f"\n   K={k_value} (고정)")
        labels, silhouette = cluster_data(embeddings, k_value)
        print(f"   Silhouette Score: {silhouette:.3f}")
    else:
        # Auto: find optimal K
        k_range = None
        if args.k_range:
            k_range = [int(k) for k in args.k_range.split(',')]
        else:
            k_range = DEFAULT_K_RANGE

        best_k, labels, results = find_optimal_k(embeddings, k_range)
        print_clustering_results(best_k, results)
    
    df_chat['cluster_id'] = labels

    # Tagging step (conditional)
    if args.tagging_mode == 'skip':
        print_header("5️⃣ LLM 태깅")
        print("   ⏭️  Tagging skipped (use /tag-clusters-manual in Claude Code for manual tagging)")

        # Create placeholder tags
        df_chat['label'] = '[Unlabeled]'
        df_chat['category'] = '[Uncategorized]'
        df_chat['keywords'] = ''

        tags_df = pd.DataFrame({
            'cluster_id': sorted(df_chat['cluster_id'].unique()),
            'cluster_size': [len(df_chat[df_chat['cluster_id'] == cid]) for cid in sorted(df_chat['cluster_id'].unique())],
            'label': ['[Unlabeled]'] * df_chat['cluster_id'].nunique(),
            'category': ['[Uncategorized]'] * df_chat['cluster_id'].nunique(),
            'keywords': [''] * df_chat['cluster_id'].nunique()
        })
    else:
        print_header(f"5️⃣ LLM 태깅 ({args.tagging_mode} 방식)")
        tags_df = tag_clusters(df_chat, mode=args.tagging_mode)
        print_tagging_results(tags_df, df_chat)

    print_header("6️⃣ 결과 저장")
    result_file, tags_file = save_results(df_chat, tags_df, args.output, args.prefix)
    print(f"   ✅ {tags_file}")
    print(f"   ✅ {result_file}")

    # Save message data for sampled chats
    messages_file = save_messages(df_chat, df_msg, args.output, args.prefix)

    print_header("✅ 완료")

if __name__ == '__main__':
    main()
