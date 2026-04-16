#!/bin/bash
# Production Backup Script for SQLite
# Run this daily via cron: 0 2 * * * /app/backup_db.sh

BACKUP_DIR="/var/backups/adaptive_learning"
DB_FILE="/app/adaptive_learning.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/adaptive_learning.db.$TIMESTAMP"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup (database stays locked only for milliseconds)
cp "$DB_FILE" "$BACKUP_FILE"

# Compress for storage
gzip "$BACKUP_FILE"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "adaptive_learning.db.*.gz" -mtime +30 -delete

# Log successful backup
echo "[$(date)] Backup completed successfully: $BACKUP_FILE.gz" >> /var/log/adaptive_learning_backup.log

# Optional: Send to cloud storage
# aws s3 cp "$BACKUP_FILE.gz" s3://my-backups/adaptive-learning/

# Optional: Send alert if backup fails (uncomment and configure)
# if [ $? -ne 0 ]; then
#     echo "Backup failed!" | mail -s "Adaptive Learning Backup Failed" admin@school.edu
# fi
