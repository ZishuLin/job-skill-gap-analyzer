"""
HTML Report Generator - produces a beautiful self-contained HTML report
"""

import json
from datetime import datetime
from typing import Dict, List, Any



def generate_recommendations(analysis: dict, resume_skills: dict) -> list:
    """Generate personalized action recommendations based on gap analysis."""
    recs = []
    match_pct = analysis.get("overall_match_pct", 0)
    top_missing = analysis.get("top_missing", [])
    missing_skills = analysis.get("missing_skills", {})
    total_jobs = max(analysis.get("total_jobs", 1), 1)
    resume_years = analysis.get("resume_total_years", 0)
    most_needed_years = analysis.get("most_common_years_required", 0)
    category_gaps = analysis.get("category_gaps", {})
    degree_dist = analysis.get("degree_dist", {})

    # 1. Overall match assessment
    if match_pct < 30:
        recs.append({
            "icon": "⚠️", "priority": "high", "title": "Low skill match — consider broadening your target roles",
            "detail": f"Your current skill match is {match_pct:.0f}%. Consider roles like QA Engineer, DevOps Engineer, or Backend Developer which better align with your testing and infrastructure background."
        })
    elif match_pct < 50:
        recs.append({
            "icon": "📈", "priority": "medium", "title": f"Skill match at {match_pct:.0f}% — a few targeted additions will make a big difference",
            "detail": "You're in good shape. Focus on the top 3-5 missing skills below to push your match rate above 50%."
        })
    else:
        recs.append({
            "icon": "✅", "priority": "low", "title": f"Strong skill match at {match_pct:.0f}% — focus on applying",
            "detail": "Your profile is competitive. Prioritize applying and tailoring your resume keywords to each job description."
        })

    # 2. Top missing skills — group by learn-ability
    quick_learns = []
    deep_skills = []
    DEEP = {"kubernetes", "aws", "azure", "gcp", "tensorflow", "pytorch", "machine learning",
            "deep learning", "kubernetes", "terraform", "rust", "scala"}
    for s in top_missing[:8]:
        freq_pct = round(missing_skills.get(s, 0) / total_jobs * 100)
        if freq_pct >= 30:
            if s in DEEP:
                deep_skills.append((s, freq_pct))
            else:
                quick_learns.append((s, freq_pct))

    if quick_learns:
        skill_list = ", ".join(f"{s} ({p}% of jobs)" for s, p in quick_learns[:4])
        recs.append({
            "icon": "🚀", "priority": "high", "title": "Quick wins: add these to your resume soon",
            "detail": f"These skills appear frequently in jobs and are relatively quick to add: {skill_list}. Even mentioning them in projects can help with keyword matching."
        })

    if deep_skills:
        skill_list = ", ".join(f"{s} ({p}% of jobs)" for s, p in deep_skills[:3])
        recs.append({
            "icon": "📚", "priority": "medium", "title": "Longer-term investments worth making",
            "detail": f"These skills take time but significantly improve your market value: {skill_list}. Consider online courses (Coursera, A Cloud Guru, fast.ai) or small side projects."
        })

    # 3. Category-specific advice
    weakest_cats = sorted(
        [(cat, v) for cat, v in category_gaps.items() if v["coverage"] < 40 and v["total"] >= 3],
        key=lambda x: x[1]["coverage"]
    )[:2]
    for cat, data in weakest_cats:
        missing_sample = ", ".join(data["missing"][:4])
        recs.append({
            "icon": "📂", "priority": "medium", "title": f"Weak coverage in {cat} ({data['coverage']:.0f}%)",
            "detail": f"You're missing: {missing_sample}. Adding even 1-2 of these to a project will improve this category significantly."
        })

    # 4. Experience gap
    if most_needed_years > 0 and resume_years < most_needed_years:
        recs.append({
            "icon": "⏳", "priority": "medium", "title": f"Experience gap: jobs want {most_needed_years}yr, you have {resume_years}yr",
            "detail": "Focus on roles that say '0-2 years' or 'new grad welcome'. Internships, co-ops, and thesis projects count as experience — make sure they're clearly described on your resume."
        })

    # 5. Resume keyword advice
    recs.append({
        "icon": "📝", "priority": "low", "title": "Tailor your resume keywords for each application",
        "detail": "Copy keywords directly from job descriptions into your resume where truthful. ATS systems scan for exact matches. For example, if a job says 'CI/CD pipelines' use that exact phrase, not just 'CI/CD'."
    })

    # 6. Degree advantage
    if "Master's" in degree_dist or "PhD" in degree_dist:
        recs.append({
            "icon": "🎓", "priority": "low", "title": "Your Master's degree is a competitive advantage — highlight it",
            "detail": f"Grad degrees are mentioned in {degree_dist.get('Master\'s', 0) + degree_dist.get('PhD', 0)} of the analyzed jobs. Make sure your thesis project is prominently featured as real work experience."
        })

    return recs


