from dotenv import load_dotenv
from utils import get_english_city_name
from time import sleep
from tqdm import tqdm
import pywikibot
from pywikibot import pagegenerators
from openai import OpenAI
from pydantic import BaseModel
from prompts import SYSTEM_PROMPT, city_template, info_box

load_dotenv()

CLIENT = OpenAI()

LANG = 'tr'
COUNTRY = "Türkiye"
LANG_CATEGORY = "Kategori:Türkiye"
CITY_INDICATORS = ["{{IsIn|Türkiye}}", "[[Kategori:Türkiye]]", "==Şehirden", "==Otostop", "<map", "/map/"]


def translate(page):
    response = CLIENT.responses.create(
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


class ResponseModel(BaseModel):
    is_in_turkey: bool

def is_in_turkey(city):
    response = CLIENT.responses.parse(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": f"Is {city} a city or region in Turkey?"
                }
            ],
            text_format=ResponseModel
        )

    return response.output[0].content[0].parsed.is_in_turkey


def main():
    lang_wiki = pywikibot.Site(code=LANG, fam=f'hitchwiki_{LANG}')

    if not lang_wiki.user():
        lang_wiki.login()

    possible_cities = []
    gen = pagegenerators.AllpagesPageGenerator(site=lang_wiki)

    for page in gen:
        if any(s in page.text for s in CITY_INDICATORS) and page.title() != COUNTRY:
            possible_cities.append(page.title())

    cities = [city for city in tqdm(possible_cities) if is_in_turkey(city)]

    en_wiki = pywikibot.Site(code='en', fam='hitchwiki')

    if not en_wiki.user():
        en_wiki.login()

    cities_to_translate = []

    for city in tqdm(cities):
        sleep(0.5)
        pages_to_check = []
        pages_to_check.append(pywikibot.Page(en_wiki, city))
        english_city_name = get_english_city_name(original_name=city, original_lang=LANG)
        if english_city_name != city:
            pages_to_check.append(pywikibot.Page(en_wiki, english_city_name))

        if all([page.text == "" for page in pages_to_check]):
            cities_to_translate.append(city)

    for page_name in tqdm(cities_to_translate):
        original_page = pywikibot.Page(lang_wiki, page_name)
        translated_page = translate(page=original_page)

        page = pywikibot.Page(en_wiki, page_name)
        page.text = f"{{{{ai-enhanced}}}}\n{translated_page}"
        page.save(f"Create this article by translation with language model (gpt 4.1) from hitchwiki original language: {LANG} {page_name}")
        print(page.title())
        print("******")

if __name__ == "__main__":
    main()