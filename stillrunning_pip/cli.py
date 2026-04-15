#!/usr/bin/env python3
"""
stillrunning-pip — Secure pip wrapper with supply chain attack protection.

Usage:
    stillrunning-pip install requests flask
    stillrunning-pip --setup
    stillrunning-pip --version
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from .config import load_config, setup_config
from . import __version__

# Terminal colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def extract_packages(args: list) -> list:
    """Extract package names from pip install arguments."""
    packages = []
    skip_next = False

    for arg in args:
        if skip_next:
            skip_next = False
            continue

        if arg.startswith("-"):
            # Some flags take values
            if arg in ("-r", "--requirement", "-e", "--editable", "-t", "--target",
                       "-c", "--constraint", "-i", "--index-url", "--extra-index-url"):
                skip_next = True
            continue

        if arg in ("install", "i"):
            continue

        # This is a package name (possibly with version specifier)
        # Remove version specifiers for API
        pkg = arg.strip()
        if pkg:
            packages.append(pkg)

    return packages


def parse_requirements_file(filepath: str) -> list:
    """Parse a requirements.txt file."""
    packages = []
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                if "#" in line:
                    line = line.split("#")[0].strip()
                if line:
                    packages.append(line)
    except Exception:
        pass
    return packages


def call_api(packages: list, config: dict) -> dict:
    """Call stillrunning.io API."""
    # Format packages for API
    package_list = []
    for pkg in packages:
        # Parse name and version
        for sep in ["==", ">=", "<=", "~=", "!=", ">", "<", "@"]:
            if sep in pkg:
                parts = pkg.split(sep, 1)
                package_list.append({
                    "name": parts[0].strip(),
                    "version": parts[1].strip() if len(parts) > 1 else "latest"
                })
                break
        else:
            # Remove extras like [security]
            name = pkg.split("[")[0].strip() if "[" in pkg else pkg.strip()
            package_list.append({"name": name, "version": "latest"})

    payload = json.dumps({
        "packages": package_list,
        "token": config.get("token", "")
    }).encode()

    api_url = config.get("api_url", "https://stillrunning.io/api/pip-plugin/scan")
    timeout = config.get("timeout", 30)

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": f"stillrunning-pip/{__version__}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return {"error": f"API error: {e.code}", "details": error_body}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "offline": True}
    except Exception as e:
        return {"error": str(e), "offline": True}


def print_result(result: dict):
    """Print formatted result for a package."""
    verdict = result.get("verdict", "UNKNOWN")
    package = result.get("package", "unknown")
    version = result.get("version", "")
    score = result.get("score", 0)
    reason = result.get("reason", "")

    pkg_display = f"{package}=={version}" if version and version != "latest" else package

    if verdict == "DANGEROUS":
        print(f"  {RED}{BOLD}🚫 BLOCKED{RESET}    {pkg_display}")
        if reason:
            print(f"     {DIM}→ {reason}{RESET}")
    elif verdict == "SUSPICIOUS":
        print(f"  {YELLOW}⚠️  WARNING{RESET}    {pkg_display}")
        if reason:
            print(f"     {DIM}→ {reason}{RESET}")
    elif verdict == "UNKNOWN":
        print(f"  {DIM}❓ UNKNOWN{RESET}    {pkg_display}")
        if reason:
            print(f"     {DIM}→ {reason}{RESET}")
    else:
        print(f"  {GREEN}✅ CLEAN{RESET}      {pkg_display}")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Handle special flags
    if not args or "--help" in args or "-h" in args:
        print(f"""
{BOLD}stillrunning-pip{RESET} v{__version__} — Secure pip wrapper

Usage:
    stillrunning-pip install <packages>   Scan and install packages
    stillrunning-pip --setup              Configure stillrunning-pip
    stillrunning-pip --version            Show version
    stillrunning-pip <pip-command>        Pass through to pip

Examples:
    stillrunning-pip install requests flask
    stillrunning-pip install -r requirements.txt
