

This is [pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot) code for [hitchwiki](https://hitchwiki.org/).

Initially it will do custom stuff around geo and nostr, see https://github.com/Hitchwiki/hitchwiki/issues/215

It could do a lot more, many people have been running bots on wikipedia to automate a lot of the tedious maintenance stuff.


We're using Astral uv for handling packages etc.
See https://docs.astral.sh/uv/getting-started/installation/



Run the script:

    uv run hitchwiki-geo.py


The nostr notes created by this script are visible on the hitchwiki map layer of the nostroots app, you can find APKs to try at https://github.com/trustroots/nostroots/issues/80
