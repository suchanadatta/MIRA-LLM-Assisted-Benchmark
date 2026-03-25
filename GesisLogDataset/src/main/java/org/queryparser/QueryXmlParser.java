package org.queryparser;

/**
 *
 * @author suchana
 */

import org.w3c.dom.*;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class QueryXmlParser {

    private static final String[] CATEGORIES = {
            "publication",
            "research_data",
            "variables",
            "instruments_tools"
    };

    public static List<QueryCategory> parse(String xmlPath) throws Exception {

        List<QueryCategory> results = new ArrayList<>();

        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setIgnoringElementContentWhitespace(true);

        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(new File(xmlPath));
        doc.getDocumentElement().normalize();

        NodeList topNodes = doc.getElementsByTagName("top");

        for (int i = 0; i < topNodes.getLength(); i++) {
            Element top = (Element) topNodes.item(i);

            String queryId = getText(top, "num");
            String queryText = getText(top, "title");

            if (queryId == null || queryText == null) {
                continue;
            }

            for (String category : CATEGORIES) {
                NodeList catNodes = top.getElementsByTagName(category);
                if (catNodes.getLength() == 0) {
                    continue;
                }

                Element catElem = (Element) catNodes.item(0);
                String desc = getChildText(catElem, "desc");

                if (desc != null && !desc.isBlank()) {
                    results.add(new QueryCategory(
                            queryId.trim(),
                            queryText.trim(),
                            category,
                            desc.trim()
                    ));
                }
            }
        }

        return results;
    }

    private static String getText(Element parent, String tag) {
        NodeList nodes = parent.getElementsByTagName(tag);
        if (nodes.getLength() == 0) return null;
        return nodes.item(0).getTextContent();
    }

    private static String getChildText(Element parent, String tag) {
        NodeList nodes = parent.getElementsByTagName(tag);
        if (nodes.getLength() == 0) return null;
        return nodes.item(0).getTextContent();
    }
}
