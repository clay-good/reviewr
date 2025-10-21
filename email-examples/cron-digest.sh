#!/bin/bash

# Scheduled Email Digest Script for reviewr
# This script can be run via cron for daily/weekly digest reports

# ============================================================================
# Configuration
# ============================================================================

# Email settings (set these in your environment or uncomment and set here)
# export EMAIL_FROM='your-email@example.com'
# export SMTP_HOST='smtp.gmail.com'
# export SMTP_PORT='587'
# export SMTP_USERNAME='your-email@gmail.com'
# export SMTP_PASSWORD='your-app-password'

# Recipients
TEAM_EMAIL='team@example.com'
MANAGER_EMAIL='manager@example.com'

# Projects to review
PROJECTS=(
    "/path/to/project1:Project 1:https://github.com/org/project1"
    "/path/to/project2:Project 2:https://github.com/org/project2"
    "/path/to/project3:Project 3:https://github.com/org/project3"
)

# Temporary directory for results
TEMP_DIR="/tmp/reviewr-digest-$(date +%Y%m%d)"
mkdir -p "$TEMP_DIR"

# ============================================================================
# Functions
# ============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

review_project() {
    local project_path="$1"
    local project_name="$2"
    local repo_url="$3"
    local output_file="$TEMP_DIR/$(echo "$project_name" | tr ' ' '_').json"
    
    log "Reviewing $project_name..."
    
    cd "$project_path" || return 1
    
    # Pull latest changes
    if [ -d ".git" ]; then
        git pull --quiet
    fi
    
    # Run review
    reviewr . --output "$output_file" --format json
    
    if [ $? -eq 0 ]; then
        log "✓ Review completed for $project_name"
        echo "$output_file:$project_name:$repo_url"
    else
        log "✗ Review failed for $project_name"
        return 1
    fi
}

send_digest() {
    local results=("$@")
    
    log "Sending digest email..."
    
    for result in "${results[@]}"; do
        IFS=':' read -r output_file project_name repo_url <<< "$result"
        
        if [ -f "$output_file" ]; then
            reviewr email send "$output_file" \
                --to "$TEAM_EMAIL" \
                --cc "$MANAGER_EMAIL" \
                --project-name "$project_name" \
                --repository-url "$repo_url" \
                --attach-json
            
            if [ $? -eq 0 ]; then
                log "✓ Email sent for $project_name"
            else
                log "✗ Email failed for $project_name"
            fi
        fi
    done
}

send_critical_alerts() {
    local results=("$@")
    
    log "Checking for critical issues..."
    
    for result in "${results[@]}"; do
        IFS=':' read -r output_file project_name repo_url <<< "$result"
        
        if [ -f "$output_file" ]; then
            # Check if there are critical issues
            critical_count=$(jq '[.findings[] | select(.severity == "critical")] | length' "$output_file")
            
            if [ "$critical_count" -gt 0 ]; then
                log "⚠️  Found $critical_count critical issues in $project_name"
                
                reviewr email send "$output_file" \
                    --to "$TEAM_EMAIL" \
                    --critical-only \
                    --project-name "$project_name - CRITICAL ALERT" \
                    --repository-url "$repo_url"
                
                if [ $? -eq 0 ]; then
                    log "✓ Critical alert sent for $project_name"
                else
                    log "✗ Critical alert failed for $project_name"
                fi
            fi
        fi
    done
}

cleanup() {
    log "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}

# ============================================================================
# Main Script
# ============================================================================

log "Starting reviewr digest generation"

# Review all projects
results=()
for project in "${PROJECTS[@]}"; do
    IFS=':' read -r path name url <<< "$project"
    result=$(review_project "$path" "$name" "$url")
    if [ $? -eq 0 ]; then
        results+=("$result")
    fi
done

# Send critical alerts first
send_critical_alerts "${results[@]}"

# Send digest emails
send_digest "${results[@]}"

# Cleanup
cleanup

log "Digest generation completed"

# ============================================================================
# Crontab Examples
# ============================================================================

# Daily digest at 9 AM
# 0 9 * * * /path/to/cron-digest.sh >> /var/log/reviewr-digest.log 2>&1

# Weekly digest on Monday at 9 AM
# 0 9 * * 1 /path/to/cron-digest.sh >> /var/log/reviewr-digest.log 2>&1

# Twice daily (9 AM and 5 PM)
# 0 9,17 * * * /path/to/cron-digest.sh >> /var/log/reviewr-digest.log 2>&1

# Every 6 hours
# 0 */6 * * * /path/to/cron-digest.sh >> /var/log/reviewr-digest.log 2>&1

# ============================================================================
# Installation Instructions
# ============================================================================

# 1. Copy this script to a suitable location:
#    sudo cp cron-digest.sh /usr/local/bin/reviewr-digest
#    sudo chmod +x /usr/local/bin/reviewr-digest

# 2. Edit the script to set your configuration:
#    sudo nano /usr/local/bin/reviewr-digest

# 3. Test the script manually:
#    /usr/local/bin/reviewr-digest

# 4. Add to crontab:
#    crontab -e
#    # Add one of the crontab examples above

# 5. View cron logs:
#    tail -f /var/log/reviewr-digest.log

# ============================================================================
# Advanced Configuration
# ============================================================================

# Use different presets for different projects
# reviewr . --preset strict --output "$output_file"  # For production code
# reviewr . --preset quick --output "$output_file"   # For development code

# Filter by severity
# reviewr email send "$output_file" --critical-only  # Only critical issues

# Multiple recipients
# reviewr email send "$output_file" \
#   --to team@example.com \
#   --to lead@example.com \
#   --cc manager@example.com \
#   --bcc director@example.com

# Different email providers
# reviewr email send "$output_file" --provider sendgrid  # Use SendGrid
# reviewr email send "$output_file" --provider aws_ses   # Use AWS SES

# ============================================================================
# Monitoring and Alerting
# ============================================================================

# Send notification if script fails
# trap 'echo "reviewr digest failed" | mail -s "reviewr Digest Error" admin@example.com' ERR

# Log rotation (add to /etc/logrotate.d/reviewr-digest)
# /var/log/reviewr-digest.log {
#     daily
#     rotate 7
#     compress
#     delaycompress
#     missingok
#     notifempty
# }

