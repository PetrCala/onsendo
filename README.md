<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-top: 20px; margin-bottom: 20px;">
  <h1 style="color: #d2691e; font-size: 2.5em; font-weight: bold; margin-bottom: 0px;">別府八湯温泉道️</h1>
  <h5 style="margin-bottom: 20px; font-weight: normal;">♨️ 大なる温泉の道 ♨️</h5>
  <p style="font-weight: normal;">
    A Python application for tracking and analyzing onsen (hot spring) visits in Beppu, Japan. Combines database management, Strava activity tracking, weight monitoring, and data analysis to support the 88 Onsen Challenge.
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
- **Activity Tracking**: Strava integration for onsen monitoring and exercise tracking
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

- **Multiple Database Environments**: Separate dev/prod databases with safety guardrails
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

The project uses **separate dev and prod databases** for safety:

```bash
# Initialize dev database (default - safe for testing)
poetry run onsendo system init-db
# Creates: data/db/onsen.dev.db

# Initialize production database (when ready for real data)
poetry run onsendo --env prod system init-db
# Creates: data/db/onsen.prod.db
```

#### Environment Switching Methods

**Method 1: Shell Helpers (Recommended - Simple & Persistent)**

Add to your `~/.zshrc` or `~/.bashrc`:
```bash
source ~/code/onsendo/scripts/shell_helpers.sh
```

Then use simple commands:
```bash
use-prod      # Switch to production (all commands use prod)
use-dev       # Switch back to development
onsendo-env   # Show current environment
```

**Method 2: Per-Command Override**
```bash
# CLI commands
poetry run onsendo --env prod visit list

# Makefile commands
make backup ENV=prod
```

**Method 3: Environment Variable (Advanced)**
```bash
# Set for entire session
export ONSENDO_ENV=prod
poetry run onsendo visit list  # Uses prod

# Or per-command
ONSENDO_ENV=prod make backup
```

**Priority:** Explicit path > `--env` flag > `ENV=` parameter > `ONSENDO_ENV` variable > default (dev)

### Your First Commands

```bash
# All commands default to dev database (safe to experiment!)

# 1. Add your location (hotel, home, etc.)
poetry run onsendo location add

# 2. Get onsen recommendations
poetry run onsendo onsen recommend --location "Your Location Name"

# 3. Record your first visit
poetry run onsendo visit add

# 4. List your visits
poetry run onsendo visit list

# When ready for production:
poetry run onsendo --env prod visit add  # Adds to production database
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

### 🏃 Activity Tracking

Unified Strava-based system for all activities including onsen monitoring and exercise.

- Source: Automatic sync from Strava
- Features: GPS routes, heart rate time-series, performance metrics, onsen monitoring
- Commands: `strava sync`, `strava download`, `strava status`

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

### Strava Integration

Sync activities directly from Strava, download in multiple formats, and automatically link to onsen visits.

#### Setup

1. **Create Strava API application**:
   - Visit <https://www.strava.com/settings/api>
   - Create new application with callback domain: `localhost`

2. **Configure credentials**:

   ```bash
   # Add to .env
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```

3. **Authenticate**:

   ```bash
   make strava-auth
   # Browser opens for OAuth authorization
   ```

#### Quick Commands

**Sync recent activities**:

```bash
# Preview sync (dry-run)
make strava-sync DAYS=7 DRY_RUN=true

# Download and import
make strava-sync DAYS=7 IMPORT=true LINK=true

# Filter by activity type
make strava-sync DAYS=30 TYPE=Run IMPORT=true
```

**Download specific activity**:

```bash
# Download by ID
make strava-download ACTIVITY_ID=12345678

# Download and auto-link to visit
make strava-download ACTIVITY_ID=12345678 IMPORT=true LINK=true
```

**Interactive browser**:

```bash
make strava-interactive
# Full-featured terminal UI for browsing, filtering, and importing
```

#### Key Features

- **Multiple formats**: GPX, JSON, HR CSV export
- **Auto-linking**: Matches activities to visits within ±2 hour window
- **Batch operations**: Sync multiple activities with progress reporting
- **Deduplication**: Skips already-downloaded activities
- **Rate limiting**: Automatic compliance with Strava API limits (100/15min, 1000/day)

#### Visit Linking

```bash
# Auto-match based on timestamp
make strava-link EXERCISE_ID=42 AUTO_MATCH=true

# Manual link
make strava-link EXERCISE_ID=42 VISIT_ID=15
```

**Auto-link algorithm**:

- Searches visits within ±2 hours of activity start
- Shows time difference for each suggestion
- Uses closest match automatically

#### Common Issues

**Authentication failed**:

```bash
# Re-authenticate
poetry run onsendo strava auth --reauth
```

**Rate limit exceeded**:

- System automatically waits and retries
- Check usage: `poetry run onsendo strava status -v`
- Reduce sync frequency or use smaller date ranges

**No nearby visits found**:

- Auto-link only works within ±2 hour window
- Use manual linking for activities outside this range

**For detailed troubleshooting**: See [docs/STRAVA_TROUBLESHOOTING.md](docs/STRAVA_TROUBLESHOOTING.md)

**For workflow examples**: See [docs/STRAVA_WORKFLOWS.md](docs/STRAVA_WORKFLOWS.md)

### Weight Tracking

Monitor body weight trends during the Onsendo Challenge to track health and fitness progress.

#### Adding Measurements

```bash
# Interactive manual entry
poetry run onsendo weight add

