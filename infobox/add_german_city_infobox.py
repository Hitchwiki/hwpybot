import pywikibot
from pywikibot import pagegenerators
from utils import get_country_coordinates


site = pywikibot.Site('en', 'hitchwiki')
if not site.user():
    site.login()

pages = []
cat = pywikibot.Category(site, 'Category:Germany')
gen = pagegenerators.CategorizedPageGenerator(cat)
for page in gen:
    if "{{IsIn" in page.text:
        pages.append(page)
pages   
german_info_pattern = """{{{{infobox German Location
|country = Germany
|map = <map lat='{lat}' lng='{lon}' zoom='11'/>
|pop = {population}
|plate = {plate}
|motorways = {motorways}
}}}}"""

for page_name in pages:
    title = str(page_name).split(":")[1].split("]")[0]
    page = pywikibot.Page(site, title)
    if (
        "{{Infobox" not in page.text
        and "{{infobox" not in page.text
        and "[[Category:Motorways]]" not in page.text
        and "{{IsIn" in page.text
    ):
        coos = get_country_coordinates(title)
        if coos is None:
            continue
        lat, lon = coos
        info_box = german_info_pattern.format(
            lat=lat, lon=lon, population="-", plate="-", motorways="-"
        )
        page.text = f"{info_box}\n{page.text}"

        page.save("Added infobox with location programatically")
        print(title)
        print("******")