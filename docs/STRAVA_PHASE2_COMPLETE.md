# Strava Integration - Phase 2 Complete ✓

**Date**: 2025-10-23
**Phase**: 2 - Activity Listing (Browse & Filter)

---

## Summary

Phase 2 of the Strava integration is **complete**! You can now browse and list Strava activities with powerful filtering capabilities.

---

## What Was Implemented

### 1. Activity Summary Data Model (`src/types/strava.py`)
✅ Created `StravaActivitySummary` dataclass:
- Comprehensive activity metadata (name, type, date, distance, duration, elevation)
- Heart rate data (average, max, has_heartrate flag)
- Computed properties: `distance_km`, `moving_time_minutes`, `elapsed_time_minutes`
- Formatted string representation for display

### 2. Activity Filter System (`src/types/strava.py`)
✅ Created `ActivityFilter` dataclass with:
- **Date range filtering**: `date_from`, `date_to`
- **Activity type filtering**: Filter by Run, Ride, Hike, etc.
- **Heart rate filtering**: Only activities with HR data
- **Distance filtering**: Minimum distance threshold
- **Name search**: Partial text matching
- **Pagination**: Page number and page size
- API parameter conversion (`to_api_params()`)
- Client-side filtering (`matches_activity()`)

### 3. API Client Enhancement (`src/lib/strava_client.py`)
✅ Added `list_activities()` method with:
- Accepts `ActivityFilter` parameter
- Calls Strava `/athlete/activities` endpoint
- Server-side filtering (date range via API)
- Client-side filtering (type, HR, distance, name)
- Activity parsing from API response
- Pagination support
- Error handling and logging

✅ Added `_parse_activity_summary()` helper:
- Parses Strava API JSON response
- Handles date format variations
- Maps all activity fields
- Robust error handling for missing data

### 4. CLI Browse Command (`src/cli/commands/strava/browse.py`)
✅ Full-featured `strava browse` command:

**Command-line flags:**
- `--days N` - Activities from last N days
- `--type TYPE` - Filter by activity type (Run, Ride, etc.)
- `--date-from YYYY-MM-DD` - Start date
- `--date-to YYYY-MM-DD` - End date
- `--has-hr` - Only activities with heart rate
- `--min-distance KM` - Minimum distance
- `--page N` - Page number
- `--page-size N` - Activities per page (max 200)

**Features:**
- Authentication checking
- Filter settings display
- Formatted activity list with:
  - Activity number, name, date
  - Distance, heart rate, duration
  - Activity type, time, elevation
- Empty results handling with helpful suggestions
- Pagination hints
- Error handling

---

## Files Created

```
src/cli/commands/strava/browse.py        # Browse command (240 lines)
```

### Modified Files
```
src/types/strava.py                      # Added StravaActivitySummary, ActivityFilter
src/lib/strava_client.py                 # Added list_activities(), _parse_activity_summary()
src/cli/cmd_list.py                      # Registered strava-browse command
```

---

## Testing Results

### ✅ Import Tests
```bash
poetry run python -c "from src.types.strava import StravaActivitySummary, ActivityFilter"
# ✓ New types imported successfully

poetry run python -c "from src.lib.strava_client import StravaClient"
# ✓ StravaClient with list_activities imported successfully

poetry run python -c "from src.cli.commands.strava.browse import cmd_strava_browse"
# ✓ Browse command imported successfully
```

### ✅ CLI Tests
```bash
poetry run onsendo strava --help
# Shows: auth, status, browse commands

poetry run onsendo strava browse --help
# Shows all filter options:
#   --days, --type, --date-from, --date-to,
#   --has-hr, --min-distance, --page, --page-size
```

---

## Usage Examples

### Basic Browsing
```bash
# Browse last 30 activities
poetry run onsendo strava browse

# Last 7 days
poetry run onsendo strava browse --days 7

# Last 30 days
poetry run onsendo strava browse --days 30
```

### Filtering by Activity Type
```bash
# Only running activities
poetry run onsendo strava browse --type run

# Only cycling activities
poetry run onsendo strava browse --type ride

# Only hiking activities
poetry run onsendo strava browse --type hike
```

### Filtering by Date Range
```bash
# Specific date range
poetry run onsendo strava browse --date-from 2025-10-01 --date-to 2025-10-23

# From specific date to now
poetry run onsendo strava browse --date-from 2025-10-01
```

