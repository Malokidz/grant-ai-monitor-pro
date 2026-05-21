def score_text(text):
    score = 0

    keywords = {
        "genomics": 3,
        "bioinformatics": 3,
        "microbe": 2,
        "parasite": 3,
        "infectious": 3,
        "sequencing": 2,
        "metagenomics": 4
    }

    for k, v in keywords.items():
        if k in text.lower():
            score += v

    # Penalize big PI grants
    if "R01" in text or "U24" in text or "UM1" in text:
        score -= 5

    return score