""")
        if args and args[0] not in ("--help", "-h"):
            # Pass through to pip
            result = subprocess.run(["pip"] + args)
            sys.exit(result.returncode)
        sys.exit(0)

    if "--version" in args:
        print(f"stillrunning-pip {__version__}")
        sys.exit(0)

    if "--setup" in args:
        setup_config()
        sys.exit(0)

    # Only intercept install commands
    if args[0] not in ("install", "i"):
        # Pass through non-install commands
        result = subprocess.run(["pip"] + args)
        sys.exit(result.returncode)

    # Load config
    config = load_config()

    # Extract packages to check
    packages = extract_packages(args)

    # Check for -r flag and parse requirements file
    for i, arg in enumerate(args):
        if arg in ("-r", "--requirement") and i + 1 < len(args):
            req_packages = parse_requirements_file(args[i + 1])
            packages.extend(req_packages)

    # Deduplicate
    packages = list(set(packages))

    if not packages:
        # No packages to check, just pass through
        result = subprocess.run(["pip"] + args)
        sys.exit(result.returncode)

    # Print header
    print(f"\n{BOLD}🛡️  stillrunning security scan{RESET}")
    print(f"{DIM}   Checking {len(packages)} package(s)...{RESET}\n")

    # Call API
    api_result = call_api(packages, config)

    # Handle errors
    if "error" in api_result:
        offline_mode = config.get("offline_mode", "warn")

        if api_result.get("offline"):
            if offline_mode == "block":
                print(f"{RED}Error: API unreachable — install blocked{RESET}")
                print(f"{DIM}   {api_result['error']}{RESET}\n")
                sys.exit(1)
            elif offline_mode == "allow":
                print(f"{DIM}API unavailable — proceeding without scan{RESET}\n")
                result = subprocess.run(["pip"] + args)
                sys.exit(result.returncode)
            else:  # warn
                print(f"{YELLOW}⚠️  API unavailable — proceeding with caution{RESET}")
                print(f"{DIM}   {api_result['error']}{RESET}\n")
                result = subprocess.run(["pip"] + args)
                sys.exit(result.returncode)
        else:
            print(f"{RED}Error: {api_result['error']}{RESET}")
            if api_result.get("details"):
                print(f"{DIM}   {api_result['details'][:200]}{RESET}")
            print()
            sys.exit(1)

    # Process results
    results = api_result.get("results", [])
    blocked = []
    warnings = []

    for r in results:
        verdict = r.get("verdict", "CLEAN")
        if verdict == "DANGEROUS":
            blocked.append(r)
            print_result(r)
        elif verdict == "SUSPICIOUS":
            warnings.append(r)
            if config.get("warn_suspicious", True):
                print_result(r)
        elif verdict == "UNKNOWN":
            print_result(r)

    # Handle blocked packages
    if blocked and config.get("block_dangerous", True):
        print(f"\n{RED}{BOLD}❌ Installation blocked{RESET}")
        print(f"{RED}   {len(blocked)} dangerous package(s) detected{RESET}")
        print(f"\n{DIM}If you believe this is a false positive, report it at:{RESET}")
        print(f"{DIM}https://stillrunning.io/report{RESET}\n")
        sys.exit(1)

    # Handle warnings
    if warnings and config.get("warn_suspicious", True):
        print(f"\n{YELLOW}⚠️  {len(warnings)} suspicious package(s) found{RESET}")

    # Show upgrade prompt if unknown packages and no token
    unknown = [r for r in results if r.get("verdict") == "UNKNOWN"]
    if unknown and not config.get("token"):
        print(f"\n{DIM}💡 {len(unknown)} packages not AI-scanned.{RESET}")
        print(f"{DIM}   Get a token at https://stillrunning.io/pricing{RESET}")

    # All clear — proceed with install
    clean_count = len([r for r in results if r.get("verdict") == "CLEAN"])
    print(f"\n{GREEN}✅ {clean_count} package(s) verified{RESET}")
    print(f"{DIM}   Proceeding with pip install...{RESET}\n")

    result = subprocess.run(["pip"] + args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
