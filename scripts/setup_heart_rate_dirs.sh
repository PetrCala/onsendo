#!/bin/bash

# Heart Rate Directory Setup Script
# Creates the recommended directory structure for heart rate data management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --base-dir DIR     Base directory for heart rate data (default: data/heart_rate)"
    echo "  --create-examples  Create example files and directories"
    echo "  --permissions      Set restrictive file permissions (600) for privacy"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --base-dir /opt/heart_rate_data"
    echo "  $0 --create-examples --permissions"
}

# Default base directory
BASE_DIR="data/heart_rate"
CREATE_EXAMPLES=false
SET_PERMISSIONS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        --create-examples)
            CREATE_EXAMPLES=true
            shift
            ;;
        --permissions)
            SET_PERMISSIONS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

print_status "Setting up heart rate directory structure in: $BASE_DIR"

# Create main directory structure
print_status "Creating directory structure..."

mkdir -p "$BASE_DIR"/{raw,processed,archived,imports}
mkdir -p "$BASE_DIR/raw"/{apple_health,garmin,fitbit,other}

# Create monthly subdirectories for the current year and next year
CURRENT_YEAR=$(date +%Y)
NEXT_YEAR=$((CURRENT_YEAR + 1))

for year in $CURRENT_YEAR $NEXT_YEAR; do
    for month in {01..12}; do
        mkdir -p "$BASE_DIR/raw/apple_health/${year}_${month}"
        mkdir -p "$BASE_DIR/raw/garmin/${year}_${month}"
        mkdir -p "$BASE_DIR/raw/fitbit/${year}_${month}"
        mkdir -p "$BASE_DIR/raw/other/${year}_${month}"
    done
done

print_success "Directory structure created successfully!"

# Create README files in key directories
print_status "Creating documentation files..."

cat > "$BASE_DIR/README.md" << 'EOF'
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
EOF

cat > "$BASE_DIR/raw/README.md" << 'EOF'
# Raw Data Directory

This directory contains original heart rate data files from your devices.

## Important Rules

- **NEVER modify these files** - they are your source of truth
- **Keep backups** of important data
- **Use descriptive names** when exporting from devices
- **Organize by device type** and date

## Device-Specific Notes

### Apple Health
- Export to `apple_health/[YYYY_MM]/`
- Use `--format apple_health` when importing

### Garmin
- Export to `garmin/[YYYY_MM]/`
- Usually use `--format csv` when importing

### Fitbit
- Export to `fitbit/[YYYY_MM]/`
- Usually use `--format csv` when importing

### Other Devices
- Export to `other/[YYYY_MM]/`
- Determine format with `--validate-only` flag first
EOF

cat > "$BASE_DIR/processed/README.md" << 'EOF'
# Processed Data Directory

This directory contains heart rate data files that have been:
- Successfully imported into the database
- Validated for quality
- Processed and cleaned

## When to Use

- Store files after successful import
- Keep for reference and analysis
- Use for data recovery if needed

## Organization

Consider organizing by:
- Date ranges
- Activity types
- Data quality levels
EOF

cat > "$BASE_DIR/archived/README.md" << 'EOF'
# Archived Data Directory

This directory contains old heart rate data files that you want to keep but don't need immediate access to.

## When to Archive

- Files older than 6 months
- Data that has been successfully imported
- Historical records for long-term analysis

## Organization

Consider organizing by:
- Year and month
- Device type
- Activity categories

## Backup Strategy

- Regular backups of this directory
- Consider compression for long-term storage
- Verify integrity periodically
EOF

print_success "Documentation files created!"

# Set file permissions if requested
if [ "$SET_PERMISSIONS" = true ]; then
    print_status "Setting restrictive file permissions for privacy..."
    
    # Set directory permissions to 700 (owner read/write/execute)
    find "$BASE_DIR" -type d -exec chmod 700 {} \;
    
    # Set file permissions to 600 (owner read/write only)
    find "$BASE_DIR" -type f -exec chmod 600 {} \;
    
    print_success "File permissions set for privacy!"
fi

# Create example files if requested
if [ "$CREATE_EXAMPLES" = true ]; then
    print_status "Creating example files..."
    
    # Get current year and month for example files
    CURRENT_YEAR_MONTH=$(date +%Y_%m)
    
    # Ensure the directories exist before creating files
    mkdir -p "$BASE_DIR/raw/apple_health/$CURRENT_YEAR_MONTH"
    mkdir -p "$BASE_DIR/raw/garmin/$CURRENT_YEAR_MONTH"
    
    # Create example Apple Health file
    cat > "$BASE_DIR/raw/apple_health/$CURRENT_YEAR_MONTH/example_apple_health.csv" << 'EOF'
"SampleType","SampleRate","StartTime","Data"
"HEART_RATE",1,"2025-08-15T10:00:00.000Z","72;74;73;75;76;80;82;85;87"
"HEART_RATE",1,"2025-08-15T10:01:00.000Z","88;90;92;95;98;100;102;105;108"
EOF

    # Create example CSV file
    cat > "$BASE_DIR/raw/garmin/$CURRENT_YEAR_MONTH/example_garmin.csv" << 'EOF'
timestamp,heart_rate,confidence
2025-08-15 10:00:00,72,0.95
2025-08-15 10:01:00,75,0.92
2025-08-15 10:02:00,78,0.89
EOF

    print_success "Example files created!"
fi

# Create a .gitignore file for the heart rate directory
cat > "$BASE_DIR/.gitignore" << 'EOF'
# Ignore all heart rate data files by default
# Uncomment specific patterns if you want to track certain files

# Ignore all data files
*.csv
*.json
*.txt
*.health

# Ignore all subdirectories
*/

# But allow README files
!README.md
!.gitignore

# Allow specific example files if needed
# !example_*.csv
# !example_*.json
EOF

print_success ".gitignore file created!"

# Show final structure
print_status "Final directory structure:"
echo ""
tree "$BASE_DIR" 2>/dev/null || find "$BASE_DIR" -type d | sort

echo ""
print_success "Heart rate directory setup completed!"
echo ""
print_status "Next steps:"
echo "1. Export heart rate data from your devices to the appropriate raw subdirectories"
echo "2. Use the import scripts to add data to your database"
echo "3. Organize processed files in the processed/ and archived/ directories"
echo ""
print_status "Useful commands:"
echo "- Import single file: ./scripts/heart_rate_import.sh [file_path] [format]"
echo "- Batch import: ./scripts/heart_rate_batch_import.sh [directory] --recursive"
echo "- Maintenance: ./scripts/heart_rate_maintenance.sh status"
