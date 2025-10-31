import pandas as pd

# --- Load qrel file and make qrel_dict ---
qrels = pd.read_csv("./qrels/publication_qrel_trec_format.tsv", sep=r"\s+", header=None,
                    names=["query_id", "Q0", "document_id", "relevance_score"])
qrels["query_id"] = qrels["query_id"].astype(str)
qrels["document_id"] = qrels["document_id"].astype(str)

qrel_dict = (
    qrels.groupby("query_id")["document_id"]
    .apply(list)
    .to_dict()
)
# print(qrel_dict)

# --- Load BM25 results ---
bm25 = pd.read_csv("/Users/suchana/NetBeansProjects/GesisLogDataset/output/publication_top100_bm25.res",
                   sep=r"\s+", header=None,
                   names=["query_id", "Q0", "document_id", "rank", "score", "document_category"])
bm25["query_id"] = bm25["query_id"].astype(str)
bm25["document_id"] = bm25["document_id"].astype(str)

# --- Filter to keep only documents appearing in qrel_dict ---
filtered = bm25[bm25.apply(
    lambda row: row["document_id"] in qrel_dict.get(row["query_id"], []),
    axis=1
)].copy()
print(filtered)

# --- For each query_id, sort by original rank, then reassign new rank 0, 1, 2, ... ---
filtered.sort_values(by=["query_id", "rank"], inplace=True)
filtered["new_rank"] = filtered.groupby("query_id").cumcount()
print(filtered)

# --- Reorder columns and write output (6-column file) ---
# --- 6 columns in this order: query_id, Q0, document_id, new_rank, score, document_category ---
output = filtered[["query_id", "Q0", "document_id", "new_rank", "score", "document_category"]]
print(output)

# Save to file
output.to_csv("/Users/suchana/NetBeansProjects/GesisLogDataset/output/intersection_bm25_gesis/filtered_results.tsv",
              sep="\t", index=False, header=False)