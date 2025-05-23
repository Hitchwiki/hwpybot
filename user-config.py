family_files['hitchwiki'] = 'https://hitchwiki.org/en/api.php'
usernames['hitchwiki']['en'] = 'xxx'

langs = ['de', 'fr', 'tr', 'ru']
for lang in langs:
    family_files[f'hitchwiki_{lang}'] = f'https://hitchwiki.org/{lang}/api.php'
    usernames[f'hitchwiki_{lang}'][lang] = 'xxx'

password_file = 'user-password.py'

