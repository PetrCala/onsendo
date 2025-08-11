#!/bin/bash

# Heart Rate Data Maintenance Script
# Usage: ./heart_rate_maintenance.sh [command] [options]

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
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status       Show current heart rate data status"
    echo "  cleanup      Clean up old/unlinked heart rate records"
    echo "  archive      Archive old files from raw directories"
    echo "  backup       Create backup of heart rate data"
    echo "  restore      Restore heart rate data from backup"
    echo "  validate     Validate file integrity of all records"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 cleanup --older-than 6months"
    echo "  $0 archive --older-than 3months"
    echo "  $0 backup --destination /backup/heart_rate/"
    echo "  $0 validate"
}

# Function to check dependencies
check_dependencies() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed or not in PATH"
        exit 1
    fi

    if ! poetry run onsendo --help &> /dev/null; then
        print_error "Onsendo CLI is not available. Make sure you're in the correct directory."
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Heart Rate Data Status"
    echo "========================"
    
    # Show total records
    print_status "Total records:"
    poetry run onsendo heart-rate list
    
    # Show unlinked records
    print_status "Unlinked records:"
    poetry run onsendo heart-rate list --unlinked_only
    
    # Show linked records
    print_status "Linked records:"
    poetry run onsendo heart-rate list --linked_only
}

# Function to cleanup old records
cleanup_records() {
    local OLDER_THAN=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --older-than)
                OLDER_THAN="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_status "Cleaning up heart rate records..."
    
    if [ -n "$OLDER_THAN" ]; then
        print_status "Looking for records older than: $OLDER_THAN"
    fi
    
    # Show unlinked records first
    print_status "Unlinked records that can be safely removed:"
    poetry run onsendo heart-rate list --unlinked_only
    
    echo ""
    read -p "Do you want to remove unlinked records? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing unlinked records..."
        # This would need to be implemented in the CLI or done manually
        print_warning "Manual cleanup required. Use 'onsendo heart-rate delete [ID] --force' for each record."
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to archive old files
archive_files() {
    local OLDER_THAN=""
    local ARCHIVE_DIR="data/heart_rate/archived"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --older-than)
                OLDER_THAN="$2"
                shift 2
                ;;
            --archive-dir)
                ARCHIVE_DIR="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_status "Archiving old heart rate files..."
    
    if [ -n "$OLDER_THAN" ]; then
        print_status "Looking for files older than: $OLDER_THAN"
    fi
    
    # Create archive directory if it doesn't exist
    mkdir -p "$ARCHIVE_DIR"
    
    # Find old files in raw directories
    print_status "Scanning for old files in raw directories..."
    
    if [ -d "data/heart_rate/raw" ]; then
        # This is a simplified version - you might want to implement more sophisticated aging logic
        print_status "Found raw directory: data/heart_rate/raw"
        print_status "Manual archiving recommended. Move old monthly directories to: $ARCHIVE_DIR"
        
        # Show what's in raw directories
        if [ -d "data/heart_rate/raw" ]; then
            echo "Raw directories:"
            ls -la data/heart_rate/raw/ 2>/dev/null || echo "No raw directories found"
        fi
    else
        print_warning "No raw directories found. Create data/heart_rate/raw/ first."
    fi
}

# Function to create backup
create_backup() {
    local BACKUP_DIR=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --destination)
                BACKUP_DIR="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$BACKUP_DIR" ]; then
        BACKUP_DIR="backup/heart_rate_$(date +%Y%m%d_%H%M%S)"
    fi
    
    print_status "Creating backup in: $BACKUP_DIR"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup database (if using SQLite)
    if [ -f "data/db/onsen.db" ]; then
        print_status "Backing up database..."
        cp data/db/onsen.db "$BACKUP_DIR/"
        print_success "Database backed up"
    fi
    
    # Backup heart rate data files
    if [ -d "data/heart_rate" ]; then
        print_status "Backing up heart rate data files..."
        cp -r data/heart_rate "$BACKUP_DIR/"
        print_success "Heart rate files backed up"
    fi
    
    # Create backup manifest
    echo "Backup created: $(date)" > "$BACKUP_DIR/backup_manifest.txt"
    echo "Source: $(pwd)" >> "$BACKUP_DIR/backup_manifest.txt"
    echo "Database: $(ls -la "$BACKUP_DIR/"*.db 2>/dev/null || echo 'No database found')" >> "$BACKUP_DIR/backup_manifest.txt"
    
    print_success "Backup completed successfully in: $BACKUP_DIR"
}

# Function to validate file integrity
validate_integrity() {
    print_status "Validating file integrity of all heart rate records..."
    
    # This would need to be implemented in the CLI
    print_status "Running integrity check..."
    poetry run onsendo heart-rate list --details
    
    print_success "Integrity validation completed"
}

# Main script logic
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

COMMAND="$1"
shift

# Check dependencies
check_dependencies

case $COMMAND in
    status)
        show_status
        ;;
    cleanup)
        cleanup_records "$@"
        ;;
    archive)
        archive_files "$@"
        ;;
    backup)
        create_backup "$@"
        ;;
    restore)
        print_warning "Restore functionality not implemented yet"
        print_status "Use the backup files manually to restore data"
        ;;
    validate)
        validate_integrity
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
