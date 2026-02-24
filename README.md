# Job Skill Gap Analyzer

A CLI tool that scrapes real job postings, parses your resume PDF, and generates a personalized HTML skill gap report with charts and actionable recommendations. Includes an AI-powered resume tailoring feature that rewrites your resume to better match specific job postings.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- Scrapes live job postings from Arbeitnow and RemoteOK (free APIs, no key required)
- Parses your resume PDF and extracts 150+ skills across 10 categories
- Detects work experience entries and calculates total years
- Generates an interactive HTML report with Chart.js visualizations
- Ranks missing skills by how often they appear across job postings
- Generates a personalized action plan based on your specific gaps
- Compares your experience and education against job requirements
- AI-powered resume tailoring that rewrites bullet points to match a target role (uses Groq API, free)

## Report Preview

The generated HTML report includes:
- Overall skill match rate across all scraped jobs
- Top missing skills ranked by frequency
- Your strongest matching skills
- Category-level coverage breakdown
- Personalized action plan with priority levels
- Work experience timeline vs. job requirements
- Per-job breakdown table with matched and missing skills

## Installation

```bash
git clone https://github.com/ZishuLin/job-skill-gap-analyzer.git
cd job-skill-gap-analyzer
pip install -r requirements.txt
npm install docx
```

## Setup

Run the setup wizard to create your `.env` file:

```bash
python main.py init
```

This will prompt you for:
- **Groq API key** (free, used for AI resume tailoring) — get one at [console.groq.com](https://console.groq.com)
- **LinkedIn session cookie** (optional, for LinkedIn job scraping)

Your `.env` file is listed in `.gitignore` and will never be uploaded to GitHub.

## Usage

### Analyze skill gaps

```bash
python main.py analyze --query "Software Engineer" --location "Canada" --resume resume.pdf
```

```bash
# With more options
python main.py analyze --query "python developer" --location "Remote" --resume resume.pdf --limit 20 --output my_report.html
```

### Tailor your resume with AI

Scrapes current job postings, finds the best match, then uses Groq AI to rewrite your resume bullet points and summary to better fit the role. Outputs a formatted `.docx` file.

```bash
python main.py tailor --query "backend developer" --location "Remote" --resume resume.pdf
```

> The AI only rephrases and reorders your existing experience. It never adds skills or jobs you do not have.

### Parse your resume

```bash
python main.py parse resume.pdf
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Job title to search | required |
| `--location` | `-l` | Location | `Canada` |
| `--resume` | `-r` | Path to resume PDF | required |
| `--limit` | `-n` | Number of jobs to scrape | `20` |
| `--source` | `-s` | `indeed`, `linkedin`, or `both` | `indeed` |
| `--output` | `-o` | Output HTML filename | `skill_gap_report.html` |

## Project Structure

```
job-skill-gap-analyzer/
├── main.py              # CLI entry point (Click)
├── scraper.py           # Job scrapers (Arbeitnow, RemoteOK, LinkedIn)
├── resume_parser.py     # PDF parsing, skill and experience extraction
├── analyzer.py          # Skill gap analysis logic
├── report_generator.py  # HTML report and recommendations engine
├── tailor.py            # AI resume tailoring (Groq API)
├── build_resume.js      # Generates tailored .docx output (Node.js)
├── requirements.txt
├── .env.example         # Template for API keys
└── README.md
```

## Data Sources

| Source | Type | Auth Required |
|--------|------|---------------|
| [Arbeitnow](https://arbeitnow.com/api) | Free REST API | No |
| [RemoteOK](https://remoteok.com/api) | Free REST API | No |
| LinkedIn | HTML scraping | Optional session cookie |

## How It Works

1. **Scraping** — fetches job postings via public APIs with rate limiting
2. **Resume parsing** — extracts text from PDF, matches against 150+ skill patterns using regex
3. **Experience parsing** — detects `Title | Company   Date – Date` format lines and calculates duration
4. **Gap analysis** — counts skill frequency across jobs, compares against resume skills
5. **Recommendations** — rule-based engine generates prioritized suggestions based on match rate, missing skills, experience gap, and category coverage
6. **Report generation** — self-contained HTML file with Chart.js charts, no server needed
7. **AI tailoring** — sends resume and job description to Groq (Llama 3.3 70B), rewrites content to improve keyword match, outputs `.docx`

## Notes

- Indeed is not supported as they block automated access. Arbeitnow and RemoteOK are used instead.
- For best results use broad locations like `Canada` or `Remote` rather than specific cities.
- The HTML report is fully self-contained and works offline.
- Node.js is required for the `tailor` command to generate `.docx` output. Download at [nodejs.org](https://nodejs.org).

## Requirements

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pdfplumber>=0.10.0
rich>=13.7.0
click>=8.1.0
python-dateutil>=2.8.0
python-dotenv>=1.0.0
```

Node.js dependency: `docx` (installed via `npm install docx`)

## License

MIT
