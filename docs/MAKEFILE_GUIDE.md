# Makefile Quick Start Guide

This project uses a Makefile for all common development operations. The old `run.sh` script has been removed.

## Quick Reference

```bash
make help          # Show all available commands
```

## Common Tasks

### Development

```bash
make install       # Install dependencies
make test          # Run all tests
make test-unit     # Run unit tests only (fast)
make lint          # Run pylint
make coverage      # Generate coverage report
make clean         # Clean temporary files
```

### Database

```bash
make db-init                              # Initialize new database
make db-fill DATA_FILE=data.json          # Import onsen data
make db-path                              # Show database path
```

### Backups (Critical!)

```bash
make backup                               # Create local backup
make backup-list                          # List all backups
make backup-verify                        # Verify latest backup
make backup-cleanup                       # Remove old backups (keeps 50)
make backup-restore                       # Restore from backup (interactive)
make backup-full                          # Local + cloud backup
```

### Heart Rate Data

```bash
make hr-import FILE=file.csv              # Import single file
make hr-batch DIR=directory               # Batch import
make hr-status                            # Show status
make hr-manager                           # Launch interactive manager
```

### Onsen Operations

```bash
make visit-add                            # Add visit (interactive)
make visit-list                           # List all visits
make location-add                         # Add location (interactive)
make onsen-recommend LOCATION="Home"      # Get recommendations
```

## Migration from run.sh

Old command → New command:

```bash
./run.sh lint        →  make lint
./run.sh test        →  make test-unit
./run.sh test-all    →  make test
./run.sh merge       →  Use git directly or scripts/merge_and_push.sh
```

## Custom Arguments

```bash
# Run CLI with custom arguments
make run-cli ARGS="visit list"
make run-cli ARGS="heart-rate import file.csv --format apple_health"

# Customize backup retention
make backup-cleanup KEEP_BACKUPS=100

# Heart rate with options
make hr-import FILE=data.csv FORMAT=apple_health NOTES="Morning workout"
make hr-batch DIR=directory RECURSIVE=true
```

## Google Drive Setup

See [.env.example](../.env.example) for detailed setup instructions.

Quick setup:

```bash
# 1. Get OAuth2 credentials from Google Cloud Console
# 2. Save to local/gdrive/credentials.json
# 3. Authenticate
make backup-cloud
# Browser opens for authorization, token saved to local/gdrive/token.json
```

## Automated Backups

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /Users/petr/code/onsendo && make backup-auto >> logs/backup.log 2>&1
```

## Tips

- Run `make help` to see all targets with descriptions
- Most commands have colored output for better readability
- All backup operations include integrity checks
- Heart rate operations wrap the original shell scripts

## Need More Help?

- Full documentation: [CLAUDE.md](../CLAUDE.md)
- Backup system: [artifacts/db/backups/README.md](../artifacts/db/backups/README.md)
- Cloud setup: [.env.example](../.env.example)
