import re
import pywikibot
from pywikibot import pagegenerators
from tqdm import tqdm

lang_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not lang_wiki.user():
    lang_wiki.login()

pages = list(pagegenerators.AllpagesPageGenerator(site=lang_wiki))[500:]

hitching_out_pattern = re.compile(r'(=+)\s*Hitching\s+out\s*\1', re.IGNORECASE)
hitching_in_pattern = re.compile(r'(=+)\s*Hitching\s+in\s*\1', re.IGNORECASE)

for page in tqdm(pages, desc="Processing pages"):
    try:
        text = page.text
    except Exception as e:
        print(f"Error processing page: {e}")
        continue

    new_text = hitching_out_pattern.sub(lambda m: f'{m.group(1)} Hitchhiking out {m.group(1)}', text)
    new_text = hitching_in_pattern.sub(lambda m: f'{m.group(1)} Hitchhiking in {m.group(1)}', new_text)

    if new_text == text:
        continue

    try:
        page.text = new_text
        page.save("Rename 'Hitching out/in' section titles to 'Hitchhiking out/in'")
        print(f"Updated: {page.title()}")
    except Exception as e:
        print(f"Failed to save page: {e}")