def generate_html_report(
    analysis: Dict[str, Any],
    resume_skills: Dict[str, List[str]],
    jobs,
    query: str,
    location: str,
    output_path: str,
):
    """Generate a self-contained HTML report"""

    # Prepare chart data
    top_missing = analysis["top_missing"][:15]
    missing_counts = [analysis["missing_skills"].get(s, 0) for s in top_missing]

    top_matching = sorted(
        analysis["matching_skills"],
        key=analysis["matching_skills"].get,
        reverse=True
    )[:10]
    matching_counts = [analysis["matching_skills"].get(s, 0) for s in top_matching]

    category_labels = list(analysis["category_gaps"].keys())
    category_coverage = [
        round(v["coverage"], 1) for v in analysis["category_gaps"].values()
    ]

    job_rows = ""
    for j in analysis["job_analyses"][:30]:
        match_color = (
            "#22c55e" if j["match_pct"] >= 60
            else "#f59e0b" if j["match_pct"] >= 30
            else "#ef4444"
        )
        url_html = f'<a href="{j["url"]}" target="_blank">View</a>' if j.get("url") else "-"
        missing_tags = " ".join(
            f'<span class="tag tag-missing">{s}</span>'
            for s in j["missing"][:6]
        )
        matched_tags = " ".join(
            f'<span class="tag tag-matched">{s}</span>'
            for s in j["matched"][:6]
        )
        job_rows += f"""
        <tr>
            <td><strong>{j['title']}</strong><br><small>{j['company']}</small></td>
            <td>{j['location']}</td>
            <td><span class="badge" style="background:{match_color}">{j['match_pct']:.0f}%</span></td>
            <td>{matched_tags}</td>
            <td>{missing_tags}</td>
            <td>{url_html}</td>
        </tr>"""

    resume_skill_html = ""
    for cat, skills in resume_skills.items():
        if skills:
            tags = " ".join(f'<span class="tag tag-matched">{s}</span>' for s in skills)
            resume_skill_html += f"<div class='cat-row'><strong>{cat}</strong><div>{tags}</div></div>"

    missing_recs_html = ""
    for skill in top_missing[:10]:
        freq = analysis["missing_skills"].get(skill, 0)
        pct = round(freq / analysis["total_jobs"] * 100)
        missing_recs_html += f"""
        <div class="rec-item">
            <span class="tag tag-missing">{skill}</span>
            <span class="rec-freq">Required in {pct}% of jobs ({freq}/{analysis['total_jobs']})</span>
        </div>"""


    # Generate personalized recommendations
    recommendations = generate_recommendations(analysis, resume_skills)

    rec_cards_html = ""
    priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
    priority_labels = {"high": "High Priority", "medium": "Medium", "low": "Low Priority"}
    for rec in recommendations:
        color = priority_colors.get(rec["priority"], "#94a3b8")
        label = priority_labels.get(rec["priority"], "")
        rec_cards_html += f"""
        <div class="rec-card">
          <div class="rec-header">
            <span class="rec-icon">{rec["icon"]}</span>
            <div>
              <div class="rec-title">{rec["title"]}</div>
              <span class="rec-badge" style="background:{color}22;color:{color};border:1px solid {color}44">{label}</span>
            </div>
          </div>
          <div class="rec-detail">{rec["detail"]}</div>
        </div>"""

    # Experience section data
    resume_years = analysis.get("resume_total_years", 0)
    common_years = analysis.get("most_common_years_required", 0)
    exp_met_pct = round(analysis.get("exp_met_count", 0) / max(analysis["total_jobs"], 1) * 100)
    degree_dist = analysis.get("degree_dist", {})

    degree_html = ""
    if degree_dist:
        degree_items = "".join(
            f'<span class="tag tag-matched">{d}: {c} jobs</span>'
            for d, c in sorted(degree_dist.items(), key=lambda x: -x[1])
        )
        degree_html = f'<div style="margin-bottom:12px"><strong style="color:#94a3b8;font-size:0.8rem">DEGREES MENTIONED IN JOB POSTINGS</strong><div style="margin-top:6px">{degree_items}</div></div>'

    exp_entries_html = ""
    for e in analysis.get("resume_experiences", []):
        months = e.get("duration_months", 0)
        dur = f"{months//12}yr {months%12}mo" if months else ""
        exp_entries_html += f'''
        <div class="exp-entry">
          <div><div class="exp-title">{e.get("title","")}</div>
               <div class="exp-company">{e.get("company","")}</div></div>
          <div style="text-align:right">
            <div class="exp-dates">{e.get("dates","")}</div>
            <div style="color:#94a3b8;font-size:0.8rem">{dur}</div>
          </div>
        </div>'''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Skill Gap Report – {query}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }}
  .hero {{ background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); padding: 48px 32px; text-align: center; border-bottom: 1px solid #334155; }}
  .hero h1 {{ font-size: 2.2rem; font-weight: 700; color: #60a5fa; }}
  .hero p {{ margin-top: 8px; color: #94a3b8; font-size: 1rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }}
  .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; }}
  .stat-card .number {{ font-size: 2rem; font-weight: 700; color: #60a5fa; }}
  .stat-card .label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }}
  .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
  .section h2 {{ font-size: 1.2rem; font-weight: 600; color: #f1f5f9; margin-bottom: 16px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  canvas {{ max-height: 280px; }}
  .tag {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; margin: 2px; }}
  .tag-matched {{ background: #166534; color: #86efac; border: 1px solid #16a34a; }}
  .tag-missing {{ background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; color: white; font-size: 0.8rem; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ background: #0f172a; padding: 10px 8px; text-align: left; color: #94a3b8; font-weight: 600; border-bottom: 1px solid #334155; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #1e293b; vertical-align: top; }}
  tr:hover td {{ background: #243447; }}
  a {{ color: #60a5fa; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .cat-row {{ margin-bottom: 12px; }}
  .cat-row strong {{ display: block; color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
  .rec-item {{ display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #334155; }}
  .rec-freq {{ font-size: 0.82rem; color: #94a3b8; }}
  .match-bar {{ background: #334155; border-radius: 4px; height: 8px; width: 100%; margin-top: 4px; }}
  .match-fill {{ height: 8px; border-radius: 4px; background: linear-gradient(90deg, #3b82f6, #22c55e); }}
  @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>

<div class="hero">
  <h1>📊 Skill Gap Report</h1>
  <p>Query: <strong>{query}</strong> · Location: <strong>{location}</strong> · Generated: {datetime.now().strftime("%B %d, %Y %H:%M")}</p>
</div>

<div class="container">

  <!-- Stats -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="number">{analysis['total_jobs']}</div>
      <div class="label">Jobs Analyzed</div>
    </div>
    <div class="stat-card">
      <div class="number" style="color:#22c55e">{analysis['overall_match_pct']:.0f}%</div>
      <div class="label">Avg Match Rate</div>
    </div>
    <div class="stat-card">
      <div class="number" style="color:#f59e0b">{len(analysis['top_missing'])}</div>
      <div class="label">Skill Gaps Found</div>
    </div>
    <div class="stat-card">
      <div class="number">{sum(len(v) for v in resume_skills.values())}</div>
      <div class="label">Your Skills Detected</div>
    </div>
    <div class="stat-card">
      <div class="number">{analysis['unique_job_skills']}</div>
      <div class="label">Unique Skills in Jobs</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="charts-grid">
    <div class="section">
      <h2>🔴 Top Missing Skills</h2>
      <canvas id="missingChart"></canvas>
    </div>
    <div class="section">
      <h2>🟢 Your Strongest Skills</h2>
      <canvas id="matchingChart"></canvas>
    </div>
  </div>

  <div class="section">
    <h2>📂 Coverage by Category</h2>
    <canvas id="categoryChart"></canvas>
  </div>

  <!-- Recommendations -->
  <div class="section">
    <h2>🎯 Top Skills to Learn</h2>
    {missing_recs_html}
  </div>

  <!-- Resume Skills -->
  <div class="section">
    <h2>✅ Skills Detected in Your Resume</h2>
    {resume_skill_html}
  </div>


  <!-- Recommendations -->
  <div class="section">
    <h2>💡 Personalized Action Plan</h2>
    {rec_cards_html}
  </div>

  <!-- Experience Comparison -->
  <div class="section">
    <h2>💼 Experience & Education Requirements</h2>
    <div class="exp-grid">
      <div class="exp-card">
        <div class="exp-number" style="color:#60a5fa">{resume_years}yr</div>
        <div class="exp-label">Your Experience</div>
      </div>
      <div class="exp-card">
        <div class="exp-number" style="color:#f59e0b">{common_years}yr</div>
        <div class="exp-label">Most Jobs Require</div>
      </div>
      <div class="exp-card">
        <div class="exp-number" style="color:#22c55e">{exp_met_pct}%</div>
        <div class="exp-label">Jobs You Meet Exp. For</div>
      </div>
    </div>
    {degree_html}
    {exp_entries_html}
  </div>

  <!-- Job Table -->
  <div class="section">
    <h2>💼 Job Postings (sorted by match)</h2>
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>Job</th>
          <th>Location</th>
          <th>Match</th>
          <th>Your Skills ✓</th>
          <th>Missing Skills ✗</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
        {job_rows}
      </tbody>
    </table>
    </div>
  </div>

</div>

<script>
const missingLabels = {json.dumps(top_missing)};
const missingData = {json.dumps(missing_counts)};
const matchingLabels = {json.dumps(top_matching)};
const matchingData = {json.dumps(matching_counts)};
const catLabels = {json.dumps(category_labels)};
const catData = {json.dumps(category_coverage)};

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

new Chart(document.getElementById('missingChart'), {{
  type: 'bar',
  data: {{
    labels: missingLabels,
    datasets: [{{ label: 'Job postings requiring this skill', data: missingData, backgroundColor: '#ef4444aa', borderColor: '#ef4444', borderWidth: 1 }}]
  }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: '#334155' }} }}, y: {{ grid: {{ color: '#334155' }} }} }} }}
}});

new Chart(document.getElementById('matchingChart'), {{
  type: 'bar',
  data: {{
    labels: matchingLabels,
    datasets: [{{ label: 'Frequency in job postings', data: matchingData, backgroundColor: '#22c55eaa', borderColor: '#22c55e', borderWidth: 1 }}]
  }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: '#334155' }} }}, y: {{ grid: {{ color: '#334155' }} }} }} }}
}});

new Chart(document.getElementById('categoryChart'), {{
  type: 'bar',
  data: {{
    labels: catLabels,
    datasets: [{{ label: 'Coverage %', data: catData, backgroundColor: catData.map(v => v >= 60 ? '#22c55eaa' : v >= 30 ? '#f59e0baa' : '#ef4444aa'), borderWidth: 1 }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ max: 100, title: {{ display: true, text: 'Coverage (%)' }} }}, x: {{ grid: {{ color: '#334155' }} }} }} }}
}});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
