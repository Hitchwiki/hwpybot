# Bot Automations for Hitchwiki

This is [pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot) code for [hitchwiki](https://hitchwiki.org/).

## Get started
`coords_missing/` is a clean example how to manipulate articles in bulk. Copy code from there into a new directory and adjust to your needs.

## Setup

We're using [Astral uv](https://docs.astral.sh/uv/) for handling packages and running scripts.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See https://docs.astral.sh/uv/getting-started/installation/ for other installation methods.

### Install dependencies

```bash
uv sync
```

### Run a script

```bash
uv run script_name.py
```

Some scripts use [inline dependencies (PEP 723)](https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies) and `uv run` will automatically install them.