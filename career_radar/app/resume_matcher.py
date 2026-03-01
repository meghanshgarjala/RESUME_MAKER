import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class ResumeMatcher:
    def __init__(self, resume_path: str) -> None:
        self.resume_path = Path(resume_path)

    def _load_resume(self) -> Dict[str, Any]:
        if not self.resume_path.exists():
            raise FileNotFoundError(f"Master resume file not found: {self.resume_path}")
        with self.resume_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _normalize(items: List[str]) -> Set[str]:
        return {item.strip().lower() for item in items if item and item.strip()}

    def match(self, jd_keywords: List[str]) -> Dict[str, Any]:
        resume = self._load_resume()

        jd_set = self._normalize(jd_keywords)
        if not jd_set:
            return {
                "match_score": 0.0,
                "matched_skills": [],
                "missing_skills": [],
                "top_projects": [],
            }

        skill_set = self._normalize(resume.get("skills", []))
        project_matches = []

        for project in resume.get("projects", []):
            tags = self._normalize(project.get("skill_tags", []))
            overlap = jd_set.intersection(tags)
            if overlap:
                project_matches.append(
                    {
                        "name": project.get("name"),
                        "description": project.get("description"),
                        "skill_tags": sorted(tags),
                        "matched_keywords": sorted(overlap),
                        "match_count": len(overlap),
                    }
                )
            skill_set.update(tags)

        matched = sorted(jd_set.intersection(skill_set))
        missing = sorted(jd_set.difference(skill_set))
        score = (len(matched) / len(jd_set)) * 100 if jd_set else 0.0

        top_projects = sorted(
            project_matches,
            key=lambda x: (x["match_count"], len(x["matched_keywords"])),
            reverse=True,
        )[:3]

        result = {
            "match_score": round(score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "top_projects": top_projects,
        }
        logger.info("Resume match complete with score %.2f", result["match_score"])
        return result
