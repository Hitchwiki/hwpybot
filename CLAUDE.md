# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of pywikibot scripts for automating tasks on Hitchwiki (https://hitchwiki.org/), a collaborative wiki about hitchhiking. The repository contains scripts for article translation, geographic data management, link processing, and wiki content cleanup.

## Setup Requirements

### Core Dependencies
- Python 3.13+ (specified in pyproject.toml)
- Use `uv` for package management (Astral UV) - see https://docs.astral.sh/uv/getting-started/installation/
- Install dependencies: `uv sync` or use script inline dependencies

### Configuration Files Required
Each module directory requires these configuration files (copy from .example templates):
- `user-password.py` - Contains bot credentials for Hitchwiki API access
- `.env` - Environment variables (for modules using OpenAI)

### Pywikibot Configuration
The `user-config.py` file configures access to multiple Hitchwiki language wikis:
- English: hitchwiki.org/en/
- German: hitchwiki.org/de/
- French: hitchwiki.org/fr/
- Turkish: hitchwiki.org/tr/
- Russian: hitchwiki.org/ru/

## Running Scripts

Most scripts can be run with:
```bash
uv run script_name.py
```

Some scripts use inline dependencies (PEP 723) and can be run directly.

## Project Architecture

### Module Structure
- `article_translation/` - Scripts for translating wiki articles between languages using OpenAI API
- `geotag/` - Geographic data processing and Nostr integration for hitchhiking spots
- `coords_tag/` - Coordinate extraction and processing from wiki markup
- `links/` - Link processing and validation tools
- `infobox/` - Infobox template management for city pages
- `cleaning/` - Wiki content cleanup and maintenance scripts

### Key Components

#### Article Translation Module
- Uses OpenAI GPT for translating articles between languages
- Template-based translation with city-specific prompts
- Country-specific scripts (turkey, france, germany, russia)
- Clean reference implementation: `translate_turkey_openai.py`

#### Geographic Data Processing
- Coordinate extraction from wiki markup using regex patterns
- Integration with Nostr protocol for broadcasting location data
- Support for multiple coordinate formats (lat/lon, geohash, open location codes)
- SQLite database for caching coordinate data

#### Content Management
- Pywikibot integration for wiki editing and page management
- Batch processing with progress tracking using tqdm
- API caching for performance optimization
- Category-based page generation and filtering

### Development Workflow

#### For Development/Testing
Use Jupyter notebooks in each module (`experiment.ipynb`) for interactive development and testing.

#### Script Execution
- Scripts handle authentication automatically via pywikibot
- Most operations include progress bars and error handling
- API rate limiting and throttling built-in

### Data Flow
1. Scripts connect to Hitchwiki APIs using pywikibot
2. Page content is extracted and processed (coordinates, translations, etc.)
3. External APIs (OpenAI, Nostr) may be called for processing
4. Results are written back to wiki or exported to files

## Testing and Quality

No formal test framework is configured. Testing is done through:
- Interactive development in Jupyter notebooks
- Manual verification of script outputs
- Wiki sandbox testing before production runs