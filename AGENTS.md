# Repository Guidelines

## Project Structure & Module Organization

- `src/cli`, `src/analysis`, `src/db`, `src/lib`, and `src/types` contain runtime code; extend existing modules before creating new packages.
- Tests mirror this layout: put fast specs in `tests/unit/**` and boundary checks plus SQLite fixtures in `tests/integration/**`.
- `scripts/` hosts maintenance tooling, `docs/` stores long-form references, while generated artifacts belong in `output/` or `local/` and must stay untracked.

## Build, Test, and Development Commands

- Install dependencies via `poetry install`, then use `poetry run ...` or `poetry shell` for all commands.
- Inspect the CLI with `poetry run onsendo --help` and scenario-specific subcommands such as `poetry run onsendo location add`.
- Run quick feedback loops with `poetry run pytest -q -m "not integration"`; execute the full suite with `poetry run pytest`.
- Lint with `poetry run pylint src tests` and audit riskier patches using `poetry run coverage run -m pytest` followed by `poetry run coverage report`.

## Coding Style & Naming Conventions

- Follow 4-space indentation, comprehensive type hints, snake_case functions, PascalCase classes, and UPPER_SNAKE_CASE constants.
- Centralize shared logic in `src/lib` or `src/analysis` and rely on `paths.py` instead of ad-hoc path joins.
- Prefer pure functions for calculations, log through `loguru`, and remove temporary files you create under `output/`.

## Testing Guidelines

- Name test files `test_*.py` as enforced by `pytest.ini`; keep unit assertions focused and deterministic.
- Mark broader scenarios with `@pytest.mark.integration` so reviewers can run `-m "not integration"` during iteration.
- Reuse fixtures from `tests/conftest.py`, extend mock builders instead of hard-coding data, and add regression cases for every bug fix.

## Commit & Pull Request Guidelines

- Use Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`) in present tense and under 72 characters, referencing issues in the body when relevant.
- Summaries should state intent, list local verification (`pytest`, `pylint`, optional `coverage`), and include CLI screenshots or transcripts for UX changes.
- Keep branches rebased on `main`, avoid unrelated formatting churn, and request review only after checks pass.

## Key Features & Systems

- **Onsen Tracking**: Record visits with ratings, health metrics, logistics, and optional notes
- **Heart Rate Monitoring**: Import from CSV, JSON, Apple Health; link to visits with SHA-256 integrity
- **Exercise Tracking**: Import from GPX, TCX, Apple Health; GPS routes, pace/elevation validation, weekly stats for challenge targets
- **Smart Recommendations**: Distance-based filtering using Haversine formula, availability checking, visit history personalization
- **Rules Management**: Track Onsendo Challenge compliance with weekly review workflow and revision history
- **Database Migrations**: Alembic-based schema evolution without data loss

## Documentation Update Protocol

### When Documentation Updates Are Required

You MUST update README.md when:
- Adding new CLI command or command group
- Adding new data format support (heart rate, exercise)
- Adding new feature or system component
- Changing command syntax or behavior
- Adding new workflow or use case

### README Update Checklist

Before submitting any PR with new features, verify:

1. **Command Index Updated** (Reference section)
   - Add new command with brief description
   - Group with related commands
   - Use consistent format: `` `command subcommand` - Description ``

2. **Usage Example Added** (Basic Usage or Advanced Features)
   - Add to appropriate section (Basic for daily use, Advanced for heart rate/exercise/rules)
   - Show 2-3 common use cases with code blocks
   - Use `poetry run onsendo` prefix (never bare `onsendo`)

3. **Core Concepts Updated** (if new entity)
   - Add h3 subsection if introducing new entity type (like Exercise, Heart Rate)
   - Explain what it is, what it's used for, key commands
   - Keep to 3-5 bullet points

4. **Table of Contents** (if major section added)
   - Update TOC links if new h2 section added
   - Verify all anchor links work

5. **Data Formats Table** (if new format)
   - Add row to appropriate table in Reference > Supported Data Formats
   - Include: format name, file extension, source, key features/notes

6. **Example Workflows** (if common pattern)
   - Add to Reference > Example Workflows if new feature enables common use case
   - Show 3-5 step workflow with actual commands

### README Structure Rules

**Header Depth Limits**:
- h2 (`##`) for major sections only (9 top-level sections)
- h3 (`###`) for features and subsections
- h4 (`####`) for specific commands
- **NEVER use h5 or h6** - restructure content instead

**Section Placement**:
- Daily commands → Basic Usage
- Heart rate, exercise, rules, migrations, analysis → Advanced Features
- Commands reference, formats, file structure → Reference
- Test/lint/contribute → Development

**Code Example Format**:
```markdown
```bash
# Comment explaining the command
poetry run onsendo command subcommand --flag value
```
```

### Consistency Requirements

All documentation changes must maintain:
- Consistent command prefix: `poetry run onsendo` (never just `onsendo`)
- Backticks for commands in prose: "Use `visit add` to record"
- Plain text for section headings: "### Recording Visits" (no backticks)
- Relative links: `[rules](rules/onsendo-rules.md)`
- File paths inline: "stored in `data/db/`"

### Pre-Submission Verification

Run this mental checklist before submitting PR:

```
[ ] New commands added to Command Index?
[ ] Usage examples in correct section (Basic vs Advanced)?
[ ] No h5/h6 headers (restructured if needed)?
[ ] All code blocks use `poetry run onsendo` prefix?
[ ] Cross-references use correct relative paths?
[ ] Data format tables updated (if applicable)?
[ ] File organization updated (if new directories)?
[ ] Example workflows added (if common pattern)?
[ ] Table of Contents updated (if structure changed)?
```

### Examples

**Good PR** - Adding new command:
```markdown
Files changed:
- src/cli/commands/exercise/stats.py (new command)
- README.md (3 changes):
  1. Added `exercise stats` to Command Index
  2. Added usage example in Advanced Features > Exercise Management
  3. Added to "Sunday weekly review" workflow
```

**Bad PR** - Missing documentation:
```markdown
Files changed:
- src/cli/commands/exercise/stats.py (new command)
- (README.md not updated - REJECT)
```

**Good PR** - Adding new format:
```markdown
Files changed:
- src/lib/exercise_manager.py (FIT format support)
- README.md (2 changes):
  1. Added FIT to Exercise Formats table
  2. Added import example with --format fit flag
```

### README Section Reference

Quick reference for where to add documentation:

| Change Type | README Location |
|-------------|----------------|
| New CLI command | Reference > Command Index + usage section |
| New command group | Basic Usage or Advanced Features (new h3) |
| New data format | Reference > Supported Data Formats table |
| New workflow | Reference > Example Workflows |
| New feature | Advanced Features (h3 subsection) |
| New entity type | Core Concepts + Basic/Advanced usage |
| File structure change | Reference > File Organization |
| New troubleshooting | Additional Resources > Troubleshooting |

## Data & Environment Notes

- SQLite databases belong in `data/`; never commit secrets or large personal exports.
- Organize exercise/heart rate files in `data/exercise/` and `data/heart_rate/` with format-specific subdirectories.
- Confirm Python 3.12+ via `poetry env info`. For Selenium tasks, document driver requirements alongside the relevant script in `scripts/`.
