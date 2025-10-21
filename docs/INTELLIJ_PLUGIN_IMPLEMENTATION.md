# IntelliJ/JetBrains Plugin Implementation Guide

## Overview

This document provides a comprehensive guide for the Reviewr IntelliJ/JetBrains plugin implementation. The plugin brings AI-powered code review directly into IntelliJ IDEA, PyCharm, WebStorm, GoLand, and other JetBrains IDEs.

## Architecture

### Core Components

1. **ReviewrService** - Main service for running analysis
2. **ReviewrAnnotator** - External annotator for real-time analysis
3. **ReviewrInspection** - Local inspection for on-demand analysis
4. **ReviewrToolWindow** - Tool window for viewing results
5. **ReviewrSettings** - Configuration and settings management
6. **ApplyReviewrFixIntention** - Quick fix actions

### Plugin Structure

```
intellij-plugin/
├── build.gradle.kts                    # Gradle build configuration
├── src/main/
│   ├── java/com/reviewr/intellij/
│   │   ├── ReviewrService.java         # Core analysis service ✅
│   │   ├── model/
│   │   │   ├── ReviewFinding.java      # Finding data model
│   │   │   └── AnalysisResult.java     # Analysis result model
│   │   ├── annotator/
│   │   │   └── ReviewrAnnotator.java   # Real-time annotator
│   │   ├── inspection/
│   │   │   └── ReviewrInspection.java  # On-demand inspection
│   │   ├── intention/
│   │   │   └── ApplyReviewrFixIntention.java  # Quick fixes
│   │   ├── toolwindow/
│   │   │   ├── ReviewrToolWindowFactory.java
│   │   │   └── ReviewrToolWindowPanel.java
│   │   ├── settings/
│   │   │   ├── ReviewrSettings.java
│   │   │   └── ReviewrConfigurable.java
│   │   ├── action/
│   │   │   ├── AnalyzeFileAction.java
│   │   │   ├── AnalyzeProjectAction.java
│   │   │   ├── ClearCacheAction.java
│   │   │   └── OpenSettingsAction.java
│   │   └── listener/
│   │       ├── ReviewrFileEditorListener.java
│   │       └── ReviewrProjectListener.java
│   └── resources/
│       ├── META-INF/
│       │   └── plugin.xml              # Plugin configuration ✅
│       └── icons/
│           └── reviewr.svg             # Plugin icon
└── README.md
```

## Implementation Status

### ✅ Completed Components

1. **build.gradle.kts** - Gradle build configuration with IntelliJ plugin setup
2. **plugin.xml** - Complete plugin descriptor with all extensions and actions
3. **ReviewrService.java** - Core service for running reviewr CLI and parsing SARIF output

### 📝 Remaining Components (Implementation Templates)

#### 1. ReviewFinding.java

```java
package com.reviewr.intellij.model;

public class ReviewFinding {
    private String filePath;
    private int lineStart;
    private int lineEnd;
    private String severity;
    private String category;
    private String message;
    private String ruleId;
    private String suggestion;
    
    // Getters and setters
    // Constructor
    // toString, equals, hashCode
}
```

#### 2. ReviewrAnnotator.java

```java
package com.reviewr.intellij.annotator;

import com.intellij.lang.annotation.*;
import com.intellij.openapi.editor.Editor;
import com.intellij.psi.PsiFile;
import com.reviewr.intellij.ReviewrService;
import com.reviewr.intellij.model.ReviewFinding;

public class ReviewrAnnotator extends ExternalAnnotator<PsiFile, List<ReviewFinding>> {
    
    @Override
    public PsiFile collectInformation(@NotNull PsiFile file) {
        return file;
    }
    
    @Override
    public List<ReviewFinding> doAnnotate(PsiFile file) {
        // Run analysis asynchronously
        return ReviewrService.getInstance()
            .analyzeFile(file.getProject(), file.getVirtualFile())
            .join();
    }
    
    @Override
    public void apply(@NotNull PsiFile file, List<ReviewFinding> findings, 
                      @NotNull AnnotationHolder holder) {
        for (ReviewFinding finding : findings) {
            // Create annotation based on severity
            HighlightSeverity severity = mapSeverity(finding.getSeverity());
            holder.newAnnotation(severity, finding.getMessage())
                .range(/* calculate range from line numbers */)
                .withFix(new ApplyReviewrFixIntention(finding))
                .create();
        }
    }
}
```

#### 3. ReviewrInspection.java

```java
package com.reviewr.intellij.inspection;

import com.intellij.codeInspection.*;
import com.intellij.psi.PsiFile;
import com.reviewr.intellij.ReviewrService;

public class ReviewrInspection extends LocalInspectionTool {
    
    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, 
                                         @NotNull InspectionManager manager, 
                                         boolean isOnTheFly) {
        List<ReviewFinding> findings = ReviewrService.getInstance()
            .analyzeFile(file.getProject(), file.getVirtualFile())
            .join();
        
        List<ProblemDescriptor> problems = new ArrayList<>();
        for (ReviewFinding finding : findings) {
            ProblemDescriptor problem = manager.createProblemDescriptor(
                /* element */,
                finding.getMessage(),
                new ApplyReviewrFixIntention(finding),
                mapSeverity(finding.getSeverity()),
                isOnTheFly
            );
            problems.add(problem);
        }
        
        return problems.toArray(new ProblemDescriptor[0]);
    }
}
```

