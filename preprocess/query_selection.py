import pandas as pd
import openai
from openai import OpenAI

client = OpenAI(api_key=api_key)


def detect_query_lang(query, model="gpt-5"):
    system_content = f"""You are a helpful assistant to detect language of a text. Decide whether the given text is
                    in English or German. If it is English, output 'en' or if it is German, output 'de'."""

    user_content = f"""Keyword query: {query} Answer:"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
    )
    result = response.choices[0].message.content
    return result


# Load aggregated data
grouped_items = pd.read_csv("./output/per_query_total_items.tsv", sep="\t", encoding="utf-8")

# Load topic cluster names file
clusters = pd.read_csv("/Users/suchana/Research/GESIS/top-50-topics.tsv", sep="\t", encoding="utf-8")

# Remove special characters, keep only letters, numbers, and spaces
grouped_items["query_norm"] = (grouped_items["query"].astype(str)  # ensure string
                               .str.replace(r"[^A-Za-zÄÖÜäöüß0-9\s]", "", regex=True)  # remove special chars but keep
                               # german umlauts
                               .str.replace(r"\s+", " ", regex=True)  # collapse multiple spaces
                               .str.strip()  # remove leading/trailing spaces
                               .str.lower()  # normalize to lowercase (optional)
                                )
grouped_items['item_type'] = grouped_items['item_type'].str.strip().str.lower()

# Create dictionary: key = query_id, value = query
query_dict = pd.Series(grouped_items['query_norm'].values, index=grouped_items['query_id']).to_dict()

# Invert dictionary to map query -> query_id
query_to_id = {v: k for k, v in query_dict.items()}

# Group by topic_cluster and query; aggregate unique item types
item_groups = (
    grouped_items.groupby(['topic_cluster', 'query_norm'])['item_type']
      .apply(lambda x: list(set(x)))  # unique list of item_types
      .reset_index()
)

# Filter queries that have all 4 required item types
required_types = {'publication', 'research_data', 'instruments_tools', 'variables'}
item_groups['has_all_4'] = item_groups['item_type'].apply(lambda x: required_types.issubset(set(x)))
filtered = item_groups[item_groups['has_all_4']]

# Merge with topic cluster names
filtered = filtered.merge(
    clusters,
    how="left",
    left_on="topic_cluster",
    right_on="topic_cluster_no"
)

# Select and rename columns for clarity
final_query_list = filtered[['topic_cluster', 'topic_cluster_name', 'query_norm', 'item_type']]

# Map query to query_id
final_query_list = final_query_list.copy()
final_query_list['query_id'] = final_query_list['query_norm'].map(query_to_id)

# Rename query_norm back to query
final_query_list = final_query_list.rename(columns={"query_norm": "query"})

# Rearrange dataframe
final_query_list = final_query_list[['topic_cluster', 'topic_cluster_name', 'query_id', 'query', 'item_type']]

# Add a 'language' column by detecting each query's language
final_query_list["language"] = final_query_list["query"].apply(lambda q: detect_query_lang(q))

final_query_list.to_csv("./output/queries_with_4_itemtypes.tsv", sep="\t", index=False, encoding="utf-8")