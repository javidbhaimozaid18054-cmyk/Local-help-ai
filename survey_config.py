"""Questionnaire definition (Stage 1: Empathise).

Edit this list to change the survey. The question ids become the column names in the
analysis, so keep them short and unchanged once you start collecting data.

type: single (multiple choice) | likert (1 to 5) | number | text
Default topic: students living in a hostel / PG who need local services.
Change the wording if you choose another user group.
"""

CONSENT_TEXT = (
    "This short survey is part of a college project. Your answers are anonymous. "
    "We do not ask for your name, phone number or address. The data is used only for "
    "analysis in this project. You can stop at any time."
)

LIKERT_LABELS = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]

QUESTIONS = [
    {"id": "age_group", "type": "single", "label": "Your age group", "required": True,
     "options": ["17 to 19", "20 to 22", "23 to 25", "26 or above"]},
    {"id": "stay_type", "type": "single", "label": "Where do you stay?", "required": True,
     "options": ["Hostel", "PG", "Rented flat", "With family"]},
    {"id": "times_12m", "type": "number", "required": True, "min": 0, "max": 50,
     "label": "How many times in the last 12 months did you need a plumber, electrician, mechanic or similar help?"},
    {"id": "service_type", "type": "single", "required": True,
     "label": "Which service did you need most recently?",
     "options": ["Plumbing", "Electrical", "Vehicle repair", "Electronics / appliance", "Cleaning", "Carpentry", "Other"]},
    {"id": "how_found", "type": "single", "required": True,
     "label": "How did you find the provider that time?",
     "options": ["Friend or family", "Hostel / PG owner", "Google or Maps", "Listing app or website", "Walked to a shop", "Other"]},
    {"id": "minutes_to_find", "type": "number", "required": True, "min": 0, "max": 600,
     "label": "About how many minutes did it take to find a provider and agree on a visit time?"},
    {"id": "calls_made", "type": "number", "required": True, "min": 0, "max": 30,
     "label": "How many providers did you contact before one agreed to come?"},
    {"id": "price_known", "type": "single", "required": True,
     "label": "Did you know the likely price before the work started?",
     "options": ["Yes", "Partly", "No"]},
    {"id": "overcharged", "type": "single", "required": True,
     "label": "Did you feel you were overcharged?",
     "options": ["Yes", "Not sure", "No"]},
    {"id": "satisfaction", "type": "likert", "required": True,
     "label": "I am satisfied with how I find local service providers today."},
    {"id": "frustration", "type": "likert", "required": True,
     "label": "Finding a service provider is frustrating for me."},
    {"id": "trust", "type": "likert", "required": True,
     "label": "I trust the providers I find today."},
    {"id": "price_fair", "type": "likert", "required": True,
     "label": "I feel sure that I paid a fair price."},
    {"id": "would_use", "type": "likert", "required": True,
     "label": "I would use an app that shows verified providers and an estimated price."},
    {"id": "open_problem", "type": "text", "required": False,
     "label": "Describe your worst experience finding a service provider (optional). Please do not write names or phone numbers."},
    {"id": "open_feature", "type": "text", "required": False,
     "label": "Which one feature would help you most? (optional)"},
]
