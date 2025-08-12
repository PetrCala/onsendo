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

- [Set up the project](#set-up-the-project)
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
poetry run onsendo heart-rate import path/to/data.csv --validate_only

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
poetry run onsendo heart-rate list list --unlinked_only

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
- **Validation**: Use `--validate_only` to check files before importing

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

**Non-Interactive Mode**:
Most commands support a `--no-interactive` flag for scripting and automation:

```bash
poetry run onsendo location add --no-interactive --name "Home" --latitude 33.2794 --longitude 131.5006
```

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
poetry run onsendo database insert-mock-visits --scenario custom --num_days 14 --visits_per_day 2
poetry run onsendo database insert-mock-visits --scenario seasonal --season winter --num_visits 20
poetry run onsendo database insert-mock-visits --scenario custom --start_date 2024-01-01 --num_days 30
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
poetry run onsendo database drop-visits-by-criteria --rating_below 7 --force
poetry run onsendo database drop-visits-by-criteria --before_date 2024-01-01 --force
poetry run onsendo database drop-visits-by-criteria --onsen_id 5 --force
poetry run onsendo database drop-visits-by-criteria --rating_above 9 --force
```

**Filtering Options for Selective Deletion**:

- **`--onsen_id`**: Filter by specific onsen
- **`--before_date`** / **`--after_date`**: Date ranges (YYYY-MM-DD format)
- **`--rating_below`** / **`--rating_above`**: Rating-based filtering (1-10 scale)
- **`--force`**: Skip confirmation prompts
- **`--no_interactive`**: Run in non-interactive mode

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

**Health Tracking**:

1. Record detailed visit data including energy levels and hydration
2. Track how different onsens affect your well-being
3. Use this data to plan future visits based on your health goals
4. **Import heart rate data** from fitness devices to correlate physiological responses with onsen experiences
5. **Link heart rate sessions** to specific visits for comprehensive health analysis
6. **Monitor recovery patterns** by tracking heart rate changes before, during, and after onsen visits
