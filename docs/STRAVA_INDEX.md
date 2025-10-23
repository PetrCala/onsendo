# Strava Integration - Documentation Index

**Status**: Planning Complete - Ready for Implementation

---

## Quick Navigation

### 🚀 Want to Start Implementation?
**Read this first**: [STRAVA_QUICK_START.md](STRAVA_QUICK_START.md)

**Then run**: `implement strava phase 1`

### 📖 Want Full Technical Details?
**Read**: [strava_integration_spec.md](strava_integration_spec.md) (75 pages)

### 🔧 Want Command Reference?
**Read**: [strava_implementation_commands.md](strava_implementation_commands.md)

### 🆘 Lost Context or Need Recovery?
**Run**: `where am i strava`

---

## Document Overview

### [STRAVA_QUICK_START.md](STRAVA_QUICK_START.md)
**Purpose**: Quick reference card for implementation
**Length**: 3 pages
**Use when**: Starting implementation or resuming after interruption

**Contains**:
- Core commands
- Phase overview (1-6)
- Emergency recovery commands
- Example session flow

---

### [strava_integration_spec.md](strava_integration_spec.md)
**Purpose**: Complete technical specification
**Length**: 75 pages
**Use when**: Implementing specific components or understanding design decisions

**Contains**:
- System architecture
- Component specifications (StravaClient, StravaConverter, etc.)
- API integration details (endpoints, auth, rate limiting)
- Data models and conversions
- User interface flows
- Implementation phases (detailed breakdown)
- Testing strategy
- Security considerations
- Error handling
- Configuration
- File organization

**Key Sections**:
- **Component Specifications** (p. 8-45): Detailed class designs
- **API Integration Details** (p. 46-52): Strava API v3 usage
- **User Interface Flows** (p. 53-60): Interactive workflows
- **Implementation Phases** (p. 61-67): 6-week plan
- **Testing Strategy** (p. 68-70): Unit, integration, manual tests

---

### [strava_implementation_commands.md](strava_implementation_commands.md)
**Purpose**: Comprehensive command reference
**Length**: 15 pages
**Use when**: Need to find specific command or task

**Contains**:
- Phase-by-phase commands
- Individual task commands
- Testing commands
- Troubleshooting commands
- Documentation commands
- Utility commands
- Checkpoint commands
- Integration commands
- Command aliases

**Command Categories**:
1. **Phase Commands**: `implement strava phase N`
2. **Task Commands**: `implement strava task <name>`
3. **Test Commands**: `test strava <suite>`
4. **Recovery Commands**: `where am i strava`, `strava checkpoint resume`
5. **Integration Commands**: `integrate strava with <component>`

---

## Implementation Workflow

### Step 1: Read Quick Start
[STRAVA_QUICK_START.md](STRAVA_QUICK_START.md) - Understand core commands

### Step 2: Start Phase 1
Run: `implement strava phase 1`

### Step 3: Follow Phases 1-6
- Phase 1: OAuth & Authentication
- Phase 2: Activity Listing
- Phase 3: Data Conversion
- Phase 4: Interactive Browser
- Phase 5: Quick Commands
- Phase 6: Polish & Docs

### Step 4: Test & Verify
After each phase: `test strava phase N`

### Step 5: Integration
Ensure proper integration with existing Onsendo components

---

## Command Cheat Sheet

```bash
# Start/Resume Implementation
implement strava phase <1-6>          # Implement specific phase
where am i strava                     # Check current status
strava implementation status          # Show progress

# Individual Tasks
implement strava task <task-name>     # Implement single task

# Testing
test strava phase <N>                 # Test specific phase
test strava unit                      # Unit tests only
test strava end-to-end                # Full workflow test

# Recovery
strava checkpoint save "msg"          # Save progress
strava checkpoint resume              # Resume from checkpoint
show strava roadmap                   # Show all phases

# Shortcuts
sp1, sp2, sp3, sp4, sp5, sp6         # Quick phase commands
ss                                    # Status check
stest                                 # Unit tests
```

---

## Files Created During Implementation

