import json
import csv
import argparse
from openai import OpenAI
from typing import List, Dict


# -------------------- OpenAI client --------------------

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# -------------------- Helpers --------------------

def clean(text):
    if not text:
        return ""
    return text.replace("\n", " ").replace("\t", " ").strip()


def get_desc_narr(obj, key):
    return (
        clean(obj.get(key, {}).get("description", "")),
        clean(obj.get(key, {}).get("narration", ""))
    )


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


# -------------------- Batched LLM call --------------------

def gen_query_desc_narr_batch(
    batch: List[Dict[str, str]],
    model="gpt-5-mini"
):
    """
    batch = [
        {"qid": "1", "query": "public opinion on refugees"},
        ...
    ]
    """

    system_content = """
You are a helpful assistant generating description and narration for keyword queries.
A search for the keyword query will be performed on the GESIS search database.
For EACH query, generate a focused description and narration in English following 
the TREC style to define only the scope of relevance.

The search categories are:
1. publication
2. research_data
3. variables
4. instruments_and_tools

Return a JSON ARRAY.
Each array element MUST have:
- qid
- query
- publication {description, narration}
- research_data {description, narration}
- variables {description, narration}
- instruments_and_tools {description, narration}

Return ONLY valid JSON. No extra text.
"""

    user_content = "Queries:\n" + json.dumps(batch, ensure_ascii=False, indent=2)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        # temperature=0.2
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown code fences if present
    if raw.startswith("```"):
        # Remove opening fence (```json or just ```)
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        # Remove closing fence
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed for batch. Error: {e}")
        print("Raw output:\n", raw)
        return []


def narr_desc_without_bm25_batched(query_file, output_tsv, batch_size=5):
    # Load queries
    queries = []
    with open(query_file, "r", encoding="utf-8") as qf:
        reader = csv.reader(qf, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            queries.append({
                "qid": row[0],
                "query": row[1]
            })

    print(f"Total queries loaded: {len(queries)}")
    print(f"Batch size: {batch_size}")

    with open(output_tsv, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter="\t")

        # Header
        writer.writerow([
            "qid", "query",
            "pub_desc", "pub_narr",
            "research_desc", "research_narr",
            "var_desc", "var_narr",
            "instru_desc", "instru_narr"
        ])

        for batch_no, batch in enumerate(chunked(queries, batch_size), start=1):
            print(f"\n=== Processing batch {batch_no} ({len(batch)} queries) ===")

            results = gen_query_desc_narr_batch(batch)

            for item in results:
                qid = item.get("qid", "")
                query = item.get("query", "")

                pub_desc, pub_narr = get_desc_narr(item, "publication")
                res_desc, res_narr = get_desc_narr(item, "research_data")
                var_desc, var_narr = get_desc_narr(item, "variables")
                ins_desc, ins_narr = get_desc_narr(item, "instruments_and_tools")

                writer.writerow([
                    qid, query,
                    pub_desc, pub_narr,
                    res_desc, res_narr,
                    var_desc, var_narr,
                    ins_desc, ins_narr
                ])

            out.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_file", required=True)
    parser.add_argument("--output_tsv", required=True)
    parser.add_argument("--batch_size", type=int, default=5)

    args = parser.parse_args()

    narr_desc_without_bm25_batched(
        args.query_file,
        args.output_tsv,
        args.batch_size
    )


if __name__ == "__main__":
    main()
