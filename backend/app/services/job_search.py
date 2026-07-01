import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.config import get_settings


settings = get_settings()


class JobSearchAggregator:
    def __init__(self):
        self.sources = [
            AdzunaSearcher(),
            RemotiveSearcher(),
            ArbitraryAPISearcher(),
        ]

    async def search_all(self, query: str, location: str = "India",
                         experience_years: float = 2.6,
                         min_salary_lpa: float = 10.0) -> list[dict]:
        tasks = [source.search(query, location) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        seen_ids = set()
        unique_jobs = []
        for job in all_jobs:
            job_id = job.get("external_id", "")
            if job_id not in seen_ids:
                seen_ids.add(job_id)
                unique_jobs.append(job)

        return unique_jobs

    async def search_by_keywords(self, keywords: list[str], location: str = "India") -> list[dict]:
        all_jobs = []
        for keyword in keywords:
            jobs = await self.search_all(keyword, location)
            all_jobs.extend(jobs)

        seen = set()
        unique = []
        for job in all_jobs:
            eid = job.get("external_id", "")
            if eid not in seen:
                seen.add(eid)
                unique.append(job)
        return unique


class AdzunaSearcher:
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    async def search(self, query: str, location: str = "India") -> list[dict]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            return []

        country = "in" if "india" in location.lower() else "gb"
        url = f"{self.BASE_URL}/{country}/search/1"
        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": 50,
            "what": query,
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return [self._parse_job(j) for j in data.get("results", [])]
        except Exception:
            pass
        return []

    def _parse_job(self, raw: dict) -> dict:
        salary_min = raw.get("salary_min")
        salary_max = raw.get("salary_max")
        return {
            "external_id": f"adzuna_{raw.get('id', '')}",
            "title": raw.get("title", "").replace("<strong>", "").replace("</strong>", ""),
            "company": raw.get("company", {}).get("display_name", "Unknown"),
            "location": raw.get("location", {}).get("display_name", ""),
            "description": raw.get("description", ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_disclosed": salary_min is not None,
            "source": "adzuna",
            "source_url": raw.get("redirect_url", ""),
            "apply_url": raw.get("redirect_url", ""),
            "posted_date": raw.get("created"),
            "job_type": raw.get("contract_type", "full_time"),
        }


class RemotiveSearcher:
    BASE_URL = "https://remotive.com/api/remote-jobs"

    async def search(self, query: str, location: str = "India") -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.BASE_URL, params={"search": query, "limit": 50})
                if resp.status_code == 200:
                    data = resp.json()
                    return [self._parse_job(j) for j in data.get("jobs", [])]
        except Exception:
            pass
        return []

    def _parse_job(self, raw: dict) -> dict:
        salary_text = raw.get("salary", "")
        salary_min, salary_max = self._parse_salary(salary_text)
        return {
            "external_id": f"remotive_{raw.get('id', '')}",
            "title": raw.get("title", ""),
            "company": raw.get("company_name", "Unknown"),
            "location": raw.get("candidate_required_location", "Remote"),
            "description": raw.get("description", ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_disclosed": salary_min is not None,
            "source": "remotive",
            "source_url": raw.get("url", ""),
            "apply_url": raw.get("url", ""),
            "posted_date": raw.get("publication_date"),
            "job_type": raw.get("job_type", "full_time"),
            "remote": True,
        }

    def _parse_salary(self, text: str) -> tuple[float | None, float | None]:
        if not text:
            return None, None
        numbers = re.findall(r'[\d,]+', text.replace(",", ""))
        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1])
        elif len(numbers) == 1:
            return float(numbers[0]), None
        return None, None


class ArbitraryAPISearcher:
    """Searches via RapidAPI JSearch or similar aggregator APIs."""
    BASE_URL = "https://jsearch.p.rapidapi.com/search"

    async def search(self, query: str, location: str = "India") -> list[dict]:
        if not settings.rapidapi_key:
            return []

        headers = {
            "X-RapidAPI-Key": settings.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": f"{query} in {location}",
            "page": "1",
            "num_pages": "3",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.BASE_URL, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return [self._parse_job(j) for j in data.get("data", [])]
        except Exception:
            pass
        return []

    def _parse_job(self, raw: dict) -> dict:
        return {
            "external_id": f"jsearch_{raw.get('job_id', '')}",
            "title": raw.get("job_title", ""),
            "company": raw.get("employer_name", "Unknown"),
            "location": f"{raw.get('job_city', '')}, {raw.get('job_country', '')}",
            "description": raw.get("job_description", ""),
            "requirements": raw.get("job_highlights", {}).get("Qualifications", []),
            "salary_min": raw.get("job_min_salary"),
            "salary_max": raw.get("job_max_salary"),
            "salary_disclosed": raw.get("job_min_salary") is not None,
            "source": "jsearch",
            "source_url": raw.get("job_apply_link", ""),
            "apply_url": raw.get("job_apply_link", ""),
            "posted_date": raw.get("job_posted_at_datetime_utc"),
            "job_type": raw.get("job_employment_type", "FULLTIME"),
            "remote": raw.get("job_is_remote", False),
            "company_type": raw.get("employer_company_type", ""),
        }


def get_search_queries_for_profile(profile: dict) -> list[str]:
    base_queries = [
        "QA Engineer",
        "Software Test Engineer",
        "Automation Test Engineer",
        "SDET",
        "Quality Assurance Engineer",
        "UI Test Engineer",
        "Manual Tester",
        "Test Analyst",
        "QA Automation Engineer",
        "Software Quality Engineer",
    ]

    preferred_roles = profile.get("preferred_roles", [])
    if preferred_roles:
        base_queries.extend(preferred_roles)

    skills = profile.get("skills", [])
    if skills and isinstance(skills[0], dict):
        flat = []
        for cat in skills:
            flat.extend(cat.get("items", []))
        skills = flat

    key_skills = ["Selenium", "Cypress", "Playwright", "Appium", "API Testing"]
    for skill in key_skills:
        if skill.lower() in [s.lower() for s in skills]:
            base_queries.append(f"{skill} Test Engineer")

    return list(set(base_queries))
