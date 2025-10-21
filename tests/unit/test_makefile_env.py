"""
Unit tests for Makefile environment variable handling.

These tests verify that the Makefile correctly respects the ONSENDO_ENV
environment variable and maintains proper priority ordering.
"""

import os
import subprocess
from typing import Optional

import pytest


class TestMakefileEnvironmentHandling:
    """Test Makefile environment variable handling."""

    @staticmethod
    def run_make_command(
        target: str,
        env_var: Optional[str] = None,
        env_param: Optional[str] = None
    ) -> str:
        """
        Run a make command and return its output.

        Args:
            target: The make target to run (e.g., "show-env", "db-path")
            env_var: Value to set ONSENDO_ENV environment variable to
            env_param: Value to pass as ENV parameter to make

        Returns:
            The command output as a string
        """
        env = os.environ.copy()

        # Set ONSENDO_ENV if provided
        if env_var is not None:
            env['ONSENDO_ENV'] = env_var
        elif 'ONSENDO_ENV' in env:
            # Remove ONSENDO_ENV if it exists and we don't want it
            del env['ONSENDO_ENV']

        # Build command
        cmd = ['make', target]
        if env_param is not None:
            cmd.append(f'ENV={env_param}')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False
        )

        return result.stdout

    def test_default_environment_is_dev(self):
        """Test that default environment is dev when no variables are set."""
        output = self.run_make_command('show-env')

        assert 'dev (default)' in output or 'dev' in output

    def test_show_env_with_onsendo_env_prod(self):
        """Test show-env displays prod when ONSENDO_ENV=prod."""
        output = self.run_make_command('show-env', env_var='prod')

        assert 'prod' in output
        assert 'from environment variable' in output

    def test_show_env_with_onsendo_env_dev(self):
        """Test show-env displays dev when ONSENDO_ENV=dev."""
        output = self.run_make_command('show-env', env_var='dev')

        assert 'dev' in output
        assert 'from environment variable' in output

    def test_db_path_default(self):
        """Test db-path shows dev database by default."""
        output = self.run_make_command('db-path')

        assert 'Environment:' in output
        assert 'dev' in output
        assert 'data/db/onsen.dev.db' in output

    def test_db_path_with_onsendo_env_prod(self):
        """Test db-path shows prod database when ONSENDO_ENV=prod."""
        output = self.run_make_command('db-path', env_var='prod')

        assert 'Environment:' in output
        assert 'prod' in output
        assert 'data/db/onsen.prod.db' in output

    def test_db_path_with_onsendo_env_dev(self):
        """Test db-path shows dev database when ONSENDO_ENV=dev."""
        output = self.run_make_command('db-path', env_var='dev')

        assert 'Environment:' in output
        assert 'dev' in output
        assert 'data/db/onsen.dev.db' in output

    def test_env_parameter_overrides_onsendo_env_var(self):
        """Test that ENV parameter has higher priority than ONSENDO_ENV variable."""
        # Set ONSENDO_ENV=dev but use ENV=prod parameter
        output = self.run_make_command('db-path', env_var='dev', env_param='prod')

        assert 'prod' in output
        assert 'data/db/onsen.prod.db' in output

    def test_env_parameter_overrides_onsendo_env_var_reverse(self):
        """Test ENV parameter overrides ONSENDO_ENV (reverse case)."""
        # Set ONSENDO_ENV=prod but use ENV=dev parameter
        output = self.run_make_command('db-path', env_var='prod', env_param='dev')

        assert 'dev' in output
        assert 'data/db/onsen.dev.db' in output

    def test_use_prod_outputs_export_statement(self):
        """Test that use-prod outputs correct export statement."""
        output = self.run_make_command('use-prod')

        assert 'export ONSENDO_ENV=prod' in output

    def test_use_dev_outputs_export_statement(self):
        """Test that use-dev outputs correct export statement."""
        output = self.run_make_command('use-dev')

        assert 'export ONSENDO_ENV=dev' in output


