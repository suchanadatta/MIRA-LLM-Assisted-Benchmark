package org.searcher;

import static common.DocField.RAW_ABS;
import static common.DocField.ID;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.de.GermanAnalyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.analysis.miscellaneous.PerFieldAnalyzerWrapper;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.similarities.BM25Similarity;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.queryparser.QueryCategory;
import org.queryparser.QueryXmlParser;

/**
 *
 * @author suchana
 */

class GESISLogQuery {
    int clusterID;
    String clusterName;
    String qid;
    String query;
    String language;
    List<String> category;

    public GESISLogQuery(String qid, String query, String language) {
        this.qid = qid;
        this.query = query;
        this.language = language;
    } 
}

public class GesisPublicationSearcher {

    public IndexReader     indexReader;
    public IndexSearcher   indexSearcher;
    public String          indexPath;
    public String          resPath;
    public File            indexFile;          // place where the index is stored
    public JSONParser      jsonParser;
    public FileWriter      resFileWriter;  // the res file writer

    String queryPath;
    List<GESISLogQuery> queries;
    Analyzer defaultAnalyzer;
    Analyzer englishAnalyzer;
    Analyzer germanAnalyzer;

    public GesisPublicationSearcher(String indexPath, String queryPath, String resPath) throws IOException {

        this.queryPath = queryPath;
        // Define analyzers 
        defaultAnalyzer = new StandardAnalyzer();
        englishAnalyzer = new EnglishAnalyzer();
        germanAnalyzer = new GermanAnalyzer();
        
        // Create a HashMap for the field-analyzer mapping
        Map<String, Analyzer> analyzerMap = new HashMap<>();
        analyzerMap.put("content_en", englishAnalyzer);
        analyzerMap.put("content_de", germanAnalyzer);
        
        // Construct PerFieldAnalyzerWrapper
        Analyzer perFieldAnalyzer = new PerFieldAnalyzerWrapper(defaultAnalyzer, analyzerMap);
        
        this.resPath = resPath;
        resFileWriter = new FileWriter(resPath, true);
        System.out.println("resPath set to: " + resPath);

        this.indexPath = indexPath;
        System.out.println("indexPath set to: " + indexPath);
        indexFile = new File(indexPath);
        Directory indexDir = FSDirectory.open(indexFile.toPath());

        if (!DirectoryReader.indexExists(indexDir)) {
            System.err.println("Index doesn't exists in "+indexPath);
            System.exit(1);
        }
        /* setting indexReader. indexSearcher and similarity function for retrieval */
        indexReader = DirectoryReader.open(FSDirectory.open(indexFile.toPath()));

        indexSearcher = new IndexSearcher(indexReader);
        
        indexSearcher.setSimilarity(new BM25Similarity());
        
        jsonParser = new JSONParser();
    }

    /**
     *
     * @return
     * @throws FileNotFoundException
     * @throws IOException
     */
    public List<GESISLogQuery> readQueryFile() throws FileNotFoundException, IOException, ParseException {

        queries = new ArrayList<>();

        FileReader fileReader = new FileReader(queryPath);

        BufferedReader br = new BufferedReader(fileReader);

        String line;
        
//        JsonObject jsonObject;
        JSONObject jsonObject;

        while ((line = br.readLine()) != null) {

            GESISLogQuery fairQuery;

            // Parse the JSON string into a JsonObject
//            jsonObject = JsonParser.parseString(line).getAsJsonObject();
            jsonObject = (JSONObject)jsonParser.parse(line);

//            totQuery = new ToTQuery(jsonObject.get("query_id").getAsString(), jsonObject.get("query").getAsString());
            fairQuery = new GESISLogQuery(jsonObject.get("id").toString(), 
                                          jsonObject.get("title").toString(),
                                          jsonObject.get("language").toString());
            
            queries.add(fairQuery);

        }

        br.close();

        return queries;
    }
    
