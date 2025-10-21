<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-top: 20px; margin-bottom: 20px;">
  <h1 style="color: #d2691e; font-size: 2.5em; font-weight: bold; margin-bottom: 0px;">温泉道️</h1>
  <h5 style="margin-bottom: 20px; font-weight: normal;">♨️ 大なる温泉の道 ♨️</h5>
  <p style="font-weight: normal;">
    A Python application for tracking and analyzing onsen (hot spring) visits in Beppu, Japan. Combines database management, health tracking, exercise monitoring, and data analysis to support the 88 Onsen Challenge.
  </p>
  <p>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
    </a>
    <a href="https://www.sqlite.org/index.html">
      <img src="https://img.shields.io/badge/sqlite-3-blue.svg" alt="SQLite 3">
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
    </a>
  </p>
</div>

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Data Management](#data-management)
- [Reference](#reference)
- [Development](#development)
- [Additional Resources](#additional-resources)

---

## Overview

### What is Onsendo?

Onsendo (温泉道) helps you track, analyze, and optimize your onsen journey in Beppu, Japan. The application combines:

- **Visit Tracking**: Record detailed experiences with ratings, health metrics, and notes
- **Smart Recommendations**: Distance-based filtering and availability checking
- **Health Monitoring**: Heart rate data import and analysis
- **Exercise Integration**: GPS workout tracking with challenge compliance stats
- **Rule Management**: Weekly review system for the 88 Onsen Challenge

### The 88 Onsen Challenge

This application supports the **[88 Onsen Challenge](rules/onsendo-rules.md)** - a three-month journey (October-December 2025) to visit all 88 onsens in Beppu while maintaining a sustainable, healthy routine.

Challenge framework includes:

- Visit frequency guidelines (2 visits per day on active days)
- Sauna usage policy (3-4 times per week maximum)
- Exercise integration (running 20-35km/week, 2-4 gym sessions, 1 weekly hike)
- Health and safety protocols
- Weekly review and rule revision system

See [rules/onsendo-rules.md](rules/onsendo-rules.md) for complete details.

### Key Features

- **Location-Based Distance Calculations**: Haversine formula for accurate geographic distances
- **Multi-Format Health Data Import**: CSV, JSON, GPX, TCX, Apple Health exports
- **Intelligent Linking**: Auto-match exercises to visits via timestamps
- **Data Integrity**: SHA-256 file hashing and validation
- **Batch Processing**: Parallel import with configurable workers
- **Database Migrations**: Alembic-based schema evolution without data loss
- **Analysis Engine**: Statistical metrics, visualizations, and ML models

---

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry (Python dependency management)

### Installation

1. **Clone the repository and set up environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   poetry install
   ```

2. **Optional: Direct CLI access** (without `poetry run` prefix):

   ```bash
   # Create symlink to user bin
   ln -s "$(pwd)/.venv/bin/onsendo" ~/.local/bin/onsendo
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

   # Verify
   onsendo --help
   ```

### Database Setup

Create a new database or use an existing one:

```bash
# Create new database
poetry run python scripts/init_db.py

# OR: Copy existing database to data/db/
cp /path/to/onsen.db data/db/
```

### Your First Commands

```bash
# 1. Add your location (hotel, home, etc.)
poetry run onsendo location add

# 2. Get onsen recommendations
poetry run onsendo onsen recommend --location "Your Location Name"

# 3. Record your first visit
poetry run onsendo visit add

# 4. List your visits
poetry run onsendo visit list
```

---

## Core Concepts

The CLI is organized around six main entities:

### 🏠 Locations

User-defined places (home, hotel, station) used as starting points for distance calculations and recommendations.

- Used for: Distance calculations, milestone thresholds, recommendations
- Commands: `location add`, `location list`, `location modify`

### ♨️ Onsens

Hot spring facilities with metadata (coordinates, operating hours, facilities, ban numbers).

- Used for: Recommendations, visit recording, data scraping
- Commands: `onsen add`, `onsen recommend`, `onsen print-summary`

### 📝 Visits

Your experiences at specific onsens with comprehensive tracking data.

- Includes: Ratings (1-10), health metrics, logistics (fees, duration), weather, notes
- Commands: `visit add`, `visit list`, `visit modify`, `visit delete`

### 💓 Heart Rate Data

Physiological data from fitness devices linked to onsen visits.

- Formats: CSV, JSON, Apple Health, plain text
- Features: Validation, SHA-256 integrity, visit linking
- Commands: `heart-rate import`, `heart-rate batch-import`, `heart-rate link`

### 🏃 Exercise Sessions

Workout data with GPS routes, metrics, and challenge compliance tracking.

- Formats: GPX, TCX, Apple Health (CSV/XML), JSON
- Metrics: Distance, pace, elevation, heart rate, calories
- Commands: `exercise import`, `exercise link`, `exercise stats`

### 📋 Rules Management

Weekly review system for tracking challenge compliance and rule revisions.

- Review data: Visit metrics, health check, reflections, weekly plans
- Rule adjustments: Section modifications with rationale and safeguards
- Commands: `rules revision-create`, `rules revision-list`, `rules history`

---

## Basic Usage

### Location Management

**Add a location** (interactive):

```bash
poetry run onsendo location add
```

**List and manage**:

```bash
poetry run onsendo location list
poetry run onsendo location modify
poetry run onsendo location delete
```

**Calculate distance milestones**:

```bash
poetry run onsendo system calculate-milestones "Beppu Station" --update-engine
```

### Onsen Discovery

**Get recommendations**:

```bash
# Basic recommendations
poetry run onsendo onsen recommend --location "Beppu Station"

# With filters
poetry run onsendo onsen recommend \
  --location "Beppu Station" \
  --distance "close" \
  --exclude-visited \
  --limit 5
```

**Distance categories** (adaptive based on your location):

- `very_close`: Within 20th percentile (typically 0-5km)
- `close`: Within 50th percentile (median distance)
- `medium`: Within 80th percentile
- `far`: Beyond 80th percentile

**Get onsen information**:

```bash
poetry run onsendo onsen print-summary --ban-number "123"
poetry run onsendo onsen print-summary --onsen-id 1
```

### Recording Visits

**Add a visit** (interactive mode recommended):

```bash
poetry run onsendo visit add
```

Interactive mode guides you through:

- Onsen selection
- Date and time
- Ratings (cleanliness, atmosphere, water quality, etc.)
- Practical details (entry fee, duration, travel time)
- Health metrics (energy level changes, hydration)
- Environmental factors (weather, crowd levels)
- Optional notes

**Navigation**: Use `back` or `back N` during interactive entry to modify previous answers.

**Manage visits**:

```bash
poetry run onsendo visit list
poetry run onsendo visit modify
poetry run onsendo visit delete
```

### Getting Recommendations

The recommendation engine combines multiple factors:

**Availability checking**:

- Operating hours validation
- Closed days consideration
- Minimum stay time requirements

**Distance filtering**:

- Location-based percentile thresholds
- Actual distance in kilometers

**Personalization**:

- Exclude previously visited onsens
- Consider current location and time
- Provide Google Maps navigation links

---

## Advanced Features

### Heart Rate Tracking

Import and analyze heart rate data from fitness devices.

#### Importing Data

```bash
# Single file import
poetry run onsendo heart-rate import path/to/data.csv

# Specify format
poetry run onsendo heart-rate import data.csv --format apple_health

# Add notes
poetry run onsendo heart-rate import data.csv --notes "Morning workout"

# Validate only (don't store)
poetry run onsendo heart-rate import data.csv --validate-only

# Batch import with parallel processing
poetry run onsendo heart-rate batch-import /path/to/files/ --recursive --max-workers 8
```

#### Supported Formats

**Standard CSV**:

```csv
timestamp,heart_rate,confidence
2024-01-15 10:00:00,72,0.95
2024-01-15 10:01:00,75,0.92
```

**Apple Health**:

```csv
"SampleType","SampleRate","StartTime","Data"
"HEART_RATE",1,"2025-08-11T15:24:12.000Z","72;74;73;75;76"
```

#### Managing Records

```bash
# List all records
poetry run onsendo heart-rate list

# Show only unlinked records
poetry run onsendo heart-rate list --unlinked-only

# Link to visit
poetry run onsendo heart-rate link <hr_id> <visit_id>

# Unlink from visit
poetry run onsendo heart-rate unlink <hr_id>

# Delete record
poetry run onsendo heart-rate delete <hr_id> --force
```

#### Data Quality Features

- Physiological validation (40-200 BPM)
- Activity pattern detection
- Time-based variations
- Confidence scoring
- SHA-256 file integrity

### Exercise Management

Track workouts with GPS data, metrics, and challenge compliance.

#### Importing Workouts

```bash
# Auto-detect format
poetry run onsendo exercise import path/to/workout.gpx

# Force specific format
poetry run onsendo exercise import workout.tcx --format tcx

# Add notes
poetry run onsendo exercise import run.gpx --notes "Morning run to station"

# Batch import with parallel processing
poetry run onsendo exercise batch-import ~/Workouts/ --recursive --max-workers 8
```

#### Supported Formats

- **GPX**: GPS Exchange Format (running/cycling with GPS tracks)
- **TCX**: Training Center XML (Garmin and other devices)
- **Apple Health**: CSV/XML exports from Health app
- **JSON**: Generic workout format
- **CSV**: Simple format with timestamps and metrics

#### Linking to Visits

```bash
# Auto-match based on timestamps (2-hour window)
poetry run onsendo exercise link --exercise-id 123 --auto-match

# Manual link to specific visit
poetry run onsendo exercise link --exercise-id 123 --visit-id 456

# Unlink from visit
poetry run onsendo exercise link --exercise-id 123 --unlink
```

#### Querying and Statistics

```bash
# List all exercises
poetry run onsendo exercise list

# Filter by type and date
poetry run onsendo exercise list --type running --date-range 2025-11-01,2025-11-30

# Show unlinked only
poetry run onsendo exercise list --unlinked-only

# Weekly statistics for challenge compliance
poetry run onsendo exercise stats --week 2025-11-10
poetry run onsendo exercise stats --month 11 --year 2025
```

**Weekly stats output** shows:

- Running distance vs target (20-35km/week)
- Gym sessions vs target (2-4/week)
- Hiking completion (1/week required)
- Other activities (swimming, cycling, etc.)
- Warnings for exceeded limits or missed targets

#### Validation Features

- Pace validation (2-12 min/km for running)
- Heart rate bounds (30-220 BPM)
- Elevation consistency checks
- GPS gap detection
- Haversine distance calculation
- Duration limits (1 min to 24 hours)

### Rules & Weekly Reviews

Track challenge compliance and manage rule revisions.

#### Viewing Rules

```bash
# Print all current rules
poetry run onsendo rules print

# Print specific section
poetry run onsendo rules print --section 3

# Print rules at specific revision
poetry run onsendo rules print --version 2
```

#### Weekly Review Workflow

Every Sunday, complete a comprehensive review:

```bash
poetry run onsendo rules revision-create
```

The interactive workflow guides you through **5 phases**:

**Phase 1: Weekly Review Data**

- Summary metrics (visits, sauna sessions, running km, gym sessions, hike)
- Health check (energy 1-10, sleep hours/quality, soreness, mood)
- Reflections (what went well, patterns, warnings, standout onsens)
- Plans for next week (focus, goals, sauna limit, run volume)

**Phase 2: Rule Adjustment Context**

- Reason (fatigue, injury, schedule, weather, etc.)
- Description of needed modifications
- Expected duration (temporary or permanent)
- Health safeguards

**Phase 3: Rule Modifications**

- Select sections to modify (1-10)
- View current rules, enter new text
- Provide rationale for each change

**Phase 4: Preview & Confirmation**

- Review all collected data
- See summary of changes
- Confirm or cancel

**Phase 5: Automatic Execution**

- Creates database record
- Generates `rules/revisions/v{N}_YYYY-MM-DD.md`
- Updates `rules/onsendo-rules.md`
- Appends version history

#### Managing Revisions

```bash
# List all revisions
poetry run onsendo rules revision-list
poetry run onsendo rules revision-list --verbose --limit 10

# Show specific revision
poetry run onsendo rules revision-show --version 2
poetry run onsendo rules revision-show --format json

# Compare two revisions
poetry run onsendo rules revision-compare --version-a 1 --version-b 2

# View timeline
poetry run onsendo rules history --visual

# Export revisions
poetry run onsendo rules revision-export --format json
poetry run onsendo rules revision-export --include-weekly-reviews
```

### Database Migrations

Alembic-based schema evolution without data loss.

```bash
# Apply migrations (after pulling new code)
poetry run onsendo database migrate-upgrade

# Check current migration status
poetry run onsendo database migrate-current

# View migration history
poetry run onsendo database migrate-history --verbose

# Generate new migration (after modifying models)
poetry run onsendo database migrate-generate "Add new field description"

# Downgrade to previous migration
poetry run onsendo database migrate-downgrade -1

# Mark existing database as up-to-date
poetry run onsendo database migrate-stamp head
```

**When to use migrations**:

- After pulling code with model changes: `migrate-upgrade`
- For databases created before migration system: `migrate-stamp head` (once)
- After modifying `src/db/models.py`: `migrate-generate`
- Always backup before migrations: `make backup`

### Analysis & Visualization

Run statistical analysis and generate visualizations.

```bash
# Predefined scenarios
poetry run onsendo analysis scenario overview
poetry run onsendo analysis scenario spatial_analysis

# Custom analysis
poetry run onsendo analysis run descriptive \
  --data-categories "visit_ratings,visit_experience" \
  --metrics "mean,median,std" \
  --visualizations "correlation_matrix,bar,histogram" \
  --models "linear_regression"

# Cleanup old analyses
poetry run onsendo analysis clear-cache --cleanup-old-analyses --keep-recent 5
```

---

## Data Management

### Mock Data Generation

Generate realistic test data for development and testing.

#### Available Scenarios

```bash
# Random mix (default: 7 days, 1 visit/day)
poetry run onsendo database insert-mock-visits

# Weekend warrior (4 weekends, 2 visits each)
poetry run onsendo database insert-mock-visits --scenario weekend_warrior

# Daily visitor (almost daily for 2 weeks)
poetry run onsendo database insert-mock-visits --scenario daily_visitor

# Seasonal explorer (all four seasons)
poetry run onsendo database insert-mock-visits --scenario seasonal_explorer

# Multi-onsen enthusiast (multiple onsens per day)
poetry run onsendo database insert-mock-visits --scenario multi_onsen_enthusiast

# Custom parameters
poetry run onsendo database insert-mock-visits --scenario custom \
  --num-days 14 --visits-per-day 2 --start-date 2024-01-01
```

#### Mock Data Features

- Realistic ratings and health metrics
- Seasonal intelligence (temperature, timing adjustments)
- Multi-onsen visit ordering
- Complete field coverage
- Follows same validation as interactive entry

### Database Cleanup

```bash
# Drop all visits (with confirmation)
poetry run onsendo database drop-visits

# Skip confirmation (use with caution)
poetry run onsendo database drop-visits --force

# Drop visits by criteria
poetry run onsendo database drop-visits-by-criteria --rating-below 7 --force
poetry run onsendo database drop-visits-by-criteria --before-date 2024-01-01 --force
poetry run onsendo database drop-visits-by-criteria --onsen-id 5 --force
```

### Backup & Restore

#### Local Backups

```bash
# Create backup
make backup

# List all backups
make backup-list

# Verify integrity
make backup-verify

# Restore from backup (interactive)
make backup-restore

# Clean up old backups (keeps 50 most recent)
make backup-cleanup
```

#### Cloud Backups (Google Drive)

```bash
# Sync to Google Drive
make backup-cloud

# List cloud backups
make backup-cloud-list

# Full backup (local + cloud)
make backup-full

# Automatic backup (for cron jobs)
make backup-auto
```

**Setup Google Drive backups**:

1. Create OAuth2 credentials in Google Cloud Console
2. Save to `local/gdrive/credentials.json`
3. Run `make backup-cloud` to authenticate
4. Token saved to `local/gdrive/token.json`

See [.env.example](.env.example) for detailed setup instructions.

---

## Reference

### Command Index

**Location Commands**:

- `location add` - Add new location (interactive or with flags)
- `location list` - List all locations
- `location modify` - Update location details
- `location delete` - Remove a location

**Onsen Commands**:

- `onsen add` - Add new onsen
- `onsen recommend` - Get smart recommendations
- `onsen print-summary` - Show onsen details
- `onsen scrape-data` - Update onsen database from web

**Visit Commands**:

- `visit add` - Record new visit (interactive)
- `visit list` - List all visits
- `visit modify` - Update visit details
- `visit delete` - Remove visit record

**Heart Rate Commands**:

- `heart-rate import` - Import single file
- `heart-rate batch-import` - Import directory
- `heart-rate list` - List all records
- `heart-rate link` - Link to visit
- `heart-rate unlink` - Unlink from visit
- `heart-rate delete` - Remove record

**Exercise Commands**:

- `exercise import` - Import single workout file
- `exercise batch-import` - Import directory with parallel processing
- `exercise list` - List all sessions
- `exercise link` - Link to visit or heart rate data
- `exercise stats` - Show weekly/monthly statistics

**Rules Commands**:

- `rules print` - View current rules
- `rules revision-create` - Create weekly review
- `rules revision-list` - List all revisions
- `rules revision-show` - Show specific revision
- `rules revision-compare` - Compare two revisions
- `rules history` - View revision timeline

**Database Commands**:

- `database insert-mock-visits` - Generate test data
- `database drop-visits` - Clean up visit data
- `database drop-visits-by-criteria` - Selective deletion
- `database migrate-upgrade` - Apply migrations
- `database migrate-current` - Check migration status
- `database migrate-generate` - Create new migration

**System Commands**:

- `system init-db` - Create new database
- `system fill-db` - Import onsen data from JSON
- `system calculate-milestones` - Calculate distance thresholds

**Analysis Commands**:

- `analysis scenario <name>` - Run predefined scenario
- `analysis run <type>` - Custom analysis
- `analysis clear-cache` - Clean up old analyses

### Supported Data Formats

#### Heart Rate Formats

| Format | File Extension | Source | Notes |
|--------|---------------|---------|-------|
| CSV | `.csv` | Generic | `timestamp,heart_rate,confidence` |
| JSON | `.json` | Generic | Structured workout data |
| Apple Health | `.csv` | iPhone/Watch | Special CSV format with semicolon-separated data |
| Plain Text | `.txt` | Various | Simple timestamp + BPM |

#### Exercise Formats

| Format | File Extension | Source | Features |
|--------|---------------|---------|----------|
| GPX | `.gpx` | Garmin, Strava, etc. | Full GPS tracks, elevation, heart rate |
| TCX | `.tcx` | Garmin devices | Training Center XML with detailed metrics |
| Apple Health | `.xml`, `.csv` | iPhone/Watch | Workout summaries with auto type detection |
| JSON | `.json` | Generic | Flexible workout format |
| CSV | `.csv` | Generic | Simple tabular format |

### File Organization Best Practices

**Recommended directory structure**:

```
onsendo/
├── data/
│   ├── db/                    # SQLite databases
│   ├── heart_rate/
│   │   ├── raw/               # Original files from devices
│   │   │   ├── apple_health/
│   │   │   ├── garmin/
│   │   │   └── fitbit/
│   │   ├── processed/         # Validated files
│   │   └── archived/          # Old files
│   └── exercise/
│       ├── raw/
│       │   ├── garmin/        # .gpx, .tcx files
│       │   ├── strava/        # .gpx files
│       │   └── apple_health/  # .csv, .xml files
│       ├── processed/
│       └── archived/
├── artifacts/
│   └── db/backups/            # Database backups
└── output/
    └── analysis/              # Analysis results
```

**Best practices**:

- Separate by device: Keep files from different sources in separate subdirectories
- Date-based organization: Use `YYYY_MM` format for monthly subdirectories
- Descriptive naming: `workout_morning_run_2025_08_15.csv`
- Keep originals: Never modify raw files from devices
- File permissions: `chmod 600` for personal health data
- Regular imports: Weekly routine to import new data

### Example Workflows

**Daily onsen visit**:

```bash
# 1. Get recommendations from your location
poetry run onsendo onsen recommend --location "Hotel" --distance "close"

# 2. After visiting, record your experience
poetry run onsendo visit add

# 3. Link any exercise from earlier
poetry run onsendo exercise link --exercise-id 123 --auto-match
```

**Sunday weekly review**:

```bash
# 1. Check your week's visits
poetry run onsendo visit list

# 2. Review exercise stats
poetry run onsendo exercise stats --week 2025-11-10

# 3. Complete rule review
poetry run onsendo rules revision-create

# 4. Create backup
make backup-full
```

**Monthly data import**:

```bash
# 1. Export data from devices to organized folders

# 2. Batch import heart rate data
poetry run onsendo heart-rate batch-import data/heart_rate/raw/apple_health/2025_11/ --recursive

# 3. Batch import exercise data
poetry run onsendo exercise batch-import data/exercise/raw/garmin/2025_11/ --recursive

# 4. Archive processed files
mv data/heart_rate/raw/apple_health/2025_11/ data/heart_rate/archived/
mv data/exercise/raw/garmin/2025_11/ data/exercise/archived/
```

---

## Development

### Running Tests

```bash
# Quick feedback loop (unit tests only)
make test-unit
# OR: poetry run pytest -q -m "not integration"

# Full test suite
make test
# OR: poetry run pytest

# Integration tests only
make test-integration
# OR: poetry run pytest -m integration

# With coverage
make coverage
# OR: poetry run coverage run -m pytest && poetry run coverage report
```

### Code Quality

```bash
# Lint code
make lint
# OR: poetry run pylint src tests

# Clean temporary files
make clean
```

### Makefile Shortcuts

See all available targets:

```bash
make help
```

Common targets:

- `make install` - Install dependencies
- `make test` - Run all tests
- `make lint` - Run linter
- `make backup` - Create database backup
- `make exercise-import FILE=...` - Import exercise file
- `make hr-import FILE=...` - Import heart rate file

### Contributing

See [CLAUDE.md](CLAUDE.md) and [AGENTS.md](AGENTS.md) for:

- Code style guidelines
- Type hint conventions (Python 3.12+ syntax)
- Import ordering
- Testing conventions
- Commit message format
- Pull request checklist

---

## Additional Resources

### Documentation

- **[CLAUDE.md](CLAUDE.md)**: Comprehensive development guide for Claude Code
- **[AGENTS.md](AGENTS.md)**: Repository guidelines for AI agents
- **[rules/onsendo-rules.md](rules/onsendo-rules.md)**: Complete 88 Onsen Challenge ruleset
- **[docs/heart_rate_system.md](docs/heart_rate_system.md)**: Detailed heart rate system documentation

### Templates

- **Rule Review Sunday**: Weekly review template integrated into `rules revision-create` command
- **Exercise tracking**: Weekly stats template for challenge compliance

### Example Configurations

- **[.env.example](.env.example)**: Environment variable setup for Google Drive backups
- **[pyproject.toml](pyproject.toml)**: Project metadata and dependencies
- **[pytest.ini](pytest.ini)**: Test configuration and markers
- **[.pylintrc](.pylintrc)**: Linting configuration

### Troubleshooting

**Database issues**:

- Run `make db-path` to find database location
- Check migration status: `poetry run onsendo database migrate-current`
- Apply pending migrations: `poetry run onsendo database migrate-upgrade`
- Restore from backup: `make backup-restore`

**Import errors**:

- Use `--validate-only` flag to check files before importing
- Check file format with `--format` flag
- Review validation errors in output
- Verify file permissions: `chmod 600 <file>`

**Performance**:

- Use `--max-workers` for batch imports (default: 4)
- Archive old files to reduce directory scan time
- Clean up old analyses: `poetry run onsendo analysis clear-cache`

### License

MIT License - See [LICENSE](LICENSE) for details.
