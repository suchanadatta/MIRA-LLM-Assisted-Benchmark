import pandas as pd
import ast
import openai
from openai import OpenAI
import requests
import re, argparse

client = OpenAI(api_key=api_key)


def assess_relevance(query, abstract, model="gpt-5-mini"):
    system_content = f"""You are a helpful assistant doing graded relevance assessment. Decide whether the given 
    abstract is relevant to the keyword query. On a scale of 0 to 4, score the document where 0 indicates 
    non-relevant and 4 being the highly relevant"""

    user_content = f"""Keyword query: {query} Abstract: {abstract} Answer:"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
    )
    result = response.choices[0].message.content
    return result


def get_posts(topdoc):
    url_init = 'https://search.gesis.org/searchengine'
    url = url_init + '?q=_id:"' + topdoc + '"'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def clean_text(text):
    # Keep letters (including German ä, ö, ü, ß), numbers, and spaces
    text = re.sub(r'[^a-zA-Z0-9äöüÄÖÜß\s]', '', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading and trailing spaces
    return text.strip()


def extract_items_for_each_query_per_category(item_file, query_file):
    # Read both input files
    query_file = pd.read_csv(query_file, sep="\t", dtype=str, encoding="utf-8")
    per_query_item_set = pd.read_csv(item_file, sep="\t", dtype=str, encoding="utf-8")

    # Clean columns
    query_file["query"] = query_file["query"].str.strip()
    per_query_item_set["query"] = per_query_item_set["query"].str.strip()
    query_file["item_type"] = query_file["item_type"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )

    # Build result rows
    rows = []
    for _, row in query_file.iterrows():
        qid = row["query_id"]
        query = row["query"]
        types = row["item_type"]

        for item_type in types:
            match = per_query_item_set.loc[
                (per_query_item_set["query"] == query) & (per_query_item_set["item_type"] == item_type),
                "result_set"
            ]
            result_set = match.iloc[0] if not match.empty else ""
            rows.append({
                "query_id": qid,
                "query": query,
                "item_type": item_type,
                "result_set": result_set
            })

    # Create output DataFrame
    out_df = pd.DataFrame(rows)

    # Write to TSV (optional)
    out_df.to_csv("./data/query_itemtype_results_for_qrels.tsv", sep="\t", index=False, encoding="utf-8")

    print("Done! Saved 'query_itemtype_results_for_qrels.tsv'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--item_file", default="./data/per_query_total_items.tsv")
    parser.add_argument("--query_file", default="./data/query_with_all_category.tsv")
    parser.add_argument("--qrel_file", default="../query_qrel/qrels.tsv")
    args = parser.parse_args()

    # For each query, this module extracts items/relevant doc ids for each of the category
    extract_items_for_each_query_per_category(args.item_file, args.query_file)

    item_set_file_final = pd.read_csv("./data/query_itemtype_results_for_qrels.tsv", sep="\t", dtype=str,
                                      encoding="utf-8")
    item_set_file_final.columns = item_set_file_final.columns.str.strip().str.replace("\ufeff", "")
    print(item_set_file_final.columns.tolist())

    # create the qrel file (qid'\t'docid'\t'item_type'\t'rel_score)
    with open(args.qrel_file, "a", encoding="utf-8") as file:
        for _, row in item_set_file_final.iterrows():
            query_id = row["query_id"]
            query = row["query"]
            item_type = row["item_type"]
            result_set = [x.strip() for x in row["result_set"].split(",") if x.strip()]

            for topdoc in result_set:
                print('Assessing : ', topdoc)
                posts = get_posts(topdoc)
                hits = posts.get("hits", {}).get("hits", [])
                if not hits:
                    print("===== NO HIT =====")
                    continue
                source = hits[0].get("_source", {})
                if not any (k in source for k in ("abstract", "abstract_en", "question_text", "full_text")):
                    continue
                abstract = source.get("abstract") or source.get("abstract_en") \
                           or source.get("question_text") or source.get("full_text")
                cleaned_abstract = clean_text(str(abstract))
                print('******** GOT A CLEANED ABSTRACT ********')
                rel_score = assess_relevance(query, cleaned_abstract)
                print(topdoc, '============>', rel_score)
                qrel_content = f"{query_id}\t{topdoc}\t{item_type}\t{rel_score}\n"
                file.write(qrel_content)
                file.flush()
    file.close()


if __name__ == '__main__':
    main()