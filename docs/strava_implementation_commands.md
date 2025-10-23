# Strava Integration Implementation Commands

**Reference**: See [strava_integration_spec.md](strava_integration_spec.md) for full technical specification.

---

## Quick Start Commands

### Resume Implementation
```
implement strava phase <N>
```
Example: `implement strava phase 1`

This command tells the assistant to:
1. Read the specification document
2. Identify Phase N tasks
3. Show what will be implemented
4. Proceed with implementation

### Check Progress
```
strava implementation status
```

Shows:
- Current phase and completion percentage
- Completed tasks
- Next tasks
- Any blockers

### Skip to Specific Task
```
implement strava task <task-name>
```
Example: `implement strava task authentication-flow`

---

## Phase-by-Phase Commands

### Phase 1: Foundation (Week 1)

**Command**: `implement strava phase 1`

**What it implements**:
- [ ] StravaCredentials and StravaToken dataclasses
- [ ] OAuth2 authentication flow
- [ ] StravaClient class with basic methods
- [ ] CLI commands: `strava auth`, `strava status`
- [ ] Environment variables in `.env.example`
- [ ] Directory structure setup

**Individual task commands**:
```
implement strava task dataclasses          # Create credentials/token classes
implement strava task oauth-flow           # Implement OAuth2 flow
implement strava task client-basic         # Create StravaClient skeleton
implement strava task cli-auth             # Add auth command
implement strava task cli-status           # Add status command
implement strava task env-config           # Update .env.example
implement strava task directory-structure  # Create data/strava/, local/strava/
```

**Verification**:
```
test strava phase 1
```

---

### Phase 2: Activity Listing (Week 2)

**Command**: `implement strava phase 2`

**What it implements**:
- [ ] StravaActivitySummary dataclass
- [ ] StravaClient.list_activities()
- [ ] ActivityFilter dataclass
- [ ] Filtering logic
- [ ] CLI command: `strava browse` (list-only)
- [ ] Pagination support

**Individual task commands**:
```
implement strava task activity-summary     # Create StravaActivitySummary
implement strava task list-activities      # Implement list_activities method
implement strava task activity-filter      # Create ActivityFilter class
implement strava task cli-browse-basic     # Basic browse command (list only)
implement strava task pagination           # Add pagination logic
```

**Verification**:
```
test strava phase 2
```

---

### Phase 3: Data Conversion (Week 3)

**Command**: `implement strava phase 3`

**What it implements**:
- [ ] StravaActivityDetail dataclass
- [ ] StravaClient.get_activity()
- [ ] StravaClient.get_activity_streams()
- [ ] StravaActivityTypeMapper
- [ ] StravaToExerciseConverter
- [ ] StravaToHeartRateConverter
- [ ] StravaFileExporter (GPX, JSON, CSV)

**Individual task commands**:
```
implement strava task activity-detail      # Create StravaActivityDetail dataclass
implement strava task get-activity         # Implement get_activity method
implement strava task get-streams          # Implement get_activity_streams
implement strava task type-mapper          # Activity type mapping
implement strava task exercise-converter   # Strava → ExerciseSession
implement strava task hr-converter         # Strava → HeartRateSession
implement strava task file-exporter-gpx    # GPX export
implement strava task file-exporter-json   # JSON export
implement strava task file-exporter-csv    # CSV export
```

**Verification**:
```
test strava phase 3
test strava conversion                     # Test conversions specifically
```

---

### Phase 4: Interactive Browser (Week 4)

**Command**: `implement strava phase 4`

**What it implements**:
- [ ] BrowserState dataclass
- [ ] StravaActivityBrowser class
- [ ] Interactive filter prompts
- [ ] Activity detail view
- [ ] Multi-selection support
- [ ] Download workflow
- [ ] Import workflow
- [ ] Visit linking workflow

**Individual task commands**:
```
implement strava task browser-state        # Create BrowserState
implement strava task browser-class        # Main browser class
implement strava task filter-prompts       # Interactive filters
implement strava task detail-view          # Activity detail display
implement strava task multi-select         # Selection handling
implement strava task download-workflow    # Download UI flow
implement strava task import-workflow      # Import UI flow
implement strava task link-workflow        # Visit linking UI
```

**Verification**:
```
test strava phase 4
test strava browser                        # Manual interactive test
```

---

### Phase 5: Quick Commands (Week 5)

**Command**: `implement strava phase 5`

**What it implements**:
- [ ] `strava download` command
- [ ] `strava sync` command
- [ ] `strava link` command
- [ ] Deduplication logic
- [ ] Dry-run mode
- [ ] Progress bars

