# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Onsendo (温泉道 - "The Way of Onsen") is a Python application for tracking and analyzing onsen (hot spring) visits in Beppu, Japan. It combines SQLite database management, web scraping, data analysis, machine learning, and health tracking (heart rate data) to help users discover, visit, and analyze their onsen experiences.

## Development Commands

**IMPORTANT:** The project now uses a Makefile for all common operations. Use `make help` to see all available targets.

### Quick Start

```bash
# Install dependencies
make install

# Run tests
make test              # All tests
make test-unit         # Unit tests only (fast)
make test-integration  # Integration tests only

# Code quality
make lint              # Run pylint
make coverage          # Test coverage report
make clean             # Clean temporary files
```

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
make install
# OR: poetry install

# Run with poetry
poetry run onsendo --help
# OR: make run-cli ARGS="--help"
```

### Database Operations
```bash
# Initialize database
make db-init

# Import onsen data
make db-fill DATA_FILE=path/to/data.json

# Show database path
make db-path
```

### Backup Operations

**Critical:** The project now has a robust backup system with local and cloud (Google Drive) support.

```bash
# Create local backup
make backup

# List all backups
make backup-list

# Verify latest backup integrity
make backup-verify

# Clean up old backups (keeps 50 most recent by default)
make backup-cleanup
make backup-cleanup KEEP_BACKUPS=100  # Keep 100 backups

# Restore from backup (interactive)
make backup-restore

# Google Drive cloud backup
make backup-cloud       # Sync to Google Drive
make backup-cloud-list  # List cloud backups
make backup-full        # Local + cloud backup

# Automatic backup (for cron jobs)
make backup-auto        # Backup + cleanup + cloud sync
```

**Setting up Google Drive backups:**

1. See [.env.example](.env.example) for detailed setup instructions
2. Create OAuth2 credentials in Google Cloud Console
3. Save credentials to `local/gdrive/credentials.json`
4. Run `make backup-cloud` to authenticate (browser will open)
5. Token saved to `local/gdrive/token.json` for future use

**Backup retention strategy:**

- Local backups are timestamped: `onsen_backup_YYYYMMDD_HHMMSS.db`
- Each backup includes SHA-256 checksum for integrity verification
- Default retention: 50 most recent backups (configurable)
- Backups stored in: `artifacts/db/backups/`
- Cloud backups mirror local structure in Google Drive

### Heart Rate Management

All heart rate operations can be invoked via Makefile:

```bash
# Import single file
make hr-import FILE=path/to/file.csv
make hr-import FILE=path/to/file.csv FORMAT=apple_health NOTES="Morning workout"

# Batch import
make hr-batch DIR=path/to/directory
make hr-batch DIR=path/to/directory RECURSIVE=true FORMAT=apple_health

# Status and maintenance
make hr-status                           # Show heart rate data status
make hr-maintenance CMD=cleanup          # Run cleanup
make hr-maintenance CMD=archive          # Archive old files
make hr-maintenance CMD=validate         # Validate integrity

