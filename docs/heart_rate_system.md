# Heart Rate Data System

The heart rate data system provides a robust way to import, validate, and manage heart rate data from various sources (smart watches, fitness trackers, etc.) and link it to onsen visits.

## Features

- **Multi-format Support**: Import from CSV, JSON, and plain text files
- **Data Validation**: Comprehensive quality checks before storage
- **File Integrity**: SHA-256 hashing for data integrity verification
- **Visit Linking**: Easy linking of heart rate data to onsen visits
- **Batch Import**: Process multiple files efficiently with parallel processing
- **Robust Error Handling**: Graceful handling of malformed data and errors

## Supported File Formats

### CSV Format

```csv
timestamp,heart_rate,confidence
2024-01-15 10:00:00,72,0.95
2024-01-15 10:01:00,75,0.92
```

### JSON Format

```json
[
  {"timestamp": "2024-01-15T10:00:00", "heart_rate": 72, "confidence": 0.95},
  {"timestamp": "2024-01-15T10:01:00", "heart_rate": 75, "confidence": 0.92}
]
```

### Text Format

```plain
2024-01-15 10:00:00,72,0.95
2024-01-15 10:01:00,75,0.92
```

## Data Validation

The system performs comprehensive validation to ensure data quality:

- **Duration Checks**: Minimum 1 minute, maximum 24 hours
- **Data Point Count**: Minimum 5 measurements
- **Heart Rate Range**: 30-220 BPM (physiologically reasonable)
- **Data Gaps**: Warns about suspicious time gaps (>5 minutes)
- **Variation**: Ensures reasonable heart rate variation

## CLI Commands

### Import Single File

```bash
# Import a heart rate data file
onsendo heart-rate import path/to/data.csv

# Force specific format
onsendo heart-rate import path/to/data.csv --format csv

# Add notes
onsendo heart-rate import path/to/data.csv --notes "Morning workout session"

# Validate only (don't store)
onsendo heart-rate import path/to/data.csv --validate-only
```

### Batch Import

```bash
# Import all heart rate files from a directory
onsendo heart-rate batch-import /path/to/heart_rate_files/

# Recursive search
onsendo heart-rate batch-import /path/to/heart_rate_files/ --recursive

# Dry run to see what would be imported
onsendo heart-rate batch-import /path/to/heart_rate_files/ --dry-run

# Use 8 parallel workers
onsendo heart-rate batch-import /path/to/heart_rate_files/ --max-workers 8
```

### Manage Records

```bash
# List all heart rate records
onsendo heart-rate list list

# Show only unlinked records
onsendo heart-rate list list --unlinked-only

# Show details including file integrity
onsendo heart-rate list list --details

# Link heart rate data to a visit
onsendo heart-rate list link 123 456  # Link HR record 123 to visit 456

# Unlink heart rate data from visit
onsendo heart-rate list unlink 123

# Delete a record
onsendo heart-rate list delete 123

# Force delete without confirmation
onsendo heart-rate list delete 123 --force
```

## Integration with Onsen Visits

### During Visit Creation

When adding a visit interactively, you can link heart rate data:

1. Run `onsendo visit add-interactive`
2. When prompted for heart rate data, enter:
   - `list` to see available unlinked records
   - A specific record ID to link
   - Press Enter to skip

### Manual Linking

```bash
# Link existing heart rate data to a visit
onsendo heart-rate list link 123 456
```

## Database Schema

The system creates a `heart_rate_data` table with:

- **id**: Primary key
- **visit_id**: Foreign key to onsen_visits (optional)
- **recording_start/end**: Session timestamps
- **data_format**: File format (csv, json, text)
- **data_file_path**: Path to original file
- **data_hash**: SHA-256 hash for integrity
- **average/min/max_heart_rate**: Statistical summary
- **total_recording_minutes**: Duration
- **data_points_count**: Number of measurements
- **notes**: Optional user notes
- **created_at**: Record creation timestamp

## Workflow Example

1. **Export Data**: Export heart rate data from your device to CSV/JSON
2. **Import**: Use `onsendo heart-rate import` to import the file
3. **Validate**: System automatically validates data quality
4. **Store**: Data is stored with file integrity checks
5. **Link**: During visit creation, link the heart rate data
6. **Analyze**: Access heart rate data through the database

## Error Handling

The system is designed to be robust:

- **Malformed Files**: Graceful error messages with specific issues
- **Validation Failures**: Clear explanation of quality problems
- **Database Errors**: Rollback on failures, clear error reporting
- **File Integrity**: Automatic hash verification
- **Missing Files**: Clear warnings when source files are not found

## Best Practices

1. **Data Quality**: Ensure your device exports clean, consistent data
2. **File Organization**: Use descriptive filenames and organize by date
3. **Backup**: Keep original device exports as backup
4. **Validation**: Use `--validate-only` flag to check data before importing
5. **Batch Processing**: Use batch import for multiple files
6. **Notes**: Add descriptive notes during import for better organization

## Troubleshooting

### Common Issues

- **"File not found"**: Check file path and permissions
- **"Invalid data format"**: Ensure file matches expected format
- **"Validation failed"**: Review data quality issues reported
- **"Database error"**: Check database connection and permissions

### Data Quality Issues

- **Too few data points**: Ensure at least 5 measurements
- **Unrealistic heart rates**: Check for sensor errors or data corruption
- **Large time gaps**: Verify data export completeness
- **Low variation**: May indicate sensor malfunction

## Future Enhancements

- **More Formats**: Support for FIT, TCX, and other fitness formats
- **Advanced Analytics**: Heart rate variability, recovery metrics
- **Device Integration**: Direct import from popular fitness platforms
- **Visualization**: Charts and graphs for heart rate trends
- **Export**: Export processed data in various formats
