# Phase 3: Data Conversion - COMPLETE ✓

**Status**: Implementation complete
**Date**: 2025-10-24

## Summary

Phase 3 implemented comprehensive data conversion and file export functionality for Strava integration. The system can now:

1. Map Strava activity types to Onsendo exercise types
2. Convert Strava activities to ExerciseSession objects
3. Convert Strava heart rate data to HeartRateSession objects
4. Export activities to GPX, JSON, and CSV file formats

## Files Created/Modified

### Created Files

**src/lib/strava_converter.py** (~580 lines)
- Complete converter and exporter implementation
- Four main classes with full functionality

### Modified Files

**src/lib/strava_client.py**
- Added `get_activity()` method for detailed activity retrieval
- Added `get_activity_streams()` method for GPS/HR/cadence stream data
- Added `_parse_activity_detail()` helper for API response parsing

**src/types/strava.py**
- Added `StravaActivityDetail` dataclass (comprehensive activity data)
- Added `StravaStream` dataclass (time-series stream data)

## Implementation Details

### 1. StravaActivityTypeMapper

Maps 30+ Strava activity types to Onsendo ExerciseType enum.

**Supported Activity Types**:
- Running: Run, TrailRun, VirtualRun
- Cycling: Ride, VirtualRide, MountainBikeRide, GravelRide, EBikeRide
- Hiking & Walking: Hike, Walk
- Swimming: Swim
- Yoga: Yoga
- Gym: WeightTraining, Workout, Crossfit, StairStepper, Elliptical, Rowing, RockClimbing
- Other: AlpineSki, BackcountrySki, Canoeing, Kayaking, Snowboard, Surfing

**Usage**:
```python
from src.lib.strava_converter import StravaActivityTypeMapper
from src.types.exercise import ExerciseType

exercise_type = StravaActivityTypeMapper.map_type("Run")
# Returns: ExerciseType.RUNNING
```

### 2. StravaToExerciseConverter

Converts Strava activities to ExerciseSession objects compatible with Onsendo's ExerciseManager.

**Features**:
- Maps all activity metadata (distance, duration, calories, elevation)
- Combines GPS, altitude, heart rate, and velocity streams into unified data points
- Determines indoor/outdoor status automatically
- Calculates elevation gain if not provided by API
- Preserves activity name and description as notes

**Data Point Fields**:
- Timestamp (datetime)
- Latitude/Longitude (GPS coordinates)
- Elevation (meters)
- Heart rate (BPM)
- Speed (m/s)
- Distance (km, cumulative)

**Usage**:
```python
from src.lib.strava_converter import StravaToExerciseConverter

# Get activity and streams from client
activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678)

# Convert to ExerciseSession
session = StravaToExerciseConverter.convert(activity, streams)

# Store in database
from src.lib.exercise_manager import ExerciseDataManager
manager = ExerciseDataManager(db_session)
manager.store_session(session)
```

### 3. StravaToHeartRateConverter

Converts Strava heart rate streams to HeartRateSession objects compatible with Onsendo's HeartRateManager.

**Features**:
- Extracts heart rate time-series data
- Combines with time stream for accurate timestamps
- Handles missing time stream by estimating 1-second intervals
- Creates HeartRateSession with proper metadata

**Usage**:
```python
from src.lib.strava_converter import StravaToHeartRateConverter

# Get activity with heart rate stream
activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678, ["heartrate", "time"])

if "heartrate" in streams:
    hr_session = StravaToHeartRateConverter.convert(
        activity, streams["heartrate"]
    )

    # Store in database
    from src.lib.heart_rate_manager import HeartRateDataManager
    hr_manager = HeartRateDataManager(db_session)
    hr_manager.store_session(hr_session)
```

### 4. StravaFileExporter

Exports Strava activities to standard file formats for offline storage and compatibility with other tools.

#### export_to_gpx()

Exports GPS route with elevation and heart rate to GPX format (XML).

**Requirements**:
- Must have `time` and `latlng` streams
- Optional: `altitude` stream for elevation
- Optional: `heartrate` stream for HR data

**GPX Features**:
- Standard GPX 1.1 format
- Track metadata (name, timestamp, activity type)
- Track points with lat/lon/elevation/time
- Heart rate in GPX extensions

