#!/bin/bash

# Heart Rate Data Batch Import Script
# Usage: ./heart_rate_batch_import.sh [directory] [options]

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
    echo "Usage: $0 [directory] [options]"
    echo ""
    echo "Arguments:"
    echo "  directory    Directory containing heart rate data files (required)"
    echo ""
    echo "Options:"
    echo "  --recursive  Search subdirectories recursively"
    echo "  --format     Force specific format for all files (csv, json, text, apple_health)"
    echo "  --notes      Add notes to all imported sessions"
    echo "  --dry_run    Show what would be imported without storing data"
    echo "  --workers    Maximum number of parallel workers (default: 4)"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 data/heart_rate/raw/apple_health/2025_08/"
    echo "  $0 data/heart_rate/raw/ --recursive --format apple_health"
    echo "  $0 data/heart_rate/raw/ --recursive --notes 'August 2025 data' --dry_run"
    echo "  $0 data/heart_rate/raw/ --recursive --workers 8"
}

# Parse command line arguments
DIRECTORY=""
RECURSIVE=false
FORMAT=""
NOTES=""
DRY_RUN=false
WORKERS=4

while [[ $# -gt 0 ]]; do
    case $1 in
        --recursive)
            RECURSIVE=true
            shift
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --notes)
            NOTES="$2"
            shift 2
            ;;
        --dry_run)
            DRY_RUN=true
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$DIRECTORY" ]; then
                DIRECTORY="$1"
            else
                print_error "Multiple directories specified. Only one allowed."
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if directory is specified
if [ -z "$DIRECTORY" ]; then
    print_error "Directory is required"
    show_usage
    exit 1
fi

# Check if directory exists
if [ ! -d "$DIRECTORY" ]; then
    print_error "Directory not found: $DIRECTORY"
    exit 1
fi

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

print_status "Starting batch import from: $DIRECTORY"

# Build the command
CMD="poetry run onsendo heart-rate batch-import \"$DIRECTORY\""

if [ "$RECURSIVE" = true ]; then
    CMD="$CMD --recursive"
    print_status "Searching subdirectories recursively"
fi

if [ -n "$FORMAT" ]; then
    CMD="$CMD --format $FORMAT"
    print_status "Using forced format: $FORMAT"
fi

if [ -n "$NOTES" ]; then
    CMD="$CMD --notes \"$NOTES\""
    print_status "Adding notes: $NOTES"
fi

if [ "$DRY_RUN" = true ]; then
    CMD="$CMD --dry-run"
    print_status "Running in dry-run mode (no data will be stored)"
fi

CMD="$CMD --max-workers $WORKERS"
print_status "Using $WORKERS parallel workers"

# Show what will be imported
print_status "Scanning for heart rate data files..."
if [ "$RECURSIVE" = true ]; then
    FILE_COUNT=$(find "$DIRECTORY" -type f \( -name "*.csv" -o -name "*.json" -o -name "*.txt" -o -name "*.health" \) | wc -l)
else
    FILE_COUNT=$(find "$DIRECTORY" -maxdepth 1 -type f \( -name "*.csv" -o -name "*.json" -o -name "*.txt" -o -name "*.health" \) | wc -l)
fi

if [ "$FILE_COUNT" -eq 0 ]; then
    print_warning "No heart rate data files found in $DIRECTORY"
    exit 0
fi

print_status "Found $FILE_COUNT potential heart rate data files"

# Show file list if not too many
if [ "$FILE_COUNT" -le 20 ]; then
    print_status "Files to be processed:"
    if [ "$RECURSIVE" = true ]; then
        find "$DIRECTORY" -type f \( -name "*.csv" -o -name "*.json" -o -name "*.txt" -o -name "*.health" \) | sort
    else
        find "$DIRECTORY" -maxdepth 1 -type f \( -name "*.csv" -o -name "*.json" -o -name "*.txt" -o -name "*.health" \) | sort
    fi
    echo ""
fi

# Ask for confirmation
if [ "$DRY_RUN" = false ]; then
    echo ""
    read -p "Proceed with importing $FILE_COUNT files? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Batch import cancelled by user."
        exit 0
    fi
fi

# Execute the batch import
print_status "Executing batch import..."
if eval "$CMD"; then
    if [ "$DRY_RUN" = true ]; then
        print_success "Dry run completed successfully!"
    else
        print_success "Batch import completed successfully!"
        
        # Show summary
        print_status "Import summary:"
        poetry run onsendo heart-rate list
    fi
else
    print_error "Batch import failed. Please check the error messages above."
    exit 1
fi
