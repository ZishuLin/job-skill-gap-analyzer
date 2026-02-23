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
    """🔍 Job Skill Gap Analyzer"""
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
    console.print(f"\n[bold cyan]🚀 Job Skill Gap Analyzer[/bold cyan]")
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

    console.print(f"\n[bold green]✅ Done![/bold green]")
    console.print(f"📊 Analyzed [cyan]{len(jobs)}[/cyan] jobs")
    console.print(f"🎯 Skill match: [cyan]{analysis['overall_match_pct']:.1f}%[/cyan]")
    console.print(f"💼 Experience: [cyan]{total_years}yr[/cyan] (jobs want avg [cyan]{analysis['most_common_years_required']}yr[/cyan])")
    console.print(f"📋 Top missing: [red]{', '.join(analysis['top_missing'][:5])}[/red]")
    console.print(f"\n📄 Report: [bold]{output}[/bold]")

@cli.command()
@click.argument('resume', type=click.Path(exists=True))
def parse(resume):
    """Parse skills and experience from your resume PDF"""
    from rich.table import Table
    console.print(f"\n[bold cyan]📄 Parsing:[/bold cyan] {resume}\n")

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
        console.print(f"\n[bold cyan]💼 Work Experience[/bold cyan]")
        exp_table = Table()
        exp_table.add_column("Title", style="white")
        exp_table.add_column("Company", style="cyan")
        exp_table.add_column("Dates", style="yellow")
        exp_table.add_column("Duration", style="green")
        for e in experiences:
            months = e.get("duration_months", 0)
            dur = f"{months//12}yr {months%12}mo" if months else "?"
            exp_table.add_row(e.get("title",""), e.get("company",""), e.get("dates",""), dur)
        console.print(exp_table)
        total = get_total_experience_years(experiences)
        console.print(f"\n[bold]Total experience: {total} years[/bold]")
    else:
        console.print("\n[yellow]No work experience detected. Check resume format.[/yellow]")

if __name__ == '__main__':
    cli()