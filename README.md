# stillrunning-pip

> The zero-config pip wrapper that catches malicious packages before they install.
> Try it in 5 seconds. No setup, no signup, no config.

[![PyPI](https://img.shields.io/pypi/v/stillrunning-pip)](https://pypi.org/project/stillrunning-pip/)
[![Threats blocked](https://stillrunning.io/badge/protected)](https://stillrunning.io/security-advisories)

## Try it now

```bash
pip install stillrunning-pip
stillrunning-pip install requests
```

That's it. Every package you install is now checked against [200,000+ verified malicious packages](https://stillrunning.io/security-advisories) from OSV.dev, GitHub Advisory, and 6 other threat intelligence sources, updated nightly.

## What you get for free

- 10 scans per day per IP, no signup required
- Blocks confirmed-malicious packages automatically
- Warns about suspicious packages
- Works with `pip install <pkg>` and `pip install -r requirements.txt`
- 5-second installs, 5-second scans

## Replace pip globally (optional)

```bash
alias pip='stillrunning-pip'
```

Add to `~/.bashrc` or `~/.zshrc` for every install in every project to be scanned.

## Hit the rate limit?

Get the full `stillrunning` package — covers pip, uv, poetry, pdm, pipenv, conda, pixi, npm, bun, pnpm, with unlimited scans, AI analysis of unknown packages, and import-time protection:

```bash
pip install stillrunning
```

[stillrunning.io/pricing](https://stillrunning.io/pricing) for paid tiers.

## How it works

Before each install, stillrunning-pip queries the public API:

```
GET https://stillrunning.io/api/check-package?name=<pkg>
```

If the package is on the verified blocklist, the install is halted with a clear message. Every block traces back to a public security advisory you can verify yourself at [stillrunning.io/security-advisories](https://stillrunning.io/security-advisories).

## Power user features

Set `STILLRUNNING_TOKEN` to unlock unlimited scans and AI analysis of unknown packages. Get a token at [stillrunning.io/pricing](https://stillrunning.io/pricing).

```bash
export STILLRUNNING_TOKEN=sr_...
stillrunning-pip install <pkg>
```

## Bypass scanning

If you need to install something stillrunning is blocking and you've verified it's safe:

```bash
pip install <package>
```

Just use vanilla pip directly. stillrunning-pip is opt-in via being the binary you call.

## Relationship to stillrunning

`stillrunning-pip` is the simplest member of the [stillrunning](https://github.com/johhnyg/stillrunning) family. It does one thing: scans pip installs against the verified threat database.

For broader coverage (uv, poetry, pdm, pipenv, conda, pixi, npm, bun, pnpm), import-time protection, MCP server for Claude Code, GitHub Action for CI, and unlimited scans, install the main package: `pip install stillrunning`.

## License

MIT

---

[stillrunning.io](https://stillrunning.io) | [@bit_bot9000](https://x.com/bit_bot9000)
