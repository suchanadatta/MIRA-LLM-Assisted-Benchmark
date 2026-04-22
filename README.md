# MIRA - An LLM-Assisted Benchmark for Multi-Category Integrated Retrieval

**MIRA** dataset, a novel test collection designed to address the critical evaluation gap in multi-categorical information retrieval.
The modern search experience is integrated, yet IR benchmarks have lagged behind, constrained by a lack of collections that mirror this reality.
MIRA dataset directly confronts this challenge by providing a unified framework encompassing four distinct scholarly categories - `Publications`, `Research Data`, `Variables` and `Instruments & Tools` - all grounded in real user queries from the [GESIS Search](https://search.gesis.org/) platform.

## Metadata Export
The collection contains metadata on `7,634` research datasets; `206,434` high-quality metadata variables; `604` instruments & tools; and `254,097` publications with a total of `468,769` documents, provided as a set of JSON files.

- **Metadata** and **Lucene Index** can be found in Zenodo under DOI [10.5281/zenodo.19660347](https://doi.org/10.5281/zenodo.19660347) 

- **Licence** : Check out the [licence information](license.txt) here.


## Metadata Schema

| Field         | Type         | Description                                                                  |
| ------------- | ------------ |------------------------------------------------------------------------------|
| `id`          | string       | Unique identifier of the item                                                |
| `type`        | string       | Item type (`publication`, `research_data`, `instruments_tools`, `variables`) |
| `title`       | string       | Title of the item                                                            |
| `title_en`    | string       | English title (if available)                                                 |
| `date`        | string       | Publication or creation year                                                 |
| `url`         | string       | Gesis Search URL pointing to the item                                        |
| `abstract`    | string       | Abstract/description (not available for `variables`)                         |
| `abstract_en` | string       | English abstract (not available for `variables`)                             |
| `person`      | list[string] | Associated persons (e.g., authors); not available for `variables`            |
| `topic`       | list[string] | Topic keywords; not available for `variables`                                |
| `topic_en`    | list[string] | English topic keywords; not available for `variables`                        |

### Type-Specific Fields

#### Research Data
| Field                 | Type   | Description                        |
| --------------------- | ------ | ---------------------------------- |
| `content_description` | string | Description of the dataset content |

#### Variables
| Field              | Type   | Description                                         |
| ------------------ | ------ |-----------------------------------------------------|
| `question_text`    | string | Question text associated with the variable          |
| `question_text_en` | string | English version of the question text (if available) |

### Field Availability by Item Type
| Field                    | publication | research_data | instruments_tools | variables |
|--------------------------| ----------- | ------------- | ----------------- |-----------|
| `id`                     | ✓           | ✓             | ✓                 | ✓         |
| `type`                   | ✓           | ✓             | ✓                 | ✓         |
| `title`                  | ✓           | ✓             | ✓                 | ✓         |
| `title_en`               | ✓           | ✓             | ✓                 | ✓         |
| `date`                   | ✓           | ✓             | ✓                 | ✓         |
| `url`                    | ✓           | ✓             | ✓                 | ✓         |
| `abstract`/`abstract_en` | ✓           | ✓             | ✓                 | ✗         |
| `content_description`    | ✗           | ✓             | ✗                 | ✗         |
| `person`                 | ✓           | ✓             | ✓                 | ✗         |
| `question_text`          | ✗           | ✗             | ✗                 | ✓         |
| `question_text_en`       | ✗           | ✗             | ✗                 | ✓         |
| `topic` / `topic_en`     | ✓           | ✓             | ✓                 | ✗         |


## Topic Modeling

The initial pool of multi-category topics contained significant semantic overlap, as users frequently expressed core information needs through multiple query variants. Therefore, to group these variations, we performed topic modeling on the `412,032` pre-selected topics using `BERTopic` and ended up with `200` potential topics.
[Topic Modeling](topic_modelling) includes a Jupyter notebook that trains topic models for our corpus and produce artifacts (e.g. topic-term tables, document-topic distributions, etc.).

#### Prepare data
Create a CSV file (e.g., `queries.csv`) with a single text column:

<pre>csv 

text
"arbeitszufriedenheit"
"migration in Germany"
"global warming"
"right-wing extremism"
...
</pre>


#### What the pipeline does
This pipeline applies BERTopic to discover clusters/themes from search queries. Concretely, the workflow includes:
- Fitting a BERTopic model to identify topical clusters/themes. Under the hood, BerTopic performs:
  - Embedding extraction for each query using `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - Dimensionality reduction with `UMAP`
  - Clustering with `HDBSCAN`
- (Optional) Reduce/merge similar topics, especially small or overlapping ones
- Export topic summaries and per-document assignments
- Saves the trained model for reuse
- Generate a word cloud based on topic frequencies

**Model configuration:** We use BERTopic with default settings, which corresponds to the following clustering setup:

```python
UMAP(
    n_neighbors=15,
    n_components=5,
    min_dist=0.0,
    metric="cosine",
)

HDBSCAN(
    min_cluster_size=10,
    metric="euclidean",
    cluster_selection_method="eom",
    prediction_data=True,
)
```


Word cloud of the [top 50 topics](topic_modelling/top-50-topics.tsv) derived from topic modeling is as follows.

<img src="topic_modelling/top50_topics_wordcloud.png" alt="word-cloud" width="600"/>

## Topics

MIRA topics originate from real user queries submitted to the GESIS Search platform. We used user logs collected between `2017 and 2024`, comprising `16,335,937` interactions. After filtering via topic modeling, we select `200` potential queries covering 4 categories. More details in the paper.

#### LLM-assisted Topic Curation
- We used `gpt-5-mini` to generate `description` and `narration` of each of the topic.
- For each topic, [descriptions and narrations](models/generate_query_narr_desc_llm_batch.py) are generated using an LLM, guided by a purpose-built prompt designed to produce category-aware topic expansions.
- We used the following prompt.
 <pre> 
|---------------------------------------------------------------------------------------------------------------------| 
| Prompt                                                                                                              |
|---------------------------------------------------------------------------------------------------------------------|
| You are a helpful assistant generating description and narration for keyword queries. A search for the keyword      |
| query will be performed on the GESIS search database. For EACH query, generate a focused description and narration  |
| in English following the TREC style to define only the scope of relevance.                                          | 
| The search categories are: 1. publication 2. research_data 3. variables 4. instruments_and_tools                    |
| Return a JSON ARRAY. Each array element MUST have:                                                                  |
| - qid                                                                                                               |
| - query                                                                                                             |
| - publication {description, narration}                                                                              |
| - research_data {description, narration}                                                                            |
| - variables {description, narration}                                                                                |
| - instruments_and_tools {description, narration}                                                                    |
| Return ONLY valid JSON. No extra text.                                                                              |
|---------------------------------------------------------------------------------------------------------------------|
</pre>
- We create a [structured representation](models/make_query_trec_format.py) including the original topic and a full description along with a detailed narration of the final [200 topics](query_qrel/new/query.xml), which are distinct for each category following the standard TREC format. A sample query is given below.
  
```xml
<top>
<num>221</num>
<title>immigration</title>
<publication>
	<desc>Publications on immigration and migrants, covering migration flows, integration, policy, socioeconomic outcomes, health, and legal status.</desc>
	<narr>Include empirical studies, reviews, policy analyses and theoretical works that address international migration, immigrant integration and assimilation, labor market outcomes of immigrants, refugee/asylum issues, migration policy and laws, remittances, transnationalism, and migrant health and education. Relevant disciplines: sociology, demography, economics, political science, public health and law. Exclude studies exclusively about internal migration (unless relevant), tourism travel statistics not related to migration, and purely historical migration narratives with no contemporary analytical relevance unless explicitly comparative.</narr>
</publication>
<research_data>
	<desc>Datasets and administrative sources capturing migration status, flows, immigrant characteristics, integration indicators, and asylum/refugee records.</desc>
	<narr>Include population registers, immigration and naturalization administrative data, household and labor force surveys with migrant identifiers (country of birth, citizenship, year of arrival), refugee and asylum seeker databases, longitudinal migrant cohort studies, and datasets on remittances and migrant networks. Data should allow analysis of migration status, origin/destination, length of stay and integration outcomes. Exclude datasets that only report tourist or short-term travel without migration intent, and non-human migration data.</narr>
</research_data>
<variables>
	<desc>Variables that identify and characterize migrants and migration processes: country of birth, citizenship, migration reason/status, length of residence, legal status, language proficiency, and integration outcomes.</desc>
	<narr>Include variables such as migrant status (immigrant, emigrant, refugee, asylum-seeker), country of birth, citizenship, parental country of birth, year of arrival, length of stay, legal residency status, reason for migration, language skills, education credentials, employment and income, housing, naturalization, social integration indicators, and access to services. Also include remittance behavior and transnational ties when linked to migration. Exclude variables that do not permit identification of migration-related attributes or that only measure temporary travel for tourism.</narr>
</variables>
<instruments_tools>
	<desc>Standard instruments, questionnaires and coding schemes used in migration research, and tools for measuring integration and legal status.</desc>
	<narr>Include survey modules and question batteries for migration (e.g., migrant background question sets used in EU surveys), language proficiency assessments, integration scales (social, economic, civic integration indices), legal-status coding schemes, and tools for harmonizing migration variables across datasets (e.g., harmonization guides for country of birth, citizenship, and year of arrival). Also include translations/translation protocols for migrant surveys and instruments for measuring xenophobia or attitudes toward immigrants. Exclude administrative IT systems unrelated to research use and instruments designed solely for immigration officers' operational use without research documentation.</narr>
</instruments_tools>
</top>
```

## LLM-assisted Relevance Judgements
- For each of the 200 selected topics, we identified a pool of candidate documents to be judged.
- We select documents from all four categories that received a `view_record` or `download` or `export` user interaction after the query was issued in the GESIS Search.
- We used `gpt-5-mini` to judge those documents.
- Judgments were made on a graded relevance scale from '0' to '4'.
  - `0` → Not Relevant,
  - `1` → Marginally Relevant,
  - `2` → Fairly Relevant,
  - `3` → Highly Relevant, and
  - `4` → Perfectly Relevant
- We provided LLM with the `topic description` and the `document metadata`, instructing it to assess their relevance.
- We used the following [prompt](models/generate_qrel_file_with_desc_batch.py) while assessing the documents by the LLM.
 <pre> 
|---------------------------------------------------------------------------------------------------------------------| 
| Prompt                                                                                                              |
|---------------------------------------------------------------------------------------------------------------------|
| You are an adversarial relevance assessor for an information retrieval evaluation. Your job is NOT to reward good   |
| papers. Your job is to identify ONLY those documents that are indispensable for satisfying the query's information  |
| need. Assume the following:                                                                                         |
| - Most retrieved documents are NOT relevant.                                                                        |
| - Even well-written, on-topic abstracts are usually NOT highly relevant.                                            |
| - A score of 4 should be exceptionally rare.                                                                        |
| Core principle: A document is relevant ONLY if it would cause a clear loss of information if excluded from the      |
| result set for this query. Relevance MUST be judged against the FULL query intent, not topical similarity. Relevance| 
| scale (strictly enforced):                                                                                          |
|                                                                                                                     |
| 0 = Not relevant                                                                                                    |  
|   The abstract does not explicitly attempt to answer the query intent.                                              |
|   Background mentions, shared terminology, or general alignment DO NOT count.                                       |
|                                                                                                                     |
| 1 = Weakly related                                                                                                  |  
|   The abstract is in the same broad area, but does not answer the query.                                            |
|   It could appear in results for many different, loosely related queries.                                           |
|                           																						  |
| 2 = Conditionally relevant																						  |
|   The abstract addresses part of the query intent, BUT:															  |
|   - only indirectly, OR																							  |
|   - as a secondary concern, OR																					  |
|   - without producing concrete insight for the query.																  |
|																													  |
| 3 = Strongly relevant      																						  |
|   The abstract clearly and explicitly addresses the query intent,													  |
|   BUT the query is not the sole or dominant focus of the work.													  |
|   Removing this document would reduce coverage, but not break it.													  |
|																													  |
| 4 = Essential (assign ONLY if ALL conditions hold):																  |
|   - The query intent is the central research problem																  |
|   - The methods are designed specifically for this intent															  |
|   - The results directly and uniquely answer the query															  |
|   - The document would be a canonical or defining reference														  |
|   - Removing it would materially damage the answer to the query													  |
|																													  |
| IMPORTANT CONSTRAINTS:																							  |
| - If ANY of the 4 conditions are missing → score MUST be ≤ 3   													  |
| - If you hesitate between 3 and 4 → choose 3																		  |
| - If you hesitate between 2 and 3 → choose 2																		  |
| - If relevance is plausible but not explicit → choose 1 or 0														  |
| - Score 4 should feel uncomfortable to assign																		  |
|																													  |
| Ignore ranking position and prior scores.																			  |
| Output ONLY a single integer from 0 to 4.                                                                           |
|---------------------------------------------------------------------------------------------------------------------|
</pre>
- Each judgment has 4 attributes - `topic_id`, `document_id`, `document_category`, `relevance_score`.
- We finally obtain a pool of `55,279` LLM-annotated [relevance judgments](query_qrel/new/qrels.tsv).
- A randomly chosen `10% sample` of the annotations were validated by human annotators. Agreement between the human and the LLM judgments was measured using quadratic-weighted Cohen’s 𝜅, yielding 𝜅 = 0.86, which indicates substantial agreements.

## Evaluation

A number of statistical and neural models are [evaluated](evaluation/custom_eval.py) using standard IR metrics, such as `P@10`, `nDCG@10`, `MAP` and `GMAP`. Retreival effectiveness of each query can also be measured using this [script](evaluation/custom_eval_per_query.py).
	
| Publications        | Models      | P@10   | nDCG@10 | MAP    | GMAP   |
|---------------------|-------------|--------|---------|--------|--------|
|                     | BM25        | 0.6120 | 0.6091  | 0.5098 | 0.5260 |            
|                     | RLM         | 0.6242 | 0.6213  | 0.5200 | 0.5365 |            
|                     | ColBERT     | 0.6523 | 0.6492  | 0.5434 | 0.5607 |            
|                     | MonoT5      | 0.6365 | 0.6335  | 0.5302 | 0.5470 |

| Research Data       | Models      | P@10   | nDCG@10 | MAP    | GMAP   |
|---------------------|-------------|--------|---------|--------|--------|
|                     | BM25        | 0.5045 | 0.5321  | 0.4023 | 0.3058 |            
|                     | RLM         | 0.5146 | 0.5427  | 0.4103 | 0.3119 |            
|                     | ColBERT     | 0.5377 | 0.5639  | 0.4263 | 0.3241 |            
|                     | MonoT5      | 0.5247 | 0.5736  | 0.4337 | 0.3297 |

| Variables           | Models      | P@10   | nDCG@10 | MAP    | GMAP   |
|---------------------|-------------|--------|---------|--------|--------|
|                     | BM25        | 0.4905 | 0.4408  | 0.5057 | 0.1648 |            
|                     | RLM         | 0.5003 | 0.4496  | 0.5158 | 0.1681 |            
|                     | ColBERT     | 0.5198 | 0.4672  | 0.5354 | 0.1745 |            
|                     | MonoT5      | 0.5288 | 0.4752  | 0.5249 | 0.1711 |                    

| Instruments & Tools | Models      | P@10   | nDCG@10 | MAP    | GMAP   |
|---------------------|-------------|--------|---------|--------|--------|
|                     | BM25        | 0.4190 | 0.4711  | 0.4540 | 0.2152 |            
|                     | RLM         | 0.4274 | 0.4805  | 0.4631 | 0.2195 |            
|                     | ColBERT     | 0.4436 | 0.4988  | 0.4807 | 0.2243 |            
|                     | MonoT5      | 0.4349 | 0.4890  | 0.4713 | 0.2234 |


