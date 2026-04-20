package org.indexer;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.StringReader;
import java.util.HashMap;
import java.util.Map;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.analysis.de.GermanAnalyzer;
import org.apache.lucene.analysis.miscellaneous.PerFieldAnalyzerWrapper;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.index.ConcurrentMergeScheduler;
import org.apache.lucene.index.IndexOptions;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.MultiTerms;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.Terms;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.BytesRef;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;



public class GesisResearchIndexer {

    Analyzer defaultAnalyzer;
    Analyzer englishAnalyzer;
    Analyzer germanAnalyzer;
    static IndexWriter indexWriter;
    JSONParser jsonParser;
    static int docCount;
    

    public GesisResearchIndexer(String collPath, String indexPath) throws IOException {

        Directory indexDir = FSDirectory.open(new File(indexPath).toPath());
        
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
        
        // IndexWriter Config
        IndexWriterConfig iwcfg = new IndexWriterConfig(perFieldAnalyzer);
        iwcfg.setOpenMode(IndexWriterConfig.OpenMode.CREATE);
//        iwcfg.setCodec(new SimpleTextCodec());
        iwcfg.setRAMBufferSizeMB(2048); // default is 16 (MB)
        iwcfg.setUseCompoundFile(false);
        iwcfg.setMergeScheduler(new ConcurrentMergeScheduler());
        
        jsonParser = new JSONParser();
        
        docCount = 0;

        indexWriter = new IndexWriter(indexDir, iwcfg);
    }

    FieldType constructStrField(boolean toStore, boolean toStore_tokenized, boolean toStore_TermVector) {

        FieldType ft = new FieldType();
        ft.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS);
        ft.setStored(toStore);
        // ft.setTokenized(toStore_tokenized);
         ft.setStoreTermVectors(toStore_TermVector);
        // ft.setStoreTermVectorPositions(true);

