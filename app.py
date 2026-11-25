"""LocalHelp AI - Flask backend.

Run:   python app.py        (then open http://127.0.0.1:5000)

Pages
  /          prototype (frontend in templates/index.html + static/)
  /survey    questionnaire for Stage 1 (answers saved in SQLite)
  /test      observer panel for usability tests (stopwatch for the current method)
  /sus       System Usability Scale form for testers

JSON API (used by the JavaScript files in static/js)
  GET  /api/providers          POST /api/analyze        POST /api/requests
  POST /api/requests/<id>/rating
  POST /api/events             POST /api/tasks          POST /api/sus
  GET  /api/survey/questions   POST /api/survey         GET  /api/summary
  GET  /export/<table>.csv     (localhost only, or with EXPORT_TOKEN)
"""
import csv
import io
import json
import os
import re
import sqlite3

from flask import Flask, Response, abort, jsonify, render_template, request

import db
from ai_rules import analyze
from survey_config import CONSENT_TEXT, LIKERT_LABELS, QUESTIONS

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB: photos are never uploaded
app.teardown_appcontext(db.close_db)
db.init_db()

CATEGORIES = ["plumbing", "electrical", "vehicle", "electronics", "cleaning", "carpentry", "home", "other"]
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
EXPORT_TABLES = ["providers", "requests", "events", "tasks", "sus", "survey_responses", "provider_signups"]


# ---------- helpers ----------
def err(message, status=400):
    return jsonify({"error": message}), status


def clean_code(value):
    """Participant codes are anonymous labels like P01. Returns None if missing or invalid."""
    value = (value or "").strip()
    return value if CODE_RE.match(value) else None


