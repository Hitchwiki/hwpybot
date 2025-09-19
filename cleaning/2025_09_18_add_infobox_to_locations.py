#!/usr/bin/env python3
"""
Script to identify geographical articles without infoboxes and add appropriate infoboxes with coordinates.

This script:
1. Identifies articles that are geographical locations (cities, regions, water bodies, etc.)
2. Extracts or looks up coordinates for these locations
3. Adds appropriate infoboxes at the top of articles

Requires .env file with OPENAI_API_KEY for OpenAI API calls.
"""

import re
import requests
from typing import Optional, Tuple
from dotenv import load_dotenv

import pywikibot
from pywikibot import pagegenerators
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

# Initialize wikis
lang_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not lang_wiki.user():
    lang_wiki.login()

# Initialize OpenAI client
client = OpenAI()

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


def is_geographical_openai(title: str, text: str) -> bool:
    """Use OpenAI to determine if article is about a geographical location."""
    prompt = f"""
    Analyze this wiki article and determine if it's about a geographical location that can be shown on a map.

    Consider these as geographical:
    - Cities, towns, villages
    - Countries, states, regions, provinces
    - Rivers, lakes, mountains, islands
    - Highways, roads, bridges
    - Borders, administrative divisions

    Do NOT consider these as geographical:
    - People, organizations, events
    - Abstract concepts, topics
    - Products, services, technologies

    Article title: {title}
    Article text (first 500 chars): {text[:100]}

    Respond with only "YES" if it's a geographical location, "NO" if it's not.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )

        answer = response.choices[0].message.content.strip().upper()
        return answer == "YES"
    except Exception as e:
        print(f"OpenAI error for {title}: {e}")
        return False


def lookup_coordinates_wikipedia(title: str) -> Optional[Tuple[float, float]]:
    """Try to get coordinates from Wikipedia/Wikidata."""
    try:
        # Try Wikipedia API
        wikipedia_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")
        response = requests.get(wikipedia_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'coordinates' in data:
                coords = data['coordinates']
                return coords['lat'], coords['lon']
    except Exception as e:
        print(f"Wikipedia lookup error for {title}: {e}")

    return None


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


def lookup_coordinates_openai(title: str) -> Optional[Tuple[float, float]]:
    """Use OpenAI to get coordinates for known locations."""
    prompt = f"""
    Provide the latitude and longitude coordinates for the geographical location: {title}

    Respond with only the coordinates in this exact format:
    lat,lng

    For example: 52.5200,13.4050

    If you don't know the exact coordinates or the location doesn't exist, respond with: UNKNOWN
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )

        answer = response.choices[0].message.content.strip()

        if answer == "UNKNOWN":
            return None

        if ',' in answer:
            parts = answer.split(',')
            if len(parts) == 2:
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                # Basic validation
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return lat, lng
    except Exception as e:
        print(f"OpenAI coordinate lookup error for {title}: {e}")

    return None


def get_coordinates(title: str) -> Optional[Tuple[float, float]]:
    """Get coordinates using multiple methods."""
    # 2. Try Wikipedia
    coords = lookup_coordinates_wikipedia(title)
    if coords:
        return coords

    # 3. Try Nominatim
    coords = lookup_coordinates_nominatim(title)
    if coords:
        return coords

    # 4. Try OpenAI as last resort
    coords = lookup_coordinates_openai(title)
    if coords:
        return coords

    return None


def add_infobox_to_article(page: pywikibot.Page, coordinates: Tuple[float, float]) -> bool:
    """Add infobox to the beginning of the article."""
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

        # Add infobox at the beginning
        page.text = f"{infobox}\n{page.text}"
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

            # Skip if already has infobox
            if has_infobox(text):
                continue

            articles_processed += 1

            is_geographical = False
            if len(text) > 100:  # Only for substantial articles
                is_geographical = is_geographical_openai(title, text)

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
                if add_infobox_to_article(page, coordinates):
                    articles_with_infobox_added += 1
                    print(f"✓ Added infobox to {title}")

                    # Update local cache
                    articles[article]["text"] = page.text
                    break
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