# LocalHelp AI

Web prototype for the integrated assignment "Design for Impact" (Design Thinking, Web Technology,
Python, Probability and Statistics). Users describe a local problem (plumber, electrician, mechanic
and so on), get a rule-based analysis and cost range, compare nearby providers and request a service.
The app records usage data (time, clicks, errors) so Stage 5 testing uses real measurements.

**All providers, prices and reviews are fictional sample data.** The "AI analysis" is a keyword matcher
written in Python (`ai_rules.py`), not a trained model. Say this clearly in your report and viva.

## 1. Run it (5 minutes)

```bash
python -m venv venv
venv\Scripts\activate          # Windows      (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The database file `localhelp.db` is created automatically.

## 2. Folder map

| File | Subject | What it does |
|---|---|---|
| `templates/*.html` | Web Technology | Pages: prototype, survey, test panel, SUS form, provider signup, admin |
| `static/css/style.css` | Web Technology | Responsive layout, light and dark mode |
| `static/js/app.js` | Web Technology | 8-step prototype flow, validation, calls the API |
| `static/js/tracker.js` | Web Tech + Stats | Records time, clicks, errors, backtracks |
| `static/js/survey.js, sus.js, test.js` | Web Technology | Survey, SUS and observer pages |
| `app.py` | Python | Flask server, routes, input validation, provider approval, CSV export |
| `db.py` | Python | SQLite tables and sample providers |
| `ai_rules.py` | Python | Keyword-based problem analysis and cost range |
| `survey_config.py` | Stats | The questionnaire (edit this to change questions) |
| `analysis/analyze.py` | Stats + Python | All statistics, charts and the text report |

## 3. How each stage uses the project

**Stage 1 Empathise.** Edit `survey_config.py` for your user group. Share `/survey` with 30 or more
people (see section 5 for hosting). Do 5 interviews separately and write notes yourself.
Write your sampling plan BEFORE collecting data.

**Stage 2 Define.** Run `python analysis/analyze.py`. It gives descriptive statistics, charts,
Pearson and Spearman correlations, confidence intervals, a baseline hypothesis test and a ranked
list of pain points. Use these numbers in your persona, POV, HMW and MoSCoW table.

**Stage 3 Ideate.** Write your null and alternative hypotheses on paper BEFORE testing. Example:
H0 the prototype takes the same time as the current method, H1 it takes less time.

**Stage 4 Prototype.** This project is the prototype. Make wireframes first (paper or Figma), then
adjust the HTML, CSS and JS to match your final concept.

**Stage 5 Test.** Open `/test` on your laptop.
1. Enter a participant code such as P01 (never a name).
2. Current method trial: read the task aloud, press Start on the stopwatch, Stop when the participant
   has found a provider and agreed a time, then Save. The method can be Google, WhatsApp or calls.
3. Prototype trial: click "Open prototype for this participant". The participant presses Start task
   and completes the booking. Time, clicks, errors and success are saved automatically.
4. The participant fills the SUS questionnaire (the link appears after the task).
5. Alternate the order (current first, prototype first) for every other participant to reduce
   learning effects. Test at least 10 people, more is better.
6. Run `python analysis/analyze.py` again. It runs a paired t-test (or Wilcoxon if the differences
   are not normal), reports effect size and confidence intervals, compares success rates and
   computes the SUS score.

You need at least 3 improvement opportunities from testing. Change the prototype, then test again.

## 4. What is measured

| Measure | Where it comes from |
|---|---|
| Time per task | stopwatch (current method), automatic timer (prototype) |
| Clicks | automatic, prototype only |
| Errors | validation messages and server errors seen (prototype), observer count (current) |
| Backtracks | number of Back presses (prototype) |
| Success | booking confirmed vs Give up (prototype), observer (current) |
| Satisfaction | SUS score and survey Likert items |

Clicks on buttons are logged by label. Text typed by users is never stored in the usage log.

## 5. Putting the survey online (important)

People can only open `http://127.0.0.1:5000` on your own computer. Pick one:

- **Easiest: Google Forms.** Use the same questions, then export responses as CSV, rename the column
  headings to the question ids in `survey_config.py` (for example `minutes_to_find`), and run
  `python analysis/analyze.py --survey-csv responses.csv`.
- **Host the app free on PythonAnywhere** (supports Flask and SQLite): upload the folder, create a
  virtualenv with `pip install -r requirements.txt`, create a Flask web app pointing to `app.py`.
  Set the environment variable `EXPORT_TOKEN` and download CSVs from
  `/export/survey_responses.csv?token=YOUR_TOKEN`, or download `localhelp.db` and run the analysis
  on your computer. For hosted use, run it without `debug=True`.

## 6. Export data for submission

While the app runs on your computer, open these links (they work only on localhost):

`/export/survey_responses.csv`, `/export/tasks.csv`, `/export/sus.csv`, `/export/events.csv`

The data contains no names or phone numbers. Check the open-text answers for personal details
before submitting.

## 7. Ethics checklist (from the brief)

- Informed consent: the survey has a consent box. Read a consent line to test participants too.
- Anonymous codes only (P01, P02). Do not write down names next to codes.
- Do not fabricate, copy or alter data. Report negative results honestly.
- Credit libraries: Flask, pandas, SciPy, Matplotlib. The SUS statements come from Brooke (1996),
  "SUS: a quick and dirty usability scale".
- **Disclose AI tool use:** this code and the first versions of the project documents were
  written with help from Claude (Anthropic). Mention this in your report and slides.
- Commit regularly to a Git repository. Understand every file so you can explain it in the viva.

## 8. Provider signup and approval (supply side)

Interviews showed that skilled local providers also need a way to get work directly.

1. A provider opens `/provider` (link "For Professionals" in the top bar) and fills the form.
   No phone number or address is collected.
2. You open `http://127.0.0.1:5000/admin` (works only on your computer, or with `?token=` when hosted).
3. Press **Approve**. The provider is added to the list customers see, marked "New provider".
   Press **Reject** to hide it. Check the details yourself before approving.

Signups are stored in the `provider_signups` table and can be exported at `/export/provider_signups.csv`.

## 9. Ideas to improve (only if time allows)

1. Replace the sample providers with a few real local providers (with their permission).
2. Replace `ai_rules.py` with a call to a real AI model, keeping the same `analyze()` function.
3. Add a simple admin page that lists requests.
