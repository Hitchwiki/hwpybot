from dotenv import load_dotenv

import pywikibot
from pywikibot import pagegenerators
from openai import OpenAI
from prompts import SYSTEM_PROMPT, city_template, german_info_box
from tqdm import tqdm

load_dotenv()

de_wiki = pywikibot.Site(code='de', fam='hitchwiki_de')
if not de_wiki.user():
    de_wiki.login()
german_cities = []
gen = pagegenerators.AllpagesPageGenerator(site=de_wiki)
for page in gen:
    if "{{Infobox Stadt" in page.text:
        german_cities.append(page)
only_german_cities = []
# going two categories up means from federal state level to country level
# country level has to be Germany
for city in german_cities:
    page = pywikibot.Page(de_wiki, city.title())
    first_level = next(page.categories(), None)
    if first_level is not None and first_level.title() == "Kategorie:Deutschland":
        only_german_cities.append(page.title())
    category_page = next(first_level.categories(), None)
    if category_page is not None and category_page.title() == "Kategorie:Deutschland":
        only_german_cities.append(page.title())
only_german_cities
en_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not en_wiki.user():
    en_wiki.login()
cities_to_translate = []
for city in only_german_cities:
    page = pywikibot.Page(en_wiki, city)
    if page.text == "":
        cities_to_translate.append(page.title())

client = OpenAI()

def translate(page):
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT.format(info_box=german_info_box, template=city_template)
            },
            {
                "role": "user",
                "content": page.text
            }
        ]
    )

    return response.output_text


for page_name in tqdm(cities_to_translate):
    original_page = pywikibot.Page(de_wiki, page_name)
    translated_page = translate(page=original_page)

    page = pywikibot.Page(en_wiki, page_name)
    page.text = f"{{{{ai-enhanced}}}}\n{translated_page}"
    page.save("Create this article by translation with language model (gpt 4.1) from original language.")
    print(page.title())
    print("******")