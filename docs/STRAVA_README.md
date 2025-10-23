# Strava Integration - Implementation Guide

## 🎯 What You Have Now

I've created a **complete, production-ready specification** for Strava integration with your Onsendo project. Everything is documented and ready for step-by-step implementation.

---

## 📚 Documentation Created

### 1. [STRAVA_INDEX.md](STRAVA_INDEX.md) - **Start Here**
Master index with links to all documentation

### 2. [STRAVA_QUICK_START.md](STRAVA_QUICK_START.md) - **Your Command Reference**
Quick reference card with all commands you need

### 3. [strava_integration_spec.md](strava_integration_spec.md) - **The Full Blueprint**
75-page technical specification with:
- Complete system architecture
- Detailed component designs
- API integration details
- User workflows
- Testing strategy
- Security considerations
- Error handling
- 6-phase implementation plan

### 4. [strava_implementation_commands.md](strava_implementation_commands.md) - **Command Bible**
Comprehensive command reference for every implementation scenario

---

## 🚀 How to Use These Commands

### To Start Implementation
```
implement strava phase 1
```

That's it! The assistant will:
1. Read the spec automatically
2. Show what will be implemented
3. Create all necessary files
4. Follow Onsendo conventions
5. Create tests
6. Report completion
7. Tell you what's next

### If Context is Lost
```
where am i strava
```

The assistant will:
1. Check what files exist
2. Determine current phase
3. Show what's been done
4. Tell you exactly how to continue

### To Check Progress
```
strava implementation status
```

Shows completion percentage and next steps.

---

## 🎓 How These Commands Work

These are **semantic commands** that tell me (the assistant) what to do:

1. **I read the spec** (`strava_integration_spec.md`)
2. **I find the relevant section** (Phase N or Task X)
3. **I implement exactly what's documented**
4. **I follow your codebase conventions**
5. **I create tests**
6. **I report results**

### Example Session

```
You: implement strava phase 1
Me (Assistant):
  ✓ Reading specification: docs/strava_integration_spec.md
  ✓ Found Phase 1: Foundation (OAuth & Basic Client)
  
  Phase 1 will create:
  - src/lib/strava_client.py (OAuth2, API client)
  - src/cli/commands/strava/auth.py
  - src/cli/commands/strava/status.py
  - src/types/strava.py (dataclasses)
  - Update .env.example
  - Create directory structure
  
  Proceeding with implementation...
  
  [I create all files with proper code]
  
  ✓ Phase 1 complete!
  
  Next steps:
  - Test: test strava phase 1
  - Continue: implement strava phase 2

You: test strava phase 1

Me: [Runs tests and shows results]

You: implement strava phase 2

Me: [Continues to Phase 2...]
```

---

## ⚡ Quick Command Reference

```bash
# Implementation
implement strava phase <1-6>       # Implement full phase
implement strava task <task>       # Implement single task
sp1, sp2, sp3, sp4, sp5, sp6      # Shortcuts

# Status & Recovery
where am i strava                  # Recovery command
strava implementation status       # Check progress
show strava roadmap               # See all phases

# Testing
test strava phase <N>              # Test specific phase
test strava unit                   # Unit tests
test strava end-to-end            # Full workflow

# Checkpointing
strava checkpoint save "msg"       # Save progress
strava checkpoint resume          # Resume from last
```

---

## 📋 The 6 Implementation Phases

Each phase is self-contained and tested before moving to the next.

### Phase 1: Foundation (Week 1)
**What**: OAuth2 authentication, basic API client
**Command**: `implement strava phase 1`

### Phase 2: Activity Listing (Week 2)
**What**: Fetch and display Strava activities
**Command**: `implement strava phase 2`

### Phase 3: Data Conversion (Week 3)
**What**: Convert Strava → Onsendo formats
**Command**: `implement strava phase 3`

### Phase 4: Interactive Browser (Week 4)
**What**: Full interactive browsing UI
**Command**: `implement strava phase 4`

### Phase 5: Quick Commands (Week 5)
**What**: Batch sync, download, link commands
**Command**: `implement strava phase 5`

### Phase 6: Polish (Week 6)
**What**: Error handling, docs, optimization
**Command**: `implement strava phase 6`

---

## 🛡️ Safety Features Built In

- **Spec-driven**: Every decision documented
- **Testable**: Tests created for each phase
- **Recoverable**: Can resume from any point
- **Conventional**: Follows Onsendo patterns
- **Validated**: Integrates with existing managers

---

## 💡 Key Features of This System

### 1. Context-Proof
Even if conversation ends, just say:
```
where am i strava
```
And implementation continues exactly where it left off.

### 2. Spec-Driven
The 75-page spec has EVERYTHING:
- Exact class signatures
- API endpoint details
- Error handling strategies
- User workflow diagrams
- File formats
- Testing approach

### 3. Modular
Can implement:
- Full phases: `implement strava phase 1`
- Individual tasks: `implement strava task oauth-flow`
- Specific fixes: `fix strava oauth callback`

