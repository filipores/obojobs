"""Validates AI-generated cover letters for quality and correctness."""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of cover letter validation."""

    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class OutputValidator:
    """Validates generated cover letter text against quality criteria."""

    MIN_WORDS = 150
    MAX_WORDS = 500
    MIN_PARAGRAPHS = 2
    MAX_PARAGRAPHS = 8

    # Greetings that indicate a proper salutation
    VALID_GREETINGS = [
        "sehr geehrte",
        "sehr geehrter",
        "moin",
        "hallo",
        "liebe",
        "lieber",
        "guten tag",
    ]

    # Closings that indicate a proper sign-off
    VALID_CLOSINGS = [
        "mit freundlichen grüßen",
        "viele grüße",
        "beste grüße",
        "herzliche grüße",
        "freundliche grüße",
    ]

    def validate(self, text: str, cv_text: str | None = None, user_skills: list | None = None) -> ValidationResult:
        """Run all validation checks on generated cover letter.

        Args:
            text: The generated cover letter text (body only, after briefkopf)
            cv_text: Original CV text for fact-checking (optional)
            user_skills: List of UserSkill objects for skill verification (optional)
        """
        result = ValidationResult()

        self._check_length(text, result)
        self._check_structure(text, result)
        self._check_forbidden_chars(text, result)
        self._check_repetition(text, result)

        if cv_text or user_skills:
            self._check_skill_hallucination(text, cv_text, user_skills, result)

        # Set overall validity
        result.is_valid = len(result.errors) == 0

        return result

    def _check_length(self, text: str, result: ValidationResult) -> None:
        """Check word count is within acceptable range."""
        words = text.split()
        word_count = len(words)
        result.metrics["word_count"] = word_count

        if word_count < self.MIN_WORDS:
            result.errors.append(f"Anschreiben zu kurz ({word_count} Wörter, Minimum: {self.MIN_WORDS})")
        elif word_count > self.MAX_WORDS:
            result.warnings.append(f"Anschreiben etwas lang ({word_count} Wörter, Empfehlung: max {self.MAX_WORDS})")

    def _check_structure(self, text: str, result: ValidationResult) -> None:
        """Check for required structural elements."""
        text_lower = text.lower().strip()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        result.metrics["paragraph_count"] = len(paragraphs)

        # Check greeting (text_lower is already stripped, so its start matches
        # the first paragraph's start -- no need to check both)
        has_greeting = any(text_lower.startswith(g) for g in self.VALID_GREETINGS)
        if not has_greeting:
            result.warnings.append("Keine erkennbare Anrede gefunden")

        # Check closing
        has_closing = any(c in text_lower for c in self.VALID_CLOSINGS)
        if not has_closing:
            result.warnings.append("Keine erkennbare Grußformel gefunden")

        # Check paragraph count
        if len(paragraphs) < self.MIN_PARAGRAPHS:
            result.warnings.append(
                f"Nur {len(paragraphs)} Absatz/Absätze (Empfehlung: {self.MIN_PARAGRAPHS}-{self.MAX_PARAGRAPHS})"
            )
        elif len(paragraphs) > self.MAX_PARAGRAPHS:
            result.warnings.append(f"Zu viele Absätze ({len(paragraphs)}, Empfehlung: max {self.MAX_PARAGRAPHS})")

    def _check_forbidden_chars(self, text: str, result: ValidationResult) -> None:
        """Check for forbidden characters (en-dash, em-dash as punctuation)."""
        if " – " in text or " — " in text:
            result.warnings.append("Gedankenstriche gefunden (sollten durch Kommas ersetzt werden)")

    def _check_repetition(self, text: str, result: ValidationResult) -> None:
        """Check for repetitive sentence starters."""
        sentences = re.split(r"[.!?]\s+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if len(sentences) < 3:
            return

        # Check how many sentences start with "Ich"
        ich_starts = sum(1 for s in sentences if s.startswith("Ich "))
        ich_ratio = ich_starts / len(sentences)
        result.metrics["ich_start_ratio"] = round(ich_ratio, 2)

        if ich_ratio > 0.5:
            result.warnings.append(
                f"{ich_starts} von {len(sentences)} Sätzen beginnen mit 'Ich' — mehr Variation empfohlen"
            )

    def _check_skill_hallucination(
        self, text: str, cv_text: str | None, user_skills: list | None, result: ValidationResult
    ) -> None:
        """Check if mentioned technical skills actually exist in the CV.

        This is a heuristic check — it looks for common tech skills mentioned
        in the cover letter and verifies they appear in the CV or user skills.
        """
        # Build set of known skills from CV and user_skills
        known_skills = set()

        if user_skills:
            for skill in user_skills:
                known_skills.add(skill.skill_name.lower())

        cv_lower = cv_text.lower() if cv_text else ""

        # Common tech skills to check (only flag if mentioned but not in CV)
        tech_patterns = [
            r"\b(React|Angular|Vue\.?js|Next\.?js|Svelte)\b",
            r"\b(Python|Java|Kotlin|Swift|Go|Rust|Ruby|PHP|C\+\+|C#)\b",
            r"\b(TypeScript|JavaScript|Node\.?js)\b",
            r"\b(Docker|Kubernetes|AWS|Azure|GCP)\b",
            r"\b(PostgreSQL|MySQL|MongoDB|Redis)\b",
            r"\b(Spring Boot|Django|Flask|Express|FastAPI)\b",
            r"\b(TensorFlow|PyTorch|Scikit-learn)\b",
            r"\b(Git|Jenkins|GitHub Actions|CI/CD)\b",
            r"\b(Scrum|Kanban|Agile|SAFe)\b",
            r"\b(SAP|Salesforce|Jira|Confluence)\b",
        ]

        mentioned_skills = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentioned_skills.update(m.lower() for m in matches)

        # Check each mentioned skill against CV and user skills.
        # mentioned_skills is already lowercased, so direct comparison works.
        hallucinated = []
        for skill in mentioned_skills:
            if skill in known_skills:
                continue
            if cv_lower and skill in cv_lower:
                continue
            hallucinated.append(skill)

        if hallucinated:
            result.metrics["potentially_hallucinated_skills"] = hallucinated
            result.warnings.append(f"Möglicherweise erfundene Skills: {', '.join(hallucinated)} — nicht im CV gefunden")
