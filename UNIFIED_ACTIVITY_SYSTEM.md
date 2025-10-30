# Unified Activity System - Migration Guide

## Overview

The Onsendo project has transitioned from separate heart rate and exercise tracking systems to a **unified Activity system** powered by Strava. This document explains the changes and how to use the new system.

## What Changed?

### Before (Old System)
- **Separate tables**: `heart_rate_data` and `exercise_sessions`
- **Multiple import sources**: GPX, TCX, Apple Health, CSV, manual entry
- **Redundant data**: Same activity could exist in multiple places
- **Complex linking**: Activities could link to both HR data and visits

### After (New System)
- **Single table**: `activities`
- **Single source**: All activities imported from Strava
- **Unique identifier**: `strava_id` ensures no duplicates
- **Simple tagging**: Activities tagged as "onsen monitoring" can link to visits
- **Clear separation**: Onsen monitoring vs regular exercise activities

## Database Changes

### New Table: `activities`
```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    strava_id TEXT UNIQUE NOT NULL,           -- Strava activity ID
    visit_id INTEGER,                         -- FK to onsen_visits (nullable)
    is_onsen_monitoring BOOLEAN DEFAULT FALSE,-- Tag for onsen HR monitoring
    recording_start DATETIME NOT NULL,
    recording_end DATETIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    activity_type TEXT NOT NULL,              -- running, cycling, yoga, etc.
    activity_name TEXT,
    distance_km REAL,
    calories_burned INTEGER,
    elevation_gain_m REAL,
    avg_heart_rate REAL,
    min_heart_rate REAL,
    max_heart_rate REAL,
    indoor_outdoor TEXT,
    route_data TEXT,                          -- JSON GPS route
    strava_data_hash TEXT NOT NULL,           -- For sync detection
    last_synced_at DATETIME,
    notes TEXT,
    created_at DATETIME,
    FOREIGN KEY (visit_id) REFERENCES onsen_visits(id)
)
```

### Archived Tables
- `heart_rate_data` → `heart_rate_data_archived`
- `exercise_sessions` → `exercise_sessions_archived`

These tables are preserved but no longer used by the application.

## Running the Migration

### Step 1: Backup Your Database
```bash
make backup ENV=prod  # Or dev, depending on which database you want to migrate
```

### Step 2: Run the Migration
```bash
# For dev database
poetry run onsendo database migrate-upgrade

# For prod database
poetry run onsendo --env prod database migrate-upgrade
```

This will:
1. Rename old tables to `_archived`
2. Create the new `activities` table
3. Preserve all existing data

### Step 3: Import Activities from Strava
```bash
# Import last 30 days with interactive tagging
poetry run onsendo strava sync --days 30 --interactive --auto-link

# Or auto-tag based on naming pattern
poetry run onsendo strava sync --days 30 --auto-tag-pattern "onsen"

# Import everything (last year)
poetry run onsendo strava sync --days 365 --interactive --skip-existing
```

## New Workflow

### 1. Import All Activities from Strava
```bash
# Basic import (no tagging)
poetry run onsendo strava sync --days 7

# Interactive tagging for onsen monitoring
poetry run onsendo strava sync --days 7 --interactive

# Auto-tag activities with "onsen" in name
poetry run onsendo strava sync --days 14 --auto-tag-pattern "onsen"
```

### 2. Tag Activities as Onsen Monitoring
If you didn't tag during import, you can tag later:
```python
from src.db.conn import get_db
from src.lib.activity_manager import ActivityManager

with get_db() as db:
    manager = ActivityManager(db)

    # Tag activity 42 as onsen monitoring
    manager.tag_as_onsen_monitoring(42)

    # Link to visit 15
    manager.link_to_visit(42, 15)
```

### 3. Query Activities
```python
from src.db.conn import get_db
from src.lib.activity_manager import ActivityManager

with get_db() as db:
    manager = ActivityManager(db)

    # Get all activities
    all_activities = manager.get_by_strava_id("12345678")

    # Get only onsen monitoring sessions
    onsen_activities = manager.get_onsen_monitoring_activities()

    # Get regular exercise activities
    exercises = manager.get_unlinked()

    # Get activities for a visit
    visit_activities = manager.get_by_visit(15)

    # Get weekly summary
    from datetime import datetime, timedelta
    week_start = datetime(2025, 11, 1)
    week_end = week_start + timedelta(days=7)
    summary = manager.get_weekly_summary(week_start, week_end)
```

