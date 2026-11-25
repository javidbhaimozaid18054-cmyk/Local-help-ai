"""Database helpers for LocalHelp AI (SQLite).

Tables
------
providers         sample service providers (REPLACE with real ones if you collect them)
requests          service requests made through the prototype (+ rating after completion)
events            usage log: page steps, clicks, errors (for usability analysis)
tasks             timed task trials: current method (observer) and prototype (automatic)
sus               System Usability Scale answers and score
survey_responses  answers to the questionnaire (stored as JSON, one row per respondent)
provider_signups  providers who registered on /provider (pending until approved on /admin)
"""
import os
import sqlite3

from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("LOCALHELP_DB", os.path.join(BASE_DIR, "localhelp.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    rating REAL,
    reviews INTEGER,
    distance_km REAL,
    price_min INTEGER,
    price_max INTEGER,
    experience_years INTEGER,
    available_now INTEGER DEFAULT 1,
    areas TEXT
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_code TEXT,
    session_id TEXT,
    category TEXT,
    problem_text TEXT,
    has_photo INTEGER DEFAULT 0,
    issue TEXT,
    urgency TEXT,
    est_min INTEGER,
    est_max INTEGER,
    provider_id INTEGER,
    date_pref TEXT,
    time_pref TEXT,
    notes TEXT,
    rating INTEGER,
    review TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    participant_code TEXT,
    event_type TEXT,
    step INTEGER,
    detail TEXT,
    client_ts REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_code TEXT NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('current', 'prototype')),
    task_name TEXT,
    trial_order INTEGER,
    seconds REAL,
    clicks INTEGER,
    errors INTEGER,
    backtracks INTEGER,
    success INTEGER,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_code TEXT,
    q1 INTEGER, q2 INTEGER, q3 INTEGER, q4 INTEGER, q5 INTEGER,
    q6 INTEGER, q7 INTEGER, q8 INTEGER, q9 INTEGER, q10 INTEGER,
    score REAL,
    comment TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answers TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS provider_signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    area TEXT NOT NULL,
    experience_years INTEGER,
    price_min INTEGER,
    price_max INTEGER,
    about TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TEXT DEFAULT (datetime('now'))
);
"""

# Sample providers. These names and numbers are FICTIONAL demo data.
SEED_NAMES = {
    "plumbing": ["Raj Plumbing Services", "Patel Plumbing", "Ahmed Plumbing Works"],
    "electrical": ["Shree Electricals", "Bright Wiring Co.", "Khan Electric Works"],
    "vehicle": ["Sharma Auto Care", "Speedy Bike Garage", "Mehta Motors"],
    "electronics": ["Fix-It Electronics", "Digital Doctor", "Joshi Repair Hub"],
    "cleaning": ["Sparkle Home Cleaners", "Clean Nest Services", "Shine Pro Team"],
    "carpentry": ["Solanki Carpentry", "Woodcraft Works", "Vishal Furniture Fix"],
    "home": ["Om Home Fixers", "Suraj Repair Team", "Patel Handyman"],
    "other": ["Local Helpers", "City Task Pros", "QuickHelp Services"],
}
SEED_BASE_PRICE = {
    "plumbing": (300, 800), "electrical": (250, 700), "vehicle": (200, 900),
    "electronics": (250, 1200), "cleaning": (400, 1500), "carpentry": (350, 1400),
    "home": (300, 1000), "other": (250, 900),
}
SEED_DISTANCE = [1.2, 2.0, 2.4]
SEED_RATING = [4.7, 4.5, 4.3]
SEED_REVIEWS = [320, 210, 180]


def get_db():
    """Return the SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and insert sample providers if the table is empty."""
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    if con.execute("SELECT COUNT(*) FROM providers").fetchone()[0] == 0:
        for category, names in SEED_NAMES.items():
            lo, hi = SEED_BASE_PRICE[category]
            for i, name in enumerate(names):
                con.execute(
                    """INSERT INTO providers
                       (name, category, rating, reviews, distance_km, price_min, price_max,
                        experience_years, available_now, areas)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (name, category, SEED_RATING[i], SEED_REVIEWS[i], SEED_DISTANCE[i],
                     lo + i * 20, hi - i * 50, 5 + i, 0 if i == 1 else 1,
                     "Ahmedabad, Danilimda, Bapunagar"),
                )
    con.commit()
    con.close()
