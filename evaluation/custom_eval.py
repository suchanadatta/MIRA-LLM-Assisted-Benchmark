import pandas as pd
from collections import defaultdict
import numpy as np


def load_relevance_judgments(file_path):
    """Load relevance judgments from file."""
    judgments = defaultdict(dict)
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                query_id, doc_id, doc_category, rel_score = parts[0], parts[1], parts[2], int(parts[3])
                judgments[query_id][(doc_id, doc_category)] = rel_score
    return judgments


def load_bm25_results(file_path):
    """Load BM25 results from file."""
    results = defaultdict(list)
    df = pd.read_csv(file_path, sep='\t')

    for _, row in df.iterrows():
        query_id = str(row['query_id'])
        doc_id = row['item']
        rank = row['rank']
        score = row['score']
        # Assuming document_category is 'publication' or should be extracted from results
        doc_category = row['category']  # Default category - adjust if your file has this column
        results[query_id].append({
            'doc_id': doc_id,
            'doc_category': doc_category,
            'rank': rank,
            'score': score
        })

    return results


def get_relevance(query_id, doc_id, doc_category, judgments):
    """Get relevance score for a document."""
    if query_id in judgments and (doc_id, doc_category) in judgments[query_id]:
        return judgments[query_id][(doc_id, doc_category)]
    return 0


def compute_dcg(relevances, k=None):
    """Compute Discounted Cumulative Gain."""
    if k:
        relevances = relevances[:k]
    dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))
    return dcg


def compute_idcg(judgments, query_id, k=None):
    """Compute Ideal DCG (perfect ranking)."""
    rels = sorted(judgments[query_id].values(), reverse=True)
    return compute_dcg(rels, k)


def compute_ap(ranked_docs, query_id, judgments):
    """Compute Average Precision."""
    relevant_count = 0
    ap_sum = 0

    for rank, doc in enumerate(ranked_docs, 1):
        rel = get_relevance(query_id, doc['doc_id'], doc['doc_category'], judgments)
        if rel > 0:
            relevant_count += 1
            ap_sum += relevant_count / rank

    total_relevant = sum(1 for rel in judgments[query_id].values() if rel > 0)
    if total_relevant == 0:
        return 0.0

    return ap_sum / total_relevant


def compute_recall(ranked_docs, query_id, judgments, k=None):
    """Compute Recall."""
    if k:
        ranked_docs = ranked_docs[:k]

    relevant_count = sum(
        1 for doc in ranked_docs if get_relevance(query_id, doc['doc_id'], doc['doc_category'], judgments) > 0)
    total_relevant = sum(1 for rel in judgments[query_id].values() if rel > 0)

    if total_relevant == 0:
        return 0.0

    return relevant_count / total_relevant


def compute_precision_at_k(ranked_docs, query_id, judgments, k):
    """Compute Precision@k."""
    ranked_docs_k = ranked_docs[:k]
    relevant_count = sum(
        1 for doc in ranked_docs_k if get_relevance(query_id, doc['doc_id'], doc['doc_category'], judgments) > 0)

    return relevant_count / k if k > 0 else 0.0


def compute_ndcg(ranked_docs, query_id, judgments, k=None):
    """Compute Normalized DCG."""
    relevances = [get_relevance(query_id, doc['doc_id'], doc['doc_category'], judgments) for doc in ranked_docs]
    dcg = compute_dcg(relevances, k)
    idcg = compute_idcg(judgments, query_id, k)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def compute_mrr(ranked_docs, query_id, judgments):
    """Compute Mean Reciprocal Rank."""
    for rank, doc in enumerate(ranked_docs, 1):
        rel = get_relevance(query_id, doc['doc_id'], doc['doc_category'], judgments)
        if rel > 0:
            return 1.0 / rank

    return 0.0


def evaluate(judgments, results):
    """Compute all metrics."""
    metrics = {
        'MAP': [],
        'Recall': [],
        'Recall@100': [],
        'Precision@100': [],
        'NDCG': [],
        'NDCG@100': [],
        'MRR': []
    }

    for query_id in results:
        if query_id not in judgments:
            continue

        ranked_docs = results[query_id]

        metrics['MAP'].append(compute_ap(ranked_docs, query_id, judgments))
        metrics['Recall'].append(compute_recall(ranked_docs, query_id, judgments))
        metrics['Recall@100'].append(compute_recall(ranked_docs, query_id, judgments, k=100))
        metrics['Precision@100'].append(compute_precision_at_k(ranked_docs, query_id, judgments, k=100))
        metrics['NDCG'].append(compute_ndcg(ranked_docs, query_id, judgments))
        metrics['NDCG@100'].append(compute_ndcg(ranked_docs, query_id, judgments, k=100))
        metrics['MRR'].append(compute_mrr(ranked_docs, query_id, judgments))

    # Compute averages
    summary = {}
    for metric_name, values in metrics.items():
        summary[metric_name] = np.mean(values) if values else 0.0

    return summary, metrics


# Main execution
if __name__ == "__main__":
    # Load files
    judgments = load_relevance_judgments('./qrels/qrels.tsv')
    results = load_bm25_results('/Users/suchana/NetBeansProjects/GesisLogDataset/output/eval_test_merged.tsv')

    # Compute metrics
    summary, all_metrics = evaluate(judgments, results)

    # Print results
    print("=" * 50)
    print("EVALUATION METRICS SUMMARY")
    print("=" * 50)
    for metric, value in summary.items():
        print(f"{metric:20s}: {value:.4f}")
    print("=" * 50)