<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-top: 20px; margin-bottom: 20px;">
  <h1 style="color: #d2691e; font-size: 2.5em; font-weight: bold; margin-bottom: 0px;">温泉道️</h1>
  <h5 style="margin-bottom: 20px; font-weight: normal;">♨️ 大なる温泉の道 ♨️</h5>
  <p style="font-weight: normal;">
    This is a Python-based application to help me manage and track onsen (hot spring) visits and experiences, while in Beppu. It provides a command-line interface for adding onsen locations, recording visits with personal ratings, and managing the onsen journey data.
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

## The Onsendo Challenge

This application supports the **[88 Onsen Challenge](rules/onsendo-rules.md)** - a three-month journey (October-December 2025) to visit all 88 onsens in Beppu while maintaining a sustainable, healthy daily routine that integrates physical exercise, recovery, and work-life balance.

The challenge ruleset defines:

- Visit frequency and timing guidelines (2 visits per day on active days)
- Sauna usage policy (3-4 times per week maximum)
- Exercise integration (running, gym, hiking schedule)
- Health and safety protocols
- Data logging requirements

See [rules/onsendo-rules.md](rules/onsendo-rules.md) for the complete challenge framework and guidelines.

---

- [The Onsendo Challenge](#the-onsendo-challenge)
- [Set up the project](#set-up-the-project)
- [Installation for Direct CLI Access](#installation-for-direct-cli-access)
- [How to use](#how-to-use)
  - [Quick Start](#quick-start)
  - [Preparing a database](#preparing-a-database)
  - [Using Command Line Interface](#using-command-line-interface)
    - [Core Concepts and Workflows](#core-concepts-and-workflows)
    - [Managing Your Locations](#managing-your-locations)
      - [Adding a Location](#adding-a-location)
      - [Why Locations Matter](#why-locations-matter)
      - [Listing and Managing Locations](#listing-and-managing-locations)
    - [Discovering and Managing Onsens](#discovering-and-managing-onsens)
      - [Adding an Onsen](#adding-an-onsen)
      - [Getting Onsen Information](#getting-onsen-information)
      - [Data Scraping (for administrators)](#data-scraping-for-administrators)
    - [Recording Your Visits](#recording-your-visits)
      - [Adding a Visit](#adding-a-visit)
      - [Key Features of Visit Recording](#key-features-of-visit-recording)
      - [Managing Visit Records](#managing-visit-records)
      - [Heart Rate Data Management](#heart-rate-data-management)
    - [Getting Smart Recommendations](#getting-smart-recommendations)
      - [Basic Recommendations](#basic-recommendations)
      - [Advanced Filtering](#advanced-filtering)
      - [Distance Categories](#distance-categories)
    - [Understanding Distance Calculations](#understanding-distance-calculations)
      - [How Distances Are Calculated](#how-distances-are-calculated)
      - [Distance Milestones](#distance-milestones)
      - [Calculating Milestones for a Location](#calculating-milestones-for-a-location)
    - [How Recommendations Work](#how-recommendations-work)
      - [Availability Checking](#availability-checking)
      - [Distance Filtering](#distance-filtering)
      - [Personalization](#personalization)
      - [Smart Defaults](#smart-defaults)
    - [System Management](#system-management)
    - [Rules Management](#rules-management)
    - [Database Management and Testing](#database-management-and-testing)
    - [Tips for Effective Use](#tips-for-effective-use)
    - [Example Workflows](#example-workflows)

## Set up the project

- Get [Python](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/docs/)
- Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

- Run `poetry install`

## Installation for Direct CLI Access

To use `onsendo` directly from your command line without `poetry run`, set up a symlink and PATH:

**Option 1: Symlink to user bin directory (Recommended)**

```bash
# Create symlink (run from project root)
ln -s "$(pwd)/.venv/bin/onsendo" ~/.local/bin/onsendo

# Ensure ~/.local/bin is in PATH (add to ~/.zshrc if not present)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Option 2: Add project bin to PATH**

```bash
# Add to ~/.zshrc (replace /path/to/onsendo with actual path)
echo 'export PATH="/path/to/onsendo/.venv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Verify installation:**

```bash
onsendo --help  # Should work without 'poetry run'
```

**Note:** After updating dependencies with `poetry install`, the symlink remains valid automatically.

## How to use

### Quick Start

1. **Set up your database** (see [Preparing a database](#preparing-a-database) below)
2. **Add your first location** to start getting recommendations:

   ```bash
   poetry run onsendo location add
   ```

3. **Get onsen recommendations** from your location:

   ```bash
   poetry run onsendo onsen recommend --location "Your Location Name"
   ```

4. **Record your first visit** after visiting an onsen:

   ```bash
   poetry run onsendo visit add
   ```

5. **Generate test data** (optional, for development/testing):

   ```bash
   poetry run onsendo database insert-mock-visits --scenario random
   ```

### Preparing a database

You can either choose to create your own database, or use the provided one.

- To create a new database, run `poetry run python scripts/init_db.py`. This creates a new sub-folder in the `data` folder, and puts a new SQLite database file there.
- To use the provided database, simply copy it over to this folder.

### Using Command Line Interface

The project offers a comprehensive command-line interface for managing your onsen journey. To see all available commands:

```bash
poetry run onsendo --help
```

For detailed help on any command group:

```bash
poetry run onsendo location --help
poetry run onsendo onsen --help
poetry run onsendo visit --help
poetry run onsendo heart-rate --help
poetry run onsendo system --help
poetry run onsendo database --help
```

#### Core Concepts and Workflows

The CLI is organized around five main concepts that reflect how you interact with onsens in real life:

**🏠 Locations** - Places you stay or visit from (home, hotel, etc.)
**♨️ Onsens** - Hot spring facilities you can visit
**📝 Visits** - Your actual experiences at specific onsens
**💓 Heart Rate** - Physiological data from fitness devices linked to visits
**⚙️ System** - Database management and data processing

#### Managing Your Locations

Locations are the starting points for your onsen adventures. They're used to calculate distances to onsens and provide context for recommendations.

##### Adding a Location

```bash
poetry run onsendo location add
```

This will guide you through adding a new location (like your home or hotel) with an interactive prompt for:

- Name (e.g., "Beppu Station Hotel")
- Coordinates (latitude/longitude)
- Optional description

##### Why Locations Matter

The system uses your locations to calculate distances to onsens, which affects recommendations and helps you plan your visits based on travel time and convenience.

##### Listing and Managing Locations

```bash
poetry run onsendo location list          # See all your locations
poetry run onsendo location modify       # Update location details
poetry run onsendo location delete       # Remove a location
```

#### Discovering and Managing Onsens

Onsens are the hot spring facilities themselves. The system maintains a database of onsens with details like operating hours, facilities, and locations.

##### Adding an Onsen

```bash
poetry run onsendo onsen add --ban-number "123" --name "Beppu Onsen" --address "Beppu City"
```

##### Getting Onsen Information

```bash
poetry run onsendo onsen print-summary --onsen-id 1
poetry run onsendo onsen print-summary --ban-number "123"
```

##### Data Scraping (for administrators)

```bash
poetry run onsendo onsen scrape-data
```

This fetches current onsen data from the web to keep your database up-to-date.

#### Recording Your Visits

Visits capture your personal experiences at onsens. This is where you record ratings, observations, and details that help you remember and compare different experiences.

##### Adding a Visit

```bash
poetry run onsendo visit add
```

The interactive mode will guide you through recording:

- Which onsen you visited
- When you visited
- Personal ratings (cleanliness, atmosphere, etc.)
- Practical details (entry fee, stay duration, travel time)
- Health metrics (energy level changes, hydration)
- Environmental factors (weather, crowd levels)

##### Key Features of Visit Recording

- **Interactive Mode**: Guided prompts with validation and navigation
- **Comprehensive Data**: Capture everything from basic ratings to detailed health metrics
- **Navigation**: Use "back" or "back N" to go back and modify previous answers
- **Flexibility**: Most fields are optional, so you can record as much or as little detail as you want

##### Managing Visit Records

```bash
poetry run onsendo visit list            # See all your visits
poetry run onsendo visit modify          # Update visit details
poetry run onsendo visit delete          # Remove a visit record
```

##### Heart Rate Data Management

The heart rate data system allows you to import, store, and link heart rate recordings from various fitness devices (smartwatches, fitness trackers, etc.) to your onsen visits. This enables comprehensive health tracking and analysis of how onsen experiences affect your physiological responses.

**Key Features**:

- **Multi-format Support**: Import from CSV, JSON, Apple Health, and plain text
- **Data Validation**: Automatic quality checks ensure only reliable data is stored
- **Visit Linking**: Connect heart rate sessions to specific onsen visits
- **File Integrity**: SHA-256 hashing verifies data hasn't been corrupted
- **Flexible Storage**: Store data with or without linking to visits

**Supported Data Formats**:

*Standard CSV Format*:

```csv
timestamp,heart_rate,confidence
2024-01-15 10:00:00,72,0.95
2024-01-15 10:01:00,75,0.92
```

*Apple Health Format*:

```csv
"SampleType","SampleRate","StartTime","Data"
"HEART_RATE",1,"2025-08-11T15:24:12.000Z","72;74;73;75;76;80;82;85;87"
"HEART_RATE",1,"2025-08-11T15:25:12.000Z","88;90;92;95;98;100;102;105;108"
```

**Importing Heart Rate Data**:

```bash
# Import a single file
poetry run onsendo heart-rate import path/to/data.csv

# Force specific format
poetry run onsendo heart-rate import path/to/data.csv --format csv

# Add notes
poetry run onsendo heart-rate import path/to/data.csv --notes "Morning workout session"

# Validate only (don't store)
poetry run onsendo heart-rate import path/to/data.csv --validate-only

# Batch import from directory
poetry run onsendo heart-rate batch-import /path/to/heart_rate_files/ --recursive
```

**Linking to Onsen Visits**:

When adding a visit interactively, you can link heart rate data:

1. Complete the visit details
2. When prompted for heart rate data, enter the ID of an unlinked record
3. Or type `list` to see available unlinked heart rate records
4. The system will automatically link the selected data to your visit

**Managing Heart Rate Records**:

```bash
# List all records
poetry run onsendo heart-rate list list

# Show only unlinked records
poetry run onsendo heart-rate list list --unlinked-only

# Show details including file integrity
poetry run onsendo heart-rate list list --details

# Link to a visit
poetry run onsendo heart-rate list link 123 456  # Link HR record 123 to visit 456

# Unlink from visit
poetry run onsendo heart-rate list unlink 123

# Delete a record
poetry run onsendo heart-rate list delete 123 --force
```

**Mock Data Generation**:

For testing and development, you can generate realistic heart rate data:

```python
from src.testing.mocks.mock_heart_rate_data import (
    create_workout_session,
    create_sleep_session,
    create_daily_sessions
)

# Create a complete workout session
workout = create_workout_session()

# Export to Apple Health format
workout.export_apple_health_format("workout.csv")
```

**Data Quality Features**:

- **Physiological Accuracy**: Heart rates within realistic bounds (40-200 BPM)
- **Activity Patterns**: Different patterns for resting, exercise, recovery, and sleep
- **Time-based Variations**: Morning vs evening patterns, seasonal adjustments
- **Confidence Scores**: Data quality assessment for each measurement
- **Export Formats**: Support for all major data formats including Apple Health

**File Storage and Organization**:

For production use, organize your heart rate files in a structured directory system:

```plain
onsendo/
├── data/
│   ├── heart_rate/                    # Main heart rate data directory
│   │   ├── raw/                       # Original files from devices
│   │   │   ├── apple_health/          # Apple Health exports
│   │   │   ├── garmin/                # Garmin exports
│   │   │   ├── fitbit/                # Fitbit exports
│   │   │   └── other/                 # Other device formats
│   │   ├── processed/                 # Cleaned/validated files
│   │   ├── archived/                  # Old files you want to keep
│   │   └── imports/                   # Files currently being imported
```

**Best Practices**:

- **Separate by Device**: Keep files from different devices in separate subdirectories
- **Date-Based Organization**: Use `YYYY_MM` format for monthly subdirectories
- **Descriptive Naming**: Use names like `workout_morning_run_2025_08_15.csv`
- **Keep Originals**: Never modify raw files from your devices
- **Regular Imports**: Set up weekly routines to import new data

**Import Workflow**:

```bash
# 1. Export from device to organized directory
# 2. Import with correct format flag
poetry run onsendo heart-rate import data/heart_rate/raw/apple_health/2025_08/workout_2025_08_15.csv --format apple_health

# 3. Batch import from monthly directories
poetry run onsendo heart-rate batch-import data/heart_rate/raw/apple_health/2025_08/ --recursive

# 4. Move processed files to archive
mv data/heart_rate/raw/apple_health/2025_08/ data/heart_rate/archived/2025_08/
```

**Security and Backup**:

- **File Permissions**: `chmod 600 data/heart_rate/raw/**/*.csv` for privacy
- **Regular Backups**: Use `rsync` or git for version control
- **Validation**: Use `--validate-only` to check files before importing

#### Getting Smart Recommendations

The recommendation system helps you discover new onsens and plan your visits based on your preferences and current situation.

##### Basic Recommendations

```bash
poetry run onsendo onsen recommend --location "Beppu Station"
```

##### Advanced Filtering

```bash
poetry run onsendo onsen recommend \
  --location "Beppu Station" \
  --distance "close" \
  --time "2024-01-15 14:00" \
  --exclude-visited \
  --limit 5
```

##### Distance Categories

- `very_close`: Within the closest 20% of onsens (typically 0-5km)
- `close`: Within the median distance (typically 5-15km)  
- `medium`: Within 80% of onsens (typically 15-50km)
- `far`: Beyond the medium threshold

#### Understanding Distance Calculations

The system uses sophisticated distance calculations to help you plan your onsen visits effectively.

##### How Distances Are Calculated

- Uses the Haversine formula for accurate geographic distance calculations
- Distances are calculated from your locations to each onsen's coordinates
- Results are in kilometers for easy understanding

##### Distance Milestones

The system automatically calculates distance thresholds based on the actual distribution of onsens around your location:

- **20th percentile**: Very close onsens (closest 20%)
- **50th percentile**: Close onsens (median distance)
- **80th percentile**: Medium distance onsens
- **Beyond 80th percentile**: Far onsens

This means the categories adapt to your specific location - if you're in a dense onsen area, "close" might mean 2km, while in a rural area it might mean 20km.

##### Calculating Milestones for a Location

```bash
poetry run onsendo system calculate-milestones "Beppu Station" --update-engine
```

#### How Recommendations Work

The recommendation engine combines multiple factors to suggest the best onsens for your situation:

##### Availability Checking

- Checks if the onsen is open at your target time
- Considers operating hours and closed days
- Ensures the onsen stays open long enough for your visit

##### Distance Filtering

- Filters onsens based on your preferred distance category
- Uses calculated milestones for intelligent distance categorization
- Provides actual distances in the results

##### Personalization

- Can exclude onsens you've already visited
- Considers your current location for travel planning
- Factors in time constraints and preferences

##### Smart Defaults

- Automatically excludes closed onsens
- Suggests reasonable time windows
- Provides Google Maps links for easy navigation

#### System Management

**Database Operations**:

```bash
poetry run onsendo system init-db              # Create a new database
poetry run onsendo system fill-db data.json   # Import onsen data
```

**Database Migrations**:

The project uses Alembic for database schema migrations. This allows you to update your database schema (add new tables, columns, etc.) without losing existing data or recreating the database from scratch.

```bash
# Apply migrations to update your database schema
poetry run onsendo database migrate-upgrade

# Check current migration status
poetry run onsendo database migrate-current

# View migration history
poetry run onsendo database migrate-history
poetry run onsendo database migrate-history --verbose

# Generate new migration when models are modified
poetry run onsendo database migrate-generate "Add new field description"

# Downgrade to previous migration (if needed)
poetry run onsendo database migrate-downgrade -1
poetry run onsendo database migrate-downgrade <revision_id>

# Mark existing database as up-to-date (for databases created before migrations)
poetry run onsendo database migrate-stamp head
```

**When to Use Migrations**:

- **After pulling new code**: If new features add database tables or columns, run `migrate-upgrade`
- **For existing databases**: If you have a database created before the migration system, run `migrate-stamp head` once to mark it as current
- **When developing**: After modifying models in `src/db/models.py`, generate a new migration with `migrate-generate`
- **Before major changes**: Always backup your database before running migrations

**Migration Workflow Example**:

```bash
# 1. Someone adds a new column to a model (e.g., OnsenVisit)
# 2. They generate a migration: database migrate-generate "Add notes to visits"
# 3. You pull the code including the new migration file
# 4. Apply the migration: database migrate-upgrade
# 5. Your database now has the new column without losing any data!
```

**Non-Interactive Mode**:
Most commands support a `--no-interactive` flag for scripting and automation:

```bash
poetry run onsendo location add --no-interactive --name "Home" --latitude 33.2794 --longitude 131.5006
```

#### Rules Management

The rules management system helps you track and revise the [Onsendo Challenge ruleset](rules/onsendo-rules.md) following the **Rule Review Sunday** template. This system integrates weekly reviews, health tracking, and rule adjustments into a comprehensive revision tracking workflow.

**Why Rules Management Matters**:

The 88 Onsen Challenge follows strict guidelines for visits, exercise, and health. The rules management system allows you to:

- Track your weekly progress against challenge targets
- Document health and wellbeing metrics
- Revise rules when needed (fatigue, injury, schedule changes)
- Maintain a complete history of rule changes and their reasons
- Generate human and LLM-readable revision files

**Core Commands**:

```bash
# View current rules
poetry run onsendo rules print                    # Print all rules
poetry run onsendo rules print --section 3        # Print specific section only

# Create a weekly rule revision (interactive)
poetry run onsendo rules revision-create

# List all revisions
poetry run onsendo rules revision-list
poetry run onsendo rules revision-list --verbose --limit 10

# Show specific revision details
poetry run onsendo rules revision-show
poetry run onsendo rules revision-show --version 2
poetry run onsendo rules revision-show --format json

# Compare two revisions
poetry run onsendo rules revision-compare
poetry run onsendo rules revision-compare --version-a 1 --version-b 2

# View revision history
poetry run onsendo rules history
poetry run onsendo rules history --visual           # With ASCII timeline
```

**The Rule Review Sunday Workflow**:

Every Sunday, complete a comprehensive weekly review:

```bash
poetry run onsendo rules revision-create
```

This interactive workflow guides you through 5 phases:

**Phase 1: Weekly Review Data**

- Summary metrics (onsen visits, sauna sessions, running distance, gym sessions, hike)
- Health check (energy level 1-10, sleep hours/quality, soreness, mood)
- Reflections (what went well, patterns noticed, warning signs, standout onsens)
- Plans for next week (focus, goals, sauna limit, run volume, hike destination)

**Phase 2: Rule Adjustment Context**

- Reason for adjustment (fatigue, injury, schedule, etc.)
- Description of modifications needed
- Expected duration (temporary or permanent)
- Health safeguards applied

**Phase 3: Rule Modifications**

- Select which rule sections to modify (1-10)
- For each section: view current rules, enter new text, provide rationale
- Supports multiple section modifications in one revision

**Phase 4: Preview & Confirmation**

- Review all collected data
- See summary of changes
- Confirm or cancel the revision

**Phase 5: Automatic Execution**

- Creates database record with all review data
- Generates markdown file: `rules/revisions/v{N}_YYYY-MM-DD.md`
- Updates main rules file: `rules/onsendo-rules.md`
- Appends version history to rules file

**Example Weekly Review**:

```bash
# Sunday evening after completing your week
poetry run onsendo rules revision-create

# Follow the prompts:
# - Enter 12 onsen visits, 6.5 hours soaking, 3 sauna sessions
# - Energy level: 8/10, Sleep: 7.5 hours, Mood: positive
# - Reflection: "Maintained good balance this week"
# - Next week focus: "Recovery, reduce intensity slightly"
# - Adjustment reason: "fatigue"
# - Modify Section 2 (Visit Frequency): Reduce from 2 to 1-2 visits per day
# - Preview and confirm

# Result: v2 revision created with full weekly data and rule changes
```

**Viewing and Comparing Revisions**:

```bash
# List all your revisions
poetry run onsendo rules revision-list
# Output shows: version, date, week period, sections modified, summary

# Compare two weeks
poetry run onsendo rules revision-compare --version-a 1 --version-b 2
# Shows: metrics comparison, rule changes side-by-side, unified diff

# View detailed revision
poetry run onsendo rules revision-show --version 2
# Shows: complete weekly review data, health metrics, rule changes

# View history timeline
poetry run onsendo rules history --visual
# Shows: ASCII timeline of all revisions with dates and changes
```

**Export and Analysis**:

```bash
# Export for analysis
poetry run onsendo rules revision-export --format json --include-weekly-reviews
poetry run onsendo rules revision-export --format csv
poetry run onsendo rules revision-export --version 2 --format markdown

# Modify revision metadata (not rules)
poetry run onsendo rules revision-modify --version 2
# Can update: weekly metrics, health data, reflections, adjustment context
# Cannot update: version number, dates, actual rule changes
```

**Revision Files**:

Each revision creates a detailed markdown file stored in `rules/revisions/` with format `v{N}_YYYY-MM-DD.md`:

```markdown
# Rule Revision v2

**Revision Date:** 2025-11-17
**Week Period:** 2025-11-11 → 2025-11-17

## Weekly Review Summary
[Full metrics table]

## Health and Wellbeing
[Energy, sleep, soreness, mood details]

## Reflections
[5 reflection questions with your answers]

## Rule Adjustment Context
[Reason, description, duration, safeguards]

## Modified Sections
[Before/after for each modified section with rationale]
```

**Integration with Challenge**:

The rules system integrates seamlessly with your onsen tracking:

```bash
# 1. Track visits all week
poetry run onsendo visit add  # After each onsen visit

# 2. Sunday: Review your week's data
poetry run onsendo visit list  # See all visits this week
# Count: 12 visits, calculate total soaking time manually

# 3. Create rule revision with the data
poetry run onsendo rules revision-create
# Enter the counts and metrics from your visits

# 4. Next week: Compare progress
poetry run onsendo rules revision-compare --version-a 1 --version-b 2
# See how your metrics changed week-over-week
```

**Use Cases**:

- **Weekly Reviews**: Systematic tracking of challenge progress
- **Rule Adjustments**: Document when and why rules need modification
- **Health Tracking**: Monitor energy, sleep, and wellbeing trends
- **Historical Analysis**: Compare different weeks and identify patterns
- **Integrity Verification**: Signature section ensures honest self-assessment

#### Database Management and Testing

The system provides powerful tools for managing your database and generating test data for development and testing purposes.

**Mock Data Generation**:

Generate realistic onsen visit data to test the system or populate your database with sample data:

```bash
# Insert random mock data (default: 7 days, 1 visit per day)
poetry run onsendo database insert-mock-visits

# Insert specific scenario types
poetry run onsendo database insert-mock-visits --scenario weekend_warrior
poetry run onsendo database insert-mock-visits --scenario daily_visitor
poetry run onsendo database insert-mock-visits --scenario seasonal_explorer
poetry run onsendo database insert-mock-visits --scenario multi_onsen_enthusiast

# Custom scenarios with parameters
poetry run onsendo database insert-mock-visits --scenario custom --num-days 14 --visits-per-day 2
poetry run onsendo database insert-mock-visits --scenario seasonal --season winter --num-visits 20
poetry run onsendo database insert-mock-visits --scenario custom --start-date 2024-01-01 --num-days 30
```

**Available Scenarios**:

- **`random`**: Mix of single and multi-onsen days with configurable parameters
- **`weekend_warrior`**: Multiple onsens visited on weekends (4 weekends, 2 visits each)
- **`daily_visitor`**: Almost daily visits over 2 weeks
- **`seasonal_explorer`**: Different onsens visited across all four seasons
- **`multi_onsen_enthusiast`**: Multiple onsens per day over 5 different days
- **`custom`**: Fully configurable with custom days, visits per day, and start date
- **`seasonal`**: Season-specific visits with appropriate characteristics

**Mock Data Features**:

- **Realistic Data**: Generates data that mimics real onsen visits
- **Logic Chain Compliance**: Follows the same validation rules as interactive visit recording
- **Seasonal Intelligence**: Adjusts temperatures, timing, and characteristics based on season
- **Multi-onsen Support**: Properly handles visit ordering and cross-references
- **Comprehensive Coverage**: Includes all visit fields from ratings to health metrics

**Database Cleanup**:

Remove visit data from your database for testing or maintenance:

```bash
# Drop all visits (with confirmation prompt)
poetry run onsendo database drop-visits

# Skip confirmation (use with caution)
poetry run onsendo database drop-visits --force

# Drop visits based on specific criteria
poetry run onsendo database drop-visits-by-criteria --rating-below 7 --force
poetry run onsendo database drop-visits-by-criteria --before-date 2024-01-01 --force
poetry run onsendo database drop-visits-by-criteria --onsen-id 5 --force
poetry run onsendo database drop-visits-by-criteria --rating-above 9 --force
```

**Filtering Options for Selective Deletion**:

- **`--onsen-id`**: Filter by specific onsen
- **`--before-date`** / **`--after-date`**: Date ranges (YYYY-MM-DD format)
- **`--rating-below`** / **`--rating-above`**: Rating-based filtering (1-10 scale)
- **`--force`**: Skip confirmation prompts
- **`--no-interactive`**: Run in non-interactive mode

**Safety Features**:

- **Confirmation Prompts**: All deletion operations require confirmation unless `--force` is used
- **Non-Interactive Protection**: Cannot delete without confirmation in non-interactive mode
- **Detailed Logging**: Shows exactly what will be deleted before confirmation
- **Verification**: Confirms successful deletion and shows remaining visit count

**Use Cases**:

- **Development Testing**: Generate realistic data to test new features
- **System Validation**: Verify that the system handles various data scenarios correctly
- **Performance Testing**: Test with large datasets to ensure scalability
- **Data Reset**: Clean slate for testing different scenarios
- **Demo Purposes**: Show the system's capabilities with sample data

**Example Testing Workflow**:

```bash
# 1. Generate test data
poetry run onsendo database insert-mock-visits --scenario weekend_warrior

# 2. Test the system with the data
poetry run onsendo visit list
poetry run onsendo onsen recommend --location "Hotel"

# 3. Clean up when done testing
poetry run onsendo database drop-visits --force
```

#### Tips for Effective Use

1. **Start with Locations**: Add your main locations first so the system can provide accurate distance calculations
2. **Use Interactive Mode**: For visits and complex operations, the interactive mode guides you through all options
3. **Record Consistently**: The more visit data you record, the better the system can understand your preferences
4. **Update Regularly**: Use the scraping commands to keep onsen data current
5. **Experiment with Filters**: Try different distance categories and time windows to discover new options

#### Example Workflows

**Planning a Day Trip**:

1. Check recommendations from your hotel: `onsendo onsen recommend --location "Hotel" --distance "medium"`
2. Record your visit: `onsendo visit add`
3. Update your location if you move: `onsendo location add`

**Discovering New Areas**:

1. Calculate milestones for a new location: `onsendo system calculate-milestones "New Area"`
2. Get recommendations with the new distance categories
3. Record visits to build your personal database

**Managing Database Artifacts**:

1. Update presentation artifacts: `onsendo system update-artifacts`
2. Generate empty database templates for distribution
3. Create sample databases with onsen data and locations
4. Maintain current database state snapshots for documentation

**Health Tracking**:

1. Record detailed visit data including energy levels and hydration
2. Track how different onsens affect your well-being
3. Use this data to plan future visits based on your health goals
4. **Import heart rate data** from fitness devices to correlate physiological responses with onsen experiences
5. **Link heart rate sessions** to specific visits for comprehensive health analysis
6. **Monitor recovery patterns** by tracking heart rate changes before, during, and after onsen visits
