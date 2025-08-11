#!/bin/bash

# Heart Rate Data Import Script
# Usage: ./heart_rate_import.sh [file_path] [format] [notes]

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
    echo "Usage: $0 [file_path] [format] [notes]"
    echo ""
    echo "Arguments:"
    echo "  file_path    Path to heart rate data file (required)"
    echo "  format       File format: csv, json, text, apple_health (optional, auto-detected if not specified)"
    echo "  notes        Optional notes about the recording session"
    echo ""
    echo "Examples:"
    echo "  $0 data/heart_rate/raw/apple_health/2025_08/workout.csv"
    echo "  $0 data/heart_rate/raw/apple_health/2025_08/workout.csv apple_health"
    echo "  $0 data/heart_rate/raw/apple_health/2025_08/workout.csv apple_health 'Morning workout session'"
    echo ""
    echo "Supported formats:"
    echo "  csv          Standard CSV with timestamp,heart_rate[,confidence] columns"
    echo "  json         JSON array of objects with timestamp and heart_rate fields"
    echo "  text         Plain text with timestamp,heart_rate[,confidence] lines"
    echo "  apple_health Apple Health export format"
}

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed or not in PATH"
    exit 1
fi

# Check if onsendo is available
if ! poetry run onsendo --help &> /dev/null; then
    print_error "Onsendo CLI is not available. Make sure you're in the correct directory."
    exit 1
fi

# Check arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

FILE_PATH="$1"
FORMAT="$2"
NOTES="$3"

# Validate file path
if [ ! -f "$FILE_PATH" ]; then
    print_error "File not found: $FILE_PATH"
    exit 1
fi

print_status "Starting heart rate data import..."

# Build the command
CMD="poetry run onsendo heart-rate import \"$FILE_PATH\""

if [ -n "$FORMAT" ]; then
    CMD="$CMD --format $FORMAT"
    print_status "Using specified format: $FORMAT"
else
    print_status "Auto-detecting file format..."
fi

if [ -n "$NOTES" ]; then
    CMD="$CMD --notes \"$NOTES\""
    print_status "Adding notes: $NOTES"
fi

# First, validate the data
print_status "Validating data before import..."
VALIDATE_CMD="$CMD --validate_only"

if eval "$VALIDATE_CMD"; then
    print_success "Data validation passed!"
else
    print_error "Data validation failed. Please check your file format and data."
    exit 1
fi

# Ask for confirmation before importing
echo ""
read -p "Data validation successful. Proceed with import? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Importing heart rate data..."
    
    if eval "$CMD"; then
        print_success "Heart rate data imported successfully!"
        
        # Show the imported record
        print_status "Fetching imported record details..."
        poetry run onsendo heart-rate list --unlinked_only
        
    else
        print_error "Import failed. Please check the error messages above."
        exit 1
    fi
else
    print_warning "Import cancelled by user."
    exit 0
fi
