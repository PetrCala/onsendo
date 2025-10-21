"""
Unit tests for database configuration system.

Tests the environment-aware database configuration including:
- Environment resolution priority
- Production blocking
- URL generation
- Error handling
"""

import os
import pytest

from src.config import (
    DatabaseEnvironment,
    DatabaseConfig,
    get_database_config,
    ensure_not_prod_in_tests,
)
from src.const import CONST


class TestDatabaseEnvironment:
    """Test DatabaseEnvironment enum."""

    def test_environment_values(self):
        """Test that environment enum has correct values."""
        assert DatabaseEnvironment.DEV.value == "dev"
        assert DatabaseEnvironment.PROD.value == "prod"
        assert DatabaseEnvironment.TEST.value == "test"


class TestDatabaseConfig:
    """Test DatabaseConfig dataclass."""

    def test_config_creation(self):
        """Test creating DatabaseConfig instances."""
        config = DatabaseConfig(
            env=DatabaseEnvironment.DEV,
            url="sqlite:///test.db",
            path="/path/to/test.db",
            is_prod=False
        )
        assert config.env == DatabaseEnvironment.DEV
        assert config.url == "sqlite:///test.db"
        assert config.path == "/path/to/test.db"
        assert config.is_prod is False

    def test_production_flag(self):
        """Test is_prod flag is set correctly."""
        dev_config = DatabaseConfig(
            env=DatabaseEnvironment.DEV,
            url="sqlite:///dev.db",
            path=None,
            is_prod=False
        )
        assert dev_config.is_prod is False

        prod_config = DatabaseConfig(
            env=DatabaseEnvironment.PROD,
            url="sqlite:///prod.db",
            path=None,
            is_prod=True
        )
        assert prod_config.is_prod is True


class TestGetDatabaseConfig:
    """Test get_database_config() function."""

    def test_default_environment(self, monkeypatch):
        """Test that default environment is dev when no overrides."""
        # Clear any environment variables
        monkeypatch.delenv("ONSENDO_ENV", raising=False)
        monkeypatch.delenv("ONSENDO_DATABASE", raising=False)

        config = get_database_config()

        assert config.env == DatabaseEnvironment.DEV
        assert config.url == CONST.DEV_DATABASE_URL
        assert config.is_prod is False

    def test_env_override_parameter(self, monkeypatch):
        """Test that env_override parameter takes precedence."""
        monkeypatch.delenv("ONSENDO_ENV", raising=False)

        config = get_database_config(env_override="prod")

        assert config.env == DatabaseEnvironment.PROD
        assert config.url == CONST.PROD_DATABASE_URL
        assert config.is_prod is True

    def test_path_override_parameter(self, monkeypatch):
        """Test that path_override parameter takes highest precedence."""
        monkeypatch.delenv("ONSENDO_DATABASE", raising=False)

        custom_path = "/custom/path/db.db"
        config = get_database_config(
            env_override="prod",
            path_override=custom_path
        )

        # Path override means we use dev env but custom path
        assert config.env == DatabaseEnvironment.DEV
        assert config.path == os.path.abspath(custom_path)
        assert config.url == f"sqlite:///{os.path.abspath(custom_path)}"
        assert config.is_prod is False

    def test_environment_variable(self, monkeypatch):
        """Test that ONSENDO_ENV environment variable works."""
        monkeypatch.setenv("ONSENDO_ENV", "prod")

        config = get_database_config()

        assert config.env == DatabaseEnvironment.PROD
        assert config.url == CONST.PROD_DATABASE_URL
        assert config.is_prod is True

    def test_database_path_environment_variable(self, monkeypatch):
        """Test behavior when ONSENDO_DATABASE is not implemented."""
        # Note: ONSENDO_DATABASE is not currently implemented in config.py
        # This test documents expected future behavior or current absence
        custom_path = "/env/path/db.db"
        monkeypatch.setenv("ONSENDO_DATABASE", custom_path)

        config = get_database_config()

        # Currently defaults to dev since ONSENDO_DATABASE is not implemented
        assert config.env == DatabaseEnvironment.DEV
        assert "onsen.dev.db" in config.url

    def test_priority_resolution_order(self, monkeypatch):
        """Test priority: path_override > env_override > ONSENDO_ENV > default."""
        # Set environment variable
        monkeypatch.setenv("ONSENDO_ENV", "prod")

        # env_override should take precedence over environment variable
        config1 = get_database_config(env_override="dev")
        assert config1.env == DatabaseEnvironment.DEV

        # path_override should take precedence over everything
        custom_path = "/priority/test.db"
        config2 = get_database_config(
            env_override="prod",
            path_override=custom_path
        )
        assert config2.path == os.path.abspath(custom_path)
        assert config2.env == DatabaseEnvironment.DEV  # Path override uses dev

    def test_production_blocking_default(self, monkeypatch):
        """Test that production is blocked when allow_prod=False."""
        monkeypatch.delenv("ONSENDO_ENV", raising=False)

        with pytest.raises(ValueError, match="Production database access not allowed"):
            get_database_config(env_override="prod", allow_prod=False)

    def test_production_blocking_with_env_var(self, monkeypatch):
        """Test production blocking with environment variable."""
        monkeypatch.setenv("ONSENDO_ENV", "prod")

        with pytest.raises(ValueError, match="Production database access not allowed"):
            get_database_config(allow_prod=False)

    def test_production_allowed_when_explicit(self):
        """Test that production works when allow_prod=True."""
        config = get_database_config(env_override="prod", allow_prod=True)

        assert config.env == DatabaseEnvironment.PROD
        assert config.is_prod is True

    def test_test_environment(self, monkeypatch):
        """Test that test environment uses in-memory database."""
        monkeypatch.setenv("ONSENDO_ENV", "test")

        config = get_database_config()

        assert config.env == DatabaseEnvironment.TEST
        assert config.url == CONST.MOCK_DATABASE_URL
        assert config.url == "sqlite:///:memory:"
        assert config.is_prod is False

    def test_invalid_environment(self, monkeypatch):
        """Test handling of invalid environment value."""
        monkeypatch.setenv("ONSENDO_ENV", "invalid")

        with pytest.raises(ValueError, match="Invalid ONSENDO_ENV"):
            get_database_config()

    def test_dev_url_format(self):
        """Test that dev database URL is correctly formatted."""
        config = get_database_config(env_override="dev")

        assert config.url.startswith("sqlite:///")
        assert "onsen.dev.db" in config.url

    def test_prod_url_format(self):
        """Test that prod database URL is correctly formatted."""
        config = get_database_config(env_override="prod", allow_prod=True)

        assert config.url.startswith("sqlite:///")
        assert "onsen.prod.db" in config.url

    def test_path_override_converts_to_absolute(self):
        """Test that relative paths are converted to absolute."""
        relative_path = "relative/path/db.db"
        config = get_database_config(path_override=relative_path)

        assert os.path.isabs(config.path)
        assert config.path.endswith("relative/path/db.db")

    def test_config_attributes(self):
        """Test that DatabaseConfig has all expected attributes."""
        config = get_database_config()

        # Verify all expected attributes exist
        assert hasattr(config, 'env')
        assert hasattr(config, 'url')
        assert hasattr(config, 'path')
        assert hasattr(config, 'is_prod')

        # Note: DatabaseConfig is not frozen, so attributes can be modified
        # This is intentional for flexibility


