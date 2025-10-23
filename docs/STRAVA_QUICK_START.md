# Strava Integration - Quick Start Guide

**Critical**: Always reference [strava_integration_spec.md](strava_integration_spec.md) for full details.

---

## Core Implementation Commands

### Resume After Context Loss
```
where am i strava
```
Shows what's been done and what's next.

### Implement Next Phase
```
implement strava phase <1-6>
```

### Check Status
```
strava implementation status
```

---

## The 6 Phases

### Phase 1: Foundation ✓ OAuth & Basic Client
```
implement strava phase 1
```
**Creates**: OAuth flow, StravaClient, auth/status commands, .env setup

### Phase 2: Activity Listing ✓ Browse & Filter
```
implement strava phase 2
```
**Creates**: list_activities(), ActivityFilter, basic browse command

### Phase 3: Data Conversion ✓ Strava → Onsendo
```
implement strava phase 3
```
**Creates**: Type mapping, ExerciseSession converter, HR converter, file exporters

### Phase 4: Interactive Browser ✓ Full UI Workflow
```
implement strava phase 4
```
**Creates**: Interactive browser, detail view, download/import/link workflows

### Phase 5: Quick Commands ✓ Batch Operations
```
implement strava phase 5
```
**Creates**: download/sync/link commands, deduplication, progress bars

### Phase 6: Polish ✓ Production Ready
```
implement strava phase 6
```
**Creates**: Error handling, docs, Makefile, optimization

---

## Individual Task Commands

If you need to implement just one part:
```
implement strava task <task-name>
```

**Common tasks**:
- `dataclasses` - Create data models
- `oauth-flow` - OAuth implementation
- `list-activities` - Activity fetching
- `type-mapper` - Activity type mapping
- `exercise-converter` - Strava → ExerciseSession
- `hr-converter` - Strava → HeartRateSession
- `browser-class` - Interactive browser
- `cmd-download` - Download command
- `cmd-sync` - Sync command

---

## Emergency Recovery

### Lost All Context?
```
where am i strava
```
This command will:
1. Read the spec
2. Check what files exist
3. Determine current phase
4. Suggest next command

### Show Full Roadmap
```
show strava roadmap
```
Shows all 6 phases with completion checkboxes.

### Restart a Phase
```
restart strava phase <N>
```
Shows checklist even if partially complete.

---

## Testing Commands

```
test strava phase <N>         # Test specific phase
test strava unit              # All unit tests
test strava integration       # Integration tests
test strava end-to-end        # Full workflow test
```

---

## Integration with Existing Code

```
integrate strava with exercise-manager       # Link to ExerciseManager
integrate strava with heart-rate-manager     # Link to HeartRateManager
integrate strava with cli-commands           # Register CLI commands
```

---

## Command Shortcuts

```
sp1     # implement strava phase 1
sp2     # implement strava phase 2
...
ss      # strava implementation status
stest   # test strava unit
```

---

## Key Files Reference

### Specification
- `docs/strava_integration_spec.md` - Full technical spec (75 pages)
- `docs/strava_implementation_commands.md` - Detailed command reference
- `docs/STRAVA_QUICK_START.md` - This file

### Implementation Files (to be created)
```
src/lib/strava_client.py          # API client
src/lib/strava_converter.py       # Data conversion
src/lib/strava_browser.py         # Interactive UI
src/cli/commands/strava/*.py      # CLI commands
src/types/strava.py               # Type definitions
tests/unit/test_strava_*.py       # Unit tests
tests/integration/test_strava_integration.py
```

### Configuration
```
.env.example                      # Add STRAVA_* variables
local/strava/token.json          # OAuth tokens (created at runtime)
data/strava/activities/          # Downloaded files
```

---

## If Implementation Stops Mid-Phase

1. Run: `where am i strava`
2. Review what files exist
3. Continue with: `implement strava phase <N>` (resume)
4. Or skip to: `implement strava task <specific-task>`

---

## Checkpointing for Long Sessions

```
strava checkpoint save "description"    # Save progress
strava checkpoint list                  # List checkpoints
strava checkpoint resume                # Resume from last
```

---

## Example: Typical Session

```
User: implement strava phase 1Assistant: 
  ✓ Reading specification...
  ✓ Phase 1: Foundation (OAuth & Basic Client)
  
  Tasks to implement:
  1. Create StravaCredentials and StravaToken dataclasses
  2. Implement OAuth2 authentication flow
  3. Create StravaClient class
  4. Add CLI commands (auth, status)
  5. Update .env.example
  6. Create directory structure
  
  Proceeding with implementation...
  
  [Creates all Phase 1 files]
  
  ✓ Phase 1 complete!
  
  Test with: test strava phase 1
  Continue with: implement strava phase 2

User: test strava phase 1
Assistant: [Runs tests, shows results]

User: implement strava phase 2
Assistant: [Continues to Phase 2...]
```

---

## Critical Notes

1. **Always read the spec first**: The assistant should reference `strava_integration_spec.md` before starting any phase
2. **Follow existing patterns**: Use Onsendo conventions (PATHS enum, loguru, type hints, etc.)
3. **Test after each phase**: Don't move to next phase until tests pass
4. **Update docs as you go**: Keep README and command docs in sync

---

## What the Assistant Should Do

When you say `implement strava phase N`, the assistant should:

1. ✓ Read `docs/strava_integration_spec.md` (the full spec)
2. ✓ Identify Phase N section
3. ✓ List tasks for that phase
4. ✓ Show what will be created/modified
5. ✓ Ask for confirmation (or proceed if obvious)
6. ✓ Create all required files
7. ✓ Follow Onsendo code style (type hints, docstrings, etc.)
8. ✓ Integrate with existing code (don't duplicate)
9. ✓ Create corresponding tests
10. ✓ Verify against spec
11. ✓ Report completion
12. ✓ Suggest next command

---

## Remember

- **Spec is source of truth**: `docs/strava_integration_spec.md`
- **Commands are shortcuts**: They tell the assistant what section of spec to implement
- **Checkpoints save progress**: Use them for long sessions
- **Emergency recovery**: `where am i strava` always works

---

**Start Here**: `implement strava phase 1`