**Individual task commands**:
```
implement strava task cmd-download         # Download command
implement strava task cmd-sync             # Sync command
implement strava task cmd-link             # Link command
implement strava task deduplication        # Prevent duplicate imports
implement strava task dry-run              # Dry-run mode for sync
implement strava task progress-bars        # Progress indicators
```

**Verification**:
```
test strava phase 5
test strava batch-operations               # Test sync with multiple activities
```

---

### Phase 6: Polish & Documentation (Week 6)

**Command**: `implement strava phase 6`

**What it implements**:
- [ ] Error handling improvements
- [ ] Retry logic with exponential backoff
- [ ] Makefile targets
- [ ] README documentation
- [ ] Troubleshooting guide
- [ ] Example workflows
- [ ] Performance optimization

**Individual task commands**:
```
implement strava task error-handling       # Comprehensive error handling
implement strava task retry-logic          # Exponential backoff
implement strava task makefile             # Makefile integration
implement strava task readme               # README.md updates
implement strava task troubleshooting      # Troubleshooting guide
implement strava task examples             # Example workflows
implement strava task optimize             # Performance improvements
```

**Verification**:
```
test strava phase 6
test strava end-to-end                     # Full workflow test
```

---

## Testing Commands

### Run Tests for Specific Phase
```
test strava phase <N>
```

### Run Specific Test Suite
```
test strava unit                           # All unit tests
test strava integration                    # All integration tests
test strava conversion                     # Conversion tests
test strava browser                        # Interactive browser (manual)
test strava batch-operations               # Batch sync tests
test strava end-to-end                     # Full workflow
```

### Create Test Fixtures
```
create strava test-fixtures                # Generate mock API responses
```

---

## Troubleshooting Commands

### Show Implementation Context
```
show strava context
```
Shows:
- Current specification section
- Related files already created
- Dependencies needed
- Next logical step

### Fix Specific Issue
```
fix strava <issue-description>
```
Example: `fix strava oauth callback not working`

### Review Code
```
review strava <component>
```
Example: `review strava StravaClient`

Shows code review with:
- Spec compliance check
- Code quality issues
- Missing error handling
- Suggestions

---

## Documentation Commands

### Update Documentation
```
update strava docs <section>
```
Examples:
- `update strava docs readme`
- `update strava docs troubleshooting`
- `update strava docs makefile`

### Generate Examples
```
generate strava examples
```
Creates example usage scripts in `examples/strava/`

---

## Utility Commands

### Add Missing Type Hints
```
add strava type-hints <file>
```

### Add Missing Tests
```
add strava tests <component>
```
Example: `add strava tests StravaConverter`

### Add Error Handling
```
add strava error-handling <file>
```

### Format Code
```
format strava code
```
Runs pylint and fixes issues in all Strava-related files

---

## Checkpoint Commands

### Save Progress
```
strava checkpoint save "<description>"
```
Example: `strava checkpoint save "Phase 1 complete - OAuth working"`

Creates checkpoint with:
- Current phase/task status
- Files modified
- Tests passing
- Known issues

### Resume from Checkpoint
```
strava checkpoint resume
```
Shows last checkpoint and continues from there

### List Checkpoints
```
strava checkpoint list
```

---

## Integration Commands

### Integrate with Existing Code
```
integrate strava with <component>
```
Examples:
- `integrate strava with exercise-manager`
- `integrate strava with heart-rate-manager`
- `integrate strava with cli-commands`

### Check Integration Points
```
check strava integration
```
Verifies:
- Proper use of existing managers
- Database model compatibility
- CLI command registration
- Path management via PATHS enum

---

## Command Aliases (Shortcuts)

```
# Quick phase implementation
sp1    # = implement strava phase 1
sp2    # = implement strava phase 2
sp3    # = implement strava phase 3
sp4    # = implement strava phase 4
sp5    # = implement strava phase 5
sp6    # = implement strava phase 6

# Quick testing
stest  # = test strava unit
stest2 # = test strava integration
steste # = test strava end-to-end

# Quick status
ss     # = strava implementation status
```

---

## Emergency Recovery Commands

### Lost Context - Show Where We Are
```
where am i strava
```
Shows:
- Specification summary
- What's been implemented (by checking files)
- What's next
- Recommended command to continue

### Start Fresh Phase
```
restart strava phase <N>
```
Shows checklist for phase, even if partially complete

### Show Full Roadmap
```
show strava roadmap
```
Displays all 6 phases with checkboxes

---

## Example Usage Scenarios

### Scenario 1: Starting Implementation
```
User: implement strava phase 1