#### 4. ApplyReviewrFixIntention.java

```java
package com.reviewr.intellij.intention;

import com.intellij.codeInsight.intention.IntentionAction;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiFile;
import com.reviewr.intellij.model.ReviewFinding;

public class ApplyReviewrFixIntention implements IntentionAction {
    private final ReviewFinding finding;
    
    public ApplyReviewrFixIntention(ReviewFinding finding) {
        this.finding = finding;
    }
    
    @Override
    public String getText() {
        return "Apply Reviewr fix: " + finding.getSuggestion();
    }
    
    @Override
    public void invoke(@NotNull Project project, Editor editor, PsiFile file) {
        // Apply the fix using reviewr autofix command
        // Or apply the suggestion directly
    }
}
```

#### 5. ReviewrToolWindowFactory.java

```java
package com.reviewr.intellij.toolwindow;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.wm.*;
import com.intellij.ui.content.*;

public class ReviewrToolWindowFactory implements ToolWindowFactory {
    
    @Override
    public void createToolWindowContent(@NotNull Project project, 
                                       @NotNull ToolWindow toolWindow) {
        ReviewrToolWindowPanel panel = new ReviewrToolWindowPanel(project);
        Content content = ContentFactory.SERVICE.getInstance()
            .createContent(panel, "", false);
        toolWindow.getContentManager().addContent(content);
    }
}
```

#### 6. ReviewrSettings.java

```java
package com.reviewr.intellij.settings;

import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.components.*;

@State(name = "ReviewrSettings", storages = @Storage("reviewr.xml"))
public class ReviewrSettings implements PersistentStateComponent<ReviewrSettings.State> {
    
    public static class State {
        public boolean enabled = true;
        public String reviewrPath = "";
        public boolean securityAnalysis = true;
        public boolean performanceAnalysis = true;
        public boolean realTimeAnalysis = true;
        public int analysisDelay = 1000; // ms
    }
    
    private State state = new State();
    
    public static ReviewrSettings getInstance() {
        return ApplicationManager.getApplication()
            .getService(ReviewrSettings.class);
    }
    
    @Override
    public State getState() {
        return state;
    }
    
    @Override
    public void loadState(@NotNull State state) {
        this.state = state;
    }
    
    // Getters and setters
}
```

## Building and Testing

### Build the Plugin

```bash
cd intellij-plugin
./gradlew buildPlugin
```

The plugin will be built to `build/distributions/reviewr-1.0.0.zip`.

### Run in IDE

```bash
./gradlew runIde
```

This launches a new IntelliJ IDEA instance with the plugin installed.

### Test the Plugin

```bash
./gradlew test
```

### Publish to JetBrains Marketplace

```bash
export PUBLISH_TOKEN="your-token"
./gradlew publishPlugin
```

## Features

### Real-Time Analysis
- External annotator runs on file save/edit
- Configurable delay to avoid excessive analysis
- Inline warnings and errors in editor

### On-Demand Analysis
- Analyze current file: `Ctrl+Alt+R`
- Analyze entire project: Tools → Reviewr → Analyze Entire Project
- Context menu: Right-click → Analyze with Reviewr

### Quick Fixes
- Apply suggested fixes with Alt+Enter
- Preview changes before applying
- Undo support

### Tool Window
- View all findings in project
- Filter by severity, category, file
- Navigate to finding location
- Export results

### Settings
- Enable/disable real-time analysis
- Configure reviewr CLI path
- Enable/disable specific analyzers
- Set analysis delay

## Integration with Reviewr CLI

The plugin executes the reviewr CLI with the following command:

```bash
python3 -m reviewr review <file> --format sarif --local-only
```

Options:
- `--local-only`: Use local analyzers only (faster, no API calls)
- `--enable-security`: Enable security analysis
- `--enable-performance`: Enable performance analysis
- `--format sarif`: Output in SARIF format for parsing

## Next Steps

1. **Complete remaining Java classes** - Implement all components listed above
2. **Add icons** - Create SVG icons for the plugin
3. **Write tests** - Create unit and integration tests
4. **Build and test** - Test in IntelliJ IDEA, PyCharm, WebStorm
5. **Documentation** - Create user guide and screenshots
6. **Publish** - Submit to JetBrains Marketplace

## Resources

- [IntelliJ Platform SDK](https://plugins.jetbrains.com/docs/intellij/welcome.html)
- [Plugin Development Guidelines](https://plugins.jetbrains.com/docs/intellij/plugin-development-guidelines.html)
- [IntelliJ Platform Explorer](https://plugins.jetbrains.com/intellij-platform-explorer/)

