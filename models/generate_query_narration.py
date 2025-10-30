import requests
import json
import pandas as pd
import openai
from openai import OpenAI
import argparse


client = OpenAI(api_key=api_key)


def gen_query_desc_narr(query, paragraph, model="gpt-5-mini"):
    system_content_desc = f"""You are a helpful assistant generating description for keyword queries. 
    Write a short description (1–2 sentences) of the query in English. This should summarize the information need clearly 
    and concisely. An information need is the underlying motivation or purpose that drives a person to seek information
    — it represents the gap between what someone knows and what they want or need to know in order to accomplish 
    a goal."""

    system_content_narr = f""" You are a helpful assistant generating narration for keyword queries. Write a English
    narrative in 4-5 sentences that explains what makes a document relevant or non-relevant for this query. 
    The narrative should include details, examples, and possible edge cases."""

    user_content = f"""Keyword query: {query} Paragraph: {paragraph} Answer:"""

    response_desc = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content_desc},
            {"role": "user", "content": user_content}
        ],
    )
    result_desc = response_desc.choices[0].message.content

    response_narr = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content_narr},
            {"role": "user", "content": user_content}
        ],
    )
    result_narr = response_narr.choices[0].message.content
    return result_desc, result_narr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--item_file", default="./data/publication_top20_bm25.res")
    parser.add_argument("--query_narr_desc", default="./data/publication_narr_desc.tsv")
    args = parser.parse_args()

    # Load item file with retrieval score
    df = pd.read_csv(args.item_file, sep="\t", dtype=str, encoding="utf-8")

    # Check the column names
    print(df.columns.tolist())

    # Remove BOM and strip whitespace from column names
    df.columns = df.columns.str.strip().str.replace("\ufeff", "")

    # Group by query_id and concatenate abstracts/question_text
    grouped = (df.groupby("query_id", as_index=False).agg({
                "query": "first",
                "title_de": lambda x: " ".join(x.dropna().astype(str)),
                "title_en": lambda x: " ".join(x.dropna().astype(str)),
                "question_text": lambda x: " ".join(x.dropna().astype(str))})
    )

    # generate narration and description for each query with the concatenated abstract
    with open(args.query_narr_desc, "a", encoding="utf-8") as file:
        file.write("query_id\tquery\tvar_desc\tvar_narr\n")
        for _, row in grouped.iterrows():
            query_id = row["query_id"]
            query = row["query"]
            print("====== Generating NARR and DESC for query ID : ", query_id, ":::::::: ", query, "=======")
            if row["title_en"]:
                print('######### It has ENGLISH title ########')
                abstract = row["title_en"] + row["question_text"]
            else:
                print('######### It has GERMAN title ########')
                abstract = row["title_de"] + row["question_text"]
            desc, narr = gen_query_desc_narr(query, abstract)
            print("******* Writing DESC and NARR in the file *******\n")
            file_content = f"{query_id}\t{query}\t{desc}\t{narr}\n"
            file.write(file_content)
            file.flush()
    file.close()


if __name__ == '__main__':
    main()
