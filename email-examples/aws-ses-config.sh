#!/bin/bash

# AWS SES Configuration for reviewr Email Integration

# ============================================================================
# AWS SES Setup
# ============================================================================
# 1. Sign up for AWS: https://aws.amazon.com/
# 2. Go to SES console: https://console.aws.amazon.com/ses/
# 3. Verify email address or domain
# 4. Create IAM user with SES permissions
# 5. Generate access keys
# 6. Request production access (to send to any email)

export EMAIL_FROM='your-email@example.com'
export EMAIL_FROM_NAME='Code Review Bot'
export EMAIL_PROVIDER='aws_ses'
export AWS_REGION='us-east-1'
export AWS_ACCESS_KEY_ID='your-access-key-id'
export AWS_SECRET_ACCESS_KEY='your-secret-access-key'

# Test the configuration
# reviewr email test --to test-recipient@example.com

# ============================================================================
# IAM Policy for SES
# ============================================================================
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": [
#         "ses:SendEmail",
#         "ses:SendRawEmail"
#       ],
#       "Resource": "*"
#     }
#   ]
# }

# ============================================================================
# Usage Examples
# ============================================================================

# Send review results
# reviewr . --output review-results.json
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider aws_ses \
#   --project-name "My Project"

# Send only critical findings
# reviewr email send review-results.json \
#   --to security@example.com \
#   --provider aws_ses \
#   --critical-only \
#   --project-name "My Project"

# Send to multiple recipients with CC
# reviewr email send review-results.json \
#   --to developer1@example.com \
#   --to developer2@example.com \
#   --cc manager@example.com \
#   --provider aws_ses \
#   --project-name "My Project"

# Include repository URL
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider aws_ses \
#   --project-name "My Project" \
#   --repository-url "https://github.com/myorg/myapp"

# Attach JSON file
# reviewr email send review-results.json \
#   --to team@example.com \
#   --provider aws_ses \
#   --attach-json \
#   --project-name "My Project"

# ============================================================================
# CI/CD Integration Examples
# ============================================================================

# GitHub Actions
# - name: Send email report
#   env:
#     EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
#     AWS_REGION: ${{ secrets.AWS_REGION }}
#     AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
#     AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
#   run: |
#     reviewr email send review-results.json \
#       --to team@example.com \
#       --provider aws_ses \
#       --project-name "${{ github.repository }}"

# GitLab CI
# code_review:
#   script:
#     - reviewr . --output review-results.json
#     - reviewr email send review-results.json --to team@example.com --provider aws_ses
#   variables:
#     EMAIL_FROM: $EMAIL_FROM
#     AWS_REGION: $AWS_REGION
#     AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
#     AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY

# ============================================================================
# AWS Regions
# ============================================================================
# US East (N. Virginia): us-east-1
# US East (Ohio): us-east-2
# US West (Oregon): us-west-2
# Europe (Ireland): eu-west-1
# Europe (Frankfurt): eu-central-1
# Asia Pacific (Tokyo): ap-northeast-1
# Asia Pacific (Sydney): ap-southeast-2

# ============================================================================
# AWS SES Features
# ============================================================================
# - High deliverability rates
# - Scalable infrastructure
# - Dedicated IP addresses
# - Email receiving
# - Bounce and complaint handling
# - Reputation dashboard
# - Configuration sets

# ============================================================================
# Pricing (as of 2024)
# ============================================================================
# First 62,000 emails/month: Free (when sent from EC2)
# Additional emails: $0.10 per 1,000 emails
# Dedicated IP: $24.95/month per IP
# Data transfer: Standard AWS rates

# ============================================================================
# Sandbox vs Production
# ============================================================================
# Sandbox Mode (default):
# - Can only send to verified email addresses
# - Limited to 200 emails/day
# - Maximum send rate of 1 email/second
#
# Production Mode (requires request):
# - Can send to any email address
# - Higher sending limits (based on reputation)
# - Higher send rate

# To request production access:
# 1. Go to SES console
# 2. Click "Request Production Access"
# 3. Fill out the form with your use case
# 4. Wait for approval (usually 24 hours)

