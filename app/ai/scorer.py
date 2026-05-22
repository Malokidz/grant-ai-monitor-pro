import json

def load_keywords():
    with open("app/config/keywords.json") as f:
        return [kw.lower() for kw in json.load(f)["keywords"]]

KEYWORD_LIST = load_keywords()

def score_text(text):
    """Score a grant based on how many of your keywords appear."""
    text_lower = text.lower()
    score = 0
    matched = []
    for kw in KEYWORD_LIST:
        if kw in text_lower:
            score += 1
            matched.append(kw)
    return score, matched   # return both score and list of matched keywords
