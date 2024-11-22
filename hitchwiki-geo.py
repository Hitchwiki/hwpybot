# /// script
# dependencies = [
#   "pywikibot",
#   "pynostr",
#   "openlocationcode",
#   "geohash2",
# ]
# ///

import sys
import os
import time
        
from pprint import pprint

from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from pynostr.event import Event, EventKind

from openlocationcode import openlocationcode
import geohash2

import pywikibot

from pywikibot import pagegenerators, family

import settings


def main():
    site = pywikibot.Site('en', 'hitchwiki')
    # print(site.title())
    
    cat = pywikibot.Category(site, 'Category:Belgium')
    gen = pagegenerators.CategorizedPageGenerator(cat)

    nostr_post = NostrPost()

    for page in gen:
        # Do something with the page object, for example:
        print(page)
        txt = page.text
        if "<map" in txt:
            print("The text contains a map.")
            import re
            map_lines = [line for line in txt.split('\n') if "<map" in line]
            for line in map_lines:
                print(f"Line containing <map: {line}")
                map_params = re.search(r"<map\s+lat=['\"](?P<lat>[^'\"]*)['\"]\s+lng=['\"](?P<lng>[^'\"]*)['\"]\s+zoom=['\"](?P<zoom>[^'\"]*)['\"]\s+view=['\"](?P<view>[^'\"]*)['\"](\s+\w+=[\"'][^\"']*[\"'])*\s*/?>", line)
                if map_params:
                    lat = map_params.group('lat')
                    lng = map_params.group('lng')
                    zoom = map_params.group('zoom')
                    view = map_params.group('view')
                    print(f"Map parameters: lat={lat}, lng={lng}, zoom={zoom}, view={view}")

                    nostr_post.post(page, lat, lng, zoom, view)

        elif "{{IsIn" in txt:
            print("The text contains {{IsIn}}")
        else:
            print("no geo info in this article")
        time.sleep(2)


class NostrPost:
    def __init__(self):
        private_key_obj = PrivateKey.from_nsec(settings.nsec)
        self.private_key_hex = private_key_obj.hex()
        npub = private_key_obj.public_key.bech32()
        print(f"Posting as npub {npub}")

        self.relay_manager = RelayManager(timeout=5)
        for relay in settings.relays:
            self.relay_manager.add_relay(relay)

    def post(self, page, lat, lng, zoom, view):
        print(page)

        lat = float(lat)
        lng = float(lng)

        text = page.text
        title = page.title()
        

        event_content = f"hitchwiki {title}"
        event_kind = 30399
        d_tag = ''.join(c for c in title.lower() if c.isalnum() or c.isspace()).replace(' ', '_')
        page_url = page.full_url()
        page_path = '/' + '/'.join(page_url.split('/')[3:])

        pluscode = openlocationcode.encode(lat, lng)
        geohash = geohash2.encode(lat, lng)

        # see also https://github.com/Trustroots/nostroots/blob/main/docs/Events.md
        event = Event(kind=event_kind, content=event_content, tags=
                      [
                       ['d', d_tag],
                       ['L', "open-location-code"],
                       ['l', pluscode, "open-location-code"],
                       ['L', "open-location-code-prefix"],
                       ['l', pluscode[:6]+"00+", "open-location-code-prefix"],
                       ['L', "open-location-code-prefix"],
                       ['l', pluscode[:4]+"0000+", "open-location-code-prefix"],
                       ['L', "open-location-code-prefix"],
                       ['l', pluscode[:2]+"000000+", "open-location-code-prefix"],
                       ['L', "trustroots-circle"],
                       ['l', "hitchhikers", "trustroots-circle"],
                       ['g', geohash],
                       ['t', 'hitchwiki'],
                       ['linkPath', page_path]  ## linkPath isn't defined in any NIP
                      ]);
        
        event.sign(self.private_key_hex)
        
        print('vars(event)')
        pprint(vars(event))

        if settings.post_to_relays:
            print("posting to relays")
            self.relay_manager.publish_event(event)
            self.relay_manager.run_sync()  # Sync with the relay to send the event
            print("posted nostr note, waiting a bit")
            time.sleep(3)

    def close():
        self.relay_manager.close_all_relay_connections()


if __name__ == "__main__":
    main()