# Interactive manager (original shell interface)
make hr-manager
```

## Architecture & Code Organization

### Module Structure

The codebase follows a layered architecture with clear separation of concerns:

- **`src/cli/`** - Command-line interface with subcommand groups (location, visit, onsen, heart-rate, analysis, database, system)
- **`src/db/`** - Database layer with SQLAlchemy models (Location, Onsen, OnsenVisit, HeartRateData)
- **`src/lib/`** - Core business logic and utilities (distance calculations, recommendations, heart rate management)
- **`src/analysis/`** - Analysis engine with data pipeline, metrics, models, and visualizations
- **`src/types/`** - Type definitions and enums for analysis and general use
- **`src/testing/`** - Test utilities, mocks, and fixtures
- **`tests/unit/`** - Fast unit tests (run with `-m "not integration"`)
- **`tests/integration/`** - Database and boundary tests (marked with `@pytest.mark.integration`)

### Key Architectural Patterns

**Database Models** (`src/db/models.py`):
- `Location` - User-defined locations for distance calculations
- `Onsen` - Hot spring facilities with detailed metadata (ban_number, coordinates, facilities, hours)
- `OnsenVisit` - Visit records with ratings, health metrics, logistics, weather
- `HeartRateData` - Physiological data linked to visits via foreign key

**Path Management** (`src/paths.py`):
- All file paths are centralized in the `PATHS` enum
- Never use ad-hoc path joins - always reference `PATHS` constants
- Key paths: `DB_DIR`, `OUTPUT_DIR`, `ARTIFACTS_DIR`, `TMP_DATA_DIR`

**CLI Command Groups** (`src/cli/commands/`):
- Each group has its own subdirectory (location/, visit/, onsen/, etc.)
- Commands are registered in `cmd_list.py` and organized by prefix
- Interactive mode is preferred for complex data entry (visits, locations)

**Analysis System** (`src/analysis/`):
- `engine.py` - Main orchestrator for analysis workflows
- `data_pipeline.py` - Transforms raw database data to analysis-ready formats
- `metrics.py` - Statistical calculations and summary metrics
- `visualizations.py` - Charts, maps, and interactive dashboards (matplotlib, seaborn, plotly, folium)
- `models.py` - Machine learning models (regression, classification, clustering)

**Heart Rate System** (`src/lib/heart_rate_manager.py`):
- Supports multiple formats: CSV, JSON, Apple Health, plain text
- Comprehensive validation: duration, data points, physiological ranges, gaps
- File integrity via SHA-256 hashing
- Batch import with parallel processing

**Recommendation Engine** (`src/lib/recommendation.py`):
- Distance-based filtering using Haversine formula
- Availability checking against operating hours and closed days
- Personalization based on visit history
- Distance categories: very_close (20%), close (50%), medium (80%), far (>80%)

**Parsers** (`src/lib/parsers/`):
- `usage_time.py` - Parse operating hours with complex time ranges
- `closed_days.py` - Parse closure information (holidays, weekdays, irregular)
- `stay_restriction.py` - Parse time-based restrictions

### Important Design Decisions

1. **Lazy Imports for Analysis**: Analysis models use lazy importing to avoid loading heavy ML libraries at CLI startup. Import statements are inside functions/methods.

2. **Distance Milestones**: Distance categories are calculated per-location based on percentiles of actual distances to all onsens, not fixed thresholds.

3. **Visit Ordering**: Multi-onsen visits on the same day track ordering via `order_in_day` and `previous_visit_id` fields.

4. **Non-Interactive Mode**: Most CLI commands support `--no-interactive` flag for scripting.

5. **Mock Data Generation**: Realistic mock visit data follows same validation rules as interactive entry, with seasonal intelligence.

6. **Analysis Output Structure**: Each analysis run creates timestamped subdirectory in `output/analysis/` for organization and cleanup.

## CLI Usage Patterns

### Location Management
```bash
# Add location (interactive)
poetry run onsendo location add

# Add location (non-interactive)
poetry run onsendo location add --no-interactive --name "Home" --latitude 33.2794 --longitude 131.5006

# Calculate distance milestones
poetry run onsendo system calculate-milestones "Beppu Station" --update-engine
```

### Onsen Discovery
```bash
# Get recommendations
poetry run onsendo onsen recommend --location "Beppu Station" --distance "close" --exclude-visited

# Scrape latest onsen data
poetry run onsendo onsen scrape-data

# Get onsen info
poetry run onsendo onsen print-summary --ban-number "123"
```

### Visit Recording
```bash
# Add visit (interactive - preferred)
poetry run onsendo visit add

# List visits
poetry run onsendo visit list

# Modify/delete visits
poetry run onsendo visit modify
poetry run onsendo visit delete
```

### Heart Rate Data
```bash
# Import single file
poetry run onsendo heart-rate import path/to/data.csv --format apple_health

# Batch import
poetry run onsendo heart-rate batch-import /path/to/files/ --recursive --max-workers 8

# Manage records
poetry run onsendo heart-rate list list --unlinked-only
poetry run onsendo heart-rate list link <hr_id> <visit_id>
```

### Analysis & Visualization
```bash
# Run predefined scenario
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

### Database Management
```bash
# Insert mock data for testing
poetry run onsendo database insert-mock-visits --scenario weekend_warrior
poetry run onsendo database insert-mock-visits --scenario custom --num-days 14 --visits-per-day 2

# Clean up test data
poetry run onsendo database drop-visits --force
poetry run onsendo database drop-visits-by-criteria --rating-below 7 --force
```

## Testing Conventions

