import pywikibot
from pywikibot import pagegenerators
from tqdm import tqdm

lang_wiki = pywikibot.Site(code='en', fam='hitchwiki')
if not lang_wiki.user():
    lang_wiki.login()

pages = list(pagegenerators.AllpagesPageGenerator(site=lang_wiki))

articles = {}
for page in tqdm(pages, desc="Processing pages"):
    try:
        articles[page.title()] = {"text": page.text}
    except Exception as e:
        print(f"Error processing page: {e}")
        continue


for article, items in tqdm(articles.items()):
    text = items["text"]
    if "[[Category:City's]]" in text or "{{Category|City's}}" in text:
        corrected_text = text.replace("[[Category:City's]]", "[[Category:Cities]]").replace("{{Category|City's}}", "[[Category:Cities]]")

        page = pywikibot.Page(lang_wiki, article)
        page.text = corrected_text
        page.save(f"Correct City's category in {article}")
        print(page.title())
        print("******")

        articles[article]["text"] = corrected_text

# update local copy of articles
with open("articles.py", "w") as f:
    f.write("articles = ")
    f.write(repr(articles))
    f.write("\n")