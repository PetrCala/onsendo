# Heart Rate Data Examples

This directory contains example files demonstrating the heart rate data system, including mock data generation and various export formats.

## Mock Data Generation

### `demo_mock_heart_rate.py`

A comprehensive demonstration script that shows how to:

- Generate realistic mock heart rate sessions (resting, workout, sleep)
- Create daily activity patterns
- Export data in multiple formats (CSV, JSON, Apple Health)
- Combine multiple sessions into realistic scenarios

Run with:

```bash
poetry run python examples/heart_rate/demo_mock_heart_rate.py
```

## Sample Data Files

### 🚫 Documentation Examples (Not for Import)

These files are meant to demonstrate file formats and are **NOT suitable for import**:

- **`apple_health_sample.csv`** - Simple example of Apple Health CSV format (minimal data)
- **`heart_rate_sample.csv`** - Standard CSV format example (minimal data)
- **`mock_sleep_apple_health.csv`** - Generated sleep session in Apple Health format (minimal data)

### ✅ Import-Ready Files

These files contain realistic data and **CAN be imported** for testing:

- **`resting_session.csv`** - Generated resting session in standard CSV format
- **`workout_apple_health.csv`** - Generated workout session in Apple Health format  
- **`sleep_session.json`** - Generated sleep session in JSON format
- **`daily_sessions.txt`** - Text summary of multiple daily sessions
- **`mixed_scenario_apple_health.csv`** - Combined daily + workout sessions

> **Note**: When using the heart rate import system, focus on the import-ready files. The documentation examples are too minimal and will fail validation.

## Apple Health CSV Format

The Apple Health format follows this structure:

```csv
"SampleType","SampleRate","StartTime","Data"
"HEART_RATE",1,"2025-08-11T15:24:12.000Z","72;74;73;75;76;80;82;85;87"
"HEART_RATE",1,"2025-08-11T15:25:12.000Z","88;90;92;95;98;100;102;105;108"
```

Where:

- **SampleType**: Always "HEART_RATE" for heart rate data
- **SampleRate**: Sampling frequency in Hz (usually 1.0)
- **StartTime**: ISO 8601 timestamp with Z suffix (UTC)
- **Data**: Semicolon-separated heart rate values in BPM

## Using the Examples

### Import Apple Health Data

```python
from src.lib.heart_rate_manager import HeartRateDataImporter

# Import Apple Health CSV
session = HeartRateDataImporter.import_from_file(
    'examples/heart_rate/apple_health_sample.csv', 
    format_hint='apple_health'
)

print(f"Imported {session.data_points_count} data points")
print(f"Duration: {session.duration_minutes} minutes")
print(f"Heart rate range: {session.min_heart_rate}-{session.max_heart_rate} BPM")
```

### Generate Mock Data

```python
from src.testing.mocks.mock_heart_rate_data import create_workout_session

# Create a realistic workout session
session = create_workout_session()

# Export to Apple Health format
session.export_apple_health_format('my_workout.csv')
```

### Create Realistic Scenarios

```python
from src.testing.mocks.mock_heart_rate_data import create_realistic_scenario

# Generate a complete day with multiple sessions
daily_sessions = create_realistic_scenario("daily", num_sessions=4)

# Generate a workout session
workout_sessions = create_realistic_scenario("workout")

# Generate a mixed scenario (daily + workout)
mixed_sessions = create_realistic_scenario("mixed", num_sessions=3)
```

## Data Quality

All generated mock data includes:

- **Realistic heart rate ranges** (40-200 BPM)
- **Physiological patterns** (resting, exercise, recovery, sleep)
- **Time-based variations** (morning vs evening patterns)
- **Confidence scores** for data quality assessment
- **Proper timestamp sequencing** with configurable sample rates

## File Sizes

- **Small samples**: 1-10 KB (short sessions, few data points)
- **Medium sessions**: 10-100 KB (typical workout or daily sessions)
- **Large sessions**: 100+ KB (long sleep sessions, complex scenarios)

## Testing

All examples are covered by comprehensive unit tests:

```bash
# Test mock data generation
poetry run python -m pytest tests/unit/mocks_tests/test_mock_heart_rate_data.py -v

# Test heart rate manager
poetry run python -m pytest tests/unit/lib_tests/test_heart_rate_manager.py -v
```

## Integration

These examples work seamlessly with the main heart rate system:

- Import mock data using the standard import commands
- Validate data quality before storage
- Link to onsen visit records
- Export in any supported format

The mock system is particularly useful for:

- Development and testing
- Demonstrating system capabilities
- Creating training datasets
- Validating import/export functionality
