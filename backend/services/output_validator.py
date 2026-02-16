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

    VALID_GREETINGS = [
        "sehr geehrte",
        "sehr geehrter",
        "moin",
        "hallo",
        "liebe",
        "lieber",
        "guten tag",
    ]

    VALID_CLOSINGS = [
        "mit freundlichen grüßen",
        "viele grüße",
        "beste grüße",
        "herzliche grüße",
        "freundliche grüße",
    ]

    TECH_PATTERNS = [
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

    # Phrases that softly claim familiarity with a skill without outright stating it
    GRAY_ZONE_INDICATORS = [
        "konzepte kenne",
        "konzepte sind mir",
        "konzepte versteh",
        "aus der praxis vertraut",
        "aus der praxis bekannt",
        "aus der praxis geläufig",
        "ist mir vertraut",
        "ist mir bekannt",
        "ist mir nicht fremd",
        "sind mir vertraut",
        "sind mir bekannt",
        "sind mir nicht fremd",
        "grundlagen kenne",
        "grundlagen versteh",
        "grundlagen beherrsch",
        "erste erfahrung",
        "erste berührungspunkte",
        "in kleinen projekten",
        "in kleineren projekten",
        "bereits kennengelernt",
        "schon kennengelernt",
        "nicht ganz neu",
        "nicht ganz unbekannt",
        "nicht unbekannt",
        "verständnis mitbringe",
        "verständnis habe ich",
    ]

    # Markers that indicate an honest disclaimer (should be kept)
    HONEST_MARKERS = [
        "habe ich bisher nicht eingesetzt",
        "bisher nicht eingesetzt",
        "bisher nicht genutzt",
        "noch nicht eingesetzt",
        "noch nicht genutzt",
        "kenne ich bisher nicht",
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

    def _find_non_cv_skills(self, text: str, cv_text: str | None, user_skills: list | None) -> dict[str, str]:
        """Find tech skills mentioned in text but absent from CV.

        Returns a dict mapping lowercase skill name to its original-case form
        as it appeared in the text (e.g. {"react": "React"}).
        """
        known_skills = set()
        if user_skills:
            for skill in user_skills:
                known_skills.add(skill.skill_name.lower())

        cv_lower = cv_text.lower() if cv_text else ""

        # Collect mentioned skills with original casing
        mentioned: dict[str, str] = {}
        for pattern in self.TECH_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1)
                mentioned.setdefault(name.lower(), name)

        return {k: v for k, v in mentioned.items() if k not in known_skills and k not in cv_lower}

    def _check_skill_hallucination(
        self, text: str, cv_text: str | None, user_skills: list | None, result: ValidationResult
    ) -> None:
        """Check if mentioned technical skills actually exist in the CV."""
        non_cv = self._find_non_cv_skills(text, cv_text, user_skills)
        if non_cv:
            result.metrics["potentially_hallucinated_skills"] = list(non_cv.keys())
            result.warnings.append(
                f"Möglicherweise erfundene Skills: {', '.join(non_cv.keys())} — nicht im CV gefunden"
            )

    def fix_gray_zone_claims(self, text: str, cv_text: str | None = None, user_skills: list | None = None) -> str:
        """Remove sentences that softly claim familiarity with non-CV skills.

        The model often generates a correct disclaimer like
        "React habe ich bisher nicht eingesetzt, arbeite mich aber gerne ein."
        but then immediately undermines it with a gray-zone sentence like
        "Die Konzepte sind mir aus der Praxis vertraut."

        This filter removes such undermining sentences from paragraphs that
        discuss non-CV skills. If no honest disclaimer remains after removal,
        a standard one is inserted.
        """
        non_cv = self._find_non_cv_skills(text, cv_text, user_skills)
        if not non_cv:
            return text

        paragraphs = text.split("\n\n")
        fixed_paragraphs = []

        for para in paragraphs:
            para_lower = para.lower()

            # Only process paragraphs that mention a non-CV skill
            mentioned_in_para = {k: v for k, v in non_cv.items() if k in para_lower}
            if not mentioned_in_para:
                fixed_paragraphs.append(para)
                continue

            has_honest_disclaimer = any(m in para_lower for m in self.HONEST_MARKERS)

            # Split into sentences preserving paragraph structure
            sentences = re.split(r"(?<=[.!?])\s+", para)
            kept = []
            removed_any = False

            for sentence in sentences:
                sentence_lower = sentence.lower()
                has_gray_zone = any(indicator in sentence_lower for indicator in self.GRAY_ZONE_INDICATORS)
                if has_gray_zone:
                    logger.info("Gray-zone claim removed: %s", sentence[:80])
                    removed_any = True
                    continue
                kept.append(sentence)

            # If we removed gray-zone sentences and no honest disclaimer
            # exists in the remaining text, add standard disclaimers
            if removed_any and not has_honest_disclaimer:
                for _skill_lower, skill_original in mentioned_in_para.items():
                    disclaimer = f"{skill_original} habe ich bisher nicht eingesetzt," " arbeite mich aber gerne ein."
                    kept.append(disclaimer)

            fixed_paragraphs.append(" ".join(kept))

        return "\n\n".join(fixed_paragraphs)
