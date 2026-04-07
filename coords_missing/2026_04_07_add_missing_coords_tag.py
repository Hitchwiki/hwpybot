import re
import pywikibot
from pywikibot import pagegenerators
from tqdm import tqdm

lang_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not lang_wiki.user():
    lang_wiki.login()

pages = list(pagegenerators.AllpagesPageGenerator(site=lang_wiki))[5200:]

infobox_pattern = re.compile(r'\{\{Infobox\s+\w+\s+Location', re.IGNORECASE)

for page in tqdm(pages, desc="Processing pages"):
    try:
        text = page.text
    except Exception as e:
        print(f"Error processing page: {e}")
        continue

    if not infobox_pattern.search(text):
        continue
    if '{{Coords|' in text or '{{Coords-missing}}' in text:
        continue

    try:
        page.text = '{{Coords-missing}}<br>\n' + text
        page.save("Add {{Coords-missing}} tag to article missing coordinates")
        print(f"Updated: {page.title()}")
    except Exception as e:
        print(f"Failed to save page: {e}")
