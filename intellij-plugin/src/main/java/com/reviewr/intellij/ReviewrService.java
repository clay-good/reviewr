package com.reviewr.intellij;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.components.Service;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.reviewr.intellij.model.ReviewFinding;
import com.reviewr.intellij.settings.ReviewrSettings;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Core service for running Reviewr analysis.
 * This service manages the execution of the reviewr CLI and parsing of results.
 */
@Service
public final class ReviewrService {
    private static final Logger LOG = Logger.getInstance(ReviewrService.class);
    private final Gson gson = new Gson();

    public static ReviewrService getInstance() {
        return ApplicationManager.getApplication().getService(ReviewrService.class);
    }

    /**
     * Analyze a single file asynchronously.
     *
     * @param project The current project
     * @param file The file to analyze
     * @return CompletableFuture with list of findings
     */
    public CompletableFuture<List<ReviewFinding>> analyzeFile(Project project, VirtualFile file) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                ReviewrSettings settings = ReviewrSettings.getInstance();
                
                if (!settings.isEnabled()) {
                    LOG.info("Reviewr is disabled in settings");
                    return new ArrayList<>();
                }

                // Get file path
                String filePath = file.getPath();
                String language = detectLanguage(file);
                
                if (language == null) {
                    LOG.debug("Unsupported file type: " + file.getName());
                    return new ArrayList<>();
                }

                // Build reviewr command
                List<String> command = buildCommand(settings, filePath, language);
                
                // Execute reviewr
                ProcessBuilder pb = new ProcessBuilder(command);
                pb.directory(new File(project.getBasePath()));
                pb.redirectErrorStream(true);
                
                Process process = pb.start();
                
