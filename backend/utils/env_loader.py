#!/usr/bin/env python3
"""
Environment Loader - Load environment variables from .env file
Extracted from original EnvLoader class
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env_file(env_path=None):
    """
    Load environment variables from .env file

    Args:
        env_path: Path to .env file (defaults to parent directory's .env)

    Returns:
        dict: Environment variables as key-value pairs
    """
    if env_path is None:
        # Default to .env in parent directory (project root)
        env_path = Path(__file__).parent.parent.parent / '.env'

    env_vars = {}

    if not os.path.exists(env_path):
        logger.warning(f"⚠️  .env file not found at {env_path}")
        return env_vars

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Strip quotes and whitespace
                    clean_value = value.strip().strip('"').strip("'")
                    env_vars[key.strip()] = clean_value
                    # Also set in os.environ for other parts of the app
                    os.environ[key.strip()] = clean_value

        logger.info(f"✅ Loaded {len(env_vars)} environment variables from .env")
    except Exception as e:
        logger.error(f"❌ Error loading .env file: {e}")

    return env_vars
