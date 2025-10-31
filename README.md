# MIRA - An LLM-Assisted Benchmark for Multi-Category Integrated Retrieval

**MIRA** dataset, a novel test collection designed to address the critical evaluation gap in multi-categorical information retrieval.
The modern search experience is integrated, yet IR benchmarks have lagged behind, constrained by a lack of collections that mirror this reality.
MIRA dataset directly confronts this challenge by providing a unified framework encompassing four distinct scholarly categories - **Publications**, **Research Data**, **Variables** and **Instruments & Tools** - all grounded in real user queries from the GESIS Search platform.

## Metadata Export
All metadata of the GESIS Search corpus with documents for the categories research datasets, variables, instruments & tools, and publications are available in JSON format.

- **Metadata** : Download [MIRA collection](https://drive.google.com/file/d/1jTTYd83bYTqeMB2DR4DSOWQQuYl4y_Sa/view?usp=drive_link) here.
   
- **Lucene Index** : The [Lucene (version 8)](https://drive.google.com/file/d/1i8U389G4wSj7dMz41xehKQvvBryZuIs-/view?usp=drive_link) index of the metadata can be accessed here.
  
- **Licence** : Check out the [licence information](license.txt) here.

## Topic Modeling

The initial pool of multi-category topics contained significant semantic overlap, as users frequently expressed core information needs through multiple query variants. Therefore, to group these variations, we performed topic modeling on the 412,032 pre-selected topics using **BERTopic** and ended up with 215 potential topics.
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
- Embeds queries with sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Fits BERTopic to discover clusters/themes
- (Optional) Reduces/merges small/overlapping topics
- Exports topic summaries and per-document assignments
- Saves the model for reuse
- Creates a wordcloud based on topic frequencies

![Word cloud of the top 50 topics derived from topic modeling](topic_modelling/top50_topics_wordcloud.png)

## Topics