class TestMakefileEnvironmentSwitching:
    """Test environment switching workflow using eval."""

    def test_environment_switching_workflow(self):
        """
        Test complete workflow of switching environments.

        This simulates a user session:
        1. Start with default (dev)
        2. Switch to prod
        3. Switch back to dev
        """
        # Create a shell script that simulates the workflow
        script = """
        set -e

        # Test 1: Default
        OUTPUT1=$(make show-env)
        if ! echo "$OUTPUT1" | grep -q "dev"; then
            echo "FAIL: Default should be dev"
            exit 1
        fi

        # Test 2: Switch to prod
        eval $(make use-prod)
        OUTPUT2=$(make show-env)
        if ! echo "$OUTPUT2" | grep -q "prod"; then
            echo "FAIL: After use-prod should be prod"
            exit 1
        fi

        # Test 3: Verify ONSENDO_ENV is set
        if [ "$ONSENDO_ENV" != "prod" ]; then
            echo "FAIL: ONSENDO_ENV should be prod"
            exit 1
        fi

        # Test 4: Verify db-path uses prod
        OUTPUT3=$(make db-path)
        if ! echo "$OUTPUT3" | grep -q "onsen.prod.db"; then
            echo "FAIL: db-path should show prod database"
            exit 1
        fi

        # Test 5: Switch back to dev
        eval $(make use-dev)
        OUTPUT4=$(make show-env)
        if ! echo "$OUTPUT4" | grep -q "dev"; then
            echo "FAIL: After use-dev should be dev"
            exit 1
        fi

        # Test 6: Verify ONSENDO_ENV is dev
        if [ "$ONSENDO_ENV" != "dev" ]; then
            echo "FAIL: ONSENDO_ENV should be dev"
            exit 1
        fi

        echo "PASS"
        """

        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0, f"Workflow test failed: {result.stdout}\n{result.stderr}"
        assert 'PASS' in result.stdout

    def test_env_parameter_override_in_session(self):
        """
        Test that ENV parameter can override session-level ONSENDO_ENV.

        Simulates setting ONSENDO_ENV=dev then running a single command with ENV=prod.
        """
        script = """
        set -e

        # Set session to dev
        eval $(make use-dev)

        # Run one command with ENV=prod (should use prod)
        OUTPUT1=$(make db-path ENV=prod)
        if ! echo "$OUTPUT1" | grep -q "onsen.prod.db"; then
            echo "FAIL: ENV=prod should override ONSENDO_ENV=dev"
            exit 1
        fi

        # Next command should use dev again (session is still dev)
        OUTPUT2=$(make db-path)
        if ! echo "$OUTPUT2" | grep -q "onsen.dev.db"; then
            echo "FAIL: Should return to dev after ENV=prod override"
            exit 1
        fi

        echo "PASS"
        """

        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0, f"Override test failed: {result.stdout}\n{result.stderr}"
        assert 'PASS' in result.stdout


class TestMakefileIntegrationWithPython:
    """Test that Python code respects ONSENDO_ENV set by Makefile."""

    def test_python_respects_onsendo_env_prod(self):
        """Test that Python config respects ONSENDO_ENV=prod."""
        script = """
        set -e

        eval $(make use-prod)

        ENV=$(poetry run python -c "from src.config import get_database_config; c = get_database_config(); print(c.env.value)" 2>/dev/null)

        if [ "$ENV" != "prod" ]; then
            echo "FAIL: Python should use prod when ONSENDO_ENV=prod"
            exit 1
        fi

        echo "PASS"
        """

        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0, f"Python prod test failed: {result.stdout}\n{result.stderr}"
        assert 'PASS' in result.stdout

    def test_python_respects_onsendo_env_dev(self):
        """Test that Python config respects ONSENDO_ENV=dev."""
        script = """
        set -e

        eval $(make use-dev)

        ENV=$(poetry run python -c "from src.config import get_database_config; c = get_database_config(); print(c.env.value)" 2>/dev/null)

        if [ "$ENV" != "dev" ]; then
            echo "FAIL: Python should use dev when ONSENDO_ENV=dev"
            exit 1
        fi

        echo "PASS"
        """

        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0, f"Python dev test failed: {result.stdout}\n{result.stderr}"
        assert 'PASS' in result.stdout

    def test_python_default_is_dev(self):
        """Test that Python config defaults to dev when no ONSENDO_ENV set."""
        script = """
        set -e

        # Explicitly unset ONSENDO_ENV
        unset ONSENDO_ENV

        ENV=$(poetry run python -c "from src.config import get_database_config; c = get_database_config(); print(c.env.value)" 2>/dev/null)

        if [ "$ENV" != "dev" ]; then
            echo "FAIL: Python should default to dev"
            exit 1
        fi

        echo "PASS"
        """

        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0, f"Python default test failed: {result.stdout}\n{result.stderr}"
        assert 'PASS' in result.stdout


class TestMakefilePriorityOrdering:
    """Test priority ordering of environment selection in Makefile."""

    def test_priority_1_env_parameter_highest(self):
        """Test ENV parameter has highest priority (overrides ONSENDO_ENV)."""
        # ONSENDO_ENV=dev but ENV=prod should result in prod
        output = subprocess.run(
            ['bash', '-c', 'export ONSENDO_ENV=dev; make db-path ENV=prod'],
            capture_output=True,
            text=True,
            check=False
        ).stdout

        assert 'prod' in output
        assert 'onsen.prod.db' in output

    def test_priority_2_onsendo_env_variable(self):
        """Test ONSENDO_ENV variable has second priority (overrides default)."""
        # No ENV parameter, but ONSENDO_ENV=prod should result in prod
        output = subprocess.run(
            ['bash', '-c', 'export ONSENDO_ENV=prod; make db-path'],
            capture_output=True,
            text=True,
            check=False
        ).stdout

        assert 'prod' in output
        assert 'onsen.prod.db' in output

    def test_priority_3_default_is_dev(self):
        """Test default is dev when no ENV or ONSENDO_ENV set."""
        # No ENV parameter, no ONSENDO_ENV should result in dev
        output = subprocess.run(
            ['bash', '-c', 'unset ONSENDO_ENV; make db-path'],
            capture_output=True,
            text=True,
            check=False
        ).stdout

        assert 'dev' in output
        assert 'onsen.dev.db' in output
