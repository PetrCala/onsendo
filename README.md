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
   poetry run onsendo database insert-mock --scenario random
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
poetry run onsendo system --help
poetry run onsendo database --help
```

#### Core Concepts and Workflows

The CLI is organized around four main concepts that reflect how you interact with onsens in real life:

**🏠 Locations** - Places you stay or visit from (home, hotel, etc.)
**♨️ Onsens** - Hot spring facilities you can visit
**📝 Visits** - Your actual experiences at specific onsens
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
poetry run onsendo database insert-mock

# Insert specific scenario types
poetry run onsendo database insert-mock --scenario weekend_warrior
poetry run onsendo database insert-mock --scenario daily_visitor
poetry run onsendo database insert-mock --scenario seasonal_explorer
poetry run onsendo database insert-mock --scenario multi_onsen_enthusiast

# Custom scenarios with parameters
poetry run onsendo database insert-mock --scenario custom --num_days 14 --visits_per_day 2
poetry run onsendo database insert-mock --scenario seasonal --season winter --num_visits 20
poetry run onsendo database insert-mock --scenario custom --start_date 2024-01-01 --num_days 30
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
poetry run onsendo database insert-mock --scenario weekend_warrior

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