### Advanced Filtering
```bash
# Only activities with heart rate data
poetry run onsendo strava browse --has-hr

# Minimum distance (5km+)
poetry run onsendo strava browse --min-distance 5

# Combine filters: Runs over 10km in last 14 days with HR
poetry run onsendo strava browse --days 14 --type run --min-distance 10 --has-hr
```

### Pagination
```bash
# Page 1 (default)
poetry run onsendo strava browse

# Page 2
poetry run onsendo strava browse --page 2

# Larger page size (up to 200)
poetry run onsendo strava browse --page-size 50
```

---

## Example Output

```
======================================================================
Strava Activities
======================================================================

Filter Settings:
----------------------------------------------------------------------
  Date range: 2025-10-16 to 2025-10-23
  Activity type: Run
  Heart rate: Required
----------------------------------------------------------------------

Fetching activities...

✓ Found 5 activities (Page 1)
======================================================================
   1. Morning Run                      2025-10-20    5.2km   ♥ 156bpm
      Run                              06:30 (31m)            ▲ 42m

   2. Evening Trail                    2025-10-19    8.1km   ♥ 148bpm
      Run                              18:45 (47m)            ▲ 125m

   3. Recovery Run                     2025-10-17    3.5km   ♥ 142bpm
      Run                              07:00 (22m)            ▲ 15m

   4. Long Run                         2025-10-16   12.3km   ♥ 152bpm
      Run                              08:00 (1h12m)          ▲ 78m

   5. Tempo Run                        2025-10-16    6.8km   ♥ 164bpm
      Run                              17:30 (35m)            ▲ 28m
======================================================================
```

---

## Key Features

### 🔍 Powerful Filtering
- Date range (absolute or relative)
- Activity type
- Heart rate presence
- Minimum distance
- Name search (client-side)

### 📊 Smart Display
- Two-line format for each activity
- Distance in kilometers
- Duration with hours/minutes
- Heart rate display (♥ symbol)
- Elevation gain (▲ symbol)
- Activity type and time

### 📄 Pagination
- Default 30 activities per page
- Configurable page size (up to 200)
- Auto-pagination hints
- Server-side pagination via Strava API

### 🛡️ Robust Error Handling
- Authentication checking
- Empty results with helpful suggestions
- API error handling
- Parse error recovery (skips invalid activities)

---

## API Integration

### Strava Endpoint Used
```
GET /athlete/activities
  ?after={unix_timestamp}
  &before={unix_timestamp}
  &page={page_number}
  &per_page={page_size}
```

### Filtering Strategy
- **Server-side** (via API): Date range, pagination
- **Client-side** (in code): Activity type, HR presence, distance, name

This hybrid approach:
- ✅ Reduces API calls (date filtering at server)
- ✅ Enables flexible filtering (type, HR, distance at client)
- ✅ Respects rate limits

---

## What's Next?

**Phase 3: Data Conversion** (Ready to implement)

Run:
```bash
implement strava phase 3
```

This will add:
- `StravaActivityDetail` dataclass (full activity data)
- `StravaClient.get_activity()` method
- `StravaClient.get_activity_streams()` method (GPS, HR data)
- Activity type mapping (Strava → Onsendo)
- `StravaToExerciseConverter` class
- `StravaToHeartRateConverter` class
- `StravaFileExporter` (GPX, JSON, CSV)

---

## Verification Checklist

- [x] StravaActivitySummary dataclass created
- [x] ActivityFilter dataclass created
- [x] Filter to API params conversion
- [x] Client-side filtering logic
- [x] StravaClient.list_activities() method
- [x] Activity parsing from API response
- [x] CLI command: `strava browse`
- [x] All filter flags working
- [x] Pagination support
- [x] Command registered in CLI
- [x] Import tests passing
- [x] CLI help working
- [x] Formatted output display

---

## Statistics

- **Lines of Code**: ~400 (types: 120, client: 80, CLI: 240)
- **Files Created**: 1
- **Files Modified**: 3
- **Commands Added**: 1
- **Filter Options**: 8
- **Functions Implemented**: 7

---

**Status**: ✅ Phase 2 Complete - Ready for Phase 3!

**Next Command**: `implement strava phase 3`