### Test Organization
- **Unit tests** (`tests/unit/`): Fast, isolated, no database
- **Integration tests** (`tests/integration/`): Database fixtures, boundary tests
- Mark integration tests with `@pytest.mark.integration`
- Use `-m "not integration"` for quick feedback during development

### Test File Naming
- Must match pattern `test_*.py` (enforced by `pytest.ini`)
- Mirror source structure: `tests/unit/test_distance.py` tests `src/lib/distance.py`

### Fixtures
- Shared fixtures in `tests/conftest.py`
- Use mock builders from `src/testing/mocks/` instead of hard-coding test data
- Add regression tests for every bug fix

## Code Style & Conventions

### General Style
- 4-space indentation (no tabs)
- Comprehensive type hints on all functions
- snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants
- Use `loguru` for logging (not print statements)

### Imports
- Standard library first, then third-party, then local imports
- For analysis code: use lazy imports inside functions to avoid loading heavy ML libraries at startup
- Import from `src.paths.PATHS` for all file paths

### File Operations
- Always use `PATHS` enum from `src/paths.py` for file paths
- Clean up temporary files created in `output/` after use
- Store persistent data in appropriate subdirectories: `data/`, `output/`, `artifacts/`

### Function Design
- Prefer pure functions for calculations
- Extract shared logic to `src/lib` or `src/analysis`
- Keep CLI commands thin - delegate to library functions
- Validate inputs early and fail fast with clear error messages

## Commit & Pull Request Guidelines

### Commit Messages
Use Conventional Commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks
- `docs:` - Documentation updates
- `test:` - Test additions/updates

Format: Present tense, under 72 characters, reference issues in body when relevant.

Example:
```
feat: add batch import for heart rate data

Implements parallel processing with configurable workers.
Supports recursive directory scanning and dry-run mode.

Closes #123
```

### Pull Requests
- Include local verification: `pytest`, `pylint`, optional `coverage`
- Add CLI screenshots or transcripts for UX changes
- Keep branches rebased on `main`
- Avoid unrelated formatting changes
- Request review only after checks pass

## Data & Environment Notes

### Database
- SQLite databases stored in `data/db/`
- Never commit databases with personal data
- Use `scripts/init_db.py` or `onsendo system init-db` to create new databases
- Mock data scenarios available for testing (see Database Management commands)

### Python Version
- Requires Python 3.12+
- Verify with `poetry env info`

### External Dependencies
- Selenium tasks require ChromeDriver (document requirements in relevant script)
- Heart rate batch import uses shell scripts in `scripts/` for automation

### Secrets & Privacy
- Never commit secrets, API keys, or personal health data
- Heart rate files should have permissions `chmod 600`
- `.gitignore` covers `data/`, `local/`, `output/` directories

## Key Files & Entry Points

- **`src/cli/__main__.py`** - CLI entry point, argument parsing
- **`src/cli/cmd_list.py`** - Command registration and configuration
- **`src/db/models.py`** - Database schema definitions
- **`src/paths.py`** - Centralized path management
- **`src/const.py`** - Application constants (URLs, database config)
- **`pyproject.toml`** - Project metadata and dependencies
- **`pytest.ini`** - Test configuration and markers
- **`.pylintrc`** - Linting configuration

## Common Development Tasks

### Adding a New CLI Command
1. Define command in appropriate `src/cli/commands/{group}/` file
2. Register in `src/cli/cmd_list.py` with proper group prefix
3. Add business logic to `src/lib/` or relevant module
4. Add tests in `tests/unit/` or `tests/integration/`

### Adding a Database Column
1. Update model in `src/db/models.py`
2. Create database migration or use `init_db.py` for fresh database
3. Update mock data generators in `src/testing/mocks/`
4. Update analysis data categories if relevant (`src/types/analysis.py`)

### Adding a New Analysis Type
1. Extend `AnalysisType` enum in `src/types/analysis.py`
2. Implement analysis logic in `src/analysis/engine.py`
3. Add visualizations in `src/analysis/visualizations.py` if needed
4. Create predefined scenario in `src/cli/commands/analysis/`
5. Update documentation

### Adding a New Data Format for Heart Rate
1. Implement parser in `src/lib/heart_rate_manager.py`
2. Add format to `HeartRateDataFormat` enum
3. Update validation logic
4. Add test cases with sample files
5. Update documentation in `docs/heart_rate_system.md`
