#!/usr/bin/env python3
"""
Script to identify geographical articles without infoboxes and add appropriate infoboxes with coordinates.

This script:
1. Identifies articles that are geographical locations by checking if Wikipedia returns lat/lon coordinates
2. Uses Nominatim to get more accurate coordinates when available
3. Adds appropriate infoboxes at the top of articles

No external API keys required - uses Wikipedia API and Nominatim OpenStreetMap service.
"""

import re
import requests
from typing import Optional, Tuple

import pywikibot
from pywikibot import pagegenerators
from tqdm import tqdm

# Initialize wikis
lang_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not lang_wiki.user():
    lang_wiki.login()

# Infobox template
INFOBOX_TEMPLATE = """{{{{infobox Location
|country = {country}
|state = {state}
|map = <map lat='{lat}' lng='{lng}' zoom='9' />
|pop = {population}
|plate = {plate}
|motorways = {motorways}
}}}}"""


def has_infobox(text: str) -> bool:
    """Check if article already has an infobox."""
    return bool(re.search(r'\{\{infobox|\{\{Infobox', text, re.IGNORECASE))


def is_geographical_location(title: str) -> bool:
    """Determine if article is about a geographical location by checking if Wikipedia has coordinates."""
    try:
        # Add headers to identify your request properly
        headers = {
            'User-Agent': 'YourAppName/1.0 (your.email@example.com) Python/requests'
        }
        
        wikipedia_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")
        response = requests.get(wikipedia_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # If Wikipedia has coordinates, it's a geographical location
            if 'coordinates' in data:
                return True
    except Exception as e:
        print(f"Wikipedia lookup error for {title}: {e}")

    return False


def lookup_coordinates_nominatim(title: str) -> Optional[Tuple[float, float]]:
    """Try to get coordinates from Nominatim (OpenStreetMap)."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': title,
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'Hitchwiki-Bot/1.0'}

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Nominatim lookup error for {title}: {e}")

    return None


def get_coordinates(title: str) -> Optional[Tuple[float, float]]:
    """Get coordinates using Nominatim for better accuracy."""

    coords = lookup_coordinates_nominatim(title)
    if coords:
        print(f"Using Nominatim coordinates for {title}")
        return coords

    return None


def add_infobox_to_article(page: pywikibot.Page, page_text:str, coordinates: Tuple[float, float]) -> bool:
    """Add infobox after stub/AI-enhanced templates or at the beginning of the article."""
    try:
        lat, lng = coordinates

        # Create infobox with coordinates
        infobox = INFOBOX_TEMPLATE.format(
            country="-",
            state="-",
            lat=lat,
            lng=lng,
            population="-",
            plate="-",
            motorways="-"
        )

        # Find insertion point after stub or AI-enhanced templates
        text = page_text # page.text
        lines = text.split('\n')
        insertion_line = 0

        # Look for stub or AI-enhanced templates at the top
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('{{stub}}') or stripped_line.startswith('{{Stub}}') or \
               stripped_line.startswith('{{Ai-enhanced}}') or stripped_line.startswith('{{AI-enhanced}}'):
                insertion_line = i + 1
            elif stripped_line and not stripped_line.startswith('{{'):
                # Stop at first non-template content
                break

        # Insert infobox at the determined position
        lines.insert(insertion_line, infobox)
        page.text = '\n'.join(lines)
        page.save("Added infobox with coordinates to geographical article")

        return True
    except Exception as e:
        print(f"Error adding infobox to {page.title()}: {e}")
        return False


def main():
    """Main processing function."""
    # Load or create articles cache
    try:
        from articles import articles
        print("Loaded articles from articles.py")
    except ImportError:
        print("articles.py not found, creating it...")
        pages = list(pagegenerators.AllpagesPageGenerator(site=lang_wiki))

        articles = {}
        for page in tqdm(pages, desc="Processing pages"):
            try:
                articles[page.title()] = {"text": page.text}
            except Exception as e:
                print(f"Error processing page: {e}")
                continue

        # Save articles cache
        with open("articles.py", "w") as f:
            f.write("articles = ")
            f.write(repr(articles))
            f.write("\n")
        print("Created articles.py")

    articles_processed = 0
    articles_with_infobox_added = 0

    for article, items in tqdm(articles.items(), desc="Processing articles"):
        try:
            title = article
            text = items["text"]

            if "Airport" in title:
                continue

            # Skip if already has infobox
            if has_infobox(text):
                continue

            if "#redirect" in text or "#REDIRECT" in text:
                continue

            articles_processed += 1

            # Check if this is a geographical location by looking for Wikipedia coordinates
            is_geographical = is_geographical_location(title)

            if not is_geographical:
                continue

            print(f"\nProcessing geographical article: {title}")

            # Get coordinates
            coordinates = get_coordinates(title)

            if coordinates:
                lat, lng = coordinates
                print(f"Found coordinates: {lat}, {lng}")

                # Add infobox to wiki page
                page = pywikibot.Page(lang_wiki, title)
                if add_infobox_to_article(page, text, coordinates):
                    articles_with_infobox_added += 1
                    print(f"✓ Added infobox to {title}")

                    # Update local cache
                    articles[article]["text"] = page.text

                    # if articles_with_infobox_added == 300:
                    #     break
                else:
                    print(f"✗ Failed to add infobox to {title}")
            else:
                print(f"⚠ No coordinates found for {title}")

        except Exception as e:
            print(f"Error processing {title}: {e}")
            continue

    # Update local copy of articles
    with open("articles.py", "w") as f:
        f.write("articles = ")
        f.write(repr(articles))
        f.write("\n")

    print("\nProcessing complete!")
    print(f"Articles processed: {articles_processed}")
    print(f"Infoboxes added: {articles_with_infobox_added}")


if __name__ == "__main__":
    main()