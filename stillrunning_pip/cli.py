#!/usr/bin/env python3
"""
stillrunning-pip v1.1.0 — Zero-config pip wrapper with supply chain protection.

Usage:
    stillrunning-pip install requests flask
    stillrunning-pip --version
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

from . import __version__

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

API_BASE = "https://stillrunning.io"
TIMEOUT = 5


def extract_packages(args: list) -> list:
    """Extract package names from pip install arguments."""
    packages = []
    skip_next = False

    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("-"):
            if arg in ("-r", "--requirement", "-e", "--editable", "-t", "--target",
                       "-c", "--constraint", "-i", "--index-url", "--extra-index-url"):
                skip_next = True
            continue
        if arg in ("install", "i"):
            continue
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


def parse_package_name(pkg: str) -> str:
    """Extract package name from specifier like requests>=2.0[security]."""
    for sep in ["==", ">=", "<=", "~=", "!=", ">", "<", "@"]:
        if sep in pkg:
            pkg = pkg.split(sep, 1)[0]
            break
    if "[" in pkg:
        pkg = pkg.split("[")[0]
    return pkg.strip().lower()


def check_package(name: str, token: str = None) -> dict:
    """Check a single package against the API. Returns verdict dict."""
    try:
        url = f"{API_BASE}/api/check-package?name={name}&ecosystem=pip"
        headers = {"User-Agent": f"stillrunning-pip/{__version__}"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"verdict": "RATE_LIMITED", "package": name}
        return {"verdict": "ERROR", "package": name, "error": str(e)}
    except Exception as e:
        return {"verdict": "ERROR", "package": name, "error": str(e)}


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(f"""
{BOLD}stillrunning-pip{RESET} v{__version__} — Zero-config pip wrapper

Usage:
    stillrunning-pip install <packages>   Scan and install packages
    stillrunning-pip --version            Show version
    stillrunning-pip <pip-command>        Pass through to pip

Examples:
    stillrunning-pip install requests flask
    stillrunning-pip install -r requirements.txt

No setup required. Works immediately.
""")
        if args and args[0] not in ("--help", "-h"):
            result = subprocess.run(["pip"] + args)
            sys.exit(result.returncode)
        sys.exit(0)

    if "--version" in args:
        print(f"stillrunning-pip {__version__}")
        sys.exit(0)

    if "--setup" in args:
        print(f"\n{GREEN}stillrunning-pip works without setup.{RESET}")
        print(f"Just run: stillrunning-pip install <package>")
        print(f"\nFor unlimited scans, set STILLRUNNING_TOKEN env var.")
        print(f"Get a token at: https://stillrunning.io/pricing\n")
        sys.exit(0)

    if args[0] not in ("install", "i"):
        result = subprocess.run(["pip"] + args)
        sys.exit(result.returncode)

    packages = extract_packages(args)
    for i, arg in enumerate(args):
        if arg in ("-r", "--requirement") and i + 1 < len(args):
            packages.extend(parse_requirements_file(args[i + 1]))
    packages = list(set(packages))

    if not packages:
        result = subprocess.run(["pip"] + args)
        sys.exit(result.returncode)

    print(f"\n{BOLD}stillrunning{RESET} checking {len(packages)} package(s)...\n")

    token = os.environ.get("STILLRUNNING_TOKEN", "")
    blocked = []
    warnings = []
    rate_limited = False

    for pkg_spec in packages:
        name = parse_package_name(pkg_spec)
        if not name:
            continue

        result = check_package(name, token)
        verdict = result.get("verdict", "UNKNOWN")

        if verdict == "BLOCKED":
            blocked.append(name)
            reason = result.get("reason", "Known malicious package")
            print(f"  {RED}BLOCKED{RESET}  {name}")
            print(f"           {DIM}{reason}{RESET}")
        elif verdict == "SUSPICIOUS":
            warnings.append(name)
            print(f"  {YELLOW}WARNING{RESET}  {name}")
        elif verdict == "RATE_LIMITED":
            rate_limited = True
            print(f"  {YELLOW}SKIPPED{RESET}  {name} {DIM}(rate limit){RESET}")
        elif verdict == "ERROR":
            print(f"  {DIM}SKIPPED{RESET}  {name} {DIM}(API unavailable){RESET}")
        else:
            print(f"  {GREEN}CLEAN{RESET}    {name}")

    print()

    if rate_limited:
        print(f"{YELLOW}Free tier limit reached (10/day).{RESET}")
        print(f"For unlimited scans: pip install stillrunning")
        print(f"https://stillrunning.io/pricing\n")

    if blocked:
        print(f"{RED}{BOLD}Installation blocked{RESET}")
        print(f"{len(blocked)} dangerous package(s): {', '.join(blocked)}")
        print(f"\nVerify at: https://stillrunning.io/security-advisories")
        print(f"To bypass: pip install <package>\n")
        sys.exit(1)

    if warnings:
        print(f"{YELLOW}{len(warnings)} suspicious package(s) — proceeding with caution{RESET}\n")

    print(f"{DIM}Running pip install...{RESET}\n")
    result = subprocess.run(["pip"] + args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
