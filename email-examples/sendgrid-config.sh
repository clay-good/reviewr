#!/bin/bash

# SendGrid Configuration for reviewr Email Integration

# ============================================================================
# SendGrid Setup
# ============================================================================
# 1. Sign up for SendGrid: https://signup.sendgrid.com/
# 2. Create API key: https://app.sendgrid.com/settings/api_keys
# 3. Verify sender email: https://app.sendgrid.com/settings/sender_auth
# 4. Use the API key below

export EMAIL_FROM='your-email@example.com'
export EMAIL_FROM_NAME='Code Review Bot'
export EMAIL_PROVIDER='sendgrid'
export SENDGRID_API_KEY='your-sendgrid-api-key'

# Test the configuration
# reviewr email test --to test-recipient@example.com

# ============================================================================
# Usage Examples
# ============================================================================

# Send review results
# reviewr . --output review-results.json
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider sendgrid \
#   --project-name "My Project"

# Send only critical findings
# reviewr email send review-results.json \
#   --to security@example.com \
#   --provider sendgrid \
#   --critical-only \
#   --project-name "My Project"

# Send to multiple recipients with CC
# reviewr email send review-results.json \
#   --to developer1@example.com \
#   --to developer2@example.com \
#   --cc manager@example.com \
#   --provider sendgrid \
#   --project-name "My Project"

# Include repository URL
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider sendgrid \
#   --project-name "My Project" \
#   --repository-url "https://github.com/myorg/myapp"

# Attach JSON file
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider sendgrid \
#   --attach-json \
#   --project-name "My Project"

# ============================================================================
# CI/CD Integration Examples
# ============================================================================

# GitHub Actions
# - name: Send email report
#   env:
#     EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
#     SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
#   run: |
#     reviewr email send review-results.json \
#       --to team@example.com \
#       --provider sendgrid \
#       --project-name "${{ github.repository }}"

# GitLab CI
# code_review:
#   script:
#     - reviewr . --output review-results.json
#     - reviewr email send review-results.json --to team@example.com --provider sendgrid
#   variables:
#     EMAIL_FROM: $EMAIL_FROM
#     SENDGRID_API_KEY: $SENDGRID_API_KEY

# ============================================================================
# SendGrid Features
# ============================================================================
# - High deliverability rates
# - Advanced analytics
# - Template management
# - Webhook events
# - IP reputation management
# - Dedicated IP addresses (paid plans)

# ============================================================================
# Pricing (as of 2024)
# ============================================================================
# Free: 100 emails/day
# Essentials: $19.95/month (50,000 emails/month)
# Pro: $89.95/month (100,000 emails/month)
# Premier: Custom pricing