### 4. Analysis Integration
```python
from src.analysis.data_pipeline import DataPipeline
from src.types.analysis import DataCategory

with get_db() as db:
    pipeline = DataPipeline(db)

    # Get all activities
    df = pipeline.get_data_for_categories([DataCategory.ACTIVITY_ALL])

    # Get only onsen monitoring activities
    df = pipeline.get_data_for_categories([DataCategory.ACTIVITY_ONSEN])

    # Get regular exercise activities
    df = pipeline.get_data_for_categories([DataCategory.ACTIVITY_EXERCISE])

    # Get activity metrics
    df = pipeline.get_data_for_categories([DataCategory.ACTIVITY_METRICS])
```

## Command Reference

### Strava Sync Command
```bash
poetry run onsendo strava sync [OPTIONS]

Options:
  --days N                  Sync activities from last N days (default: 7)
  --type TYPE              Only sync specific activity type (Run, Ride, etc.)
  --interactive            Prompt to tag activities as onsen monitoring
  --auto-tag-pattern TEXT  Auto-tag activities with name matching pattern
  --auto-link              Suggest linking tagged activities to nearby visits
  --dry-run                Show what would be synced without importing
  --skip-existing          Skip activities that already exist in database
```

### Examples
```bash
# Daily sync (no tagging)
poetry run onsendo strava sync

# Weekly sync with interactive tagging
poetry run onsendo strava sync --days 7 --interactive --auto-link

# Monthly sync for running activities only
poetry run onsendo strava sync --days 30 --type Run

# Bulk import with auto-tagging
poetry run onsendo strava sync --days 365 --auto-tag-pattern "onsen" --skip-existing

# Dry run to preview
poetry run onsendo strava sync --days 30 --dry-run
```

## Benefits of the New System

### 1. Single Source of Truth
- All activities come from Strava
- No duplicate imports from different sources
- Strava ID ensures uniqueness

### 2. Simple Data Model
- One table instead of two
- Clear tagging system (is_onsen_monitoring)
- Straightforward linking to visits

### 3. Better Workflow
- Import everything from Strava
- Tag only what matters (onsen monitoring)
- Link only tagged activities to visits
- Keep all exercises for analysis

### 4. Analysis Ready
- Weekly/monthly volume stats
- Activity type breakdown
- Correlation with onsen visits
- All metrics in one place

## Deprecated Commands

The following command groups are deprecated:
- `poetry run onsendo exercise *` - Use `strava sync` instead
- `poetry run onsendo heart-rate *` - Use `strava sync` with tagging

These commands will show deprecation warnings and may be removed in a future version.

## Troubleshooting

### Migration Failed
```bash
# Restore from backup
make backup-restore

# Try migration again
poetry run onsendo database migrate-upgrade
```

### Activities Not Importing
1. Check Strava authentication: `poetry run onsendo strava status`
2. Re-authenticate if needed: `poetry run onsendo strava auth`
3. Check rate limits: Activities/day limit is 1000

### Missing Activities
```bash
# Check if activity exists by Strava ID
poetry run onsendo strava download <activity_id>

# Re-sync with skip-existing
poetry run onsendo strava sync --days 30 --skip-existing
```

### Old Data Access
Old data is archived but still accessible:
```python
# Query archived exercise sessions
from sqlalchemy import text
with get_db() as db:
    result = db.execute(text("SELECT * FROM exercise_sessions_archived"))
    rows = result.fetchall()
```

## Future Enhancements

Planned improvements:
1. Automatic activity tagging based on HR patterns
2. Auto-detect onsen visits from Strava location data
3. Enhanced correlation analysis
4. Activity recommendations based on onsen visits
5. Weekly stats dashboards

## Support

For issues or questions:
1. Check logs: `tail -f logs/onsendo.log`
2. Review migration: `poetry run onsendo database migrate-history`
3. Open issue: https://github.com/your-repo/onsendo/issues
