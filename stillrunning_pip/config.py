"""Configuration loading for stillrunning-pip."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".stillrunning"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "token": "",
    "block_dangerous": True,
    "warn_suspicious": True,
    "offline_mode": "warn",  # "warn", "block", "allow"
    "timeout": 30,
    "api_url": "https://stillrunning.io/api/pip-plugin/scan"
}


def load_config() -> dict:
    """Load config from ~/.stillrunning/config.json"""
    config = DEFAULT_CONFIG.copy()

    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                user_config = json.load(f)
                config.update(user_config)
    except Exception:
        pass

    # Environment variable overrides
    if os.environ.get("STILLRUNNING_TOKEN"):
        config["token"] = os.environ["STILLRUNNING_TOKEN"]

    return config


def save_config(config: dict):
    """Save config to ~/.stillrunning/config.json"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def setup_config():
    """Interactive config setup."""
    print("\n" + "=" * 50)
    print("stillrunning-pip Setup")
    print("=" * 50 + "\n")

    config = load_config()

    # Token
    print("Enter your stillrunning.io token (or press Enter to skip):")
    print("Get a token at https://stillrunning.io/pricing")
    token = input("> ").strip()
    if token:
        config["token"] = token

    # Block dangerous
    print("\nBlock installs for dangerous packages? [Y/n]")
    response = input("> ").strip().lower()
    config["block_dangerous"] = response != "n"

    # Warn suspicious
    print("\nWarn about suspicious packages? [Y/n]")
    response = input("> ").strip().lower()
    config["warn_suspicious"] = response != "n"

    # Offline mode
    print("\nBehavior when API is unreachable? [warn/block/allow] (default: warn)")
    response = input("> ").strip().lower()
    if response in ("warn", "block", "allow"):
        config["offline_mode"] = response

    save_config(config)
    print(f"\nConfig saved to {CONFIG_FILE}")
    print("You can now use: stillrunning-pip install <package>\n")
