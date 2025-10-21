# Exercise Data Examples

This directory contains example exercise data files in various formats that can be imported into Onsendo.

## Example Files

### 1. `example_run.json` - Simple JSON Format
A basic running session with distance, duration, and heart rate data.

### 2. `example_workout.csv` - CSV Format
A CSV file with exercise metadata and optional GPS points.

### 3. `example_route.gpx` - GPX Format
A GPS Exchange Format file with a running route including elevation data.

## Usage

Import any of these example files:

```bash
# JSON format
poetry run onsendo exercise import examples/exercise/example_run.json

# CSV format
poetry run onsendo exercise import examples/exercise/example_workout.csv

# GPX format
poetry run onsendo exercise import examples/exercise/example_route.gpx
```

## Creating Your Own Files

### JSON Format

```json
{
  "exercise_type": "running",
  "activity_name": "Morning Run",
  "start_time": "2025-11-03T07:00:00",
  "end_time": "2025-11-03T07:45:00",
  "distance_km": 8.5,
  "calories_burned": 650,
  "elevation_gain_m": 120,
  "avg_heart_rate": 155,
  "min_heart_rate": 110,
  "max_heart_rate": 175,
  "indoor_outdoor": "outdoor",
  "weather_conditions": "Sunny, 18°C"
}
```

### CSV Format

```csv
type,exercise_type,activity_name,start_time,end_time,distance_km,calories_burned
metadata,running,Morning Run,2025-11-03T07:00:00,2025-11-03T07:45:00,8.5,650
```

### Apple Health Export

Apple Health exports are typically in CSV format with specific column names:

```csv
type,workout_type,start_time,end_time,distance_km,calories,avg_heart_rate,min_heart_rate,max_heart_rate
workout,HKWorkoutActivityTypeRunning,2025-11-03T07:00:00,2025-11-03T07:45:00,8.5,650,155,110,175
```

## Supported Data Formats

- **GPX**: GPS Exchange Format (`.gpx`) - Common for GPS devices and apps
- **TCX**: Training Center XML (`.tcx`) - Used by Garmin and other fitness devices
- **Apple Health**: CSV/XML exports from Apple Health app
- **JSON**: Generic JSON format with exercise metadata
- **CSV**: Simple CSV format with timestamps and metrics

## Exporting from Popular Apps

### Apple Health
1. Open Health app on iPhone
2. Tap your profile picture
3. Export All Health Data
4. Extract the `export.csv` file
5. Use `--format apple_health` when importing

### Garmin Connect
1. Go to Activities
2. Select the workout
3. Export as TCX or GPX
4. Import directly

### Strava
1. Go to your activity
2. Export as GPX
3. Import directly
