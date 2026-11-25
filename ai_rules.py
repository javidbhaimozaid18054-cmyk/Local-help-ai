"""Rule-based problem analysis for LocalHelp AI.

This is a simple keyword matcher written in plain Python. It understands English and
a few Hinglish words. It is NOT a trained model. To upgrade it later, keep the same
analyze() function signature and replace the body with a call to an ML / LLM API.
"""
import re

# category -> (min cost, max cost) in rupees, used as an *estimate range only*
COST_RANGE = {
    "plumbing": (300, 800), "electrical": (250, 700), "vehicle": (200, 900),
    "electronics": (250, 1200), "cleaning": (400, 1500), "carpentry": (350, 1400),
    "home": (300, 1000), "other": (250, 900),
}

RULES = [
    {"category": "plumbing",
     "pattern": r"leak|pipe|tap|plumb|drain|toilet|flush|paani|pani|nal\b|cistern|geyser|tank",
     "issue": "Possible pipe or tap leakage",
     "tip": "It looks like a pipe joint, tap or connector is leaking. Close the water valve near it until help arrives.",
     "urgency": "Medium", "service": "Plumber"},
    {"category": "electrical",
     "pattern": r"switch|wire|wiring|fan|light|bulb|short|spark|bijli|electric|mcb|socket|inverter|current",
     "issue": "Possible wiring or switch fault",
     "tip": "This may be a loose connection or a worn switch. Turn off the main switch for that circuit and do not touch exposed wires.",
     "urgency": "High", "service": "Electrician"},
    {"category": "vehicle",
     "pattern": r"bike|car\b|scooter|puncture|engine|tyre|tire|brake|battery|gadi|vehicle|starter",
     "issue": "Possible vehicle mechanical issue",
     "tip": "It could be a tyre, battery or brake problem. Avoid driving until it is checked.",
     "urgency": "Medium", "service": "Mechanic"},
    {"category": "electronics",
     "pattern": r"\bac\b|fridge|refrigerator|\btv\b|laptop|phone|washing|cooler|mobile|computer|microwave|screen",
     "issue": "Possible appliance or electronics fault",
     "tip": "Unplug the device and note any error code or sound. A technician can run a quick diagnosis.",
     "urgency": "Low", "service": "Technician"},
    {"category": "cleaning",
     "pattern": r"clean|safai|dust|stain|sofa|bathroom|kitchen|sanitize|pest",
     "issue": "Deep cleaning needed",
     "tip": "Share the room count or area so the provider can quote an exact price.",
     "urgency": "Low", "service": "Cleaner"},
    {"category": "carpentry",
     "pattern": r"door|wood|table|furniture|cupboard|drawer|hinge|darwaza|lakdi|bed\b|wardrobe",
     "issue": "Possible furniture or door damage",
     "tip": "Likely a loose hinge, joint or worn wood. A carpenter can usually fix it on site.",
     "urgency": "Low", "service": "Carpenter"},
]

DEFAULT = {
    "category": "home", "issue": "General home repair",
    "tip": "Add a few more details or a photo so the provider can prepare the right tools.",
    "urgency": "Low", "service": "Handyman",
}


def analyze(text, category=None):
    """Return the likely issue, urgency, service type and cost range."""
    text = (text or "").lower()
    hit = None
    matched_by = "keyword"
    for rule in RULES:
        if re.search(rule["pattern"], text):
            hit = rule
            break
    if hit is None and category:
        hit = next((r for r in RULES if r["category"] == category), None)
        matched_by = "category"
    if hit is None:
        hit = DEFAULT
        matched_by = "default"
    lo, hi = COST_RANGE.get(hit["category"], COST_RANGE["home"])
    return {
        "category": hit["category"],
        "issue": hit["issue"],
        "tip": hit["tip"],
        "urgency": hit["urgency"],
        "service": hit["service"],
        "est_min": lo,
        "est_max": hi,
        "matched_by": matched_by,
    }
