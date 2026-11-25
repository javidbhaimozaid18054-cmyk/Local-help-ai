# Putting LocalHelp AI online (PythonAnywhere, free)

You get a link like `https://YOURNAME.pythonanywhere.com`. Use it for the live demo and share it with testers.
Replace YOURNAME with your PythonAnywhere username everywhere below.

## Steps

1. Create a free "Beginner" account at pythonanywhere.com and log in.
2. **Upload the project.** Easiest way: push the project to GitHub first (`git remote add origin ...`, `git push`),
   then open **Consoles -> Bash** on PythonAnywhere and run:
   `git clone https://github.com/YOURGITHUB/localhelp-ai.git`
   (Other way: **Files** tab -> upload a zip -> in a Bash console run `unzip yourfile.zip`.)
3. In the Bash console:
   ```
   cd localhelp-ai
   python3 -m venv venv
   source venv/bin/activate
   pip install flask
   ```
   Only Flask is needed on the server. pandas, SciPy and Matplotlib are used on your own computer for analysis.
4. Open the **Web** tab -> **Add a new web app** -> **Manual configuration** -> choose the newest Python version.
5. On the Web tab set:
   - **Source code:** `/home/YOURNAME/localhelp-ai`
   - **Virtualenv:** `/home/YOURNAME/localhelp-ai/venv`
6. Click the **WSGI configuration file** link, delete everything inside, and paste:
   ```python
   import os, sys
   path = '/home/YOURNAME/localhelp-ai'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ['EXPORT_TOKEN'] = 'write-a-long-secret-word-here'
   from app import app as application
   ```
   Save, then press the green **Reload** button on the Web tab.
7. Open `https://YOURNAME.pythonanywhere.com`. The database file is created on the first visit.

## Admin and data download (hosted)

The admin page and CSV exports only work from your own computer, or with the secret word from step 6:

- Approve providers: `https://YOURNAME.pythonanywhere.com/admin?token=YOUR-SECRET-WORD`
- Download data: `https://YOURNAME.pythonanywhere.com/export/tasks.csv?token=YOUR-SECRET-WORD`
  (also `sus.csv`, `events.csv`, `requests.csv`, `provider_signups.csv`)

Never share the secret word. You can also download `localhelp.db` from the Files tab and run
`python analysis/analyze.py --db localhelp.db` on your computer.

## After you change code

Upload the changed files (or `git pull` in the console) and press **Reload** on the Web tab.

## Good to know

- The test panel (`/test`) and questionnaire pages are public on the hosted site. Only share the link with your testers.
- Keep a local copy running as a backup for the viva in case the internet is slow.
- If the page shows an error, open the Web tab -> **Error log** and read the last lines.
