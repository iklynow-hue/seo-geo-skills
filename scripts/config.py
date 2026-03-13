#!/usr/bin/env python3
"""
Configuration loader for SGEO
Supports YAML (~/.sgeorc) and JSON (sgeo.config.json) formats
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import PyYAML, but make it optional
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


DEFAULT_CONFIG = {
    "timeout": 30,
    "max_workers": 10,
    "user_agent": "SGEO-Audit-Bot/1.0 (SEO+GEO Analysis)",
    "api_keys": {
        "pagespeed": None
    },
    "output_dir": "outputs/",
    "auto_open_report": True,
    "generate_pdf": True
}


def load_yaml_config(path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML config file."""
    if not HAS_YAML:
        return None

    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if isinstance(config, dict) else None
    except Exception as e:
        print(f"Warning: Failed to load YAML config from {path}: {e}")
        return None


def load_json_config(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON config file."""
    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config if isinstance(config, dict) else None
    except Exception as e:
        print(f"Warning: Failed to load JSON config from {path}: {e}")
        return None


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override config into base config."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def load_config() -> Dict[str, Any]:
    """
    Load configuration from multiple sources with priority:
    1. Default values (lowest priority)
    2. ~/.sgeorc (YAML format, if PyYAML installed)
    3. sgeo.config.json in project root (highest priority)

    Returns merged configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()

    # Try loading ~/.sgeorc (YAML)
    home_config_path = Path.home() / ".sgeorc"
    if HAS_YAML:
        home_config = load_yaml_config(home_config_path)
        if home_config:
            config = merge_configs(config, home_config)
            print(f"Loaded config from {home_config_path}")

    # Try loading sgeo.config.json in project root
    # Find project root (where scripts/ directory is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    project_config_path = project_root / "sgeo.config.json"

    project_config = load_json_config(project_config_path)
    if project_config:
        config = merge_configs(config, project_config)
        print(f"Loaded config from {project_config_path}")

    return config


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get a config value, supporting dot notation for nested keys.
    Example: get_config_value(config, "api_keys.pagespeed")
    """
    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def print_config_info():
    """Print information about config file support."""
    print("Configuration file support:")
    print(f"  YAML support: {'Yes' if HAS_YAML else 'No (install PyYAML: pip install pyyaml)'}")
    print(f"  Config locations (priority order):")
    print(f"    1. Default values")
    print(f"    2. ~/.sgeorc (YAML format)")
    print(f"    3. sgeo.config.json (project root)")
    print()


if __name__ == "__main__":
    # Test config loading
    print_config_info()
    config = load_config()
    print("Current configuration:")
    print(json.dumps(config, indent=2))