# Quick entry via flags
poetry run onsendo weight add --weight 72.5 --conditions fasted --notes "Morning weigh-in"

# With full metadata
poetry run onsendo weight add \
  --weight 72.5 \
  --conditions fasted \
  --time-of-day morning \
  --notes "After workout"
```

#### Importing from Files

```bash
# Import from CSV
poetry run onsendo weight import weights.csv

# Import from JSON
poetry run onsendo weight import data.json --format json

# Import from Apple Health export
poetry run onsendo weight import export.xml --format apple_health

# Add notes to all imported measurements
poetry run onsendo weight import weights.csv --notes "Imported from scale"

# Validate without importing
poetry run onsendo weight import weights.csv --validate-only
```

#### Supported Formats

**CSV**:
```csv
timestamp,weight_kg,conditions,time_of_day,notes
2025-11-01 07:30:00,72.5,fasted,morning,After workout
2025-11-02 07:30:00,72.3,fasted,morning,
```

**JSON**:
```json
[
  {
    "timestamp": "2025-11-01T07:30:00",
    "weight_kg": 72.5,
    "conditions": "fasted",
    "time_of_day": "morning",
    "notes": "After workout"
  }
]
```

**Apple Health**: Automatically extracts BodyMass records from Health app XML exports.

#### Querying Measurements

```bash
# List all measurements
poetry run onsendo weight list

# Filter by date range
poetry run onsendo weight list --date-range 2025-11-01,2025-11-30

# Limit results
poetry run onsendo weight list --limit 20

# JSON output
poetry run onsendo weight list --format json
```

#### Statistics and Trends

```bash
# Weekly summary
poetry run onsendo weight stats --week 2025-11-03

# Monthly summary
poetry run onsendo weight stats --month 11 --year 2025

# All-time statistics
poetry run onsendo weight stats --all-time
```

**Statistics include**:
- Total measurements
- Average, minimum, maximum weight
- Weight change (first to last)
- 7-day and 30-day moving averages
- Trend detection (stable, gaining, losing)
- Measurements by source
- Recommendations for tracking consistency

#### Exporting Data

```bash
# Export to CSV
poetry run onsendo weight export --format csv --output weights.csv

# Export to JSON
poetry run onsendo weight export --format json

# Export specific date range
poetry run onsendo weight export --format csv --date-range 2025-11-01,2025-11-30
```

#### Measurement Best Practices

- **Consistency**: Weigh yourself at the same time each day (morning is best)
- **Conditions**: Track fasted measurements for most accurate trends
- **Frequency**: Daily measurements provide better trend data than weekly
- **Same scale**: Use the same scale for all measurements
- **After bathroom**: Weigh yourself after using the bathroom, before eating

#### Validation Features

- Weight range enforcement (40-200 kg)
- Future timestamp detection
- Valid condition and time-of-day validation
- Automatic data source normalization
- SHA-256 file integrity for imported data

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

**Weight Commands**:

- `weight import` - Import weight data from file
- `weight add` - Add measurement manually (interactive or flags)
- `weight list` - List all measurements
- `weight delete` - Remove measurement
- `weight stats` - Show statistics and trends
- `weight export` - Export to CSV or JSON

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

#### Weight Formats

| Format | File Extension | Source | Format |
|--------|---------------|---------|--------|
| CSV | `.csv` | Generic | `timestamp,weight_kg,conditions,time_of_day,notes` |
| JSON | `.json` | Generic | Structured measurement data with metadata |
| Apple Health | `.xml` | iPhone/Watch | BodyMass records from Health export |

### File Organization Best Practices

**Recommended directory structure**:

```
onsendo/
├── data/
│   └── db/                    # SQLite databases
├── artifacts/
│   └── db/backups/            # Database backups
└── output/
    └── analysis/              # Analysis results
```

**Best practices**:

- Separate by purpose: Keep development and production databases separate
- Regular backups: Create backups before major operations or migrations
- Clean up analyses: Periodically remove old analysis results
- Use migrations: Always run migrations after pulling code changes

### Example Workflows

**Daily onsen visit**:

```bash
# 1. Get recommendations from your location
poetry run onsendo onsen recommend --location "Hotel" --distance "close"

# 2. After visiting, record your experience
poetry run onsendo visit add

# 3. Track your weight (if desired)
poetry run onsendo weight add
```

**Sunday weekly review**:

```bash
# 1. Check your week's visits
poetry run onsendo visit list

# 2. Review weight trends
poetry run onsendo weight stats --week 2025-11-10

# 3. Complete rule review
poetry run onsendo rules revision-create

# 4. Create backup
make backup-full
```

**Monthly weight tracking**:

```bash
# 1. Import weight data from devices
poetry run onsendo weight import data/weight/2025_11.csv --format csv

# 2. Review monthly trends
poetry run onsendo weight stats --month 11 --year 2025

# 3. Export for external analysis (optional)
poetry run onsendo weight export --format csv --output monthly_weight.csv
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
- `make strava-sync DAYS=7` - Sync activities from Strava

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
- **[docs/STRAVA_WORKFLOWS.md](docs/STRAVA_WORKFLOWS.md)**: Strava integration workflows and best practices

### Templates

- **Rule Review Sunday**: Weekly review template integrated into `rules revision-create` command
- **Weight tracking**: Daily measurement tracking for health monitoring during challenge

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
