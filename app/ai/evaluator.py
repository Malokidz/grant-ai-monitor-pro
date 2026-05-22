import os
import json
import time
from openai import OpenAI, RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def has_available_quota():
    """Return True if OpenAI account has positive credit balance."""
    try:
        test_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0.0
        )
        return True
    except RateLimitError as e:
        if "insufficient_quota" in str(e):
            print("⚠️ OpenAI quota exhausted – AI evaluation disabled.")
            return False
        raise
    except Exception as e:
        print(f"⚠️ OpenAI check failed: {e} – assuming no quota.")
        return False

def evaluate_grant(grant_text, profile):
    """
    Send grant + profile to GPT-4o-mini. Assumes quota is available (caller should check).
    """
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
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt+1}...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
