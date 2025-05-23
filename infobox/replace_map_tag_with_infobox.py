import pywikibot
from pywikibot import pagegenerators
from tqdm import tqdm
import re

site = pywikibot.Site('en', 'hitchwiki')
if not site.user():
    site.login()


map_pages = []
gen = pagegenerators.AllpagesPageGenerator(site=site)

for page in gen:
    if "<map lat" in page.text and "{{infobox" not in page.text and "{{Infobox" not in page.text:
        map_pages.append(page)

map_info_pattern = """{{{{infobox Location
|country = {country}
|state = {state}
|map = {map}
|pop = {population}
|plate = {plate}
|motorways = {motorways}
}}}}"""



for page_name in tqdm(map_pages):
    title = str(page_name).split(":")[1].split("]")[0]
    page = pywikibot.Page(site, title)
    if "{{infobox" not in page.text and "{{Infobox" not in page.text:
        match = re.search(r'<map[^>]*>', page.text)

        if match:
            result = match.group()
            print("Found:", result)
        else:
            print("No match found.")

        page.text = page.text.replace(result, "")
        info_box = map_info_pattern.format(
                country="-",
                state="-",
                map=result,
                population="-",
                plate="-",
                motorways="-",
            )
        page.text = f"{info_box}\n{page.text}"
        page.save("Added infobox to articles where map tag is already present programatically")
        print(title)
        print("******")