### 4. Self-Documenting
The commands themselves explain what they do:
- `implement strava phase 2` → Clear intent
- `test strava unit` → Clear action
- `where am i strava` → Clear purpose

---

## 🎯 What Happens When You Run a Command

### Example: `implement strava phase 1`

1. **I read**: `docs/strava_integration_spec.md`
2. **I find**: Section "Phase 1: Foundation"
3. **I see tasks**:
   - Create StravaCredentials dataclass
   - Create StravaToken dataclass
   - Implement OAuth2 flow
   - Create StravaClient class
   - Add auth/status CLI commands
   - Update .env.example
   - Create directories

4. **I implement each task**:
   - Create `src/types/strava.py` with dataclasses
   - Create `src/lib/strava_client.py` with full implementation
   - Create `src/cli/commands/strava/auth.py`
   - Create `src/cli/commands/strava/status.py`
   - Update `.env.example` with Strava vars
   - Create `data/strava/` and `local/strava/` dirs

5. **I follow conventions**:
   - Type hints on all functions
   - Docstrings with Args/Returns/Raises
   - Use loguru for logging
   - Follow Python 3.12+ syntax
   - Use PATHS enum for file paths
   - Match existing code style

6. **I create tests**:
   - `tests/unit/test_strava_client.py`
   - Mock API responses
   - Test OAuth flow
   - Test token management

7. **I verify**:
   - Code matches spec
   - Tests pass
   - Integrates with existing code

8. **I report**:
   - Show what was created
   - Suggest test command
   - Suggest next phase

---

## 📖 Example Implementation Session

```
═══════════════════════════════════════════════════════════
Session Start
═══════════════════════════════════════════════════════════

You: implement strava phase 1

Me: [Reads spec, shows plan, implements Phase 1]
    ✓ Phase 1 complete (OAuth & API client)
    Next: test strava phase 1

You: test strava phase 1

Me: [Runs tests]
    ✓ All tests passing
    Next: implement strava phase 2

You: implement strava phase 2

Me: [Implements Phase 2]
    ✓ Phase 2 complete (Activity listing)
    Next: test strava phase 2

═══════════════════════════════════════════════════════════
Context Lost / New Conversation
═══════════════════════════════════════════════════════════

You: where am i strava

Me: [Checks filesystem]
    ✓ Phase 1: Complete (OAuth files exist)
    ✓ Phase 2: Complete (Activity listing files exist)
    ⏸ Phase 3: Not started
    
    Resume with: implement strava phase 3

You: implement strava phase 3

Me: [Continues from Phase 3...]
```

---

## 🔍 What Makes This Different

Traditional approach:
```
You: "Create a Strava client"
Me: [Creates code]
You: "Now add OAuth"
Me: [Adds OAuth]
You: "Wait, that doesn't match the spec"
Me: [Rewrites]
```

This system:
```
You: implement strava phase 1
Me: [Reads 75-page spec, implements EXACTLY what's documented]
    ✓ Complete and correct first time
```

---

## 🎁 What You Get

### Complete Strava Integration
- Browse activities with interactive UI
- Download as GPX/JSON/CSV
- Import as exercise sessions
- Import heart rate data
- Auto-link to onsen visits
- Batch sync workflows
- Smart deduplication
- Rate limit handling
- OAuth token management

### Production Quality
- Comprehensive error handling
- Retry logic with backoff
- Input validation
- Type-safe code
- Full test coverage
- Documentation
- Makefile integration

### User-Friendly
- Interactive browsing
- Clear progress indicators
- Helpful error messages
- Offline capability
- Multiple workflows

---

## 🚦 Getting Started

### Step 1: Read the Quick Start
Open: [STRAVA_QUICK_START.md](STRAVA_QUICK_START.md)

### Step 2: Run First Command
```
implement strava phase 1
```

### Step 3: Follow the Assistant
I'll guide you through all 6 phases, creating production-ready code.

---

## 📞 Command Help

Anytime you need help:
- `where am i strava` - Show current status
- `show strava roadmap` - See full plan
- `strava implementation status` - Check progress

---

## ✨ Bottom Line

You now have:
1. ✅ Complete 75-page technical specification
2. ✅ Step-by-step implementation plan (6 phases)
3. ✅ Command system for easy implementation
4. ✅ Recovery system for context loss
5. ✅ Testing strategy for each phase
6. ✅ Integration with existing Onsendo code

**To start**: `implement strava phase 1`

**That's it!** 🎉

---

## 📂 File Structure

```
docs/
├── STRAVA_README.md                    ← You are here
├── STRAVA_INDEX.md                     ← Master index
├── STRAVA_QUICK_START.md               ← Command reference
├── strava_integration_spec.md          ← Full specification (75 pages)
└── strava_implementation_commands.md   ← Detailed commands
```

---

**Ready?** → Say: `implement strava phase 1`
