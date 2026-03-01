import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.email_alert import EmailAlert
from app.jd_analyzer import JDAnalyzer
from app.job_monitor import JobMonitor
from app.models import JobStore
from app.resume_builder import ResumeBuilder
from app.resume_matcher import ResumeMatcher

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
DB_PATH = DATA_DIR / "jobs.db"
RESUME_PATH = DATA_DIR / "master_resume.json"
GENERATED_DIR = BASE_DIR / "generated"


class JDRequest(BaseModel):
    job_description: str = Field(..., min_length=20, description="Raw job description text")


app = FastAPI(title="Career Radar API", version="1.1.0")

analyzer = JDAnalyzer()
matcher = ResumeMatcher(str(RESUME_PATH))
store = JobStore(str(DB_PATH))
resume_builder = ResumeBuilder(str(TEMPLATE_DIR), str(GENERATED_DIR))
emailer = EmailAlert()

rss_urls: List[str] = [url.strip() for url in os.getenv("RSS_URLS", "").split(",") if url.strip()]
target_keywords = [kw.strip() for kw in os.getenv("TARGET_KEYWORDS", "python,fastapi,ml").split(",")]
match_threshold = float(os.getenv("MATCH_THRESHOLD", "60"))

monitor = JobMonitor(
    rss_urls=rss_urls,
    target_keywords=target_keywords,
    store=store,
    matcher=matcher,
    analyzer=analyzer,
    email_alert=emailer,
    threshold=match_threshold,
)

scheduler = BackgroundScheduler()


@app.on_event("startup")
def startup_event() -> None:
    if rss_urls:
        scheduler.add_job(monitor.run, "interval", hours=6, id="job_monitor", replace_existing=True)
        scheduler.start()
        logger.info("Background scheduler started.")
    else:
        logger.warning("RSS_URLS not set. Job monitor scheduler disabled.")


@app.on_event("shutdown")
def shutdown_event() -> None:
    if scheduler.running:
        scheduler.shutdown()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze-jd")
def analyze_jd(payload: JDRequest) -> Dict[str, Any]:
    analysis = analyzer.extract_skills(payload.job_description)

    try:
        match_data = matcher.match(analysis["top_skills"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Master resume not found") from exc

    try:
        with RESUME_PATH.open("r", encoding="utf-8") as file:
            resume = json.load(file)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Master resume not found") from exc

    context = {
        "name": resume.get("name", "Candidate"),
        "headline": resume.get("headline", "Professional"),
        "skills": match_data["matched_skills"],
        "projects": match_data["top_projects"],
    }
    outputs = resume_builder.generate(context)

    return {
        "analysis": analysis,
        "match": match_data,
        "resume_outputs": outputs,
    }


@app.get("/recent-jobs")
def recent_jobs(limit: int = 20) -> Dict[str, Any]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    return {"jobs": store.recent_jobs(limit)}


@app.post("/monitor/run")
def run_monitor_once() -> Dict[str, str]:
    monitor.run()
    return {"status": "completed"}