class TestEnsureNotProdInTests:
    """Test ensure_not_prod_in_tests() function."""

    def test_blocks_prod_env_variable(self, monkeypatch):
        """Test that ONSENDO_ENV=prod is blocked in tests."""
        monkeypatch.setenv("ONSENDO_ENV", "prod")

        with pytest.raises(RuntimeError, match="Cannot run tests with ONSENDO_ENV=prod"):
            ensure_not_prod_in_tests()

    def test_allows_custom_database_path(self, monkeypatch):
        """Test that custom database paths are allowed in tests."""
        # Note: ONSENDO_DATABASE blocking is not implemented
        # Custom paths are allowed in tests
        custom_path = "/custom/test/path.db"
        monkeypatch.setenv("ONSENDO_DATABASE", custom_path)

        # Should not raise
        ensure_not_prod_in_tests()

    def test_allows_dev_environment(self, monkeypatch):
        """Test that dev environment is allowed in tests."""
        monkeypatch.setenv("ONSENDO_ENV", "dev")

        # Should not raise
        ensure_not_prod_in_tests()

    def test_allows_test_environment(self, monkeypatch):
        """Test that test environment is allowed in tests."""
        monkeypatch.setenv("ONSENDO_ENV", "test")

        # Should not raise
        ensure_not_prod_in_tests()

    def test_allows_no_environment(self, monkeypatch):
        """Test that no environment variable is allowed in tests."""
        monkeypatch.delenv("ONSENDO_ENV", raising=False)
        monkeypatch.delenv("ONSENDO_DATABASE", raising=False)

        # Should not raise
        ensure_not_prod_in_tests()


class TestIntegration:
    """Integration tests for config system."""

    def test_switching_environments(self, monkeypatch):
        """Test switching between environments."""
        monkeypatch.delenv("ONSENDO_ENV", raising=False)

        # Start with dev
        dev_config = get_database_config(env_override="dev")
        assert dev_config.env == DatabaseEnvironment.DEV

        # Switch to prod
        prod_config = get_database_config(env_override="prod", allow_prod=True)
        assert prod_config.env == DatabaseEnvironment.PROD

        # Switch to test
        test_config = get_database_config(env_override="test")
        assert test_config.env == DatabaseEnvironment.TEST

    def test_environment_variable_precedence(self, monkeypatch):
        """Test complex precedence scenarios."""
        # Scenario 1: Only environment variable set
        monkeypatch.setenv("ONSENDO_ENV", "prod")
        config1 = get_database_config(allow_prod=True)
        assert config1.env == DatabaseEnvironment.PROD

        # Scenario 2: env_override beats environment variable
        config2 = get_database_config(env_override="dev")
        assert config2.env == DatabaseEnvironment.DEV

        # Scenario 3: path_override beats both
        config3 = get_database_config(
            env_override="dev",
            path_override="/custom.db"
        )
        assert "/custom.db" in config3.path

    def test_url_consistency(self):
        """Test that URLs are consistent with paths."""
        config = get_database_config(env_override="dev")

        # Extract path from URL
        url_path = config.url.replace("sqlite:///", "")

        # Should match the path (if path is set)
        if config.path:
            assert url_path == config.path
