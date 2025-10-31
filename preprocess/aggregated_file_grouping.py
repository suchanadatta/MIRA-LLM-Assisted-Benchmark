import pandas as pd


def main():
    df_aggr = pd.read_csv('/Users/suchana/Research/GESIS/aggregated_data_v2.tsv', sep='\t', encoding="utf-8")

    df_aggr = df_aggr.loc[:, ~df_aggr.columns.str.contains('^Unnamed')]

    # Add global query_id as the first column
    df_aggr.insert(0, 'query_id', range(1, len(df_aggr) + 1))

    # Save the updated dataframe to a new TSV file
    df_aggr.to_csv('/Users/suchana/Research/GESIS/aggregated_data_v2_qid.tsv', sep="\t", index=False, encoding="utf-8")

    # Remove special characters, keep only letters, numbers, and spaces
    df_aggr["query_norm"] = (df_aggr["query"]
                             .astype(str)  # ensure string
                             .str.replace(r"[^A-Za-zÄÖÜäöüß0-9\s]", "", regex=True)  # remove special chars but keep
                             # german umlauts
                             .str.replace(r"\s+", " ", regex=True)  # collapse multiple spaces
                             .str.strip()  # remove leading/trailing spaces
                             .str.lower()  # normalize to lowercase (optional)
                             )

    # Remove unwanted item types
    df_aggr = df_aggr[~df_aggr["item_type"].isin(["gesis_bib", "gesis_product"])]

    # Group by topic_cluster + query_norm + item_type
    grouped = (df_aggr.groupby(['topic_cluster', 'query_norm', 'item_type'], dropna=False)
               .agg({"result_set": lambda rs: ", ".join(sorted(set(", ".join(rs).split(", ")))),
                     'query_id': 'first'})
               .reset_index())

    # Rename query_norm back to query
    grouped = grouped.rename(columns={"query_norm": "query"})

    # define the order of the columns
    cols = ['topic_cluster', 'query_id', 'query', 'item_type', 'result_set']
    grouped = grouped[cols]

    # Save to TSV
    grouped.to_csv("./output/per_query_total_items.tsv", sep="\t", index=False, encoding="utf-8-sig")

    # ===============================

    # Group by topic_cluster and item_type, count occurrences
    freq = grouped.groupby(["topic_cluster", "item_type"]).size().reset_index(name="count")
    freq.to_csv("./output/each_cluster_category_freq.tsv", sep="\t", index=False, encoding="utf-8")

    # ===============================

    # Group by topic_cluster and query_norm, aggregate item types
    query_item_types = (
        df_aggr.groupby(["topic_cluster", "query_norm"])["item_type"]
            .apply(lambda x: sorted(set(x)))  # unique item types
            .reset_index()
    )

    # Add column with joined list of item types
    query_item_types["item_types"] = query_item_types["item_type"].apply(lambda x: ", ".join(x))

    # Add number of categories
    query_item_types["num_category"] = query_item_types["item_type"].apply(len)

    # Drop old list column if not needed
    query_item_types = query_item_types.drop(columns=["item_type"])

    # Rename query_norm back to query
    query_item_types = query_item_types.rename(columns={"query_norm": "query"})

    query_item_types.to_csv("./output/query_item_variant_v2.tsv", sep="\t", index=False, encoding="utf-8")


if __name__ == '__main__':
    main()