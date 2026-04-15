# stillrunning-pip

Secure pip wrapper that scans packages for supply chain attacks before installing.

[![PyPI version](https://badge.fury.io/py/stillrunning-pip.svg)](https://pypi.org/project/stillrunning-pip/)
[![stillrunning](https://stillrunning.io/badge/protected)](https://stillrunning.io)

## Installation

```bash
pip install stillrunning-pip
```

## Usage

Use `stillrunning-pip` instead of `pip`:

```bash
stillrunning-pip install requests flask
stillrunning-pip install -r requirements.txt
```

Or create an alias:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias pip='stillrunning-pip'
```

## Setup

Configure your token and preferences:

```bash
stillrunning-pip --setup
```

Or create `~/.stillrunning/config.json` manually:

```json
{
  "token": "sr_your_token_here",
  "block_dangerous": true,
  "warn_suspicious": true,
  "offline_mode": "warn"
}
```

## Example Output

```
🛡️  stillrunning security scan
   Checking 5 package(s)...

  ✅ CLEAN      requests==2.31.0
  ✅ CLEAN      flask==2.3.0
  ⚠️  WARNING    sketchy-lib==1.0.0
     → Obfuscated code patterns detected
  🚫 BLOCKED    evil-pkg==0.1.0
     → Known malicious package (reverse shell)

❌ Installation blocked
   1 dangerous package(s) detected
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `token` | `""` | stillrunning.io API token for AI scanning |
| `block_dangerous` | `true` | Block installs for dangerous packages |
| `warn_suspicious` | `true` | Show warnings for suspicious packages |
| `offline_mode` | `"warn"` | Behavior when API unreachable: `warn`, `block`, `allow` |
| `timeout` | `30` | API timeout in seconds |

## Environment Variables

- `STILLRUNNING_TOKEN` — Override token from config

## Free vs Paid

| Feature | Free | With Token |
|---------|------|------------|
| Known malicious packages | Blocked | Blocked |
| Threat feed database | Checked | Checked |
| AI analysis of unknown packages | - | Yes |
| Scans per day | Unlimited (cached) | 100-10000 |

Get a token at [stillrunning.io/pricing](https://stillrunning.io/pricing)

## What It Detects

- **Known malicious packages** — Packages in our threat database (DPRK campaigns, typosquats, backdoors)
- **Typosquatting** — Packages with names similar to popular packages
- **AI-flagged packages** — Obfuscated code, credential harvesting, reverse shells

## Bypass (Not Recommended)

To bypass scanning for a single install:

```bash
pip install <package>  # Use pip directly
```

## Uninstall

```bash
pip uninstall stillrunning-pip
```

## License

MIT
