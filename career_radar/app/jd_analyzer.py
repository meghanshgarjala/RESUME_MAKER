import logging
import re
from typing import Dict, List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

logger = logging.getLogger(__name__)


class JDAnalyzer:
    def __init__(self) -> None:
        self.stopwords = set(ENGLISH_STOP_WORDS)

    @staticmethod
    def _clean_text(text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9+#.\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    def extract_skills(self, jd_text: str, top_n: int = 20) -> Dict[str, List[str]]:
        if not jd_text or not jd_text.strip():
            logger.warning("Empty JD text provided.")
            return {"keywords": [], "top_skills": []}

        cleaned = self._clean_text(jd_text)
        try:
            vectorizer = TfidfVectorizer(
                stop_words=list(self.stopwords),
                ngram_range=(1, 2),
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.]{1,}\b",
            )
            matrix = vectorizer.fit_transform([cleaned])
            terms = vectorizer.get_feature_names_out()
            scores = matrix.toarray()[0]
            scored_terms = sorted(zip(terms, scores), key=lambda item: item[1], reverse=True)
            top_terms = [term for term, score in scored_terms if score > 0][:top_n]
        except ValueError:
            logger.exception("Unable to extract terms from JD text.")
            top_terms = []

        return {"keywords": top_terms, "top_skills": top_terms}
