# MIRA-An-LLM-Assisted-Benchmark-for-Multi-Category-Integrated-Retrieval

**MIRA** dataset, a novel test collection designed to address the critical evaluation gap in multi-categorical information retrieval.
The modern search experience is integrated, yet IR benchmarks have lagged behind, constrained by a lack of collections that mirror this reality.
MIRA dataset directly confronts this challenge by providing a unified framework encompassing four distinct scholarly categories -- **Publications**, **Research Data**, **Variables** and **Instruments & Tools** -- all grounded in real user queries from the GESIS Search platform.

## Metadata Export
All metadata of the GESIS Search corpus with documents for the categories research datasets, variables, instruments & tools, and publications can be found in JSON format here [MIRA collection](https://example.com](https://drive.google.com/drive/folders/1LWrIN-J7XltmUt11O5nKpjSyucbXZ3NN?usp=drive_link). Note the [licence information](metadata-corpus/license.txt).

## Topic Modelling

This module includes a Jupyter notebook for training topic models for our corpus and producing artifacts (topic-term tables, document-topic distributions, etc.).

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
- Embeds queries with sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Fits BERTopic to discover clusters/themes
- (Optional) Reduces/merges small/overlapping topics
- Exports topic summaries and per-document assignments
- Saves the model for reuse
- Creates a wordcloud based on topic frequencies
