#!/bin/bash

# Heart Rate Data Manager - Master Script
# Provides easy access to all heart rate management functions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}   Heart Rate Data Manager    ${NC}"
    echo -e "${PURPLE}================================${NC}"
    echo ""
}

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

print_help() {
    echo -e "${CYAN}[HELP]${NC} $1"
}

# Function to show main menu
show_main_menu() {
    print_header
    echo "Available commands:"
    echo ""
    echo -e "${GREEN}1.${NC}  Setup directories    - Create recommended directory structure"
    echo -e "${GREEN}2.${NC}  Import single file   - Import one heart rate data file"
    echo -e "${GREEN}3.${NC}  Batch import        - Import multiple files from directory"
    echo -e "${GREEN}4.${NC}  View status         - Show current heart rate data status"
    echo -e "${GREEN}5.${NC}  Maintenance         - Cleanup, archive, backup operations"
    echo -e "${GREEN}6.${NC}  Quick import        - Quick import with common options"
    echo -e "${GREEN}7.${NC}  Help                - Show detailed help for each command"
    echo -e "${GREEN}8.${NC}  Exit                - Exit the manager"
    echo ""
}

# Function to show detailed help
show_detailed_help() {
    print_header
    echo "Detailed Help for Heart Rate Management"
    echo "======================================"
    echo ""
    
    echo -e "${GREEN}1. Setup Directories${NC}"
    echo "   Creates the recommended directory structure for organizing heart rate data."
    echo "   Usage: ./scripts/setup_heart_rate_dirs.sh [options]"
    echo "   Options: --create-examples, --permissions, --base-dir DIR"
    echo ""
    
    echo -e "${GREEN}2. Import Single File${NC}"
    echo "   Imports one heart rate data file with validation and confirmation."
    echo "   Usage: ./scripts/heart_rate_import.sh [file_path] [format] [notes]"
    echo "   Formats: csv, json, text, apple_health"
    echo ""
    
    echo -e "${GREEN}3. Batch Import${NC}"
    echo "   Imports multiple files from a directory with parallel processing."
    echo "   Usage: ./scripts/heart_rate_batch_import.sh [directory] [options]"
    echo "   Options: --recursive, --format, --notes, --dry-run, --workers"
    echo ""
    
    echo -e "${GREEN}4. View Status${NC}"
    echo "   Shows current heart rate data status and statistics."
    echo "   Usage: ./scripts/heart_rate_maintenance.sh status"
    echo ""
    
    echo -e "${GREEN}5. Maintenance${NC}"
    echo "   Various maintenance operations for heart rate data."
    echo "   Usage: ./scripts/heart_rate_maintenance.sh [command]"
    echo "   Commands: cleanup, archive, backup, validate"
    echo ""
    
    echo -e "${GREEN}6. Quick Import${NC}"
    echo "   Quick import with common options for Apple Health and CSV files."
    echo "   Automatically detects format and provides guided import."
    echo ""
    
    echo "Press Enter to return to main menu..."
    read
}

# Function to run setup directories
run_setup_directories() {
    print_status "Running directory setup..."
    ./scripts/setup_heart_rate_dirs.sh "$@"
}

# Function to run single file import
run_single_import() {
    print_status "Running single file import..."
    ./scripts/heart_rate_import.sh "$@"
}

# Function to run batch import
run_batch_import() {
    print_status "Running batch import..."
    ./scripts/heart_rate_batch_import.sh "$@"
}

# Function to run maintenance
run_maintenance() {
    print_status "Running maintenance operations..."
    ./scripts/heart_rate_maintenance.sh "$@"
}

# Function to run quick import
run_quick_import() {
    print_header
    echo "Quick Import - Common Heart Rate Data Import"
    echo "==========================================="
    echo ""
    
    # Get file path
    read -p "Enter file path: " FILE_PATH
    
    if [ ! -f "$FILE_PATH" ]; then
        print_error "File not found: $FILE_PATH"
        return 1
    fi
    
    # Auto-detect format based on file extension and content
    print_status "Auto-detecting file format..."
    
    if [[ "$FILE_PATH" == *.health ]]; then
        FORMAT="apple_health"
        print_status "Detected Apple Health format"
    elif [[ "$FILE_PATH" == *.csv ]]; then
        # Check if it's Apple Health format by looking at first line
        if head -n 1 "$FILE_PATH" | grep -q "SampleType"; then
            FORMAT="apple_health"
            print_status "Detected Apple Health CSV format"
        else
            FORMAT="csv"
            print_status "Detected standard CSV format"
        fi
    elif [[ "$FILE_PATH" == *.json ]]; then
        FORMAT="json"
        print_status "Detected JSON format"
    elif [[ "$FILE_PATH" == *.txt ]]; then
        FORMAT="text"
        print_status "Detected text format"
    else
        print_warning "Could not auto-detect format. Please specify manually."
        read -p "Enter format (csv/json/text/apple_health): " FORMAT
    fi
    
    # Get notes
    read -p "Enter notes (optional): " NOTES
    
    # Run import
    print_status "Running import with detected format: $FORMAT"
    ./scripts/heart_rate_import.sh "$FILE_PATH" "$FORMAT" "$NOTES"
}

# Function to check if scripts exist
check_scripts() {
    local missing_scripts=()
    
    for script in setup_heart_rate_dirs.sh heart_rate_import.sh heart_rate_batch_import.sh heart_rate_maintenance.sh; do
        if [ ! -f "scripts/$script" ]; then
            missing_scripts+=("$script")
        fi
    done
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        print_error "Missing required scripts:"
        for script in "${missing_scripts[@]}"; do
            echo "  - scripts/$script"
        done
        echo ""
        print_error "Please ensure all scripts are present in the scripts/ directory."
        exit 1
    fi
}

# Main script logic
main() {
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ] || [ ! -d "scripts" ]; then
        print_error "This script must be run from the onsendo project root directory."
        exit 1
    fi
    
    # Check if required scripts exist
    check_scripts
    
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
    
    # Main loop
    while true; do
        show_main_menu
        read -p "Enter your choice (1-8): " -n 1 -r
        echo ""
        echo ""
        
        case $REPLY in
            1)
                print_status "Setup directories selected"
                read -p "Create example files? (y/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    run_setup_directories --create-examples
                else
                    run_setup_directories
                fi
                ;;
            2)
                print_status "Single file import selected"
                read -p "Enter file path: " FILE_PATH
                read -p "Enter format (optional): " FORMAT
                read -p "Enter notes (optional): " NOTES
                run_single_import "$FILE_PATH" "$FORMAT" "$NOTES"
                ;;
            3)
                print_status "Batch import selected"
                read -p "Enter directory path: " DIRECTORY
                read -p "Search recursively? (y/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    run_batch_import "$DIRECTORY" --recursive
                else
                    run_batch_import "$DIRECTORY"
                fi
                ;;
            4)
                print_status "View status selected"
                run_maintenance status
                ;;
            5)
                print_status "Maintenance selected"
                echo "Available maintenance commands:"
                echo "  cleanup, archive, backup, validate"
                read -p "Enter command: " MAINT_CMD
                run_maintenance "$MAINT_CMD"
                ;;
            6)
                run_quick_import
                ;;
            7)
                show_detailed_help
                ;;
            8)
                print_success "Exiting Heart Rate Data Manager"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter a number between 1 and 8."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        echo ""
    done
}

# Run main function
main "$@"
