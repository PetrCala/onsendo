.PHONY: help install test test-unit test-integration lint coverage clean
.PHONY: hr-import hr-batch hr-status hr-maintenance
.PHONY: backup backup-cloud backup-full backup-cleanup backup-restore backup-list backup-verify
.PHONY: db-init db-fill db-path use-prod use-dev show-env
.PHONY: run-cli
.PHONY: strava-auth strava-status strava-browse strava-interactive strava-download strava-sync strava-link

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Database environment configuration
# Check ONSENDO_ENV environment variable first, then ENV parameter, then default to dev
ENV ?= $(if $(ONSENDO_ENV),$(ONSENDO_ENV),dev)
DB_FILE := data/db/onsen.$(ENV).db

# Backup configuration
KEEP_BACKUPS ?= 10
BACKUP_DIR := artifacts/db/backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
BACKUP_FILE := $(BACKUP_DIR)/onsen_backup_$(ENV)_$(TIMESTAMP).db

# Google Drive configuration (can be overridden via environment)
GDRIVE_CREDENTIALS ?= local/gdrive/credentials.json
GDRIVE_TOKEN ?= local/gdrive/token.json

##@ Help

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(BLUE)Usage:$(NC)\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install project dependencies
	@echo "$(BLUE)[INFO]$(NC) Installing dependencies with poetry..."
	poetry install
	@echo "$(GREEN)[SUCCESS]$(NC) Dependencies installed"

test: ## Run all tests
	@echo "$(BLUE)[INFO]$(NC) Running all tests..."
	poetry run pytest
	@echo "$(GREEN)[SUCCESS]$(NC) All tests passed"

test-unit: ## Run unit tests only (fast)
	@echo "$(BLUE)[INFO]$(NC) Running unit tests..."
	poetry run pytest -q -m "not integration"
	@echo "$(GREEN)[SUCCESS]$(NC) Unit tests passed"

test-integration: ## Run integration tests only
	@echo "$(BLUE)[INFO]$(NC) Running integration tests..."
	poetry run pytest -q -m "integration"
	@echo "$(GREEN)[SUCCESS]$(NC) Integration tests passed"

lint: ## Run pylint on source and tests
	@echo "$(BLUE)[INFO]$(NC) Running pylint..."
	poetry run pylint src tests
	@echo "$(GREEN)[SUCCESS]$(NC) Linting complete"

coverage: ## Run tests with coverage report
	@echo "$(BLUE)[INFO]$(NC) Running tests with coverage..."
	poetry run coverage run -m pytest
	poetry run coverage report
	@echo "$(GREEN)[SUCCESS]$(NC) Coverage report generated"

coverage-html: ## Generate HTML coverage report
	@echo "$(BLUE)[INFO]$(NC) Generating HTML coverage report..."
	poetry run coverage run -m pytest
	poetry run coverage html
	@echo "$(GREEN)[SUCCESS]$(NC) Coverage report at htmlcov/index.html"

clean: ## Clean up temporary files and caches
	@echo "$(BLUE)[INFO]$(NC) Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(NC) Cleanup complete"

##@ Database Operations

db-init: ## Initialize a new database (Usage: make db-init [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Initializing $(ENV) database..."
	poetry run onsendo --env $(ENV) system init-db
	@echo "$(GREEN)[SUCCESS]$(NC) $(ENV) database initialized at $(DB_FILE)"

db-fill: ## Fill database from data.json (Usage: make db-fill DATA_FILE=path/to/data.json [ENV=dev|prod])
	@if [ -z "$(DATA_FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) DATA_FILE not specified. Usage: make db-fill DATA_FILE=path/to/data.json"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Filling $(ENV) database from $(DATA_FILE)..."
	poetry run onsendo --env $(ENV) system fill-db "$(DATA_FILE)"
	@echo "$(GREEN)[SUCCESS]$(NC) $(ENV) database filled"

db-path: ## Show database path for current environment
	@echo "$(BLUE)Environment:$(NC) $(ENV)"
	@echo "$(BLUE)Database path:$(NC) $(DB_FILE)"

use-prod: ## Set ONSENDO_ENV=prod for current terminal session (Usage: eval $$(make use-prod))
	@echo "export ONSENDO_ENV=prod"

use-dev: ## Set ONSENDO_ENV=dev for current terminal session (Usage: eval $$(make use-dev))
	@echo "export ONSENDO_ENV=dev"

show-env: ## Show current database environment
	@if [ -n "$$ONSENDO_ENV" ]; then \
		echo "$(BLUE)Current environment:$(NC) $$ONSENDO_ENV (from environment variable)"; \
	else \
		echo "$(BLUE)Current environment:$(NC) dev (default)"; \
	fi

##@ Weight Management

weight-import: ## Import single weight file (Usage: make weight-import FILE=path/to/file.csv [ENV=dev|prod] [FORMAT=csv] [NOTES="notes"])
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) FILE not specified. Usage: make weight-import FILE=path/to/file.csv"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Importing weight data to $(ENV) database: $(FILE)"
	@poetry run onsendo --env $(ENV) weight import "$(FILE)" \
		$(if $(FORMAT),--format $(FORMAT),) \
		$(if $(NOTES),--notes "$(NOTES)",)

