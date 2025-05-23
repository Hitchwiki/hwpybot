from dotenv import load_dotenv
from utils import get_english_city_name
from time import sleep
load_dotenv()
lang = 'fr'
country = "France"
import pywikibot
from pywikibot import pagegenerators

lang_wiki = pywikibot.Site(code=lang, fam=f'hitchwiki_{lang}')
if not lang_wiki.user():
    lang_wiki.login()
possible_cities = []
gen = pagegenerators.AllpagesPageGenerator(site=lang_wiki)
for page in gen:
    if any(s in page.text for s in ["{{IsIn|France}}", "[[Catégorie:France]]", "== En partir ==", "<map", "/map/"]) and page.title() != country:
        possible_cities.append(page.title())
cities = []
lang_category = "Catégorie:France"
# going two categories up means from federal state level to country level
# country level has to be Germany
for city in possible_cities:
    page = pywikibot.Page(lang_wiki, city.title())
    first_level_categories = list(page.categories())
    if len(first_level_categories) == 0:
        continue
    if any([c.title() == lang_category for c in first_level_categories]):
        cities.append(page.title())
        continue
    for category in first_level_categories:
        second_level_categories = list(category.categories())
        if any([c.title() == lang_category for c in second_level_categories]):
            cities.append(page.title())
            continue
cities
en_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not en_wiki.user():
    en_wiki.login()
cities_to_translate = []
for city in cities:
    sleep(1)
    print(city)
    pages_to_check = []
    pages_to_check.append(pywikibot.Page(en_wiki, city))
    english_city_name = get_english_city_name(city)
    if english_city_name != city:
        pages_to_check.append(pywikibot.Page(en_wiki, english_city_name))

    if all([page.text == "" for page in pages_to_check]):
        cities_to_translate.append(city)
cities_to_translate
from openai import OpenAI
from prompts import SYSTEM_PROMPT, city_template, info_box
from tqdm import tqdm
client = OpenAI()

def translate(page):
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT.format(info_box=info_box, template=city_template)
            },
            {
                "role": "user",
                "content": page.text
            }
        ]
    )

    return response.output_text
for page_name in tqdm(cities_to_translate):
    original_page = pywikibot.Page(lang_wiki, page_name)
    translated_page = translate(page=original_page)

    page = pywikibot.Page(en_wiki, page_name)
    page.text = f"{{{{ai-enhanced}}}}\n{translated_page}"
    page.save(f"Create this article by translation with language model (gpt 4.1) from hitchwiki original language: {lang} {page_name}")
    print(page.title())
    print("******")