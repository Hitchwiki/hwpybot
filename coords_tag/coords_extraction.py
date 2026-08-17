import re
import urllib.parse

import requests


def fetch_real_anchors(title: str, api_url: str) -> list[dict] | None:
    """The real anchor MediaWiki itself will use for every heading on `title`,
    straight from `action=parse&prop=sections` -- `byteoffset` is measured
    against the raw wikitext, the same coordinate space `extract_coords_and_headings`
    already finds `{{Coords}}` tag positions in, so the two can be matched directly.

    Exists because `heading_to_fragment` below can only ever guess at what
    MediaWiki will render a heading's raw wikitext into. A `[[Prague]]` link is a
    solvable guess (strip brackets), but a template call is not: `{{Autobahn|17}}`
    in a heading (github.com/Hitchwiki/hwpybot/issues/5) expands to
    `File:Bundesautobahn 17 number.svg` (its display icon), giving the real
    anchor `South_towards_Prague_(File:Bundesautobahn_17_number.svg)` -- nothing
    a regex over raw wikitext could ever produce, since it never sees what the
    template expands to. Returns None on any request failure so a caller can
    fall back to the regex heuristic rather than breaking entirely offline.
    """
    try:
        resp = requests.get(
            api_url,
            params={"action": "parse", "page": title, "prop": "sections", "format": "json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["parse"]["sections"]
    except (requests.RequestException, KeyError, ValueError):
        return None


def heading_to_fragment(heading, num_same_heading_above:int):
    # 1. Trim whitespace
    heading = heading.strip()
    # 2. Remove wiki markup (e.g., '', ''', etc.)
    heading = re.sub(r"''+", "", heading)
    # 3. Normalize spaces to single underscores
    heading = re.sub(r"\s+", "_", heading)
    # Remove [ and ] characters
    heading = heading.replace("[", "").replace("]", "")
    # 4. Capitalize the first character
    if heading:
        heading = heading[0].upper() + heading[1:]
    # 5. Percent-encode non-ASCII or special characters
    # fragment = urllib.parse.quote(heading, safe='_')
    if num_same_heading_above > 0:
        heading += f"_{num_same_heading_above + 1}"
    return heading


def extract_coords_and_headings(text):
    # Find all headings with their positions
    heading_pattern = re.compile(r"^(=+)\s*(.*?)\s*\1$", re.MULTILINE)
    headings = [(m.start(), m.group(2)) for m in heading_pattern.finditer(text)]

    # Find all {{Coords|...}} tags with their positions
    coords_pattern = re.compile(r"{{Coords\|[^}]+}}")
    coords = [(m.start(), m.group(0)) for m in coords_pattern.finditer(text)]

    results = []
    for coord_pos, coord_tag in coords:
        # Find the closest preceding heading
        heading = None
        same_heading_count = 0
        for h_pos, h_text in reversed(headings):
            if heading and h_text == heading:
                same_heading_count += 1

            if h_pos < coord_pos and heading is None:
                heading = h_text

        results.append(
            {
                "heading": heading,
                "coords": coord_tag,
                # Character offset into `text`, not yet the byte offset
                # `find_coords_and_headings` needs to match against the API's
                # `action=parse&prop=sections` -- see `_char_pos_to_byte_offset`.
                "pos": coord_pos,
                "same_heading_count": same_heading_count,
            }
        )
    return results


def _char_pos_to_byte_offset(text: str, char_pos: int) -> int:
    """MediaWiki's `sections[].byteoffset` counts UTF-8 bytes into the raw
    wikitext, not characters -- a heading anywhere before a `{{Coords}}` tag
    that contains even one non-ASCII character (e.g. 'Ústí nad Labem', a real
    Dresden heading) would otherwise put every offset after it one or more
    bytes off from what the API reports, silently breaking the position match
    below for any page with non-ASCII content earlier in the article."""
    return len(text[:char_pos].encode("utf-8"))


def find_coords_and_headings(
    raw_wiki_page: str,
    title: str,
    base_url: str = "https://hitchwiki.org/en/",
    api_url: str | None = None,
) -> list[dict]:
    """For each `{{Coords}}` tag, the URL (with section anchor) it belongs under.

    Prefers MediaWiki's own real anchor for the enclosing section
    (`action=parse&prop=sections`, see `fetch_real_anchors`) over hand-computing
    one from raw wikitext -- the hand-computed version can't know what a
    template call in the heading expands to (issue #5: `{{Autobahn|17}}` in a
    heading renders as an icon image, not the literal template text), so it
    silently produces a fragment nothing on the real page ever matches. Falls
    back to the old heuristic only if the API call fails (offline, rate
    limited, etc.), so this degrades rather than breaking outright.
    """
    # NOT base_url.rsplit("/", 1)[0] -- that strips the language segment too
    # (".../fr/" -> ".../api.php", silently querying the English wiki's sections
    # for a French page; caught by testing this derivation against both /en/ and
    # /fr/ before trusting it, not assumed). api.php sits at the same path level
    # as the language prefix, not one level above it.
    api_url = api_url or (base_url.rstrip("/") + "/api.php")
    sections = fetch_real_anchors(title, api_url)
    # Sorted ascending so "last section starting at or before this byte offset"
    # is a simple linear scan; sections are already emitted in document order
    # by the API, but don't rely on that silently.
    if sections:
        sections = sorted(sections, key=lambda s: int(s["byteoffset"]))

    results = []
    for item in extract_coords_and_headings(raw_wiki_page):
        if sections:
            byte_pos = _char_pos_to_byte_offset(raw_wiki_page, item["pos"])
            enclosing = None
            for s in sections:
                if int(s["byteoffset"]) <= byte_pos:
                    enclosing = s
                else:
                    break
            fragment = enclosing["anchor"] if enclosing else None
        elif item["heading"]:
            fragment = heading_to_fragment(item["heading"], item["same_heading_count"])
        else:
            fragment = None

        link = base_url + title + ("#" + urllib.parse.quote(fragment) if fragment else "")
        item["link"] = link
        results.append(item)

    return results