"""
Resume tailoring using Groq API (free tier).
Get your API key at: https://console.groq.com
"""

import json
import requests
import os
from pathlib import Path
from resume_parser import extract_text_from_pdf

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set.\n"
            "1. Go to https://console.groq.com\n"
            "2. Click 'API Keys' -> 'Create API Key'\n"
            "3. Run: python main.py init"
        )

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Return valid JSON only, no markdown, no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def tailor_resume(
    resume_pdf_path: str,
    job_title: str,
    job_description: str,
    missing_skills: list,
    matched_skills: list,
) -> dict:
    resume_text = extract_text_from_pdf(resume_pdf_path)

    prompt = f"""Tailor the resume below to better match the target job.

STRICT RULES:
- NEVER invent experience or skills the candidate does not have
- Only rephrase, reorder, and emphasize existing content
- Naturally incorporate missing keywords where they genuinely apply
- Keep bullet points concise and achievement-focused
- Preserve all dates, company names, and job titles exactly
- Return valid JSON only, no markdown fences, no extra text

RESUME:
{resume_text}

TARGET JOB: {job_title}

JOB DESCRIPTION:
{job_description[:2000]}

MISSING SKILLS (incorporate naturally where applicable): {', '.join(missing_skills[:10])}
ALREADY MATCHING: {', '.join(matched_skills[:10])}

Return this exact JSON structure:
{{
  "summary": "2-3 sentence professional summary targeting this role",
  "skills": {{
    "Programming Languages": ["list"],
    "Backend & Systems": ["list"],
    "Databases": ["list"],
    "Cloud & DevOps": ["list"],
    "Testing & Quality": ["list"]
  }},
  "experience": [
    {{
      "title": "exact job title",
      "company": "exact company name",
      "dates": "exact dates",
      "bullets": ["rewritten bullet 1", "rewritten bullet 2"]
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "dates": "dates",
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ],
  "changes_made": ["brief description of each change made"]
}}"""

    response = call_groq(prompt)

    # Strip markdown fences if present
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])

    return json.loads(response.strip())