weight-add: ## Add weight measurement manually (Usage: make weight-add WEIGHT=72.5 [ENV=dev|prod] [CONDITIONS=fasted] [NOTES="notes"])
	@if [ -z "$(WEIGHT)" ]; then \
		echo "$(YELLOW)[INFO]$(NC) Starting interactive mode..."; \
		poetry run onsendo --env $(ENV) weight add; \
	else \
		echo "$(BLUE)[INFO]$(NC) Adding weight measurement to $(ENV) database: $(WEIGHT) kg"; \
		poetry run onsendo --env $(ENV) weight add --weight $(WEIGHT) \
			$(if $(CONDITIONS),--conditions $(CONDITIONS),) \
			$(if $(TIME_OF_DAY),--time-of-day $(TIME_OF_DAY),) \
			$(if $(NOTES),--notes "$(NOTES)",); \
	fi

weight-list: ## List weight measurements (Usage: make weight-list [ENV=dev|prod] [DATE_RANGE=2025-11-01,2025-11-30] [LIMIT=20])
	@echo "$(BLUE)[INFO]$(NC) Listing weight measurements from $(ENV) database..."
	@poetry run onsendo --env $(ENV) weight list \
		$(if $(DATE_RANGE),--date-range $(DATE_RANGE),) \
		$(if $(LIMIT),--limit $(LIMIT),) \
		$(if $(FORMAT),--format $(FORMAT),)

weight-delete: ## Delete weight measurement (Usage: make weight-delete ID=123 [ENV=dev|prod])
	@if [ -z "$(ID)" ]; then \
		echo "$(YELLOW)[INFO]$(NC) Starting interactive mode..."; \
		poetry run onsendo --env $(ENV) weight delete; \
	else \
		echo "$(BLUE)[INFO]$(NC) Deleting weight measurement $(ID) from $(ENV) database..."; \
		poetry run onsendo --env $(ENV) weight delete $(ID); \
	fi

weight-stats: ## Show weight statistics (Usage: make weight-stats WEEK=2025-11-03 [ENV=dev|prod] or MONTH=11 YEAR=2025 or ALL_TIME=true)
	@echo "$(BLUE)[INFO]$(NC) Fetching weight statistics from $(ENV) database..."
	@poetry run onsendo --env $(ENV) weight stats \
		$(if $(WEEK),--week $(WEEK),) \
		$(if $(MONTH),--month $(MONTH),) \
		$(if $(YEAR),--year $(YEAR),) \
		$(if $(ALL_TIME),--all-time,)

weight-export: ## Export weight data (Usage: make weight-export [FORMAT=csv] [OUTPUT=path/to/output.csv] [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Exporting weight data from $(ENV) database..."
	@poetry run onsendo --env $(ENV) weight export \
		$(if $(FORMAT),--format $(FORMAT),) \
		$(if $(OUTPUT),--output "$(OUTPUT)",) \
		$(if $(DATE_RANGE),--date-range $(DATE_RANGE),)

##@ Backup Operations