        return ft;
    }

    public void indexAll(String collectionPath) throws FileNotFoundException, IOException, NullPointerException, ParseException {
        
        System.out.println("Indexing started...");
        File colFile = new File(collectionPath);
        if(colFile.isDirectory())
            collectionDirectory(colFile);
        else
            indexFile(colFile);
    }
    
    private void collectionDirectory(File colDir) throws FileNotFoundException, IOException, NullPointerException, ParseException {
        
        File[] files = colDir.listFiles();
        for (File file : files) {
            System.out.println("Indexing file : " + file);
            if (file.isDirectory()) {
                System.out.println("It has subdirectories...\n");
                collectionDirectory(file);  // calling this function recursively to access all the subfolders in the directory
            }
            else
                indexFile(file);
        }
    }
    
    private void indexFile(File colFile) throws FileNotFoundException, IOException, ParseException {
        
        JSONObject eachDoc;
        
        JSONParser parser = new JSONParser();

        try (FileReader reader = new FileReader(colFile)) {
            Object obj = parser.parse(reader);

        // Top-level element is an array
        JSONArray jsonArray = (JSONArray) obj;

        for (Object element : jsonArray) {
            eachDoc = (JSONObject) element;
            parseJson(eachDoc);
        }
        } catch (Exception e) {
        e.printStackTrace();
        }
    }
    
    private void parseJson(JSONObject eachDoc) throws IOException {
        Document doc;
        String analyzedText;
        Object abs, abs_en;
        
        doc = new Document();
        
        FieldType ft_store_tv = constructStrField(true, true, true);
        FieldType ft_store = constructStrField(true, false, false);
        
        // ============ category : research_data ===========
        
        // "id"
        doc.add(new Field("id", eachDoc.get("id").toString(), ft_store));
        System.out.println("ID : " + eachDoc.get("id"));
        
        // "type"
        doc.add(new Field("type", eachDoc.get("type").toString(), ft_store));
        System.out.println("TYPE : " + eachDoc.get("type"));
        
        //"title"
        if (eachDoc.get("title") != null){
            doc.add(new Field("title", cleanText(eachDoc.get("title").toString()), ft_store));
            System.out.println("TITLE : " + eachDoc.get("title"));
        }
        else doc.add(new Field("title", "", ft_store));
        
        // "title_en"
        if (eachDoc.get("title_en") != null){
            doc.add(new Field("title_en", cleanText(eachDoc.get("title_en").toString()), ft_store));
            System.out.println("TITLE_en : " + eachDoc.get("title_en"));
        }
        else doc.add(new Field("title_en", "", ft_store));
        
        // "abstract"
        abs = eachDoc.get("abstract");
        if (abs == null) {
            System.out.println("THERE IS NO GERMAN ABSTRACT");
            doc.add(new Field("abstract_de", "", ft_store_tv));            
        }
        else if (isGermanText(abs.toString())){
            doc.add(new Field("rawabs_de", cleanText(abs.toString()), ft_store)); 
            analyzedText = analyzeText(germanAnalyzer, cleanText(abs.toString()), "abstract").toString();
            System.out.println("GERMAN ABSTRACT : " + analyzedText);
            doc.add(new Field("abstract_de", analyzedText, ft_store_tv));
        }
        
        // "abstract_en"
        abs_en = eachDoc.get("abstract_en");
        if (abs_en == null) {
            System.out.println("THERE IS NO ENGLISH ABSTRACT");
            doc.add(new Field("abstract_en", "", ft_store_tv));            
        }
        else{
            doc.add(new Field("rawabs_en", cleanText(abs_en.toString()), ft_store)); 
            analyzedText = analyzeText(englishAnalyzer, cleanText(abs_en.toString()), "abstract_en").toString();
            System.out.println("ENGLISH ABSTRACT : " + analyzedText);
            doc.add(new Field("abstract_en", analyzedText, ft_store_tv));
        } 
        
        indexWriter.addDocument(doc);
        
        System.out.println("\nIndexed doc no. : " + ++docCount + "\n");
        
    }
    
    public static boolean isGermanText(String text) {
        
        if (text == null || text.isEmpty()) return false;
        text = text.toLowerCase();

        // Common German words and characters
        String[] germanWords = {"und", "der", "die", "das", "nicht", "ist", "ein", "zu", "mit", "auf"};
        String germanChars = "äöüß";

        // Check for German-specific characters
        for (char c : germanChars.toCharArray()) {
            if (text.indexOf(c) >= 0) {
                return true;
            }
        }

        // Check for German function words
        int count = 0;
        for (String word : germanWords) {
            if (text.contains(" " + word + " ")) {
                count++;
            }
        }

        return count > 2; // Adjust threshold if needed
    }
    
    private String cleanText(String rawArticle){
        
        String pattern = "\\<(.*?)\\>";
        rawArticle = rawArticle.replaceAll(pattern, "")
                .replaceAll("[^a-zA-Z0-9äöüÄÖÜß\\.\\,]", " ").trim()
                .replaceAll(" +", " ").replaceAll(",", "");
        rawArticle = rawArticle.replaceAll("\n", "").replaceAll("\r", "");
        rawArticle = rawArticle.replaceAll(pattern, "").trim().replaceAll(" +", " ");
        
        return rawArticle;
    }  
    
    public static StringBuffer analyzeText(Analyzer analyzer, String text, String fieldName) throws IOException {

        StringBuffer tokenizedContentBuff = new StringBuffer();

        TokenStream stream = analyzer.tokenStream(fieldName, new StringReader(text));
        CharTermAttribute termAtt = stream.addAttribute(CharTermAttribute.class);

        stream.reset();

        while (stream.incrementToken()) {
            String term = termAtt.toString();
            tokenizedContentBuff.append(term).append(" ");
        }

        stream.end();
        stream.close();

        return tokenizedContentBuff;
    }


    /**
     * Returns the vocabulary size of the index for 'field'.
     * @param indexReader
     * @param field
     * @return Total number of terms in 'field' of the index
     * @throws IOException 
     */
    public static long getVocabularySize(IndexReader indexReader, String field) throws IOException {

//        Fields fields = MultiFields.getFields(indexReader);
        Terms terms = MultiTerms.getTerms(indexReader, field);
        if(null == terms) {
            System.err.println("Field: "+field);
            System.err.println("Error buildCollectionStat(): terms Null found");
        }
        long vocSize = terms.getSumTotalTermFreq();  // total number of terms in the index in that field

        return vocSize;
    }

    public static void showDocumentVector(int luceneDocid, IndexReader indexReader, String FIELDNAME) throws IOException {

        int docSize = 0;
        long docCount = indexReader.maxDoc();      // total number of documents in the index

        if(indexReader==null) {
            System.out.println("Error: null == indexReader in showDocumentVector(int,IndexReader)");
            System.exit(1);
        }

        // Term vector for this document and field, or null if term vectors were not indexed
        Terms terms = indexReader.getTermVector(luceneDocid, FIELDNAME);
        if(null == terms) {
            System.err.println("Error: Term vectors not indexed: "+luceneDocid);
            System.exit(1);
        }

        System.out.println("Unique term count: " + terms.size());
        TermsEnum iterator;
        iterator = terms.iterator();
        BytesRef byteRef = null;
        long vocSize = terms.getSumTotalTermFreq();  // total number of terms in the index in that field
        vocSize = getVocabularySize(indexReader, FIELDNAME);

        while((byteRef = iterator.next()) != null) {
        //* for each word in the document
            String t = new String(byteRef.bytes, byteRef.offset, byteRef.length);
            int df = iterator.docFreq();           // df of 't'
            long cf = iterator.totalTermFreq();    // cf of 't'
            long termFreq = iterator.totalTermFreq();    // tf of 't'
            // idf = log(#docCount / (df+1) )
            double idf = Math.log((float)(docCount)/(float)(df+1));
            double norm_cf = (double)cf / (double)vocSize;
            System.out.println(t+": tf: "+termFreq + " df: "+ df
                + " cf: " + cf);
        }
    }
    
    public static void main(String[] args) throws IOException, FileNotFoundException, ParseException {

        if (args.length != 2) {
            System.err.println("Usage mvn exec:java -Dexec.mainClass=\"your.package.MainClass\" -Dexec.args=\"/path/to/index /path/to/input.json\"");
            System.exit(1);
        }

        String INDEX_PATH = args[0];
        String INPUT_PATH = args[1];

        GesisResearchIndexer indexer = new GesisResearchIndexer(INPUT_PATH, INDEX_PATH);
        indexer.indexAll(INPUT_PATH);

        indexWriter.close();  // make sure this is correctly initialized
    }
    
    public void delete() throws IOException {
        indexWriter.deleteDocuments(new TermQuery(new Term("asdplot", "murder")));
//        indexWriter.commit();
        indexWriter.close();
    }
}
