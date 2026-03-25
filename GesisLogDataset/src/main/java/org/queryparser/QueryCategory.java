package org.queryparser;

/**
 *
 * @author suchana
 */

public class QueryCategory {

    private String queryId;
    private String queryText;
    private String category;
    private String description;

    public QueryCategory(String queryId, String queryText,
                         String category, String description) {
        this.queryId = queryId;
        this.queryText = queryText;
        this.category = category;
        this.description = description;
    }

    public String getQueryId() {
        return queryId;
    }

    public String getQueryText() {
        return queryText;
    }

    public String getCategory() {
        return category;
    }

    public String getDescription() {
        return description;
    }

    @Override
    public String toString() {
        return "QueryCategory{" +
                "queryId='" + queryId + '\'' +
                ", queryText='" + queryText + '\'' +
                ", category='" + category + '\'' +
                ", description='" + description + '\'' +
                '}';
    }
}