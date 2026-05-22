import os
import json
import time
from openai import OpenAI, RateLimitError

# Initialize the OpenAI client with your API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_grant(grant_text, profile):
    """
    Send a grant + researcher profile to GPT-4o-mini and return a structured JSON evaluation.
    Implements exponential backoff on rate limit errors.
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
                raise  # re-raise the last error
            wait_time = 2 ** attempt  # 1, 2, 4 seconds
            print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt+1}...")
            time.sleep(wait_time)
        except Exception as e:
            # For other errors, fail fast
            print(f"OpenAI API error: {e}")
            raise