**Usage**:
```python
from pathlib import Path
from src.lib.strava_converter import StravaFileExporter

activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678)

StravaFileExporter.export_to_gpx(
    activity,
    streams,
    Path("data/strava/activities/morning_run.gpx")
)
```

**Output Example**:
```xml
<?xml version='1.0' encoding='UTF-8'?>
<gpx version="1.1" creator="Onsendo Strava Integration">
  <metadata>
    <name>Morning Run</name>
    <time>2025-11-10T06:30:00Z</time>
  </metadata>
  <trk>
    <name>Morning Run</name>
    <type>Run</type>
    <trkseg>
      <trkpt lat="33.2794" lon="131.5006">
        <ele>45.2</ele>
        <time>2025-11-10T06:30:00Z</time>
        <extensions>
          <hr>142</hr>
        </extensions>
      </trkpt>
      <!-- ... more track points -->
    </trkseg>
  </trk>
</gpx>
```

#### export_to_json()

Exports complete activity data including all streams to JSON format.

**Features**:
- All activity metadata (distance, duration, heart rate, speed, etc.)
- All stream data (GPS, altitude, HR, cadence, watts, etc.)
- Human-readable format
- Easy to parse for custom tools

**Usage**:
```python
from pathlib import Path
from src.lib.strava_converter import StravaFileExporter

activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678)

StravaFileExporter.export_to_json(
    activity,
    streams,
    Path("data/strava/activities/morning_run.json")
)
```

**Output Example**:
```json
{
  "id": 12345678,
  "name": "Morning Run",
  "type": "Run",
  "sport_type": "Run",
  "start_date": "2025-11-10T06:30:00",
  "distance_m": 5240.5,
  "moving_time_s": 1680,
  "elapsed_time_s": 1740,
  "total_elevation_gain_m": 42.3,
  "calories": 425,
  "has_heartrate": true,
  "average_heartrate": 152.4,
  "max_heartrate": 178,
  "streams": {
    "time": {
      "data": [0, 1, 2, 3, ...],
      "original_size": 1680,
      "resolution": "high"
    },
    "latlng": {
      "data": [[33.2794, 131.5006], [33.2795, 131.5007], ...],
      "original_size": 1680,
      "resolution": "high"
    },
    "heartrate": {
      "data": [120, 125, 130, 135, ...],
      "original_size": 1680,
      "resolution": "high"
    }
  }
}
```

#### export_hr_to_csv()

Exports heart rate data to simple CSV format for easy analysis.

**Requirements**:
- Must have `heartrate` stream
- Optional: `time` stream for accurate timestamps (otherwise estimates 1s intervals)

**CSV Format**:
```csv
timestamp,heart_rate
2025-11-10T06:30:00,120
2025-11-10T06:30:01,125
2025-11-10T06:30:02,130
```

**Usage**:
```python
from pathlib import Path
from src.lib.strava_converter import StravaFileExporter

activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678, ["heartrate", "time"])

StravaFileExporter.export_hr_to_csv(
    activity,
    streams["heartrate"],
    streams.get("time"),
    Path("data/strava/activities/morning_run_hr.csv")
)
```

## Error Handling

All converter and exporter methods raise appropriate exceptions:

- **StravaConversionError**: Data conversion failed (missing required fields, invalid data)
- **StravaFileError**: File write operation failed (permissions, disk space, etc.)

Example error handling:
```python
from src.types.strava import StravaConversionError, StravaFileError

try:
    StravaFileExporter.export_to_gpx(activity, streams, output_path)
except StravaConversionError as e:
    print(f"Conversion error: {e}")
    print("Make sure activity has GPS data (time and latlng streams)")
except StravaFileError as e:
    print(f"File error: {e}")
    print("Check file permissions and disk space")
```

## Validation & Testing

All components have been validated:

✓ All converter classes import successfully
✓ Activity type mapping works correctly (30+ types)
✓ ExerciseSession conversion preserves all fields
✓ HeartRateSession conversion preserves timestamps and HR data
✓ GPX export creates valid XML structure
✓ JSON export includes all activity and stream data
✓ CSV export creates valid CSV with headers
✓ Error handling raises appropriate exceptions

## Integration with Existing Systems

### ExerciseManager Compatibility

The StravaToExerciseConverter creates ExerciseSession objects that are fully compatible with the existing ExerciseDataManager:

```python
from src.lib.exercise_manager import ExerciseDataManager
from src.lib.strava_converter import StravaToExerciseConverter

# Convert Strava activity
session = StravaToExerciseConverter.convert(activity, streams)

# Store using existing manager
manager = ExerciseDataManager(db_session)
stored_session = manager.store_session(session)

# Link to visit if needed
from src.lib.exercise_manager import ExerciseSessionLinkManager
link_manager = ExerciseSessionLinkManager(db_session)
link_manager.link_to_visit(stored_session.id, visit_id)
```

### HeartRateManager Compatibility

The StravaToHeartRateConverter creates HeartRateSession objects compatible with HeartRateDataManager:

```python
from src.lib.heart_rate_manager import HeartRateDataManager
from src.lib.strava_converter import StravaToHeartRateConverter

# Convert Strava heart rate stream
hr_session = StravaToHeartRateConverter.convert(activity, hr_stream)

# Store using existing manager
hr_manager = HeartRateDataManager(db_session)
stored_hr = hr_manager.store_session(hr_session)

# Link to visit if needed
hr_manager.link_to_visit(stored_hr.id, visit_id)
```

### File Format Compatibility

Exported files are compatible with existing importers:

**GPX → ExerciseManager**:
```bash
poetry run onsendo exercise import data/strava/activities/run.gpx
```

**JSON → ExerciseManager** (if JSON importer supports Strava format):
```bash
poetry run onsendo exercise import data/strava/activities/run.json --format json
```

**CSV → HeartRateManager**:
```bash
poetry run onsendo heart-rate import data/strava/activities/run_hr.csv --format csv
```

## Example Workflows

### Workflow 1: Download and Store Exercise

```python
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaToExerciseConverter
from src.lib.exercise_manager import ExerciseDataManager
from src.types.strava import StravaSettings

# 1. Setup
settings = StravaSettings.from_env()
client = StravaClient(settings.credentials, settings.token_path)
manager = ExerciseDataManager(db_session)

# 2. Fetch activity
activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678)

# 3. Convert
session = StravaToExerciseConverter.convert(activity, streams)

# 4. Store
stored = manager.store_session(session)
print(f"Stored exercise session: {stored.id}")
```

### Workflow 2: Download, Export, and Import

```python
from pathlib import Path
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaFileExporter
from src.types.strava import StravaSettings

# 1. Setup
settings = StravaSettings.from_env()
client = StravaClient(settings.credentials, settings.token_path)

# 2. Fetch activity
activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678)

# 3. Export to GPX
gpx_path = Path("data/strava/activities/morning_run.gpx")
StravaFileExporter.export_to_gpx(activity, streams, gpx_path)

# 4. Import using existing CLI command
import subprocess
subprocess.run([
    "poetry", "run", "onsendo", "exercise", "import",
    str(gpx_path), "--format", "gpx"
])
```

### Workflow 3: Extract Heart Rate Only

```python
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaToHeartRateConverter
from src.lib.heart_rate_manager import HeartRateDataManager
from src.types.strava import StravaSettings

# 1. Setup
settings = StravaSettings.from_env()
client = StravaClient(settings.credentials, settings.token_path)
hr_manager = HeartRateDataManager(db_session)

# 2. Fetch activity with HR stream only
activity = client.get_activity(12345678)
streams = client.get_activity_streams(12345678, ["heartrate", "time"])

# 3. Check if HR data exists
if "heartrate" in streams:
    # 4. Convert
    hr_session = StravaToHeartRateConverter.convert(
        activity, streams["heartrate"]
    )

    # 5. Store
    stored = hr_manager.store_session(hr_session)
    print(f"Stored HR session: {stored.id}")
else:
    print("Activity does not have heart rate data")
```

## Next Steps (Phase 4-6)

Phase 3 is now complete. Remaining phases:

**Phase 4: Interactive Browser**
- Create `strava-browse-interactive` command
- Display activity list with selection menu
- Download → View → Import → Link workflow
- Real-time progress indicators

**Phase 5: Quick Commands**
- `strava-download <activity_id>` - Download single activity
- `strava-sync` - Sync recent activities
- `strava-link` - Link downloaded activity to visit

**Phase 6: Polish & Documentation**
- Comprehensive error messages
- Makefile targets
- README documentation
- User guide with screenshots

## Command to Continue

To proceed with Phase 4:
```
implement strava phase 4
```

## Recovery Information

If context is lost, use:
```
where am i strava
```

This will show current implementation status and next steps.
