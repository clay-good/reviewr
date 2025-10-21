# Jenkins Integration

Comprehensive guide for integrating **reviewr** with Jenkins for automated code reviews in CI/CD pipelines.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Pipeline Integration](#pipeline-integration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The Jenkins integration enables **reviewr** to:
- Run automated code reviews in Jenkins pipelines
- Update build descriptions with review summaries
- Add badges to builds based on review results
- Publish review reports as artifacts
- Integrate with both declarative and scripted pipelines

## Features

### ✅ Build Integration
- **Build Description**: Automatically update build description with review summary
- **Build Badges**: Add colored badges based on review results
- **Artifact Publishing**: Publish review reports as Jenkins artifacts

### ✅ Pipeline Support
- **Declarative Pipelines**: Full support for declarative pipeline syntax
- **Scripted Pipelines**: Full support for scripted pipeline syntax
- **Parallel Execution**: Run multiple review types in parallel
- **Conditional Execution**: Different presets for different branches

### ✅ Credentials Management
- **Jenkins Credentials**: Use Jenkins credentials for secure storage
- **Environment Variables**: Configure via environment variables
- **API Token Authentication**: Secure authentication with API tokens

### ✅ Reporting
- **HTML Summaries**: Rich HTML formatting in build descriptions
- **JSON Reports**: Detailed JSON reports as artifacts
- **SARIF Format**: SARIF reports for tool integration

## Quick Start

### 1. Create Jenkins API Token

1. Go to `{JENKINS_URL}/user/{username}/configure`
2. Click **Add new Token** under **API Token**
3. Give it a name (e.g., `reviewr`)
4. Click **Generate**
5. Copy the token

### 2. Configure Jenkins Credentials

Add these credentials in Jenkins:
- `jenkins-url`: Jenkins URL (e.g., `https://jenkins.example.com`)
- `jenkins-username`: Your Jenkins username
- `jenkins-api-token`: Your API token
- `openai-api-key`: Your OpenAI API key (or other AI provider)

### 3. Create Jenkinsfile

Create a `Jenkinsfile` in your repository:

```groovy
pipeline {
    agent any
    
    environment {
        JENKINS_URL = credentials('jenkins-url')
        JENKINS_USERNAME = credentials('jenkins-username')
        JENKINS_API_TOKEN = credentials('jenkins-api-token')
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install reviewr') {
            steps {
                sh 'pip install reviewr'
            }
        }
        
        stage('Code Review') {
            steps {
                sh 'reviewr jenkins review'
            }
        }
    }
}
```

### 4. Create Jenkins Pipeline Job

1. Create a new **Pipeline** job in Jenkins
2. Configure **Pipeline** section:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL
   - **Script Path**: Jenkinsfile
3. Save and run the job

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JENKINS_URL` | Jenkins URL | Yes |
| `JENKINS_USERNAME` | Jenkins username | Yes* |
| `JENKINS_API_TOKEN` | Jenkins API token | Yes* |
| `JOB_NAME` | Job name (auto-set by Jenkins) | No |
| `BUILD_NUMBER` | Build number (auto-set by Jenkins) | No |

*Required for authentication

### Jenkins Environment Variables

Jenkins automatically sets these variables:
- `JOB_NAME`: Current job name
- `BUILD_NUMBER`: Current build number
- `BUILD_URL`: Current build URL
- `WORKSPACE`: Workspace directory

## CLI Commands

### `reviewr jenkins review`

Review code and update Jenkins build.

```bash
reviewr jenkins review [OPTIONS] [PATH]
```

**Options:**
- `--url TEXT`: Jenkins URL (defaults to JENKINS_URL env var)
- `--username TEXT`: Jenkins username (defaults to JENKINS_USERNAME env var)
- `--api-token TEXT`: Jenkins API token (defaults to JENKINS_API_TOKEN env var)
- `--job-name TEXT`: Job name (defaults to JOB_NAME env var)
- `--build-number INTEGER`: Build number (defaults to BUILD_NUMBER env var)
- `--output TEXT`: Output file for review report (JSON)
- `--no-description`: Skip setting build description
- `--no-badge`: Skip adding badge

**Examples:**

```bash
# Review current build (auto-detected from Jenkins environment)
reviewr jenkins review

# Review specific build
reviewr jenkins review --job-name my-job --build-number 123

# Review and save report
reviewr jenkins review --output review-report.json

# Review without updating build
reviewr jenkins review --no-description --no-badge
```

### `reviewr jenkins setup`

Set up Jenkins integration and test connection.

```bash
reviewr jenkins setup [OPTIONS]
```

**Options:**
- `--url TEXT`: Jenkins URL
- `--username TEXT`: Jenkins username
- `--api-token TEXT`: Jenkins API token

**Example:**

```bash
reviewr jenkins setup \
  --url https://jenkins.example.com \
  --username admin \
  --api-token YOUR_TOKEN
```

### `reviewr jenkins set-description`

Set build description.

```bash
reviewr jenkins set-description [OPTIONS] DESCRIPTION
```

**Options:**
- `--url TEXT`: Jenkins URL
- `--username TEXT`: Jenkins username
- `--api-token TEXT`: Jenkins API token
- `--job-name TEXT`: Job name
- `--build-number INTEGER`: Build number

**Examples:**

```bash
# Set simple description
reviewr jenkins set-description "Code review passed"

# Set HTML description
reviewr jenkins set-description "<strong>Review:</strong> 5 issues found"
```

### `reviewr jenkins add-badge`

Add a badge to the build.

```bash
reviewr jenkins add-badge [OPTIONS] TEXT
```

**Options:**
- `--url TEXT`: Jenkins URL
- `--username TEXT`: Jenkins username
- `--api-token TEXT`: Jenkins API token
- `--job-name TEXT`: Job name
- `--build-number INTEGER`: Build number
- `--color CHOICE`: Badge color (blue, green, yellow, red)

**Examples:**

```bash
# Add green badge
reviewr jenkins add-badge "Review: Passed" --color green

# Add red badge
reviewr jenkins add-badge "Review: Issues Found" --color red
```

## Pipeline Integration

### Declarative Pipeline

#### Basic Configuration

```groovy
pipeline {
    agent any
    
    environment {
        JENKINS_URL = credentials('jenkins-url')
        JENKINS_USERNAME = credentials('jenkins-username')
        JENKINS_API_TOKEN = credentials('jenkins-api-token')
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install reviewr') {
            steps {
                sh 'pip install reviewr'
            }
        }
        
        stage('Code Review') {
            steps {
                sh 'reviewr jenkins review --output review-report.json'
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'review-report.json', fingerprint: true
            }
        }
    }
}
```

#### Advanced Configuration

```groovy
pipeline {
    agent any
    
    environment {
        JENKINS_URL = credentials('jenkins-url')
        JENKINS_USERNAME = credentials('jenkins-username')
        JENKINS_API_TOKEN = credentials('jenkins-api-token')
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install reviewr') {
            steps {
                sh 'pip install reviewr'
            }
        }
        
        stage('Security Review') {
            steps {
                sh '''
                    reviewr . \
                        --review-type security \
                        --security-scan \
                        --check-vulnerabilities \
                        --check-licenses \
                        --output security-report.json
                '''
            }
        }
        
        stage('Code Quality Review') {
            steps {
                sh '''
                    reviewr jenkins review \
                        --review-type correctness maintainability \
                        --code-metrics \
                        --check-complexity \
                        --check-duplication
                '''
            }
        }
    }
}
```

#### Conditional Execution

```groovy
pipeline {
    agent any
    
    environment {
        JENKINS_URL = credentials('jenkins-url')
        JENKINS_USERNAME = credentials('jenkins-username')
        JENKINS_API_TOKEN = credentials('jenkins-api-token')
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install reviewr') {
            steps {
                sh 'pip install reviewr'
            }
        }
        
        stage('Quick Review') {
            when {
                not {
                    branch 'main'
                }
            }
            steps {
                sh 'reviewr jenkins review --preset quick'
            }
        }
        
        stage('Strict Review') {
            when {
                branch 'main'
            }
            steps {
                sh 'reviewr jenkins review --preset strict'
            }
        }
    }
}
```

### Scripted Pipeline

#### Basic Configuration

```groovy
node {
    env.JENKINS_URL = credentials('jenkins-url')
    env.JENKINS_USERNAME = credentials('jenkins-username')
    env.JENKINS_API_TOKEN = credentials('jenkins-api-token')
    env.OPENAI_API_KEY = credentials('openai-api-key')
    
    try {
        stage('Checkout') {
            checkout scm
        }
        
        stage('Install reviewr') {
            sh 'pip install reviewr'
        }
        
        stage('Code Review') {
            sh 'reviewr jenkins review'
        }
        
        currentBuild.result = 'SUCCESS'
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        cleanWs()
    }
}
```

## Advanced Usage

### Multiple Review Types

```bash
# Security-focused review
reviewr jenkins review \
  --review-type security \
  --security-scan \
  --check-vulnerabilities \
  --check-licenses

