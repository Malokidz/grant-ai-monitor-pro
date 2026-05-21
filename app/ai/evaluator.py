from openai import OpenAI
import json

client = OpenAI()

def evaluate(grant_text):
    with open("app/config/profile.json") as f:
        profile = json.load(f)

    prompt = f"""
    You are an NIH grant expert.

    Grant:
    {grant_text}

    Researcher:
    {profile}

    Evaluate in JSON:
    {{
      "relevant": true/false,
      "mechanism": "",
      "eligible_as_PI": true/false,
      "recommended_role": "",
      "score": 1-10,
      "reason": ""
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
