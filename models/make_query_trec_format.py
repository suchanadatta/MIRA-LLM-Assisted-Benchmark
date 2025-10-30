import pandas as pd
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_narr_desc", default="./data/publication_narr_desc.tsv")
    parser.add_argument("--query_file", default="../query_qrel/query.xml")
    args = parser.parse_args()

    # Load 4 category query-narr-desc file
    df_publication = pd.read_csv("./data/publication_narr_desc.tsv", sep="\t", dtype=str, encoding="utf-8")
    df_research = pd.read_csv("./data/research_data_narr_desc.tsv", sep="\t", dtype=str, encoding="utf-8")
    df_variables = pd.read_csv("./data/variables_narr_desc.tsv", sep="\t", dtype=str, encoding="utf-8")
    df_instruments = pd.read_csv("./data/instruments_narr_desc.tsv", sep="\t", dtype=str, encoding="utf-8")

    query_ids = df_publication['query_id'].tolist()
    # print(query_ids)

    # generate query file in TREC format
    with open(args.query_file, "a", encoding="utf-8") as file:
        query_text = "<topics>\n"
        for id in query_ids:
            row_pub = df_publication.loc[df_publication['query_id'] == id]
            query = row_pub.iloc[0]["query"]
            pub_desc = row_pub.iloc[0]["pub_desc"]
            pub_narr = row_pub.iloc[0]["pub_narr"]

            row_res = df_research.loc[df_research['query_id'] == id]
            res_desc = row_res.iloc[0]["research_desc"]
            res_narr = row_res.iloc[0]["research_narr"]

            row_var = df_variables.loc[df_variables['query_id'] == id]
            var_desc = row_var.iloc[0]["var_desc"]
            var_narr = row_var.iloc[0]["var_narr"]

            row_ins = df_instruments.loc[df_instruments['query_id'] == id]
            ins_desc = row_ins.iloc[0]["instru_desc"]
            ins_narr = row_ins.iloc[0]["instru_narr"]

            query_text += f"<top>\n<num>{id}</num>\n" \
                          f"<title>{query}</title>\n" \
                          f"<publication>\n\t" \
                          f"<desc>{pub_desc}</desc>\n\t" \
                          f"<narr>{pub_narr}</narr>\n</publication>\n" \
                          f"<research_data>\n\t" \
                          f"<desc>{res_desc}</desc>\n\t" \
                          f"<narr>{res_narr}</narr>\n</research_data>\n" \
                          f"<variables>\n\t" \
                          f"<desc>{var_desc}</desc>\n\t" \
                          f"<narr>{var_narr}</narr>\n</variables>\n" \
                          f"<instruments_tools>\n\t" \
                          f"<desc>{ins_desc}</desc>\n\t" \
                          f"<narr>{ins_narr}</narr>\n</instruments_tools>\n</top>\n\n"
            file.write(query_text)
            query_text = ""
            file.flush()
        file.write("</topics>")
    file.close()


if __name__ == '__main__':
    main()