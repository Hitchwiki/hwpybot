family_files['hitchwiki'] = 'https://hitchwiki.org/en/api.php'
usernames['hitchwiki']['en'] = 'KnyttesBot'

langs = ['de', 'fr', 'es']
for lang in langs:
    family_files[f'hitchwiki_{lang}'] = f'https://hitchwiki.org/{lang}/api.php'
    usernames['hitchwiki_fr'][lang] = 'KnyttesBot'

password_file = 'user-password.py'