    public List<GESISLogQuery> readQueryFileTsv() throws FileNotFoundException, IOException, ParseException {        
        
        System.out.println("Read queries from path : " + queryPath);
        queries = new ArrayList<>();

        BufferedReader br = new BufferedReader(new InputStreamReader(
                new FileInputStream(queryPath), StandardCharsets.UTF_8));

        String line;
        
        GESISLogQuery gesisQuery;
        
        while ((line = br.readLine()) != null) {

            System.out.println("line: " + line);
            String[] words = line.split("\t");
            System.out.print("QID : " + words[0]);
            String qid = words[0];
            String query = words[1].replaceAll("[^a-zA-Z0-9äöüÄÖÜß.,!?;:\\s]", " ")
                    .replaceAll("\\s+", " ").trim();
            System.out.println("\tQUERY: " + query);
            String lang = words[2];
            gesisQuery = new GESISLogQuery(qid, query, lang);
            queries.add(gesisQuery);
        }
        
        br.close();

        return queries;
    }
    
    public List<GESISLogQuery> readQueryTitleDescTsv() throws FileNotFoundException, IOException, ParseException {        
        
        System.out.println("Read queries from path : " + queryPath);
        queries = new ArrayList<>();
        
        BufferedReader br = new BufferedReader(new FileReader(queryPath));
//        br.readLine();

//        BufferedReader br = new BufferedReader(new InputStreamReader(
//                new FileInputStream(queryPath), StandardCharsets.UTF_8));

        String line;
        
        GESISLogQuery gesisQuery;
        
        while ((line = br.readLine()) != null) {

//            System.out.println("line: " + line);
            String[] words = line.split("\t");
            String qid = words[0];
            System.out.print("QID : " + qid);
            String lang = words[2]; // language of the query
            System.out.print("\tLang : " + lang);
            String query = words[1] + " " + words[3]; // initial query 
            query = query.replaceAll("[^a-zA-Z0-9äöüÄÖÜß.,!?;:\\s]", " ")
                    .replaceAll("\\s+", " ").trim();
            System.out.println("\tQUERY: " + query);
            gesisQuery = new GESISLogQuery(qid, query, lang);
            queries.add(gesisQuery);
        }
        
        br.close();

        return queries;
    }
    
    /* complete this function */
//    public List<QueryCategory> readQueryTitleDescXml() throws FileNotFoundException, IOException, ParseException, Exception {        
//        
//        System.out.println("Read queries from path : " + queryPath);
//
//        List<QueryCategory> queries = QueryXmlParser.parse(queryPath);
//        for (QueryCategory qc : queries) {
//            System.out.println(qc);
//        }
//
//        System.out.println("Total objects: " + queries.size());
//        
//        return queries;
//    }
    
    /**
     * Returns a string-buffer in the TREC-res format for the passed queryId
     * @param queryId
     * @param hits
     * @param searcher
     * @param runName
     * @param fieldDocid
     * @return
     * @throws IOException 
     */    
    /**
     * Returns a string-buffer in the TREC-res format for the passed queryId
     * @param queryId
     * @param hits
     * @param searcher
     * @param runName
     * @param fieldDocid
     * @return
     * @throws IOException 
     */
    static final public StringBuffer makeTRECResFile(String queryId, String query, ScoreDoc[] hits, 
        IndexSearcher searcher, String fieldDocid) throws IOException {

        StringBuffer resBuffer = new StringBuffer();
        int hits_length = hits.length;
        for (int i = 0; i < hits_length; ++i) {
            int luceneDocId = hits[i].doc;
            Document d = searcher.doc(luceneDocId);
            resBuffer.append(queryId).append("\tQ0\t").
//                    append(query).append("\t").
                    append(d.get(ID)).append("\t").
//                    append(d.get(TITLE)).append("\t").
//                    append(d.get(fieldDocid)).append("\t").
                    append((i)).append("\t").
                    append(hits[i].score).append("\tpublication\t").
                    append(d.get(RAW_ABS)).append("\n");
        }

        return resBuffer;
    }
    
