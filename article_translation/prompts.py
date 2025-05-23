german_info_box = """{{infobox German Location
|country = Germany
|map = <map lat='lat' lng='lng' zoom='9' view='0' />
|pop = population
|state = state
|plate = license plate
|motorways = [[Ax (Germany)|Ax]],  [[Ay (Germany)|Ay]]
}}"""

info_box = """{{infobox Location
|country = country
|map = <map lat='lat' lng='lng' zoom='9' view='0' />
|pop = population
|state = state
|motorways = [[Ex]], [[Ay]]
}}"""


city_template = """'''{{FULLPAGENAMEE}}''' ((Turkish/German/French/Russian/...): Original city name) is a city in [[Country]]. 

== Hitchhiking out ==
=== "cardinal direction" towards [[Other City]] ===
==== Option 1 - Option Name (e.g. name of street, neighborhood) ====
==== Option 2 - Option Name ====

=== "cardinal direction" towards [[Yet Another City]] ===
==== Option 1 - Option Name ====


== Hitchhiking in ==
<includeonly><!---</includeonly>
'''Only''' include this section if it is difficult to enter a city, like from the ring around Berlin or the M25 around London!
<includeonly>--></includeonly>

== Places to avoid ==

== Accommodation and Sleep ==
<includeonly><!---</includeonly>
Wild camping places are good.   Please '''do not''' add regular hostels.  
<includeonly>--></includeonly>

== Other useful info ==

[[Category:Country]]
[[Category:State]]
{{IsIn|State}}
"""


SYSTEM_PROMPT = """You are a helpful mediawiki translation assistant. The mediawiki pages stem from a mediawiki about hitchhiking.
You will be given a mediawiki page in any common European language and you need to translate it into English.
Alonglside translation you have to adhere the the given FORMAT. This is very important.
Under no circumstances add information that is not present in the original text. Especially when it comes to hitchhiking places or hard facts about the city.
You are allowed to not use information from the original text that does not make sense in the context of the page or is irrelevant for hitchhiking.
You do not need to fill every section of field of the format template. Leave it empty if you do not have the information.

FORMAT:
{info_box}
{template}

Explanations:
A state is the largest administrative division in a country. E.g. Bundesland in Germany, Province in Canada, State in the USA or Regions in France.
For mentions of larger cities or countries where one can expect there is already an article for them write them as [[entity]] which will create a link to them.
For the categries and infobox field use the English names of entities.
Use all headings from the given format, this is important to easily extend the template in the future. It is okay to leave some of them empty.

Output:
Only the translated formatted text. Do not add any other text or explanation.
"""