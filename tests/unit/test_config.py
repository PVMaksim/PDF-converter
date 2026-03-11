"""Unit tests for configuration and settings."""
import pytest
import os
from unittest.mock import patch


def test_settings_load_from_env():
    """Test that settings are loaded from environment variables."""
    from src.config import Settings
    
    with patch.dict(os.environ, {
        'SECRET_KEY': 'test-secret-key',
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost/db',
        'ADMIN_TELEGRAM_ID': '123456',
    }, clear=False):
        settings = Settings()
        
        assert settings.SECRET_KEY == 'test-secret-key'
        assert settings.TELEGRAM_BOT_TOKEN == 'test-token'
        assert settings.DEBUG is False


def test_settings_default_values():
    """Test settings default values."""
    from src.config import Settings
    
    with patch.dict(os.environ, {
        'SECRET_KEY': 'test-key',
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'DATABASE_URL': 'postgresql://localhost/db',
    }, clear=False):
        settings = Settings()
        
        assert settings.DEBUG is False
        assert settings.ALLOWED_HOSTS == "*"
        assert settings.MAX_FILE_SIZE_FREE_MB == 50
        assert settings.RATE_LIMIT_FREE_PER_HOUR == 10


def test_settings_pro_limits():
    """Test PRO tier limits."""
    from src.config import Settings
    
    with patch.dict(os.environ, {
        'SECRET_KEY': 'test-key',
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'DATABASE_URL': 'postgresql://localhost/db',
    }, clear=False):
        settings = Settings()
        
        assert settings.MAX_FILE_SIZE_PRO_MB == 200
        assert settings.FILE_TTL_PRO_DAYS == 7
        assert settings.RATE_LIMIT_PRO_PER_HOUR == 100
