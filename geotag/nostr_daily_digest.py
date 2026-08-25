# /// script
# dependencies = [
#   "pynostr",
#   "requests",
# ]
# ///
"""Post one kind:1 (plain-text) nostr note per Hitchwiki language per day.

Closes the gap flagged in https://github.com/Hitchwiki/hwpybot/issues/2:
`hitchwiki-geo.py`'s `NostrPost` already publishes kind 30399 (a
parameterized-replaceable, app-specific event) per geo-tagged article, but
that kind never shows up in an ordinary nostr social client (Damus,
Amethyst, etc.) the way a plain kind:1 note does. This script is the "connect
with the nostr social media side of things" half the issue actually asks for
-- a human-readable daily digest, one post per language.

For each language: summarize the last 24h of non-bot edits via MediaWiki's
own `list=recentchanges` API. If a language had no human edits in that
window, post one random existing article instead, so every language still
gets a daily post (per the issue's own "random articles for languages
without recent changes" checkbox).

Not wired into a cron entry here -- this repo doesn't schedule
`hitchwiki-geo.py` either, so scheduling is a separate decision from the
code, same call the original scoping comment made.
"""

import time
from datetime import datetime, timedelta, timezone

import requests
from pynostr.event import Event
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager

import settings

LANGUAGES = ["en", "de", "fr", "ru", "es", "it", "pl"]
MAX_TITLES_PER_NOTE = 8


def fetch_recent_human_edits(lang: str, since: datetime) -> list[str]:
    """Distinct page titles edited by a non-bot user since `since`, newest first."""
    url = f"https://hitchwiki.org/{lang}/api.php"
    params = {
        "action": "query",
        "list": "recentchanges",
        "rcprop": "title|timestamp",
        "rcnamespace": "0",
        "rctype": "edit|new",
        "rcshow": "!bot",
        "rclimit": "50",
        "format": "json",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    changes = resp.json().get("query", {}).get("recentchanges", [])

    titles = []
    seen = set()
    for change in changes:
        ts = datetime.strptime(change["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        if ts < since:
            break  # recentchanges is newest-first, so nothing later matters
        title = change["title"]
        if title not in seen:
            seen.add(title)
            titles.append(title)
    return titles


def fetch_random_article(lang: str) -> str | None:
    url = f"https://hitchwiki.org/{lang}/api.php"
    params = {
        "action": "query",
        "list": "random",
        "rnnamespace": "0",
        "rnlimit": "1",
        "format": "json",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("query", {}).get("random", [])
    return results[0]["title"] if results else None


def wiki_url(lang: str, title: str) -> str:
    return f"https://hitchwiki.org/{lang}/{title.replace(' ', '_')}"


def format_digest(lang: str, titles: list[str], is_random_fallback: bool) -> str:
    shown = titles[:MAX_TITLES_PER_NOTE]
    links = "\n".join(f"- {wiki_url(lang, t)}" for t in shown)
    if is_random_fallback:
        header = f"Quiet day on hitchwiki.org/{lang} -- here's an article worth a look:"
    else:
        extra = len(titles) - len(shown)
        more = f" (+{extra} more)" if extra > 0 else ""
        header = f"Updated today on hitchwiki.org/{lang}{more}:"
    return f"{header}\n{links}\n\n#hitchhiking #hitchwiki"


class TextNotePost:
    def __init__(self):
        private_key_obj = PrivateKey.from_nsec(settings.nsec)
        self.private_key_hex = private_key_obj.hex()
        npub = private_key_obj.public_key.bech32()
        print(f"Posting as npub {npub}")

        self.relay_manager = RelayManager(timeout=5)
        for relay in settings.relays:
            self.relay_manager.add_relay(relay)

    def post(self, content: str):
        event = Event(kind=1, content=content, tags=[["t", "hitchhiking"]])
        event.sign(self.private_key_hex)
        print("--- kind 1 note ---")
        print(content)
        if getattr(settings, "post_to_relays", False):
            self.relay_manager.publish_event(event)
            self.relay_manager.run_sync()

    def close(self):
        self.relay_manager.close_all_relay_connections()


def main():
    since = datetime.now(timezone.utc) - timedelta(days=1)
    poster = TextNotePost()

    for lang in LANGUAGES:
        titles = fetch_recent_human_edits(lang, since)
        is_random_fallback = not titles
        if is_random_fallback:
            random_title = fetch_random_article(lang)
            if random_title is None:
                print(f"{lang}: no random article available, skipping")
                continue
            titles = [random_title]

        content = format_digest(lang, titles, is_random_fallback)
        poster.post(content)
        time.sleep(2)

    poster.close()


if __name__ == "__main__":
    main()
