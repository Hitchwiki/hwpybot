import pywikibot
from pywikibot import pagegenerators
from utils import get_country_coordinates

site = pywikibot.Site("en", "hitchwiki")
if not site.user():
    site.login()

countries = []
gen = pagegenerators.AllpagesPageGenerator(site=site)
for page in gen:
    if "{{infobox Country" in page.text:
        countries.append(page)
countries

# Initialize geocoder

map_pattern = (
    "|map = <map lat='{lat}' lng='{lon}' zoom='5' view='0' country='{country}'/>"
)
lang_tag = "|language"

for c in countries:
    title = str(c).split(":")[1].split("]")[0]
    page = pywikibot.Page(site, title)
    if "{{infobox Country" in page.text and "|map" not in page.text:
        lat, lon = get_country_coordinates(title)
        map_tag = map_pattern.format(lat=lat, lon=lon, country=title)
        start, end = page.text.split(lang_tag)
        new_page = f"{start}{map_tag}\n{lang_tag}{end}"

        page.text = new_page
        page.save("Added map tag programatically")
        print(title)
        print("******")
