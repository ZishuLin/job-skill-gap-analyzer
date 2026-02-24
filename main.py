#!/usr/bin/env python3
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from scraper import IndeedScraper, LinkedInScraper
from resume_parser import parse_resume_pdf, parse_work_experience, get_total_experience_years
from analyzer import analyze_skill_gap
from report_generator import generate_html_report

console = Console()


@click.group()
def cli():
    """Job Skill Gap Analyzer"""
    pass


@cli.command()
@click.option('--query', '-q', required=True)
@click.option('--location', '-l', default='Canada')
@click.option('--resume', '-r', required=True, type=click.Path(exists=True))
@click.option('--limit', '-n', default=20)
@click.option('--source', '-s', default='indeed', type=click.Choice(['indeed', 'linkedin', 'both']))
@click.option('--output', '-o', default='skill_gap_report.html')
def analyze(query, location, resume, limit, source, output):
    """Analyze skill gaps between your resume and job postings"""
    console.print(f"\n[bold cyan]Job Skill Gap Analyzer[/bold cyan]")
    console.print(f"Searching: [yellow]{query}[/yellow] in [yellow]{location}[/yellow]\n")

    jobs = []
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:

        if source in ('indeed', 'both'):
            task = progress.add_task("Scraping jobs...", total=None)
            try:
                scraper = IndeedScraper()
                found = scraper.search(query, location, limit=limit // 2 if source == 'both' else limit)
                jobs.extend(found)
                progress.update(task, description=f"[green]✓ Indeed: {len(found)} jobs found[/green]")
            except Exception as e:
                progress.update(task, description=f"[red]✗ Scraping failed: {e}[/red]")
            progress.stop_task(task)

        if source in ('linkedin', 'both'):
            task = progress.add_task("Scraping LinkedIn...", total=None)
            try:
                scraper = LinkedInScraper()
                found = scraper.search(query, location, limit=limit // 2 if source == 'both' else limit)
                jobs.extend(found)
                progress.update(task, description=f"[green]✓ LinkedIn: {len(found)} jobs found[/green]")
            except Exception as e:
                progress.update(task, description=f"[red]✗ LinkedIn failed: {e}[/red]")
            progress.stop_task(task)

        if not jobs:
            console.print("[bold red]No jobs found. Try a broader location like 'Canada'.[/bold red]")
            return

        task = progress.add_task("Parsing resume...", total=None)
        resume_skills = parse_resume_pdf(resume)
        experiences = parse_work_experience(resume)
        total_years = get_total_experience_years(experiences)
        progress.update(task, description=f"[green]✓ Resume: {sum(len(v) for v in resume_skills.values())} skills, {total_years}yr experience[/green]")
        progress.stop_task(task)

        task = progress.add_task("Analyzing...", total=None)
        analysis = analyze_skill_gap(resume_skills, jobs, experiences, total_years)
        progress.update(task, description="[green]✓ Analysis complete[/green]")
        progress.stop_task(task)

        task = progress.add_task("Generating report...", total=None)
        generate_html_report(analysis, resume_skills, jobs, query, location, output)
        progress.update(task, description=f"[green]✓ Report: {output}[/green]")
        progress.stop_task(task)

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"Analyzed [cyan]{len(jobs)}[/cyan] jobs")
    console.print(f"Skill match: [cyan]{analysis['overall_match_pct']:.1f}%[/cyan]")
    console.print(f"Top missing: [red]{', '.join(analysis['top_missing'][:5])}[/red]")
    console.print(f"\nReport: [bold]{output}[/bold]")


@cli.command()
@click.argument('resume', type=click.Path(exists=True))
def parse(resume):
    """Parse skills and experience from your resume PDF"""
    from rich.table import Table
    console.print(f"\n[bold cyan]Parsing:[/bold cyan] {resume}\n")

    skills = parse_resume_pdf(resume)
    table = Table(title="Detected Skills")
    table.add_column("Category", style="cyan")
    table.add_column("Skills", style="white")
    for cat, skill_list in skills.items():
        if skill_list:
            table.add_row(cat, ", ".join(skill_list))
    console.print(table)

    experiences = parse_work_experience(resume)
    if experiences:
        console.print(f"\n[bold cyan]Work Experience[/bold cyan]")
        exp_table = Table()
        exp_table.add_column("Title", style="white")
        exp_table.add_column("Company", style="cyan")
        exp_table.add_column("Dates", style="yellow")
        exp_table.add_column("Duration", style="green")
        for e in experiences:
            months = e.get("duration_months", 0)
            dur = f"{months//12}yr {months%12}mo" if months else "?"
            exp_table.add_row(e.get("title", ""), e.get("company", ""), e.get("dates", ""), dur)
        console.print(exp_table)
        total = get_total_experience_years(experiences)
        console.print(f"\n[bold]Total experience: {total} years[/bold]")
    else:
        console.print("\n[yellow]No work experience detected.[/yellow]")


@cli.command()
def init():
    """First-time setup: create .env file with your API keys"""
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        console.print("[yellow].env already exists.[/yellow]")
        overwrite = click.confirm("Overwrite it?", default=False)
        if not overwrite:
            return

    console.print("\n[bold cyan]Creating .env file[/bold cyan]")
    console.print("Press Enter to skip any optional key.\n")

    gemini_key = click.prompt(
        "Groq API key (free at console.groq.com -> API Keys)",
        default="", show_default=False,
    ).strip()

    linkedin_cookie = click.prompt(
        "LinkedIn session cookie (optional)",
        default="", show_default=False,
    ).strip()

    lines = [
        "# Auto-generated by: python main.py init",
        "# This file is in .gitignore and will NOT be uploaded to GitHub",
        "",
        "# Groq API key (free)",
        f"GROQ_API_KEY={gemini_key}",
        "",
        "# LinkedIn session cookie (optional)",
        f"LINKEDIN_SESSION_COOKIE={linkedin_cookie}",
    ]

    env_path.write_text("\n".join(lines))
    console.print(f"\n[bold green]Done![/bold green] Created [cyan]{env_path}[/cyan]")

    if gemini_key:
        console.print("\nYou can now run:")
        console.print('  [yellow]python main.py tailor --query "Software Engineer" --location "Canada" --resume resume.pdf[/yellow]')
    else:
        console.print("\n[yellow]No Gemini key set — run init again to add one.[/yellow]")


@cli.command()
@click.option('--resume', '-r', required=True, type=click.Path(exists=True))
@click.option('--query', '-q', required=True, help='Job title you are targeting')
@click.option('--location', '-l', default='Canada')
@click.option('--limit', '-n', default=10)
@click.option('--output', '-o', default='tailored_resume.docx')
def tailor(resume, query, location, limit, output):
    """Tailor your resume to a specific job using AI"""
    import json, subprocess, os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")

    from tailor import tailor_resume

    console.print(f"\n[bold cyan]AI Resume Tailoring[/bold cyan]")
    console.print(f"Target: [yellow]{query}[/yellow] in [yellow]{location}[/yellow]\n")

    if not os.environ.get("GROQ_API_KEY"):
        console.print("[bold red]Error:[/bold red] Groq API key not found.")
        console.print("Run [yellow]python main.py init[/yellow] to set it up.")
        console.print("  Get a free key at https://console.groq.com")
        return

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:

        task = progress.add_task("Scraping job postings...", total=None)
        scraper = IndeedScraper()
        jobs = scraper.search(query, location, limit=limit)
        progress.update(task, description=f"[green]✓ Found {len(jobs)} jobs[/green]")
        progress.stop_task(task)

        if not jobs:
            console.print("[red]No jobs found. Try a broader location like 'Canada'.[/red]")
            return

        task = progress.add_task("Parsing resume...", total=None)
        resume_skills = parse_resume_pdf(resume)
        experiences = parse_work_experience(resume)
        total_years = get_total_experience_years(experiences)
        progress.update(task, description="[green]✓ Resume parsed[/green]")
        progress.stop_task(task)

        task = progress.add_task("Analyzing skill gaps...", total=None)
        analysis = analyze_skill_gap(resume_skills, jobs, experiences, total_years)
        best_job = analysis["job_analyses"][0]
        progress.update(task, description=f"[green]✓ Best match: {best_job['title']} at {best_job['company']} ({best_job['match_pct']:.0f}%)[/green]")
        progress.stop_task(task)

        task = progress.add_task("Tailoring with AI...", total=None)
        try:
            best_job_obj = next(j for j in jobs if j.title == best_job["title"] and j.company == best_job["company"])
            tailored = tailor_resume(
                resume_pdf_path=resume,
                job_title=best_job["title"],
                job_description=best_job_obj.description,
                missing_skills=best_job["missing"],
                matched_skills=best_job["matched"],
            )
            progress.update(task, description="[green]✓ AI tailoring complete[/green]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ AI error: {e}[/red]")
            progress.stop_task(task)
            return
        progress.stop_task(task)

        task = progress.add_task("Building Word document...", total=None)
        try:
            from resume_parser import extract_text_from_pdf
            raw = extract_text_from_pdf(resume)
            raw_lines = raw.split('\n')
            name = raw_lines[0].strip()
            contact = raw_lines[1].strip() if len(raw_lines) > 1 else ""

            resume_data = {
                "name": name,
                "contact": contact,
                "education": [
                    {"degree": "Master of Computer Science", "school": "Dalhousie University",
                     "dates": "Expected April 2026", "note": "GPA: 3.89/4.3 · Sexton Scholar Award"},
                    {"degree": "Bachelor of Computer Science", "school": "Dalhousie University",
                     "dates": "Graduated May 2023", "note": ""},
                ],
                "additional": [
                    "Languages: English (Fluent), Mandarin Chinese (Native)",
                    "Available for 12-week Summer 2026 internship; willing to relocate to San Francisco",
                    "LeetCode: Active problem solver; practicing algorithms and data structures regularly",
                ],
                "tailored": tailored,
            }

            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resume_data.json')
            with open(data_path, 'w') as f:
                json.dump(resume_data, f, ensure_ascii=False)

            js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_resume.js')
            result = subprocess.run(['node', js_path, output, data_path], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            progress.update(task, description=f"[green]✓ Saved: {output}[/green]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ DOCX error: {e}[/red]")
            progress.stop_task(task)
            return
        progress.stop_task(task)

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"Tailored for: [cyan]{best_job['title']}[/cyan] at [cyan]{best_job['company']}[/cyan]")
    console.print(f"Match rate: [cyan]{best_job['match_pct']:.0f}%[/cyan]")
    if tailored.get("changes_made"):
        console.print("\n[bold]Changes made:[/bold]")
        for change in tailored["changes_made"]:
            console.print(f"  - {change}")
    console.print(f"\nOutput: [bold]{output}[/bold]")


if __name__ == '__main__':
    cli()