def as_int(value, lo=None, hi=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if lo is not None and n < lo:
        return None
    if hi is not None and n > hi:
        return None
    return n


def as_float(value, lo=None, hi=None):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if lo is not None and n < lo:
        return None
    if hi is not None and n > hi:
        return None
    return n


def text(value, limit):
    return str(value or "").strip()[:limit]


# ---------- pages ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/survey")
def survey_page():
    return render_template("survey.html")


@app.route("/test")
def test_page():
    return render_template("test.html")


@app.route("/sus")
def sus_page():
    return render_template("sus.html")


@app.route("/provider")
def provider_page():
    return render_template("provider.html")


@app.route("/admin")
def admin_page():
    if not admin_allowed():
        abort(403)
    return render_template("admin.html")


# ---------- prototype API ----------
@app.get("/api/providers")
def api_providers():
    category = request.args.get("category", "home")
    if category not in CATEGORIES:
        return err("Unknown category")
    sort = request.args.get("sort", "distance")
    order = {"distance": "COALESCE(distance_km, 99) ASC", "rating": "COALESCE(rating, 0) DESC",
             "price": "price_min ASC"}.get(sort)
    if order is None:
        return err("Unknown sort option")
    rows = db.get_db().execute(
        f"SELECT * FROM providers WHERE category = ? ORDER BY {order}", (category,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True) or {}
    problem = text(data.get("text"), 500)
    category = data.get("category")
    if category is not None and category not in CATEGORIES:
        return err("Unknown category")
    if not problem and not category:
        return err("Please choose a category or describe the problem.")
    return jsonify(analyze(problem, category))


@app.post("/api/requests")
def api_create_request():
    data = request.get_json(silent=True) or {}
    provider_id = as_int(data.get("provider_id"), 1)
    if provider_id is None:
        return err("Please choose a provider first.")
    row = db.get_db().execute("SELECT id FROM providers WHERE id = ?", (provider_id,)).fetchone()
    if row is None:
        return err("That provider does not exist.", 404)
    category = data.get("category")
    if category not in CATEGORIES:
        return err("Unknown category")
    notes = text(data.get("notes"), 200)
    cur = db.get_db().execute(
        """INSERT INTO requests (participant_code, session_id, category, problem_text, has_photo,
               issue, urgency, est_min, est_max, provider_id, date_pref, time_pref, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (clean_code(data.get("participant_code")), text(data.get("session_id"), 40), category,
         text(data.get("problem_text"), 500), 1 if data.get("has_photo") else 0,
         text(data.get("issue"), 120), text(data.get("urgency"), 20),
         as_int(data.get("est_min"), 0), as_int(data.get("est_max"), 0), provider_id,
         text(data.get("date_pref"), 30), text(data.get("time_pref"), 40), notes),
    )
    db.get_db().commit()
    return jsonify({"id": cur.lastrowid}), 201


@app.post("/api/requests/<int:req_id>/rating")
def api_rate_request(req_id):
    data = request.get_json(silent=True) or {}
    rating = as_int(data.get("rating"), 1, 5)
    if rating is None:
        return err("Rating must be a number from 1 to 5.")
    cur = db.get_db().execute(
        "UPDATE requests SET rating = ?, review = ? WHERE id = ?",
        (rating, text(data.get("review"), 300), req_id),
    )
    db.get_db().commit()
    if cur.rowcount == 0:
        return err("Request not found.", 404)
    return jsonify({"ok": True})


# ---------- usage data ----------
@app.post("/api/events")
def api_events():
    data = request.get_json(silent=True) or {}
    events = data.get("events")
    if not isinstance(events, list):
        return err("events must be a list")
    rows = []
    for e in events[:100]:
        if not isinstance(e, dict):
            continue
        rows.append((text(e.get("session_id"), 40), clean_code(e.get("participant_code")),
                     text(e.get("event_type"), 30), as_int(e.get("step")),
                     text(e.get("detail"), 80), as_float(e.get("client_ts"))))
    db.get_db().executemany(
        "INSERT INTO events (session_id, participant_code, event_type, step, detail, client_ts) VALUES (?,?,?,?,?,?)",
        rows)
    db.get_db().commit()
    return jsonify({"saved": len(rows)})


@app.post("/api/tasks")
def api_tasks():
    data = request.get_json(silent=True) or {}
    code = clean_code(data.get("participant_code"))
    if code is None:
        return err("Enter a participant code such as P01 (letters, numbers, - or _ only).")
    method = data.get("method")
    if method not in ("current", "prototype"):
        return err("method must be 'current' or 'prototype'")
    seconds = as_float(data.get("seconds"), 0, 3600)
    if seconds is None:
        return err("Time must be between 0 and 3600 seconds.")
    success = 1 if data.get("success") in (1, True, "1", "true", "yes") else 0
    db.get_db().execute(
        """INSERT INTO tasks (participant_code, method, task_name, trial_order, seconds, clicks,
                              errors, backtracks, success, source)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (code, method, text(data.get("task_name"), 120), as_int(data.get("trial_order"), 1, 2),
         seconds, as_int(data.get("clicks"), 0), as_int(data.get("errors"), 0),
         as_int(data.get("backtracks"), 0), success,
         "observer" if method == "current" else "auto"))
    db.get_db().commit()
    return jsonify({"ok": True}), 201


@app.post("/api/sus")
def api_sus():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers")
    if not isinstance(answers, list) or len(answers) != 10:
        return err("Please answer all 10 statements.")
    values = [as_int(a, 1, 5) for a in answers]
    if None in values:
        return err("Each answer must be from 1 to 5.")
    # SUS scoring: odd items (score - 1), even items (5 - score), total x 2.5 -> 0 to 100
    total = sum((v - 1) if i % 2 == 0 else (5 - v) for i, v in enumerate(values))
    score = total * 2.5
    db.get_db().execute(
        "INSERT INTO sus (participant_code, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10, score, comment) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (clean_code(data.get("participant_code")), *values, score, text(data.get("comment"), 300)))
    db.get_db().commit()
    return jsonify({"score": score}), 201


# ---------- survey ----------
@app.get("/api/survey/questions")
def api_survey_questions():
    return jsonify({"consent": CONSENT_TEXT, "likert_labels": LIKERT_LABELS, "questions": QUESTIONS})


@app.post("/api/survey")
def api_survey_submit():
    data = request.get_json(silent=True) or {}
    if data.get("consent") is not True:
        return err("Please tick the consent box to continue.")
    raw = data.get("answers")
    if not isinstance(raw, dict):
        return err("Invalid answers")
    clean = {}
    for q in QUESTIONS:
        value = raw.get(q["id"])
        empty = value is None or value == ""
        if empty:
            if q["required"]:
                return err(f"Please answer: {q['label']}")
            continue
        if q["type"] == "single":
            if value not in q["options"]:
                return err(f"Invalid choice for: {q['label']}")
            clean[q["id"]] = value
        elif q["type"] == "likert":
            n = as_int(value, 1, 5)
            if n is None:
                return err(f"Choose 1 to 5 for: {q['label']}")
            clean[q["id"]] = n
        elif q["type"] == "number":
            n = as_float(value, q.get("min"), q.get("max"))
            if n is None:
                return err(f"Enter a number between {q.get('min')} and {q.get('max')} for: {q['label']}")
            clean[q["id"]] = n
        else:
            clean[q["id"]] = text(value, 300)
    db.get_db().execute("INSERT INTO survey_responses (answers) VALUES (?)", (json.dumps(clean),))
    db.get_db().commit()
    return jsonify({"ok": True}), 201


@app.get("/api/summary")
def api_summary():
    con = db.get_db()
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in EXPORT_TABLES if t != "providers"}
    counts["testers_current"] = con.execute("SELECT COUNT(DISTINCT participant_code) FROM tasks WHERE method='current'").fetchone()[0]
    counts["testers_prototype"] = con.execute("SELECT COUNT(DISTINCT participant_code) FROM tasks WHERE method='prototype'").fetchone()[0]
    return jsonify(counts)


# ---------- provider signup and approval ----------
def admin_allowed():
    """Admin pages work from localhost, or anywhere with ?token=EXPORT_TOKEN."""
    token = os.environ.get("EXPORT_TOKEN")
    local = request.remote_addr in ("127.0.0.1", "::1")
    return local or bool(token and request.args.get("token") == token)


@app.post("/api/provider-signup")
def api_provider_signup():
    data = request.get_json(silent=True) or {}
    if data.get("consent") is not True:
        return err("Please tick the box to confirm that your details can be used in this demo.")
    name = text(data.get("name"), 60)
    if len(name) < 3:
        return err("Enter your name or shop name (at least 3 letters).")
    category = data.get("category")
    if category not in CATEGORIES:
        return err("Choose a service category.")
    area = text(data.get("area"), 60)
    if len(area) < 2:
        return err("Enter the area where you work.")
    experience = as_int(data.get("experience_years"), 0, 50)
    if experience is None:
        return err("Experience must be a number from 0 to 50 years.")
    price_min = as_int(data.get("price_min"), 50, 20000)
    price_max = as_int(data.get("price_max"), 50, 20000)
    if price_min is None or price_max is None:
        return err("Enter your usual charge range in rupees (50 to 20000).")
    if price_min > price_max:
        return err("The lowest charge cannot be higher than the highest charge.")
    db.get_db().execute(
        """INSERT INTO provider_signups (name, category, area, experience_years, price_min, price_max, about)
           VALUES (?,?,?,?,?,?,?)""",
        (name, category, area, experience, price_min, price_max, text(data.get("about"), 200)))
    db.get_db().commit()
    return jsonify({"ok": True}), 201


@app.get("/api/admin/signups")
def api_admin_signups():
    if not admin_allowed():
        abort(403)
    rows = db.get_db().execute("SELECT * FROM provider_signups ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/admin/signups/<int:signup_id>/<action>")
def api_admin_decide(signup_id, action):
    if not admin_allowed():
        abort(403)
    if action not in ("approve", "reject"):
        abort(404)
    con = db.get_db()
    row = con.execute("SELECT * FROM provider_signups WHERE id = ?", (signup_id,)).fetchone()
    if row is None:
        return err("Signup not found.", 404)
    if row["status"] != "pending":
        return err("This signup was already reviewed.", 409)
    if action == "approve":
        # New providers have no rating or distance yet, the UI shows them as "New provider".
        con.execute(
            """INSERT INTO providers (name, category, rating, reviews, distance_km, price_min, price_max,
                                      experience_years, available_now, areas)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (row["name"], row["category"], None, 0, None, row["price_min"], row["price_max"],
             row["experience_years"], 1, row["area"]))
    con.execute("UPDATE provider_signups SET status = ? WHERE id = ?",
                ("approved" if action == "approve" else "rejected", signup_id))
    con.commit()
    return jsonify({"ok": True})


# ---------- export ----------
@app.get("/export/<table>.csv")
def export_csv(table):
    """Download a table as CSV. Allowed from localhost, or anywhere with ?token=EXPORT_TOKEN."""
    token = os.environ.get("EXPORT_TOKEN")
    local = request.remote_addr in ("127.0.0.1", "::1")
    if not (local or (token and request.args.get("token") == token)):
        abort(403)
    if table not in EXPORT_TABLES:
        abort(404)
    cur = db.get_db().execute(f"SELECT * FROM {table}")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([d[0] for d in cur.description])
    writer.writerows(cur.fetchall())
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={table}.csv"})


@app.errorhandler(sqlite3.Error)
def handle_db_error(exc):
    app.logger.exception(exc)
    return err("Database error. Please try again.", 500)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
