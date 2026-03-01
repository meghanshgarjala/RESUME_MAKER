import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class ResumeBuilder:
    def __init__(self, templates_dir: str, output_dir: str = "generated") -> None:
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate(self, context: Dict[str, Any]) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"tailored_resume_{timestamp}.html"
        pdf_path = self.output_dir / f"tailored_resume_{timestamp}.pdf"

        template = self.env.get_template("resume_template.html")
        rendered_html = template.render(**context)
        html_path.write_text(rendered_html, encoding="utf-8")

        self._build_pdf(context, pdf_path)
        logger.info("Generated resume outputs: %s and %s", html_path, pdf_path)
        return {"html_path": str(html_path), "pdf_path": str(pdf_path)}

    def _build_pdf(self, context: Dict[str, Any], pdf_path: Path) -> None:
        pdf = canvas.Canvas(str(pdf_path), pagesize=LETTER)
        width, height = LETTER
        y = height - 50

        def draw_line(text: str, step: int = 18) -> None:
            nonlocal y
            pdf.drawString(50, y, text)
            y -= step

        draw_line(context.get("name", "Candidate"), 24)
        draw_line(context.get("headline", "Tailored Resume"), 20)
        draw_line("Skills:")
        for skill in context.get("skills", []):
            draw_line(f"- {skill}")

        draw_line("Projects:")
        for project in context.get("projects", []):
            draw_line(f"* {project.get('name', 'Project')}")
            draw_line(f"  {project.get('description', '')}", step=16)

        pdf.save()