    public void search() throws IOException, ParseException, org.apache.lucene.queryparser.classic.ParseException {
        
        TopDocs topDocs;
        ScoreDoc[] hits;
        Query luceneQuery;
        StringBuffer resBuffer;
        QueryParser parser;
        String queryStr;

//        readQueryFile();
//        readQueryFileTsv();
        readQueryTitleDescTsv();
        System.out.println("========= Total queries in the file ======== " + queries.size());
        
        for(GESISLogQuery query : queries) {
            
//            System.out.println("\nRetrieving docs for query : " + query.qid);
            
            if((query.language).equals("de")){
//                System.out.println("This is a German query");
                parser = new QueryParser("abstract_de", germanAnalyzer);
                queryStr = QueryParser.escape(query.query);
            
                luceneQuery = parser.parse(queryStr);
//                System.out.println("Lucene query : " + luceneQuery.toString("title"));
                topDocs = indexSearcher.search(luceneQuery, 100); // unused so far

                if(topDocs.scoreDocs.length == 0)
//                    System.out.println(query.qid + ": documents retrieve: " + 0);
                    System.out.println(query.qid + "\t" + 0);

                else {
                    hits = topDocs.scoreDocs;
                    // Get the explanation for the first document
                    int docId = topDocs.scoreDocs[0].doc;
                    
//                    Explanation explanation;// = indexSearcher.explain(query, docId);
//                    explanation = indexSearcher.explain(luceneQuery, docId);
                    // Print the explanation
//                    System.out.println("Explanation : " + explanation.toString());

//                    System.out.println(query.qid + ": documents retrieve: " + hits.length);
                    System.out.println(query.qid + "\tGerman query\t" + hits.length);
                    resBuffer = makeTRECResFile(query.qid, 
                                                query.query,
                                                hits, 
                                                indexSearcher, 
                                                RAW_ABS);
                    resFileWriter.write(resBuffer.toString());
                }
            }
            else {
//                System.out.println("This is an English query");
                parser = new QueryParser("abstract_en", englishAnalyzer);
                queryStr = QueryParser.escape(query.query);
//                System.out.println("Now processing query ID : " + query.qid + " : " + queryStr); 
                
                luceneQuery = parser.parse(queryStr);
//                System.out.println("Lucene query : " + luceneQuery.toString("title"));
                topDocs = indexSearcher.search(luceneQuery, 100); // unused so far

                if(topDocs.scoreDocs.length == 0)
//                    System.out.println(query.qid + ": documents retrieve: " + 0);
                    System.out.println(query.qid + "\t" + 0);

                else {
                    hits = topDocs.scoreDocs;
                    // Get the explanation for the first document
                    int docId = topDocs.scoreDocs[0].doc;
                    
//                    Explanation explanation;// = indexSearcher.explain(query, docId);
//                    explanation = indexSearcher.explain(luceneQuery, docId);
//                    // Print the explanation
//                    System.out.println("Explanation : " + explanation.toString());

//                    System.out.println(query.qid + ": documents retrieve: " + hits.length);
                    System.out.println(query.qid + "\tEnglish query\t" + hits.length);
                    resBuffer = makeTRECResFile(query.qid, 
                                                query.query,
                                                hits, 
                                                indexSearcher, 
                                                RAW_ABS);
                    resFileWriter.write(resBuffer.toString());
                }
            }
        }
        resFileWriter.flush();
        resFileWriter.close();
    }

    public static void main(String[] args) throws IOException, ParseException, org.apache.lucene.queryparser.classic.ParseException {

        String prompt = "arguments:\n\t1. indexPath\n\t2. queryPath\n\t3. resPath";
        String indexPath = "/Volumes/SD_SSD/Suchana/index/GESIS/publication/";
//        String queryPath = "/Users/suchana/python_projects/victeur/LLM-based-relevance-judgement/output/queries_with_4_itemtypes_resaved.tsv";
        String queryPath = "/Users/suchana/python_projects/victeur/LLM-based-relevance-judgement/query_narr_desc/new/new_query_set_desc_translated.tsv";
        String resPath = "/Users/suchana/NetBeansProjects/GesisLogDataset/output/new/publication_top100_bm25_desc.res";
        
        GesisPublicationSearcher searcher = new GesisPublicationSearcher(indexPath, queryPath, resPath);
        searcher.search();
    }
}