### Source Code
```
src/lib/strava_client.py             # Strava API client
src/lib/strava_converter.py          # Data conversions
src/lib/strava_browser.py            # Interactive UI
src/types/strava.py                  # Type definitions
src/cli/commands/strava/__init__.py  # Command group
src/cli/commands/strava/auth.py      # Auth command
src/cli/commands/strava/status.py    # Status command
src/cli/commands/strava/browse.py    # Browse command
src/cli/commands/strava/download.py  # Download command
src/cli/commands/strava/sync.py      # Sync command
src/cli/commands/strava/link.py      # Link command
```

### Tests
```
tests/unit/test_strava_client.py
tests/unit/test_strava_converter.py
tests/unit/test_strava_type_mapper.py
tests/unit/test_strava_exporter.py
tests/integration/test_strava_integration.py
tests/fixtures/strava/*.json
```

### Configuration
```
.env.example                         # Strava credentials template
local/strava/token.json              # OAuth tokens (runtime)
data/strava/activities/              # Downloaded activities
```

### Documentation
```
docs/strava_integration_spec.md      # This spec
docs/strava_implementation_commands.md
docs/STRAVA_QUICK_START.md
docs/STRAVA_INDEX.md                 # This file
docs/strava_troubleshooting.md       # User guide (Phase 6)
README.md                            # Updated with Strava section (Phase 6)
```

---

## Phase Completion Checklist

Use this to track progress:

- [ ] **Phase 1: Foundation**
  - [ ] OAuth2 authentication
  - [ ] Token management
  - [ ] StravaClient basics
  - [ ] auth/status commands
  - [ ] .env configuration

- [ ] **Phase 2: Activity Listing**
  - [ ] list_activities()
  - [ ] ActivityFilter
  - [ ] Pagination
  - [ ] Basic browse command

- [ ] **Phase 3: Data Conversion**
  - [ ] Activity type mapping
  - [ ] ExerciseSession converter
  - [ ] HeartRateSession converter
  - [ ] File exporters (GPX/JSON/CSV)

- [ ] **Phase 4: Interactive Browser**
  - [ ] BrowserState & main class
  - [ ] Interactive filters
  - [ ] Detail view
  - [ ] Download/import/link workflows

- [ ] **Phase 5: Quick Commands**
  - [ ] download command
  - [ ] sync command
  - [ ] link command
  - [ ] Deduplication
  - [ ] Progress indicators

- [ ] **Phase 6: Polish**
  - [ ] Error handling
  - [ ] Retry logic
  - [ ] Makefile targets
  - [ ] README updates
  - [ ] Troubleshooting guide

---

## Key Design Principles

1. **Spec is Source of Truth**: Always reference [strava_integration_spec.md](strava_integration_spec.md)
2. **Follow Onsendo Patterns**: Use existing conventions (PATHS, loguru, type hints)
3. **Test Each Phase**: Don't proceed until tests pass
4. **Integrate, Don't Duplicate**: Use existing ExerciseManager, HeartRateManager
5. **User Control**: Interactive with options to review before committing
6. **Offline Capable**: Downloaded files work independently

---

## Support & Troubleshooting

### Implementation Stuck?
1. Run: `where am i strava`
2. Check spec: [strava_integration_spec.md](strava_integration_spec.md)
3. Review commands: [strava_implementation_commands.md](strava_implementation_commands.md)
4. Restart phase: `restart strava phase N`

### Need to Understand a Component?
Reference the **Component Specifications** section in [strava_integration_spec.md](strava_integration_spec.md)

### API Questions?
See **API Integration Details** in [strava_integration_spec.md](strava_integration_spec.md)

### Error Handling Questions?
See **Error Handling** section in [strava_integration_spec.md](strava_integration_spec.md)

---

## Version History

| Version | Date       | Changes |
|---------|------------|---------|
| 1.0     | 2025-10-23 | Initial specification and planning complete |

---

**Ready to Start?** → [STRAVA_QUICK_START.md](STRAVA_QUICK_START.md)

**First Command**: `implement strava phase 1`
