# Personal Career Intelligence System (V1)

This repository contains a modular Python 3.11 FastAPI backend named **Career Radar**.

## Project Structure

```text
career_radar/
├── app/
│   ├── main.py
│   ├── jd_analyzer.py
│   ├── resume_matcher.py
│   ├── resume_builder.py
│   ├── job_monitor.py
│   ├── email_alert.py
│   └── models.py
├── data/
│   └── master_resume.json
├── templates/
│   └── resume_template.html
├── requirements.txt
└── Dockerfile
```

## Features

- JD skill extraction using TF-IDF (`scikit-learn`)
- Resume match scoring and missing skill detection
- Relevant project selection from master resume
- Tailored resume generation in HTML and PDF
- RSS job monitoring with SQLite persistence
- Email alerts when match score exceeds threshold
- APScheduler background polling every 6 hours
- `.env` configuration support and structured logging

## Quick Start

### 1) Run locally

```bash
cd career_radar
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) API Endpoints

- `GET /health`
- `POST /analyze-jd`
- `GET /recent-jobs?limit=20`
- `POST /monitor/run` (manual single RSS scan)

Example request:

```bash
curl -X POST http://localhost:8000/analyze-jd \
  -H "Content-Type: application/json" \
  -d '{"job_description":"Looking for Python FastAPI engineer with Docker, NLP, SQL, APScheduler, and SQLite experience."}'
```

### 3) Docker

```bash
cd career_radar
docker build -t career-radar .
docker run --env-file .env -p 8000:8000 career-radar
```

## Environment Variables

See `career_radar/.env.example` for all supported settings:

- `RSS_URLS` comma-separated RSS URLs
- `TARGET_KEYWORDS` keyword filter for job feeds
- `MATCH_THRESHOLD` alert threshold (default 60)
- SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`)
- `ALERT_FROM_EMAIL`, `ALERT_TO_EMAIL`

## Notes

- SQLite DB file is created at runtime at `career_radar/data/jobs.db`.
- Tailored resumes are saved to `career_radar/generated/`.
