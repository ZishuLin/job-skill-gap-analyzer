# 🔍 Job Skill Gap Analyzer

A CLI tool that scrapes job postings from public job boards, parses your resume PDF, and generates a personalized **HTML skill gap report** with charts and actionable recommendations.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🕷️ **Scrapes real job postings** from Arbeitnow & RemoteOK (free APIs, no key required)
- 📄 **Parses your resume PDF** — extracts 150+ skills across 10 categories
- 💼 **Extracts work experience** — detects job titles, companies, and calculates total years
- 📊 **Generates an interactive HTML report** with Chart.js visualizations
- 🎯 **Skill gap analysis** — ranks missing skills by how often they appear in job postings
- 💡 **Personalized action plan** — auto-generates recommendations based on your specific gaps
- 🎓 **Experience & education comparison** — shows how your background stacks up against job requirements

## 📸 Report Preview

The generated report includes:
- Overall match rate across all scraped jobs
- Top missing skills (ranked by frequency)
- Your strongest matching skills
- Category-level coverage breakdown
- Personalized action plan with priority levels
- Work experience timeline vs. job requirements
- Per-job breakdown table with matched/missing skills

## 🚀 Installation

```bash
git clone https://github.com/yourusername/job-skill-gap-analyzer.git
cd job-skill-gap-analyzer
pip install -r requirements.txt
```

## 📖 Usage

### Analyze skill gaps

```bash
python main.py analyze --query "Software Engineer" --location "Canada" --resume resume.pdf
```

```bash
# More options
python main.py analyze \
  --query "python developer" \
  --location "Canada" \
  --resume resume.pdf \
  --limit 20 \
  --output my_report.html
```

> **Windows PowerShell users**: use backtick `` ` `` for line continuation, or write the command on one line.

### Just parse your resume

```bash
python main.py parse resume.pdf
```

This shows all detected skills and work experience without scraping any jobs.

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Job title to search | required |
| `--location` | `-l` | Location to search | `Canada` |
| `--resume` | `-r` | Path to resume PDF | required |
| `--limit` | `-n` | Number of jobs to scrape | `20` |
| `--source` | `-s` | `indeed`, `linkedin`, or `both` | `indeed` |
| `--output` | `-o` | Output HTML filename | `skill_gap_report.html` |

## 🗂️ Project Structure

```
job-skill-gap-analyzer/
├── main.py              # CLI entry point (Click)
├── scraper.py           # Job scrapers (Arbeitnow, RemoteOK, LinkedIn)
├── resume_parser.py     # PDF parsing + skill/experience extraction
├── analyzer.py          # Skill gap analysis logic
├── report_generator.py  # HTML report + recommendations engine
├── requirements.txt
└── README.md
```

## 🔌 Data Sources

| Source | Type | Auth Required |
|--------|------|---------------|
| [Arbeitnow](https://arbeitnow.com/api) | Free REST API | No |
| [RemoteOK](https://remoteok.com/api) | Free REST API | No |
| LinkedIn | HTML scraping | Optional (session cookie) |

### Enabling LinkedIn

LinkedIn requires a session cookie for reliable results:

1. Log into LinkedIn in your browser
2. Open DevTools → Application → Cookies → copy the `li_at` value
3. Set as environment variable:
   ```bash
   export LINKEDIN_SESSION_COOKIE="your_li_at_value_here"
   ```
4. Run with `--source linkedin` or `--source both`

## 🛠️ How It Works

1. **Scraping** — fetches job postings via public APIs with polite rate limiting
2. **Resume parsing** — extracts text from PDF, matches against 150+ skill patterns using regex
3. **Experience parsing** — detects `Title | Company   Date – Date` format lines, calculates duration
4. **Gap analysis** — counts skill frequency across all jobs, compares against resume skills
5. **Recommendations** — rule-based engine generates prioritized suggestions based on match rate, missing skills, experience gap, and category coverage
6. **Report generation** — self-contained HTML file with Chart.js charts, no server needed

## ⚠️ Notes

- **Indeed is not supported** — they block all automated access. Arbeitnow and RemoteOK are used instead.
- For best results, use broad locations like `"Canada"` or `"Remote"` rather than small cities.
- Rate limiting is built in (random 1–2.5s delays between requests) to be respectful to APIs.
- The HTML report is fully self-contained — open it in any browser, no internet needed.

## 📦 Requirements

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pdfplumber>=0.10.0
rich>=13.7.0
click>=8.1.0
```

## 📄 License

MIT
