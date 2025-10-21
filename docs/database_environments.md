# Database Environments

Onsendo supports multiple database environments to separate development work from production data.

## Overview

The database environment system provides:

- **Multiple Environments**: `dev` (default) and `prod`
- **Explicit Production Access**: Production database requires explicit opt-in
- **Safety Guardrails**: Confirmation prompts for destructive operations on production
- **Test Isolation**: Tests physically cannot access production database
- **Session-Scoped Control**: Environment variables for batch operations

## Environments

### Development (`dev`)

- **Default environment** for all commands
- Safe for experiments and testing
- Can be reset or modified freely
- Located at: `data/db/onsen.dev.db`

### Production (`prod`)

- Your actual onsen visit records
- Requires explicit `--env prod` flag or `ONSENDO_ENV=prod`
- Protected with confirmation prompts for destructive operations
- Located at: `data/db/onsen.prod.db`

### Test (`test`)

- In-memory SQLite database (`sqlite:///:memory:`)
- Used automatically by pytest
- Isolated per test, automatically cleaned up

## Environment Selection

The system resolves the database environment using this priority order:

1. **Explicit path override**: `--database /path/to/custom.db`
2. **CLI flag**: `--env prod`
3. **Environment variable**: `ONSENDO_ENV=prod`
4. **Default**: `dev`

## Usage Examples

### Daily Development Work

```bash
# All commands default to dev environment
poetry run onsendo visit list
poetry run onsendo visit add
poetry run onsendo onsen recommend

# Output: → Using DEV database: data/db/onsen.dev.db
```

### Production Access (One-Off)

```bash
# Use --env prod for single command
poetry run onsendo visit list --env prod

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️  PRODUCTION DATABASE
#    Path: data/db/onsen.prod.db
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Production Access (Session-Scoped)

```bash
# Set environment variable for entire session
export ONSENDO_ENV=prod

# All commands now use production
poetry run onsendo visit list
poetry run onsendo visit add
poetry run onsendo rules-revision-create

# Unset when done
unset ONSENDO_ENV
```

### Custom Database Path

```bash
# Use a different database file entirely
poetry run onsendo visit list --database /path/to/experiment.db
```

## Safety Features

### Destructive Operation Warnings

Destructive operations (add, modify, delete) show a banner when targeting production:

```bash
$ poetry run onsendo visit delete --env prod

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  PRODUCTION DATABASE
   Path: data/db/onsen.prod.db
   Operation: Delete visit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type 'yes' to confirm: yes
```

### Confirmation Prompts

Production destructive operations require typed confirmation:

- Type `yes` (exactly) to proceed
- Use `--force` flag to skip confirmation (use carefully!)

```bash
# Requires confirmation
poetry run onsendo database drop-visits --env prod

# Skip confirmation (dangerous!)
poetry run onsendo database drop-visits --env prod --force
```

### Test Safety

Tests automatically block production database access:

```bash
$ ONSENDO_ENV=prod poetry run pytest
ERROR: CRITICAL: Cannot run tests with ONSENDO_ENV=prod set.
Tests must use isolated databases to prevent data corruption.
Please unset ONSENDO_ENV or set it to 'dev' or 'test'.
```

### Mock Data Protection

Commands that generate mock data (like `database insert-mock-visits`) automatically block production access:

```python
# This will fail with clear error
poetry run onsendo database insert-mock-visits --env prod
# Error: Production database access not allowed for mock data generation
```

## Migration Guide

### For New Users

Initialize both databases:

```bash
# Initialize dev database (interactive)
poetry run onsendo database init

# Initialize production database
poetry run onsendo database init --env prod
```

### For Existing Users

If you have an existing `data/db/onsen.db`, migrate to the new system:

```bash
# Run one-time migration
poetry run onsendo database migrate-to-envs

