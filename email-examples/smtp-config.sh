#!/bin/bash

# SMTP Configuration Examples for reviewr Email Integration

# ============================================================================
# Gmail Configuration
# ============================================================================
# Note: You must use an App Password, not your regular Gmail password
# 1. Go to https://myaccount.google.com/apppasswords
# 2. Generate an app password
# 3. Use the generated password below

export EMAIL_FROM='your-email@gmail.com'
export SMTP_HOST='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USERNAME='your-email@gmail.com'
export SMTP_PASSWORD='your-app-password'
export SMTP_USE_TLS='true'

# Test the configuration
# reviewr email test --to test-recipient@example.com

# ============================================================================
# Outlook/Office 365 Configuration
# ============================================================================

# export EMAIL_FROM='your-email@outlook.com'
# export SMTP_HOST='smtp.office365.com'
# export SMTP_PORT='587'
# export SMTP_USERNAME='your-email@outlook.com'
# export SMTP_PASSWORD='your-password'
# export SMTP_USE_TLS='true'

# ============================================================================
# Yahoo Mail Configuration
# ============================================================================

# export EMAIL_FROM='your-email@yahoo.com'
# export SMTP_HOST='smtp.mail.yahoo.com'
# export SMTP_PORT='587'
# export SMTP_USERNAME='your-email@yahoo.com'
# export SMTP_PASSWORD='your-app-password'
# export SMTP_USE_TLS='true'

# ============================================================================
# Custom SMTP Server Configuration
# ============================================================================

# export EMAIL_FROM='your-email@example.com'
# export SMTP_HOST='smtp.example.com'
# export SMTP_PORT='587'
# export SMTP_USERNAME='your-username'
# export SMTP_PASSWORD='your-password'
# export SMTP_USE_TLS='true'

# ============================================================================
# Usage Examples
# ============================================================================

# Send review results
# reviewr . --output review-results.json
# reviewr email send review-results.json \
#   --to team@example.com \
#   --project-name "My Project"

# Send only critical findings
# reviewr email send review-results.json \
#   --to security@example.com \
#   --critical-only \
#   --project-name "My Project"

# Send to multiple recipients with CC
# reviewr email send review-results.json \
#   --to developer1@example.com \
#   --to developer2@example.com \
#   --cc manager@example.com \
#   --project-name "My Project"

# Include repository URL
# reviewr email send review-results.json \
#   --to team@example.com \
#   --project-name "My Project" \
#   --repository-url "https://github.com/myorg/myapp"

# Attach JSON file
# reviewr email send review-results.json \
#   --to team@example.com \
#   --attach-json \
#   --project-name "My Project"

