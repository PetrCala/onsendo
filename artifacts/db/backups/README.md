# Database Backups

This directory contains timestamped backups of the Onsendo database.

## Backup Files

Each backup consists of:

- `onsen_backup_YYYYMMDD_HHMMSS.db` - SQLite database backup
- `onsen_backup_YYYYMMDD_HHMMSS.db.sha256` - SHA-256 checksum for integrity verification

## Usage

### Create a Backup

```bash
# Create local backup
make backup

# Create backup and sync to Google Drive
make backup-full
```

### List Backups

```bash
# List local backups
make backup-list

# List cloud backups
make backup-cloud-list
```

### Restore from Backup

```bash
# Interactive restore
make backup-restore

# Manual restore
cp onsen_backup_20251010_120000.db ../../data/db/onsen.db
```

### Verify Backup Integrity

```bash
# Verify latest backup
make backup-verify

# Manual verification
shasum -a 256 -c onsen_backup_20251010_120000.db.sha256
```

### Cleanup Old Backups

```bash
# Keep 50 most recent (default)
make backup-cleanup

# Keep 100 most recent
make backup-cleanup KEEP_BACKUPS=100
```

## Retention Policy

- **Default retention**: 50 most recent backups
- **Automatic cleanup**: Run `make backup-auto` for scheduled backups with cleanup
- **Cloud backups**: All backups are synced to Google Drive (incremental)

## Best Practices

1. **Backup before major operations**:
   - Before database migrations
   - Before bulk data imports
   - Before running cleanup/deletion commands

2. **Regular backups**:
   - Set up a cron job with `make backup-auto`
   - Cloud backups ensure off-site redundancy

3. **Verify backups periodically**:
   - Run `make backup-verify` weekly
   - Test restore process occasionally

4. **Security**:
   - Backups contain personal data (visits, heart rate)
   - Keep local backups secure (permissions: 600)
   - Google Drive provides encrypted storage

## Automated Backups

### Cron Job Example

```bash
# Daily backup at 2 AM with cleanup and cloud sync
0 2 * * * cd /path/to/onsendo && make backup-auto >> logs/backup.log 2>&1
```

### Manual Automation Script

```bash
#!/bin/bash
# backup_daily.sh

cd /path/to/onsendo
source .venv/bin/activate

make backup
make backup-cleanup KEEP_BACKUPS=50
make backup-cloud || echo "Cloud sync failed, backup still saved locally"
```

## Troubleshooting

### Backup Failed

Check database integrity:

```bash
sqlite3 data/db/onsen.db "PRAGMA integrity_check;"
```

### Cloud Sync Failed

Re-authenticate with Google Drive:

```bash
rm local/gdrive/token.json
make backup-cloud
```

### Out of Disk Space

Clean up old backups:

```bash
make backup-cleanup KEEP_BACKUPS=10
```

### Corrupted Backup

Verify checksums of all backups:

```bash
for f in artifacts/db/backups/*.db; do
    shasum -a 256 -c "$f.sha256" 2>/dev/null || echo "FAILED: $f"
done
```

## Recovery Scenarios

### Scenario 1: Accidental Data Deletion

```bash
# Find backup from before deletion
make backup-list

# Restore
make backup-restore
# Select the backup timestamp before deletion
```

### Scenario 2: Database Corruption

```bash
# Restore from latest verified backup
make backup-verify
make backup-restore
```

### Scenario 3: System Failure

```bash
# Restore from Google Drive
make backup-cloud-list

# Download manually or restore token and sync
make backup-cloud
```

## File Structure

```
artifacts/db/backups/
├── README.md                              # This file
├── onsen_backup_20251010_120000.db        # Backup database
├── onsen_backup_20251010_120000.db.sha256 # Checksum
├── onsen_backup_20251010_140000.db
├── onsen_backup_20251010_140000.db.sha256
└── ...
```

## Notes

- Backups are **not committed to git** (see `.gitignore`)
- Each backup is a complete copy of the database
- Timestamps are in local timezone
- SHA-256 ensures data integrity during storage/transfer
- Google Drive provides version history for additional safety
