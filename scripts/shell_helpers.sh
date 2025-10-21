#!/bin/bash
# Onsendo Database Environment Shell Helpers
#
# Add this to your ~/.zshrc or ~/.bashrc:
#   source ~/code/onsendo/scripts/shell_helpers.sh
#
# Then use simple commands to switch database environments:
#   use-prod    # Switch to production
#   use-dev     # Switch to development
#   onsendo-env # Show current environment

use-prod() {
    export ONSENDO_ENV=prod
    echo "✅ Switched to PRODUCTION database (data/db/onsen.prod.db)"
    echo "⚠️  All commands now affect PRODUCTION data!"
}

use-dev() {
    export ONSENDO_ENV=dev
    echo "✅ Switched to DEVELOPMENT database (data/db/onsen.dev.db)"
}

onsendo-env() {
    if [ -n "$ONSENDO_ENV" ]; then
        echo "Environment: $ONSENDO_ENV"
        if [ "$ONSENDO_ENV" = "prod" ]; then
            echo "Database: data/db/onsen.prod.db"
            echo "⚠️  WARNING: Using PRODUCTION database"
        else
            echo "Database: data/db/onsen.dev.db"
        fi
    else
        echo "Environment: dev (default)"
        echo "Database: data/db/onsen.dev.db"
    fi
}

# Compatibility function (works in both bash and zsh)
show-env() {
    onsendo-env
}