                // Read output
                StringBuilder output = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                    }
                }
                
                int exitCode = process.waitFor();
                
                if (exitCode != 0) {
                    LOG.warn("Reviewr exited with code " + exitCode + ": " + output);
                    return new ArrayList<>();
                }
                
                // Parse SARIF output
                return parseSarifOutput(output.toString(), filePath);
                
            } catch (Exception e) {
                LOG.error("Error running Reviewr analysis", e);
                return new ArrayList<>();
            }
        });
    }

    /**
     * Analyze entire project asynchronously.
     *
     * @param project The project to analyze
     * @return CompletableFuture with list of findings
     */
    public CompletableFuture<List<ReviewFinding>> analyzeProject(Project project) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                ReviewrSettings settings = ReviewrSettings.getInstance();
                
                if (!settings.isEnabled()) {
                    return new ArrayList<>();
                }

                // Build reviewr command for project
                List<String> command = buildProjectCommand(settings, project.getBasePath());
                
                // Execute reviewr
                ProcessBuilder pb = new ProcessBuilder(command);
                pb.directory(new File(project.getBasePath()));
                pb.redirectErrorStream(true);
                
                Process process = pb.start();
                
                // Read output
                StringBuilder output = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                    }
                }
                
                int exitCode = process.waitFor();
                
                if (exitCode != 0) {
                    LOG.warn("Reviewr exited with code " + exitCode);
                    return new ArrayList<>();
                }
                
                // Parse SARIF output
                return parseSarifOutput(output.toString(), null);
                
            } catch (Exception e) {
                LOG.error("Error running Reviewr project analysis", e);
                return new ArrayList<>();
            }
        });
    }

    private List<String> buildCommand(ReviewrSettings settings, String filePath, String language) {
        List<String> command = new ArrayList<>();
        
        // Use python3 -m reviewr or direct reviewr command
        if (settings.getReviewrPath().isEmpty()) {
            command.add("python3");
            command.add("-m");
            command.add("reviewr");
        } else {
            command.add(settings.getReviewrPath());
        }
        
        command.add("review");
        command.add(filePath);
        command.add("--format");
        command.add("sarif");
        command.add("--local-only");  // Use local analyzers only for speed
        
        // Add language-specific flags
        if (settings.isSecurityAnalysisEnabled()) {
            command.add("--enable-security");
        }
        if (settings.isPerformanceAnalysisEnabled()) {
            command.add("--enable-performance");
        }
        
        return command;
    }

    private List<String> buildProjectCommand(ReviewrSettings settings, String projectPath) {
        List<String> command = new ArrayList<>();
        
        if (settings.getReviewrPath().isEmpty()) {
            command.add("python3");
            command.add("-m");
            command.add("reviewr");
        } else {
            command.add(settings.getReviewrPath());
        }
        
        command.add("review");
        command.add(projectPath);
        command.add("--format");
        command.add("sarif");
        command.add("--local-only");
        
        if (settings.isSecurityAnalysisEnabled()) {
            command.add("--enable-security");
        }
        if (settings.isPerformanceAnalysisEnabled()) {
            command.add("--enable-performance");
        }
        
        return command;
    }

    private String detectLanguage(VirtualFile file) {
        String extension = file.getExtension();
        if (extension == null) return null;
        
        return switch (extension.toLowerCase()) {
            case "py" -> "python";
            case "js", "jsx" -> "javascript";
            case "ts", "tsx" -> "typescript";
            case "go" -> "go";
            case "rs" -> "rust";
            case "java" -> "java";
            default -> null;
        };
    }

    private List<ReviewFinding> parseSarifOutput(String sarifJson, String filterFilePath) {
        List<ReviewFinding> findings = new ArrayList<>();
        
        try {
            JsonObject sarif = gson.fromJson(sarifJson, JsonObject.class);
            JsonArray runs = sarif.getAsJsonArray("runs");
            
            if (runs == null || runs.size() == 0) {
                return findings;
            }
            
            JsonObject run = runs.get(0).getAsJsonObject();
            JsonArray results = run.getAsJsonArray("results");
            
            if (results == null) {
                return findings;
            }
            
            for (int i = 0; i < results.size(); i++) {
                JsonObject result = results.get(i).getAsJsonObject();
                ReviewFinding finding = parseSarifResult(result);
                
                // Filter by file if specified
                if (filterFilePath == null || finding.getFilePath().equals(filterFilePath)) {
                    findings.add(finding);
                }
            }
            
        } catch (Exception e) {
            LOG.error("Error parsing SARIF output", e);
        }
        
        return findings;
    }

    private ReviewFinding parseSarifResult(JsonObject result) {
        ReviewFinding finding = new ReviewFinding();
        
        // Extract message
        JsonObject message = result.getAsJsonObject("message");
        if (message != null) {
            finding.setMessage(message.get("text").getAsString());
        }
        
        // Extract severity
        String level = result.get("level").getAsString();
        finding.setSeverity(mapSarifLevel(level));
        
        // Extract location
        JsonArray locations = result.getAsJsonArray("locations");
        if (locations != null && locations.size() > 0) {
            JsonObject location = locations.get(0).getAsJsonObject();
            JsonObject physicalLocation = location.getAsJsonObject("physicalLocation");
            
            if (physicalLocation != null) {
                JsonObject artifactLocation = physicalLocation.getAsJsonObject("artifactLocation");
                if (artifactLocation != null) {
                    finding.setFilePath(artifactLocation.get("uri").getAsString());
                }
                
                JsonObject region = physicalLocation.getAsJsonObject("region");
                if (region != null) {
                    finding.setLineStart(region.get("startLine").getAsInt());
                    finding.setLineEnd(region.has("endLine") ? 
                        region.get("endLine").getAsInt() : finding.getLineStart());
                }
            }
        }
        
        // Extract rule ID and category
        String ruleId = result.get("ruleId").getAsString();
        finding.setRuleId(ruleId);
        finding.setCategory(extractCategory(ruleId));
        
        return finding;
    }

    private String mapSarifLevel(String level) {
        return switch (level.toLowerCase()) {
            case "error" -> "critical";
            case "warning" -> "high";
            case "note" -> "medium";
            default -> "info";
        };
    }

    private String extractCategory(String ruleId) {
        if (ruleId.contains("security")) return "security";
        if (ruleId.contains("performance")) return "performance";
        if (ruleId.contains("complexity")) return "complexity";
        if (ruleId.contains("type")) return "type";
        return "quality";
    }
}

