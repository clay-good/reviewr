package com.reviewr.intellij.settings;

import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.components.PersistentStateComponent;
import com.intellij.openapi.components.State;
import com.intellij.openapi.components.Storage;
import com.intellij.util.xmlb.XmlSerializerUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Persistent settings for the Reviewr plugin.
 */
@State(
    name = "ReviewrSettings",
    storages = @Storage("reviewr.xml")
)
public class ReviewrSettings implements PersistentStateComponent<ReviewrSettings> {
    
    // General settings
    public boolean enabled = true;
    public String reviewrPath = "";  // Path to reviewr CLI (empty = use system python3 -m reviewr)
    public boolean useLocalAnalysisOnly = true;  // Use --local-only flag for faster analysis
    
    // Analysis settings
    public boolean securityAnalysis = true;
    public boolean performanceAnalysis = true;
    public boolean qualityAnalysis = true;
    public boolean realTimeAnalysis = true;
    public int analysisDelayMs = 1000;  // Delay before running analysis after edit
    
    // Display settings
    public boolean showInfoFindings = false;
    public boolean showLowFindings = true;
    public boolean showMediumFindings = true;
    public boolean showHighFindings = true;
    public boolean showCriticalFindings = true;
    
    // API settings (for AI-powered analysis)
    public String apiProvider = "claude";  // claude, openai, gemini
    public String apiKey = "";
    
    /**
     * Get the singleton instance of ReviewrSettings.
     */
    public static ReviewrSettings getInstance() {
        return ApplicationManager.getApplication().getService(ReviewrSettings.class);
    }
    
    @Nullable
    @Override
    public ReviewrSettings getState() {
        return this;
    }
    
    @Override
    public void loadState(@NotNull ReviewrSettings state) {
        XmlSerializerUtil.copyBean(state, this);
    }
    
    // Convenience methods
    public boolean isEnabled() {
        return enabled;
    }
    
    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }
    
    public String getReviewrPath() {
        return reviewrPath;
    }
    
    public void setReviewrPath(String reviewrPath) {
        this.reviewrPath = reviewrPath;
    }
    
    public boolean isUseLocalAnalysisOnly() {
        return useLocalAnalysisOnly;
    }
    
    public void setUseLocalAnalysisOnly(boolean useLocalAnalysisOnly) {
        this.useLocalAnalysisOnly = useLocalAnalysisOnly;
    }
    
    public boolean isSecurityAnalysis() {
        return securityAnalysis;
    }
    
    public void setSecurityAnalysis(boolean securityAnalysis) {
        this.securityAnalysis = securityAnalysis;
    }
    
    public boolean isPerformanceAnalysis() {
        return performanceAnalysis;
    }
    
    public void setPerformanceAnalysis(boolean performanceAnalysis) {
        this.performanceAnalysis = performanceAnalysis;
    }
    
    public boolean isQualityAnalysis() {
        return qualityAnalysis;
    }
    
    public void setQualityAnalysis(boolean qualityAnalysis) {
        this.qualityAnalysis = qualityAnalysis;
    }
    
    public boolean isRealTimeAnalysis() {
        return realTimeAnalysis;
    }
    
    public void setRealTimeAnalysis(boolean realTimeAnalysis) {
        this.realTimeAnalysis = realTimeAnalysis;
    }
    
    public int getAnalysisDelayMs() {
        return analysisDelayMs;
    }
    
    public void setAnalysisDelayMs(int analysisDelayMs) {
        this.analysisDelayMs = analysisDelayMs;
    }
    
    public boolean shouldShowFinding(String severity) {
        if (severity == null) return true;
        
        switch (severity.toLowerCase()) {
            case "critical":
                return showCriticalFindings;
            case "high":
                return showHighFindings;
            case "medium":
                return showMediumFindings;
            case "low":
                return showLowFindings;
            case "info":
                return showInfoFindings;
            default:
                return true;
        }
    }
}

