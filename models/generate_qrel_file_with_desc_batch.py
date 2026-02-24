import pandas as pd
import ast
import openai
from openai import OpenAI
import requests
import re
import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
import json


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = f"""
You are an adversarial relevance assessor for an information retrieval evaluation.

Your job is NOT to reward good papers.
Your job is to identify ONLY those documents that are indispensable
for satisfying the query's information need.

Assume the following:
- Most retrieved documents are NOT relevant.
- Even well-written, on-topic abstracts are usually NOT highly relevant.
- A score of 4 should be exceptionally rare.

Core principle:
A document is relevant ONLY if it would cause a clear loss of information
if excluded from the result set for this query.

Relevance MUST be judged against the FULL query intent, not topical similarity.

Relevance scale (strictly enforced):

0 = Not relevant  
    The abstract does not explicitly attempt to answer the query intent.
    Background mentions, shared terminology, or general alignment DO NOT count.

1 = Weakly related  
    The abstract is in the same broad area, but does not answer the query.
    It could appear in results for many different, loosely related queries.

2 = Conditionally relevant  
    The abstract addresses part of the query intent, BUT:
    - only indirectly, OR
    - as a secondary concern, OR
    - without producing concrete insight for the query.

3 = Strongly relevant  
    The abstract clearly and explicitly addresses the query intent,
    BUT the query is not the sole or dominant focus of the work.
    Removing this document would reduce coverage, but not break it.

4 = Essential (assign ONLY if ALL conditions hold):
    - The query intent is the central research problem
    - The methods are designed specifically for this intent
    - The results directly and uniquely answer the query
    - The document would be a canonical or defining reference
    - Removing it would materially damage the answer to the query

IMPORTANT CONSTRAINTS:
- If ANY of the 4 conditions are missing → score MUST be ≤ 3
- If you hesitate between 3 and 4 → choose 3
- If you hesitate between 2 and 3 → choose 2
- If relevance is plausible but not explicit → choose 1 or 0
- Score 4 should feel uncomfortable to assign

Ignore ranking position and prior scores.
Output ONLY a single integer from 0 to 4.
"""


def assess_relevance_batch(batch_data, model="gpt-5-mini"):
    """
    Assess relevance for a batch of documents at once.

    Args:
        batch_data: List of dicts with keys: 'query', 'description', 'abstract', 'doc_id'
        model: OpenAI model name

    Returns:
        Dict mapping doc_id to relevance score
    """
    # Build batch content
    user_content = "Assess the following documents:\n\n"
    for item in batch_data:
        user_content += f"""Document ID: {item['doc_id']}
Keyword query: {item['query']}
Query description: {item['description']}
Abstract: {item['abstract']}

---
"""

    user_content += "\nProvide scores in JSON format: {\"doc_id\": score, ...}"

    try:
        # Determine temperature based on model
        # Some models only support temperature=1 (default), others support 0 for deterministic output
        # Models known to require temperature=1: gpt-4o-mini, gpt-5-mini (if it exists)
        models_requiring_temp_1 = ['gpt-4o-mini', 'gpt-5-mini']
        temperature = 1 if any(m in model for m in models_requiring_temp_1) else 0

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature
        )

        result = response.choices[0].message.content

        # Parse JSON response
        # Remove markdown code blocks if present
        result = re.sub(r'```json\s*|\s*```', '', result).strip()
        try:
            scores = json.loads(result)
            # Validate that scores is a dictionary
            if not isinstance(scores, dict):
                print(f"Warning: Expected dict but got {type(scores).__name__}: {scores}")
                print(f"Raw LLM response: {result}")
                # Return default scores
                return {item['doc_id']: "0" for item in batch_data}

            return scores

        except json.JSONDecodeError as je:
            print(f"JSON decode error: {je}")
            print(f"Raw response: {result}")
            # Return default scores on JSON error
            return {item['doc_id']: "0" for item in batch_data}

    except Exception as e:
        print(f"Error in batch assessment: {e}")
        # Return default scores on error
        return {item['doc_id']: "0" for item in batch_data}


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