# This will:
# 1. Create backup of current database
# 2. Copy onsen.db → onsen.prod.db
# 3. Copy onsen.db → onsen.dev.db
# 4. Verify integrity
```

**After migration:**
- Your original `onsen.db` remains unchanged
- `onsen.prod.db` contains your production data
- `onsen.dev.db` is your new default for development
- A timestamped backup is saved in `artifacts/db/backups/`

## Makefile Integration

Use the `ENV` parameter with Makefile targets:

```bash
# Default to dev
make backup

# Target production
make backup ENV=prod

# Visit list
make visit-list ENV=prod
```

## Command Update Pattern

### For Read-Only Commands

Commands that only read data (list, print, recommend, stats):

```python
from src.config import get_database_config

def my_command(args: argparse.Namespace) -> None:
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        # Command logic
        pass
```

### For Destructive Commands

Commands that modify data (add, delete, modify):

```python
from src.config import get_database_config
from src.lib.cli_display import show_database_banner, confirm_destructive_operation

def my_destructive_command(args: argparse.Namespace) -> None:
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for production
    show_database_banner(config, operation="Delete visit")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "delete visit", force=force)
    except ValueError as e:
        print(str(e))
        return

    with get_db(url=config.url) as db:
        # Command logic
        pass
```

### For Mock Data Commands

Commands that should never touch production:

```python
from src.config import get_database_config

def my_mock_command(args: argparse.Namespace) -> None:
    # Get database configuration with production blocked
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None),
        allow_prod=False  # Will raise error if ONSENDO_ENV=prod
    )

    with get_db(url=config.url) as db:
        # Command logic
        pass
```

## Troubleshooting

### Cannot access production in tests

**Problem**: Tests fail with "Cannot run tests with ONSENDO_ENV=prod"

**Solution**: Unset the environment variable:
```bash
unset ONSENDO_ENV
poetry run pytest
```

### Accidentally deleted production data

**Problem**: Modified or deleted production data

**Solution**: Restore from automatic backups:
```bash
# List available backups
make backup-list

# Restore interactively
make backup-restore
```

### Commands not using new environment system

**Problem**: Some commands still use old `CONST.DATABASE_URL`

**Solution**: Update the command following the patterns above. See `src/cli/commands/database/init_db.py` for a complete example.

## Best Practices

1. **Use dev by default**: Never set `ONSENDO_ENV=prod` in your shell profile
2. **Session-scoped prod**: Use `export ONSENDO_ENV=prod` only for specific sessions
3. **Backup before major changes**: Run `make backup ENV=prod` before significant operations
4. **Test on dev first**: Always test new workflows on dev before running on prod
5. **Review confirmations**: Read confirmation prompts carefully for destructive operations

## Architecture

### File Locations

```
data/db/
├── onsen.db           # Legacy (kept for backwards compatibility)
├── onsen.dev.db       # Development database (default)
└── onsen.prod.db      # Production database (explicit access only)

artifacts/db/backups/
└── onsen_pre_migration_YYYYMMDD_HHMMSS.db  # Migration backup

src/
├── config.py          # Environment configuration system
└── lib/
    └── cli_display.py # Visual feedback and confirmations
```

### Configuration Module

`src/config.py` provides:

- `DatabaseEnvironment` enum (DEV, PROD, TEST)
- `DatabaseConfig` dataclass
- `get_database_config()` - Main configuration resolver
- `get_database_url()` - Convenience function
- `ensure_not_prod_in_tests()` - Test safety check

### Display Module

`src/lib/cli_display.py` provides:

- `show_database_banner()` - Production warnings
- `confirm_destructive_operation()` - Typed confirmations
- `get_database_display_path()` - Path formatting

## Future Enhancements

Potential future additions:

- **Staging environment**: Add `staging` environment for pre-production testing
- **Read-only mode**: Flag to prevent any writes to a database
- **Audit logging**: Automatic logging of all production operations
- **Database aliases**: Custom names for database files
- **Environment switching**: Interactive menu to switch environments

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Development commands and database operations
- [README.md](../README.md) - Quick start and basic usage
- [rules/onsendo-rules.md](../rules/onsendo-rules.md) - Challenge rules
