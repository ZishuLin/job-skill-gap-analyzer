"""
Job scrapers - uses multiple free public APIs, no API key required.

Sources (tried in order):
  1. Arbeitnow API     - free, no key, great for tech jobs
  2. RemoteOK API      - free, no key, remote tech jobs
  3. LinkedIn HTML     - public search pages (may need session cookie)

Indeed is NOT used - they have blocked all automated access.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    source: str
    url: str = ""
    salary: str = ""


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

LINKEDIN_COOKIE = os.environ.get("LINKEDIN_SESSION_COOKIE", "")


def _sleep(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))


# ─────────────────────────────────────────────────────────────────────────────
# Arbeitnow (https://www.arbeitnow.com/api) — free, no key
# ─────────────────────────────────────────────────────────────────────────────

class ArbeitnowScraper:
    API_URL = "https://arbeitnow.com/api/job-board-api"

    def search(self, query: str, location: str, limit: int = 20) -> List[Job]:
        jobs = []
        page = 1
        max_pages = 3  # avoid 429 rate limiting

        while len(jobs) < limit and page <= max_pages:
            try:
                resp = requests.get(
                    self.API_URL,
                    params={"search": query, "page": page},
                    headers=HEADERS,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json().get("data", [])
                if not data:
                    break

                for item in data:
                    if len(jobs) >= limit:
                        break
                    # Filter by location keyword if specified
                    job_location = item.get("location", "")
                    if location.lower() not in ("canada", "remote", "") and \
                       location.lower() not in job_location.lower() and \
                       "remote" not in job_location.lower():
                        continue  # skip non-matching locations

                    desc = BeautifulSoup(item.get("description", ""), "html.parser").get_text(" ", strip=True)
                    tags = item.get("tags", [])

                    jobs.append(Job(
                        title=item.get("title", "Unknown"),
                        company=item.get("company_name", "Unknown"),
                        location=job_location or "Remote",
                        description=(desc + " " + " ".join(tags))[:2500],
                        source="Arbeitnow",
                        url=item.get("url", ""),
                        salary=item.get("salary", ""),
                    ))

                page += 1
                _sleep()

            except Exception as e:
                print(f"Arbeitnow error: {e}")
                break

        return jobs


# ─────────────────────────────────────────────────────────────────────────────
# RemoteOK (https://remoteok.com/api) — free, no key, remote jobs only
# ─────────────────────────────────────────────────────────────────────────────

class RemoteOKScraper:
    API_URL = "https://remoteok.com/api"

    def search(self, query: str, location: str, limit: int = 20) -> List[Job]:
        jobs = []
        try:
            resp = requests.get(
                self.API_URL,
                params={"tag": query.lower().replace(" ", "-")},
                headers={**HEADERS, "Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            # First item is metadata, skip it
            if data and isinstance(data[0], dict) and "legal" in data[0]:
                data = data[1:]

            for item in data:
                if len(jobs) >= limit:
                    break
                if not isinstance(item, dict):
                    continue
                desc = BeautifulSoup(item.get("description", ""), "html.parser").get_text(" ", strip=True)
                tags = item.get("tags", [])

                jobs.append(Job(
                    title=item.get("position", "Unknown"),
                    company=item.get("company", "Unknown"),
                    location=item.get("location", "Remote"),
                    description=(desc + " " + " ".join(tags or []))[:2500],
                    source="RemoteOK",
                    url=item.get("url", ""),
                    salary=item.get("salary", ""),
                ))

        except Exception as e:
            print(f"RemoteOK error: {e}")

        return jobs


# ─────────────────────────────────────────────────────────────────────────────
# LinkedIn public HTML scraper
# ─────────────────────────────────────────────────────────────────────────────

class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs/search"

    def search(self, query: str, location: str, limit: int = 20) -> List[Job]:
        jobs = []
        start = 0

        while len(jobs) < limit:
            params = {
                "keywords": query,
                "location": location,
                "start": start,
                "f_TPR": "r2592000",
            }
            try:
                cookies = {"li_at": LINKEDIN_COOKIE} if LINKEDIN_COOKIE else {}
                resp = requests.get(
                    self.BASE_URL, params=params, headers=HEADERS,
                    cookies=cookies, timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
                if not cards:
                    break

                for card in cards:
                    if len(jobs) >= limit:
                        break
                    job = self._parse_card(card)
                    if job:
                        jobs.append(job)

                start += 25
                _sleep()

            except Exception as e:
                print(f"LinkedIn scrape error: {e}")
                break

        return jobs

    def _parse_card(self, card) -> Optional[Job]:
        try:
            title_el = card.find("h3")
            title = title_el.get_text(strip=True) if title_el else "Unknown"
            company_el = card.find("h4")
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            location_el = card.find("span", class_=re.compile(r"location"))
            location = location_el.get_text(strip=True) if location_el else ""
            link_el = card.find("a", href=True)
            url = link_el["href"].split("?")[0] if link_el else ""
            if title == "Unknown":
                return None
            return Job(title=title, company=company, location=location,
                       description=f"{title} at {company}", source="LinkedIn", url=url)
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Unified scraper used by main.py
# ─────────────────────────────────────────────────────────────────────────────

class IndeedScraper:
    """
    Indeed has blocked all automated scraping.
    This class now routes to Arbeitnow + RemoteOK instead.
    """
    def search(self, query: str, location: str, limit: int = 20) -> List[Job]:
        jobs = []

        # Try Arbeitnow first
        try:
            arb = ArbeitnowScraper()
            arb_jobs = arb.search(query, location, limit=limit)
            jobs.extend(arb_jobs)
            print(f"  Arbeitnow: {len(arb_jobs)} jobs")
        except Exception as e:
            print(f"  Arbeitnow failed: {e}")

        # Fill remaining from RemoteOK
        if len(jobs) < limit:
            try:
                rok = RemoteOKScraper()
                rok_jobs = rok.search(query, location, limit=limit - len(jobs))
                jobs.extend(rok_jobs)
                print(f"  RemoteOK: {len(rok_jobs)} jobs")
            except Exception as e:
                print(f"  RemoteOK failed: {e}")

        return jobs[:limit]
