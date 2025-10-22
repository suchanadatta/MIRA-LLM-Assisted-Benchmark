# MIRA-An-LLM-Assisted-Benchmark-for-Multi-Category-Integrated-Retrieval

## Metadata Export
All metadata of the GESIS Search corpus with documents for the categories research datasets, variables, instruments & tools, and publications can be found in JSON format in the folder [metadata-corpus](metadata-corpus). Note the [licence information](metadata-corpus/license.txt).

## Topic Modelling

This module includes a Jupyter notebook for training topic models for our corpus and producing artifacts (topic-term tables, document-topic distributions, etc.).

1) Install deps:

`pip install "bertopic[all]" sentence-transformers pandas`


2) Prepare data

Create a CSV file (e.g., `queries.csv`) with a single text column:

<pre>csv 

text
"arbeitszufriedenheit"
"migration in Germany"
"global warming"
"right-wing extremism"
...
</pre>


## What the pipeline does
- Embeds queries with sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Fits BERTopic to discover clusters/themes
- (Optional) Reduces/merges small/overlapping topics
- Exports topic summaries and per-document assignments
- Saves the model for reuse
- Creates a wordcloud based on topic frequencies