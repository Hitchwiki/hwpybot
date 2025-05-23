from dotenv import load_dotenv
from utils import get_english_city_name
from time import sleep
from tqdm import tqdm
import pywikibot
from pywikibot import pagegenerators

load_dotenv()

lang = "ru"
countries = ["Россия", "Украина", "Беларусь", "Казахстан", "Киргизия", "Узбекистан"]
lang_category = "Категория:Россия"
# collecting cities from Russia and adjacent countries
city_indicators = [
    "{{IsIn|Россия}}",
    "[[Категория:Россия]]",
    "== Выезды",
    "<map",
    "/map/",
    "{{Субъекты Российской Федерации}}",
    "== Выезды",
    "{{Регионы Украины}}",
    "== Въезд",
    "== Проживание",
    "{{Города Украины}}",
    "{{IsIn|Беларусь}}",
    "[[Категория:Беларусь]]",
    "[[Категория:Казахстан]]",
    "{{Города Киргизии}}",
    "[[Категория:Узбекистан]]",
]


lang_wiki = pywikibot.Site(code=lang, fam=f'hitchwiki_{lang}')
if not lang_wiki.user():
    lang_wiki.login()
possible_cities = []
gen = pagegenerators.AllpagesPageGenerator(site=lang_wiki)
for page in gen:
    if any(s in page.text for s in city_indicators) and all(page.title() != c for c in countries):
        possible_cities.append(page.title())
possible_cities
cities = []
# now only russian cities
cs = []
categories_to_skip = [
    "Категория:Незавершённые статьи",
    "Категория:Статьи с непроверенной информацией",
    "Категория:Нужна информация",
    "Категория:Незавершённые статьи",
]
# going two categories up means from federal state level to country level
# country level has to be Russia
for city in tqdm(possible_cities):
    page = pywikibot.Page(lang_wiki, city.title())
    first_level_categories = list(page.categories())
    if len(first_level_categories) == 0:
        continue
    if any([c.title() == lang_category for c in first_level_categories]):
        cities.append(page.title())
        continue
    flc = [
        cat
        for cat in first_level_categories
        if cat.title()
        not in categories_to_skip
    ]
    cs += flc
    for category in flc:
        second_level_categories = list(category.categories())
        cs += second_level_categories
        if any([c.title() == lang_category for c in second_level_categories]):
            cities.append(page.title())
            continue
len(cities), len(possible_cities)
en_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not en_wiki.user():
    en_wiki.login()
filtered_cities = []
avoid_categories = ['Категория:Автодороги России', "Категория:погранпереходы", "Категория:Погранпереходы"]
for city in tqdm(cities):
    page = pywikibot.Page(lang_wiki, city.title())
    first_level_categories = list(page.categories())
    if any([category in [cat.title() for cat in first_level_categories] for category in avoid_categories]):
        continue
    filtered_cities.append(city)
len(cities), len(filtered_cities)
filtered_cities
cities_to_translate = []
for city in tqdm(filtered_cities):
    sleep(0.3)
    pages_to_check = []
    pages_to_check.append(pywikibot.Page(en_wiki, city))
    english_city_name = get_english_city_name(original_name=city, original_lang=lang)
    if english_city_name != city:
        pages_to_check.append(pywikibot.Page(en_wiki, english_city_name))

    if all([page.text == "" for page in pages_to_check]):
        cities_to_translate.append((city, english_city_name))
    elif pages_to_check[0].text != "":
        print(f"Russian article for: {city}")
    elif pages_to_check[0].text == "" and len(pages_to_check[1].text) < 1000:
        print(f"Overwrite small English article for: {english_city_name}")
        cities_to_translate.append((city, english_city_name))
len(cities_to_translate)
cities_to_translate = list(set(cities_to_translate))
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
cities_to_translate
for ru_page_name, eng_page_name in tqdm(cities_to_translate):
    original_page = pywikibot.Page(lang_wiki, ru_page_name)
    translated_page = translate(page=original_page)

    page = pywikibot.Page(en_wiki, eng_page_name)
    page.text = f"{{{{ai-enhanced}}}}\n{translated_page}"
    page.save(f"Create this article by translation with language model (gpt 4.1) from hitchwiki original language: {lang} {ru_page_name}")
    print(page.title())
    print("******")