backup: ## Create local database backup with timestamp
	@echo "$(BLUE)[INFO]$(NC) Creating database backup..."
	@mkdir -p $(BACKUP_DIR)
	@if [ ! -f "$(DB_FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) Database file not found: $(DB_FILE)"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Checking database integrity..."
	@if ! sqlite3 "$(DB_FILE)" "PRAGMA integrity_check;" | grep -q "ok"; then \
		echo "$(RED)[ERROR]$(NC) Database integrity check failed!"; \
		exit 1; \
	fi
	@echo "$(GREEN)[SUCCESS]$(NC) Database integrity check passed"
	@cp "$(DB_FILE)" "$(BACKUP_FILE)"
	@echo "$(GREEN)[SUCCESS]$(NC) Backup created: $(BACKUP_FILE)"
	@ls -lh "$(BACKUP_FILE)"
	@echo "$(BLUE)[INFO]$(NC) Calculating SHA-256 hash..."
	@shasum -a 256 "$(BACKUP_FILE)" | awk '{print $$1}' > "$(BACKUP_FILE).sha256"
	@echo "$(GREEN)[SUCCESS]$(NC) Hash saved to: $(BACKUP_FILE).sha256"
	@cat "$(BACKUP_FILE).sha256"

backup-verify: ## Verify integrity of latest backup
	@echo "$(BLUE)[INFO]$(NC) Verifying latest backup..."
	@LATEST=$$(ls -t $(BACKUP_DIR)/onsen_backup_*.db 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)[ERROR]$(NC) No backups found in $(BACKUP_DIR)"; \
		exit 1; \
	fi; \
	echo "$(BLUE)[INFO]$(NC) Latest backup: $$LATEST"; \
	if [ ! -f "$$LATEST.sha256" ]; then \
		echo "$(YELLOW)[WARNING]$(NC) No checksum file found for this backup"; \
		exit 1; \
	fi; \
	STORED_HASH=$$(cat "$$LATEST.sha256"); \
	ACTUAL_HASH=$$(shasum -a 256 "$$LATEST" | awk '{print $$1}'); \
	if [ "$$STORED_HASH" = "$$ACTUAL_HASH" ]; then \
		echo "$(GREEN)[SUCCESS]$(NC) Backup integrity verified"; \
		echo "Hash: $$ACTUAL_HASH"; \
	else \
		echo "$(RED)[ERROR]$(NC) Backup integrity check failed!"; \
		echo "Expected: $$STORED_HASH"; \
		echo "Actual:   $$ACTUAL_HASH"; \
		exit 1; \
	fi

backup-list: ## List all backups with sizes and dates
	@echo "$(BLUE)[INFO]$(NC) Listing all backups..."
	@if [ ! -d "$(BACKUP_DIR)" ]; then \
		echo "$(YELLOW)[WARNING]$(NC) Backup directory not found: $(BACKUP_DIR)"; \
		exit 0; \
	fi
	@ls -lht $(BACKUP_DIR)/onsen_backup_*.db 2>/dev/null | head -20 || \
		echo "$(YELLOW)[WARNING]$(NC) No backups found in $(BACKUP_DIR)"
	@echo ""
	@TOTAL_SIZE=$$(du -sh $(BACKUP_DIR) 2>/dev/null | awk '{print $$1}'); \
	COUNT=$$(ls -1 $(BACKUP_DIR)/onsen_backup_*.db 2>/dev/null | wc -l | tr -d ' '); \
	echo "$(BLUE)[INFO]$(NC) Total backups: $$COUNT"; \
	echo "$(BLUE)[INFO]$(NC) Total size: $$TOTAL_SIZE"

backup-cleanup: ## Remove old backups (keeps KEEP_BACKUPS most recent, default: 50)
	@echo "$(BLUE)[INFO]$(NC) Cleaning up old backups (keeping $(KEEP_BACKUPS) most recent)..."
	@if [ ! -d "$(BACKUP_DIR)" ]; then \
		echo "$(YELLOW)[WARNING]$(NC) Backup directory not found: $(BACKUP_DIR)"; \
		exit 0; \
	fi
	@TOTAL=$$(ls -1 $(BACKUP_DIR)/onsen_backup_*.db 2>/dev/null | wc -l | tr -d ' '); \
	if [ $$TOTAL -le $(KEEP_BACKUPS) ]; then \
		echo "$(GREEN)[SUCCESS]$(NC) No cleanup needed ($$TOTAL backups, keeping $(KEEP_BACKUPS))"; \
		exit 0; \
	fi; \
	TO_DELETE=$$(($$TOTAL - $(KEEP_BACKUPS))); \
	echo "$(YELLOW)[WARNING]$(NC) Will delete $$TO_DELETE old backups"; \
	ls -t $(BACKUP_DIR)/onsen_backup_*.db | tail -$$TO_DELETE; \
	echo ""; \
	read -p "Proceed with deletion? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		ls -t $(BACKUP_DIR)/onsen_backup_*.db | tail -$$TO_DELETE | while read f; do \
			echo "$(BLUE)[INFO]$(NC) Deleting: $$f"; \
			rm -f "$$f" "$$f.sha256"; \
		done; \
		echo "$(GREEN)[SUCCESS]$(NC) Cleanup complete"; \
	else \
		echo "$(YELLOW)[WARNING]$(NC) Cleanup cancelled"; \
	fi

backup-restore: ## Restore database from backup (interactive selection)
	@echo "$(BLUE)[INFO]$(NC) Available backups:"
	@echo ""
	@ls -lht $(BACKUP_DIR)/onsen_backup_*.db 2>/dev/null | head -10 || \
		(echo "$(RED)[ERROR]$(NC) No backups found" && exit 1)
	@echo ""
	@read -p "Enter backup filename (or full path): " BACKUP; \
	if [ ! -f "$$BACKUP" ]; then \
		BACKUP="$(BACKUP_DIR)/$$BACKUP"; \
	fi; \
	if [ ! -f "$$BACKUP" ]; then \
		echo "$(RED)[ERROR]$(NC) Backup file not found: $$BACKUP"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "$(YELLOW)[WARNING]$(NC) This will replace the current database!"; \
	echo "Current database: $(DB_FILE)"; \
	echo "Restore from: $$BACKUP"; \
	echo ""; \
	read -p "Create backup of current database first? [Y/n] " -n 1 -r; \
	echo ""; \
	if [[ ! $$REPLY =~ ^[Nn]$$ ]]; then \
		$(MAKE) backup; \
		echo "$(GREEN)[SUCCESS]$(NC) Current database backed up"; \
	fi; \
	echo ""; \
	read -p "Proceed with restore? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cp "$$BACKUP" "$(DB_FILE)"; \
		echo "$(GREEN)[SUCCESS]$(NC) Database restored from $$BACKUP"; \
	else \
		echo "$(YELLOW)[WARNING]$(NC) Restore cancelled"; \
	fi

backup-cloud: ## Sync backups to Google Drive
	@echo "$(BLUE)[INFO]$(NC) Syncing backups to Google Drive..."
	@if [ ! -f "$(GDRIVE_CREDENTIALS)" ]; then \
		echo "$(RED)[ERROR]$(NC) Google Drive credentials not found: $(GDRIVE_CREDENTIALS)"; \
		echo "$(BLUE)[INFO]$(NC) To set up Google Drive:"; \
		echo "  1. Create OAuth2 credentials in Google Cloud Console"; \
		echo "  2. Download credentials.json to $(GDRIVE_CREDENTIALS)"; \
		echo "  3. Run 'make backup-cloud' again to authenticate"; \
		exit 1; \
	fi
	@poetry run python scripts/backup_to_drive.py sync "$(GDRIVE_CREDENTIALS)" "$(GDRIVE_TOKEN)" "$(BACKUP_DIR)" "db_backups"

backup-cloud-list: ## List backups in Google Drive
	@echo "$(BLUE)[INFO]$(NC) Listing backups in Google Drive..."
	@poetry run python scripts/backup_to_drive.py list "$(GDRIVE_CREDENTIALS)" "$(GDRIVE_TOKEN)"

backup-full: backup backup-cloud ## Create local backup and sync to Google Drive
	@echo "$(GREEN)[SUCCESS]$(NC) Full backup complete (local + cloud)"

backup-auto: ## Automatic backup with cleanup (for scheduled tasks)
	@echo "$(BLUE)[INFO]$(NC) Running automatic backup..."
	@$(MAKE) backup
	@$(MAKE) backup-cleanup KEEP_BACKUPS=$(KEEP_BACKUPS)
	@$(MAKE) backup-cloud || echo "$(YELLOW)[WARNING]$(NC) Cloud sync failed (continuing)"
	@echo "$(GREEN)[SUCCESS]$(NC) Automatic backup complete"

##@ CLI

run-cli: ## Run onsendo CLI with arguments (Usage: make run-cli ARGS="visit list")
	@poetry run onsendo $(ARGS)

##@ Convenience Shortcuts

onsen-recommend: ## Get onsen recommendations (Usage: make onsen-recommend [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Getting recommendations from $(ENV) database..."
	poetry run onsendo --env $(ENV) onsen recommend

visit-add: ## Add a new visit (Usage: make visit-add [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Adding visit to $(ENV) database..."
	poetry run onsendo --env $(ENV) visit add

visit-list: ## List all visits (Usage: make visit-list [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Listing visits from $(ENV) database..."
	poetry run onsendo --env $(ENV) visit list

location-add: ## Add a new location (Usage: make location-add [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Adding location to $(ENV) database..."
	poetry run onsendo --env $(ENV) location add

location-list: ## List all locations (Usage: make location-list [ENV=dev|prod])
	@echo "$(BLUE)[INFO]$(NC) Listing locations from $(ENV) database..."
	poetry run onsendo --env $(ENV) location list

##@ Strava Integration

strava-auth: ## Authenticate with Strava API (OAuth2 flow)
	@echo "$(BLUE)[INFO]$(NC) Starting Strava authentication..."
	poetry run onsendo strava auth
	@echo "$(GREEN)[SUCCESS]$(NC) Strava authentication complete"

strava-status: ## Check Strava API connection status
	@echo "$(BLUE)[INFO]$(NC) Checking Strava connection status..."
	poetry run onsendo strava status --verbose

strava-browse: ## Browse Strava activities with filters (Usage: make strava-browse DAYS=7 TYPE=Run)
	@echo "$(BLUE)[INFO]$(NC) Browsing Strava activities..."
	poetry run onsendo strava browse $(if $(DAYS),--days $(DAYS),) $(if $(TYPE),--type $(TYPE),)

strava-interactive: ## Launch interactive Strava browser
	@echo "$(BLUE)[INFO]$(NC) Launching interactive Strava browser..."
	poetry run onsendo strava interactive

strava-download: ## Download specific Strava activity (Usage: make strava-download ACTIVITY_ID=12345678 [FORMAT=gpx] [IMPORT=true] [LINK=true])
	@if [ -z "$(ACTIVITY_ID)" ]; then \
		echo "$(RED)[ERROR]$(NC) ACTIVITY_ID is required"; \
		echo "Usage: make strava-download ACTIVITY_ID=12345678 [FORMAT=gpx] [IMPORT=true] [LINK=true]"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Downloading Strava activity $(ACTIVITY_ID)..."
	poetry run onsendo strava download $(ACTIVITY_ID) \
		$(if $(FORMAT),--format $(FORMAT),) \
		$(if $(IMPORT),--import,) \
		$(if $(LINK),--auto-link,)

strava-sync: ## Sync recent Strava activities (Usage: make strava-sync [DAYS=7] [TYPE=Run] [IMPORT=true] [LINK=true] [DRY_RUN=true])
	@echo "$(BLUE)[INFO]$(NC) Syncing Strava activities..."
	poetry run onsendo strava sync \
		$(if $(DAYS),--days $(DAYS),) \
		$(if $(TYPE),--type $(TYPE),) \
		$(if $(IMPORT),--auto-import,) \
		$(if $(LINK),--auto-link,) \
		$(if $(DRY_RUN),--dry-run,)
	@if [ -z "$(DRY_RUN)" ]; then \
		echo "$(GREEN)[SUCCESS]$(NC) Strava sync complete"; \
	fi

strava-link: ## Link exercise/HR to visit (Usage: make strava-link EXERCISE_ID=42 VISIT_ID=123 or AUTO_MATCH=true)
	@if [ -z "$(EXERCISE_ID)" ] && [ -z "$(HR_ID)" ]; then \
		echo "$(RED)[ERROR]$(NC) Either EXERCISE_ID or HR_ID is required"; \
		echo "Usage: make strava-link EXERCISE_ID=42 VISIT_ID=123"; \
		echo "   or: make strava-link EXERCISE_ID=42 AUTO_MATCH=true"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Linking to visit..."
	poetry run onsendo strava link \
		$(if $(EXERCISE_ID),--exercise $(EXERCISE_ID),) \
		$(if $(HR_ID),--heart-rate $(HR_ID),) \
		$(if $(VISIT_ID),--visit $(VISIT_ID),) \
		$(if $(AUTO_MATCH),--auto-match,)
	@echo "$(GREEN)[SUCCESS]$(NC) Link complete"

##@ Default

.DEFAULT_GOAL := help
