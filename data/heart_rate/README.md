# Heart Rate Data Directory

This directory contains all heart rate data files organized by device type and date.

## Directory Structure

- **raw/**: Original files from devices (never modify these)
  - **apple_health/**: Apple Health exports
  - **garmin/**: Garmin exports  
  - **fitbit/**: Fitbit exports
  - **other/**: Other device formats
- **processed/**: Cleaned/validated files
- **archived/**: Old files you want to keep
- **imports/**: Files currently being imported

## File Naming Convention

Use descriptive names with dates:
- `workout_morning_run_2025_08_15.csv`
- `sleep_night_2025_08_15.csv`
- `daily_resting_2025_08_15.csv`

## Monthly Organization

Files are organized by year and month:
- `2025_08/` for August 2025
- `2025_09/` for September 2025

## Import Workflow

1. Export from device to appropriate `raw/[device]/[YYYY_MM]/` directory
2. Import using: `poetry run onsendo heart-rate import [file_path] --format [format]`
3. Move processed files to `processed/` or `archived/` directories
