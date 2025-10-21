package com.reviewr.intellij.model;

import java.util.Objects;

/**
 * Represents a code review finding from reviewr analysis.
 */
public class ReviewFinding {
    private String filePath;
    private int lineStart;
    private int lineEnd;
    private String severity;
    private String category;
    private String message;
    private String ruleId;
    private String suggestion;
    private String codeSnippet;
    
    public ReviewFinding() {
    }
    
    public ReviewFinding(String filePath, int lineStart, int lineEnd, String severity,
                        String category, String message, String ruleId, String suggestion) {
        this.filePath = filePath;
        this.lineStart = lineStart;
        this.lineEnd = lineEnd;
        this.severity = severity;
        this.category = category;
        this.message = message;
        this.ruleId = ruleId;
        this.suggestion = suggestion;
    }
    
    // Getters and setters
    public String getFilePath() {
        return filePath;
    }
    
    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }
    
    public int getLineStart() {
        return lineStart;
    }
    
    public void setLineStart(int lineStart) {
        this.lineStart = lineStart;
    }
    
    public int getLineEnd() {
        return lineEnd;
    }
    
    public void setLineEnd(int lineEnd) {
        this.lineEnd = lineEnd;
    }
    
    public String getSeverity() {
        return severity;
    }
    
    public void setSeverity(String severity) {
        this.severity = severity;
    }
    
    public String getCategory() {
        return category;
    }
    
    public void setCategory(String category) {
        this.category = category;
    }
    
    public String getMessage() {
        return message;
    }
    
    public void setMessage(String message) {
        this.message = message;
    }
    
    public String getRuleId() {
        return ruleId;
    }
    
    public void setRuleId(String ruleId) {
        this.ruleId = ruleId;
    }
    
    public String getSuggestion() {
        return suggestion;
    }
    
    public void setSuggestion(String suggestion) {
        this.suggestion = suggestion;
    }
    
    public String getCodeSnippet() {
        return codeSnippet;
    }
    
    public void setCodeSnippet(String codeSnippet) {
        this.codeSnippet = codeSnippet;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ReviewFinding that = (ReviewFinding) o;
        return lineStart == that.lineStart &&
               lineEnd == that.lineEnd &&
               Objects.equals(filePath, that.filePath) &&
               Objects.equals(severity, that.severity) &&
               Objects.equals(category, that.category) &&
               Objects.equals(message, that.message) &&
               Objects.equals(ruleId, that.ruleId);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(filePath, lineStart, lineEnd, severity, category, message, ruleId);
    }
    
    @Override
    public String toString() {
        return "ReviewFinding{" +
               "filePath='" + filePath + '\'' +
               ", lineStart=" + lineStart +
               ", lineEnd=" + lineEnd +
               ", severity='" + severity + '\'' +
               ", category='" + category + '\'' +
               ", message='" + message + '\'' +
               ", ruleId='" + ruleId + '\'' +
               '}';
    }
}

