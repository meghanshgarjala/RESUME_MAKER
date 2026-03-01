import json
import logging
from typing import List

import feedparser

from app.email_alert import EmailAlert
from app.jd_analyzer import JDAnalyzer
from app.models import JobStore
from app.resume_matcher import ResumeMatcher

logger = logging.getLogger(__name__)


class JobMonitor:
    def __init__(
        self,
        rss_urls: List[str],
        target_keywords: List[str],
        store: JobStore,
        matcher: ResumeMatcher,
        analyzer: JDAnalyzer,
        email_alert: EmailAlert,
        threshold: float = 60.0,
    ) -> None:
        self.rss_urls = rss_urls
        self.target_keywords = [kw.lower() for kw in target_keywords if kw.strip()]
        self.store = store
        self.matcher = matcher
        self.analyzer = analyzer
        self.email_alert = email_alert
        self.threshold = threshold

    def run(self) -> None:
        logger.info("Starting job monitor scan.")
        for url in self.rss_urls:
            try:
                feed = feedparser.parse(url)
            except Exception:
                logger.exception("Failed to parse RSS feed: %s", url)
                continue

            if getattr(feed, "bozo", False):
                logger.warning("Feed parser reported malformed feed for %s", url)

            for entry in feed.entries:
                title = entry.get("title", "")
                description = entry.get("summary", "")
                haystack = f"{title} {description}".lower()

                if self.target_keywords and not any(k in haystack for k in self.target_keywords):
                    continue

                analysis = self.analyzer.extract_skills(haystack)
                match = self.matcher.match(analysis["top_skills"])

                job = {
                    "guid": entry.get("id") or entry.get("link") or title,
                    "title": title,
                    "company": entry.get("author", "Unknown"),
                    "location": entry.get("location", "Unknown"),
                    "description": description,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "match_score": match["match_score"],
                    "missing_skills": json.dumps(match["missing_skills"]),
                }

                is_new = self.store.save_job(job)
                if is_new and match["match_score"] >= self.threshold:
                    self.email_alert.send_job_alert(job)
        logger.info("Job monitor scan completed.")
