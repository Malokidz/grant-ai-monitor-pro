from openai import OpenAI
import json
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_grant(grant_text, profile):
    prompt = f"""
You are an NIH grant expert.

Grant:
{grant_text}

Researcher profile:
{json.dumps(profile, indent=2)}

Answer **only** with a valid JSON object following this exact schema:
{{
  "relevant": true/false,
  "mechanism": "string (e.g., K99, R21, etc.)",
  "eligible_as_PI": true/false,
  "recommended_role": "PI / Co-I / Ignore",
  "score": integer 0-10,
  "reason": "short justification"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content
