"""
Skill gap analyzer - compares resume skills + experience vs job postings
"""

import re
from collections import Counter
from typing import Dict, List, Any
from resume_parser import SKILL_CATEGORIES, get_all_skills_flat
from scraper import Job

# Experience keywords found in job descriptions
EXP_PATTERNS = [
    (r'(\d+)\+?\s*years?\s+of\s+experience', 'years'),
    (r'(\d+)\+?\s*years?\s+experience', 'years'),
    (r'minimum\s+(\d+)\s+years?', 'years'),
    (r'at\s+least\s+(\d+)\s+years?', 'years'),
    (r'(\d+)-(\d+)\s+years?', 'range'),
]

DEGREE_PATTERNS = {
    "PhD": [r"ph\.?d", r"doctorate"],
    "Master's": [r"master", r"m\.sc", r"m\.s\.?\b", r"graduate degree"],
    "Bachelor's": [r"bachelor", r"b\.sc", r"b\.s\.?\b", r"undergraduate", r"b\.eng"],
}


def extract_skills_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for category, patterns in SKILL_CATEGORIES.items():
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', text_lower, re.IGNORECASE):
                display = pattern.replace("\\.", ".").replace("\\+\\+", "++").lower()
                found.append(display)
    return list(set(found))


def extract_experience_req(text: str) -> Dict[str, Any]:
    """Extract years of experience and degree requirements from job description."""
    text_lower = text.lower()
    years_required = 0

    for pattern, ptype in EXP_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            if ptype == 'range':
                years_required = int(m.group(1))  # take lower bound
            else:
                years_required = int(m.group(1))
            break

    degrees_required = []
    for degree, patterns in DEGREE_PATTERNS.items():
        for p in patterns:
            if re.search(p, text_lower):
                degrees_required.append(degree)
                break

    return {
        "years_required": years_required,
        "degrees_required": degrees_required,
    }


def analyze_skill_gap(
    resume_skills: Dict[str, List[str]],
    jobs: List[Job],
    resume_experiences: List[Dict] = None,
    resume_total_years: float = 0,
) -> Dict[str, Any]:

    resume_set = get_all_skills_flat(resume_skills)
    all_job_skills: List[str] = []
    job_analyses = []

    for job in jobs:
        job_skills = extract_skills_from_text(job.title + " " + job.description)
        all_job_skills.extend(job_skills)

        matched = [s for s in job_skills if s in resume_set]
        missing = [s for s in job_skills if s not in resume_set]
        match_pct = len(matched) / len(job_skills) * 100 if job_skills else 0

        exp_req = extract_experience_req(job.description)

        # Experience match
        exp_match = "✓ Met" if (
            exp_req["years_required"] == 0 or
            resume_total_years >= exp_req["years_required"]
        ) else f"✗ Need {exp_req['years_required']}yr (you have {resume_total_years}yr)"

        job_analyses.append({
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "url": job.url,
            "salary": getattr(job, "salary", ""),
            "skills_required": job_skills,
            "matched": matched,
            "missing": missing,
            "match_pct": match_pct,
            "years_required": exp_req["years_required"],
            "degrees_required": exp_req["degrees_required"],
            "exp_match": exp_match,
        })

    # Filter out non-tech roles (sales, marketing, etc.)
    NON_TECH_KEYWORDS = {"account executive", "sales", "marketing", "recruiter", "hr ", "human resources", "business development", "account manager", "praktikant", "grafikdesign", "graphic design", "designer", "content creation", "social media", "copywriter", "videographer", "photographer", "illustrator", "motion", "brand"}
    job_analyses = [
        j for j in job_analyses
        if not any(kw in j["title"].lower() for kw in NON_TECH_KEYWORDS)
    ] or job_analyses  # fallback to all if filter removes everything

    job_analyses.sort(key=lambda x: x["match_pct"], reverse=True)

    skill_counter = Counter(all_job_skills)
    total_jobs = len(jobs)

    missing_skills = {s: c for s, c in skill_counter.items() if s not in resume_set}
    matching_skills = {s: c for s, c in skill_counter.items() if s in resume_set}
    top_missing = sorted(missing_skills, key=missing_skills.get, reverse=True)[:20]

    # Years of experience distribution across jobs
    years_dist = Counter(
        j["years_required"] for j in job_analyses if j["years_required"] > 0
    )
    most_common_years = years_dist.most_common(1)[0][0] if years_dist else 0

    # Degree distribution
    all_degrees = []
    for j in job_analyses:
        all_degrees.extend(j["degrees_required"])
    degree_dist = Counter(all_degrees)

    # Category-level breakdown
    category_gaps = {}
    for category, patterns in SKILL_CATEGORIES.items():
        cat_skills = [p.replace("\\.", ".").replace("\\+\\+", "++").lower() for p in patterns]
        cat_in_jobs = [s for s in cat_skills if s in skill_counter]
        cat_missing = [s for s in cat_in_jobs if s not in resume_set]
        cat_matched = [s for s in cat_in_jobs if s in resume_set]
        if cat_in_jobs:
            category_gaps[category] = {
                "total": len(cat_in_jobs),
                "matched": cat_matched,
                "missing": cat_missing,
                "coverage": len(cat_matched) / len(cat_in_jobs) * 100,
            }

    overall_match_pct = (
        sum(j["match_pct"] for j in job_analyses) / len(job_analyses)
        if job_analyses else 0
    )

    return {
        "job_analyses": job_analyses,
        "skill_counter": skill_counter,
        "missing_skills": missing_skills,
        "matching_skills": matching_skills,
        "top_missing": top_missing,
        "category_gaps": category_gaps,
        "overall_match_pct": overall_match_pct,
        "total_jobs": total_jobs,
        "unique_job_skills": len(skill_counter),
        # experience summary
        "resume_total_years": resume_total_years,
        "resume_experiences": resume_experiences or [],
        "most_common_years_required": most_common_years,
        "degree_dist": dict(degree_dist),
        "exp_met_count": sum(1 for j in job_analyses if "✓" in j["exp_match"]),
    }