def load_query_descriptions(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    queries = defaultdict(dict)

    for top in root.findall('top'):
        qid = top.findtext('num')
        if not qid:
            continue

        # Capture title
        queries[qid]['title'] = top.findtext('title', '').strip()

        # Capture ONLY <desc> for each category
        for field in ['publication', 'research_data', 'variables', 'instruments_tools']:
            desc_elem = top.find(f'{field}/desc')
            queries[qid][field] = desc_elem.text.strip() if desc_elem is not None else ""

    return dict(queries)


def extract_items_for_each_query_per_category():
    # Read both input files
    query_file = pd.read_csv("./output/queries_with_4_itemtypes_PD_format.tsv", sep="\t", dtype=str, encoding="utf-8")
    per_query_item_set = pd.read_csv("./output/per_query_total_items.tsv", sep="\t", dtype=str, encoding="utf-8")

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

    # Write to TSV
    out_df.to_csv("./output/query_itemtype_results_for_qrels.tsv", sep="\t", index=False, encoding="utf-8")

    print("Done! Saved 'query_itemtype_results_for_qrels.tsv'")


def process_batch(batch, file, model="gpt-5-mini"):
    """Process a batch of documents and write results to file."""
    if not batch:
        return

    print(f"\n{'=' * 60}")
    print(f"Processing batch of {len(batch)} documents...")
    print(f"{'=' * 60}")

    # Prepare batch data for API call
    batch_data = []
    for item in batch:
        batch_data.append({
            'doc_id': item['topdoc'],
            'query': item['query'],
            'description': item['query_desc'],
            'abstract': item['abstract']
        })

    # Get batch scores
    scores = assess_relevance_batch(batch_data, model=model)

    # Write results to file
    for item in batch:
        rel_score = scores.get(item['topdoc'], "0")
        print(f"{item['topdoc']} ============> {rel_score}")
        qrel_content = f"{item['query_id']}\t{item['topdoc']}\t{item['item_type']}\t{rel_score}\n"
        file.write(qrel_content)

    file.flush()
    print(f"Batch processed successfully!\n")


def main():
    # extract_items_for_each_query_per_category()

    parser = argparse.ArgumentParser()
    parser.add_argument('--query_file', default='/Users/suchana/python_projects/victeur/LLM-based-relevance-judgement/'
                                                'query_narr_desc/new/query.xml')
    parser.add_argument('--item_file', default='/Users/suchana/python_projects/victeur/LLM-based-relevance-judgement/'
                                               'query_narr_desc/new/gesis_log_annotation_file.tsv')
    parser.add_argument('--qrel_file', default='/Users/suchana/python_projects/victeur/LLM-based-relevance-judgement/'
                                               '/test_data/foo.su')
    parser.add_argument('--batch_size', type=int, default=25, help='Number of documents to process in each batch')
    parser.add_argument('--model', type=str, default='gpt-5-mini',
                        help='OpenAI model to use (e.g., gpt-4o-mini, gpt-4, gpt-4-turbo)')
    args = parser.parse_args()

    query_dict = load_query_descriptions(args.query_file)
    print(f"Loaded {len(query_dict)} queries")

    # Read the TSV file - handle different separators
    print("\nAttempting to read TSV file...")

    # First, let's check what the file actually contains
    with open(args.item_file, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        print(f"First line (raw): {repr(first_line[:200])}")

        # Check if it has tabs
        if '\t' in first_line:
            print("File contains tab characters - using tab separator")
            separator = '\t'
        else:
            # Count spaces to guess the separator
            print("No tabs found - file appears to use spaces")
            # Use multiple spaces as separator (common in formatted text files)
            separator = r'\s{2,}'  # 2 or more spaces

    try:
        if separator == '\t':
            item_set_file_final = pd.read_csv(args.item_file, sep='\t', dtype=str, encoding='utf-8')
        else:
            # For space-separated, we need to specify we expect exactly 4 columns
            item_set_file_final = pd.read_csv(
                args.item_file,
                sep=separator,
                dtype=str,
                encoding='utf-8',
                engine='python',
                names=['query_id', 'query', 'item_type', 'result_set'],
                header=0
            )
    except Exception as e:
        print(f"Error reading file with auto-detected separator: {e}")
        print("\nTrying manual parsing...")

        # Manual parsing as fallback
        data = []
        with open(args.item_file, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
            print(f"Header: {header}")

            for line_num, line in enumerate(f, start=2):
                line = line.strip()
                if not line:
                    continue

                # Split on whitespace but limit to 4 parts
                parts = line.split(None, 3)  # Split on any whitespace, max 4 parts

                if len(parts) >= 4:
                    data.append({
                        'query_id': parts[0],
                        'query': parts[1],
                        'item_type': parts[2],
                        'result_set': parts[3]
                    })
                else:
                    print(f"Warning: Line {line_num} has only {len(parts)} parts: {parts}")

        item_set_file_final = pd.DataFrame(data)
        print(f"Manually parsed {len(item_set_file_final)} rows")

    # Clean column names - remove BOM, whitespace, and normalize
    item_set_file_final.columns = item_set_file_final.columns.str.strip().str.replace('\ufeff', '').str.replace(
        '\u200b', '')

    # Debug: Print column information
    print(f"\n{'=' * 60}")
    print("DEBUG: Column Information")
    print(f"{'=' * 60}")
    print(f"Columns found: {item_set_file_final.columns.tolist()}")
    print(f"Number of columns: {len(item_set_file_final.columns)}")
    print(f"First few rows:\n{item_set_file_final.head()}")
    print(f"{'=' * 60}\n")

    # Check for required columns
    required_columns = ['query_id', 'query', 'item_type', 'result_set']
    missing_columns = [col for col in required_columns if col not in item_set_file_final.columns]

    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {item_set_file_final.columns.tolist()}")
        print("\nPlease check your TSV file structure.")
        return

    batch = []
    batch_size = args.batch_size
    total_docs_processed = 0

    with open(args.qrel_file, 'a', encoding='utf-8') as file:
        for _, row in item_set_file_final.iterrows():
            query_id = row['query_id']
            print(f'\n{"=" * 60}')
            print(f'QUERY ID: {query_id}')
            query = row['query']
            print(f'QUERY: {query}')
            item_type = row['item_type']
            print(f'ITEM_TYPE: {item_type}')
            result_set = [x.strip() for x in row['result_set'].split(',') if x.strip()]
            print(f'RESULT_SET SIZE: {len(result_set)}')
            query_desc = query_dict[query_id][item_type]
            print(f'QUERY_DESC: {query_desc}')

            for topdoc in result_set:
                print(f'Fetching: {topdoc}')
                posts = get_posts(topdoc)

                if not posts:
                    print('===== NO LUCK =====')
                    continue

                hits = posts.get('hits', {}).get('hits', [])
                if not hits:
                    print('===== NO HITS =====')
                    continue

                source = hits[0].get('_source', {})
                if not any(k in source for k in ('abstract', 'abstract_en', 'question_text', 'full_text')):
                    print('===== NO ABSTRACT FOUND =====')
                    continue

                abstract = (source.get('abstract') or
                            source.get('abstract_en') or
                            source.get('question_text') or
                            source.get('full_text'))

                cleaned_abstract = clean_text(str(abstract))
                print('******** GOT A CLEANED ABSTRACT ********')

                # Add to batch
                batch.append({
                    'query_id': query_id,
                    'query': query,
                    'query_desc': query_desc,
                    'item_type': item_type,
                    'topdoc': topdoc,
                    'abstract': cleaned_abstract
                })

                # Process batch when it reaches batch_size
                if len(batch) >= batch_size:
                    process_batch(batch, file, model=args.model)
                    total_docs_processed += len(batch)
                    batch = []

            if batch:
                process_batch(batch, file, model=args.model)
                total_docs_processed += len(batch)

        # Process remaining documents in the last batch
        if batch:
            process_batch(batch, file, model=args.model)
            total_docs_processed += len(batch)

    print(f"\n{'=' * 60}")
    print(f"Processing complete!")
    print(f"Total documents processed: {total_docs_processed}")
    print(f"Total API calls made: {(total_docs_processed + batch_size - 1) // batch_size}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
