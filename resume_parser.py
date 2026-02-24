"""
Resume PDF parser - extracts skills and work experience
"""

import re
import pdfplumber
from typing import Dict, List, Any

SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "go", "golang",
        "rust", "kotlin", "swift", "scala", "r", "matlab", "bash", "shell", "perl",
        "ruby", "php", "dart", "julia", "sql",
    ],
    "Web & Frontend": [
        "react", "vue", "angular", "next\\.js", "html", "css", "tailwind", "bootstrap",
        "webpack", "vite", "svelte", "jquery", "graphql", "rest api", "restful",
        "websocket", "grpc", "html/css",
    ],
    "Backend & Frameworks": [
        "node\\.js", "django", "flask", "fastapi", "spring boot", "express",
        "laravel", "rails", "asp\\.net", "gin", "fiber", "microservices",
        "distributed systems",
    ],
    "Machine Learning & AI": [
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas",
        "numpy", "matplotlib", "seaborn", "hugging face", "transformers",
        "llm", "nlp", "computer vision", "deep learning", "machine learning",
        "federated learning", "reinforcement learning", "xgboost", "lightgbm",
        "openai", "langchain", "bert", "gpt", "byzantine", "anomaly detection",
        "intrusion detection", "zero-day", "threat detection",
    ],
    "Databases": [
        "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "firebase", "oracle", "sql server", "neo4j",
    ],
    "DevOps & Cloud": [
        "docker", "kubernetes", "aws", "azure", "gcp", "google cloud", "terraform",
        "ansible", "jenkins", "github actions", "ci/cd", "linux", "nginx",
        "prometheus", "grafana", "helm",
    ],
    "Networking & Security": [
        "5g", "lte", "sdn", "nfv", "wireshark", "firewall", "vpn", "tls", "ssl",
        "oauth", "jwt", "penetration testing", "ids", "ips",
        "free5gc", "ueransim", "network security", "cybersecurity",
    ],
    "Blockchain & Web3": [
        "ethereum", "smart contracts", "blockchain", "solidity", "web3",
        "decentralized", "consensus", "fault.tolerance",
    ],
    "Tools & Practices": [
        "git", "github", "gitlab", "jira", "agile", "scrum", "kanban",
        "unit testing", "pytest", "junit", "selenium", "postman", "swagger",
        "load testing", "test automation", "ci/cd pipelines",
    ],
    "Soft Skills & Other": [
        "communication", "leadership", "teamwork", "problem.solving",
        "project management", "research", "technical writing", "bilingual",
        "mandarin", "chinese", "english", "teaching", "mentoring",
    ],
}

# Matches: "Title | Company   Date – Date" on a single line
JOB_HEADER_PATTERN = re.compile(
    r'^(.+?)\s*\|\s*(.+?)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s*\d{4}\s*[–—-]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s*\d{4}|Present|Current|Now))\s*$',
    re.IGNORECASE
)

# Matches just a date range anywhere in a line
DATE_RANGE_PATTERN = re.compile(
    r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})\s*[–—-]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|Present|Current|Now)',
    re.IGNORECASE
)

SECTION_HEADERS = {
    "experience": re.compile(r'^(PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT)', re.IGNORECASE),
    "end":        re.compile(r'^(TECHNICAL\s+PROJECTS|PROJECTS|EDUCATION|SKILLS|PUBLICATIONS|CERTIFICATIONS|ADDITIONAL)', re.IGNORECASE),
}


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def parse_resume_pdf(pdf_path: str) -> Dict[str, List[str]]:
    """Extract skills from resume PDF."""
    text = extract_text_from_pdf(pdf_path)
    found: Dict[str, List[str]] = {}

    for category, patterns in SKILL_CATEGORIES.items():
        matched = []
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
                display = pattern.replace("\\.", ".").replace("\\+\\+", "++")
                matched.append(display)
        if matched:
            found[category] = matched

    return found


def parse_work_experience(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extract work experience entries from resume.
    Handles the common format: "Title | Company    Date – Date"
    """
    text = extract_text_from_pdf(pdf_path)
    lines = text.split("\n")

    in_experience = False
    experiences = []

    for line in lines:
        stripped = line.strip()

        # Detect experience section start
        if SECTION_HEADERS["experience"].match(stripped):
            in_experience = True
            continue

        # Detect section end
        if in_experience and SECTION_HEADERS["end"].match(stripped):
            break

        if not in_experience:
            continue

        # Try to match "Title | Company   Date – Date" pattern
        m = JOB_HEADER_PATTERN.match(stripped)
        if m:
            title = m.group(1).strip()
            company = m.group(2).strip()
            dates = m.group(3).strip()
            duration = _calc_duration(dates)
            experiences.append({
                "title": title,
                "company": company,
                "dates": dates,
                "duration_months": duration,
            })

    return experiences


def _calc_duration(date_str: str) -> int:
    """Calculate duration in months from a date range string."""
    import datetime
    MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
               "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

    def parse_date(s: str):
        s = s.strip().lower()
        if any(w in s for w in ["present", "current", "now"]):
            return datetime.date.today()
        for abbr, num in MONTHS.items():
            if abbr in s:
                y = re.search(r'\d{4}', s)
                if y:
                    return datetime.date(int(y.group()), num, 1)
        y = re.search(r'\d{4}', s)
        if y:
            return datetime.date(int(y.group()), 1, 1)
        return None

    m = DATE_RANGE_PATTERN.search(date_str)
    if not m:
        return 0
    start = parse_date(m.group(1))
    end = parse_date(m.group(2))
    if start and end and end >= start:
        return (end.year - start.year) * 12 + (end.month - start.month)
    return 0


def get_total_experience_years(experiences: List[Dict]) -> float:
    total = sum(e.get("duration_months", 0) for e in experiences)
    return round(total / 12, 1)


def get_all_skills_flat(resume_skills: Dict[str, List[str]]) -> set:
    all_skills = set()
    for skills in resume_skills.values():
        for s in skills:
            all_skills.add(s.lower().strip())
    return all_skills