# Code quality review
reviewr jenkins review \
  --review-type correctness maintainability \
  --code-metrics \
  --check-complexity \
  --check-duplication
```

### Using Presets

```bash
# Strict preset for production
reviewr jenkins review --preset strict

# Balanced preset for feature branches
reviewr jenkins review --preset balanced

# Quick preset for rapid iteration
reviewr jenkins review --preset quick
```

### Combining with Slack

```bash
reviewr jenkins review \
  --slack \
  --slack-channel '#code-reviews' \
  --slack-critical-only
```

## Troubleshooting

### Authentication Errors

**Error**: `Jenkins URL not provided`

**Solution**: Set the `JENKINS_URL` environment variable or pass `--url` option.

### Build Information Errors

**Error**: `Job name and build number are required`

**Solution**: Run inside Jenkins pipeline or provide `--job-name` and `--build-number` explicitly.

### Permission Errors

**Error**: `403 Forbidden`

**Solution**: Ensure your API token has the required permissions:
- Overall/Read
- Job/Read
- Job/Build
- Job/Configure

### Connection Errors

**Error**: `Connection refused`

**Solution**: Check that Jenkins URL is correct and accessible from the build agent.

## Best Practices

1. **Store Credentials Securely**: Use Jenkins credentials for API tokens
2. **Archive Reports**: Always archive review reports as artifacts
3. **Use Presets**: Use appropriate presets for different branches
4. **Parallel Execution**: Run multiple review types in parallel for faster builds
5. **Conditional Reviews**: Use stricter presets for production branches
6. **Slack Integration**: Notify team of critical issues immediately

## Next Steps

- [Security Scanning Guide](SECURITY_SCANNING.md)
- [Code Metrics Guide](CODE_METRICS.md)
- [Slack Integration](SLACK_INTEGRATION.md)
- [CI/CD Best Practices](CI_CD_BEST_PRACTICES.md)

