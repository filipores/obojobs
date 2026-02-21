"""
Interview Generator Service - Generates interview questions based on job posting and user profile using Claude API.
"""

import json
import logging
import time

from anthropic import Anthropic

from config import config

logger = logging.getLogger(__name__)


class InterviewGenerator:
    """Service to generate interview questions for job applications using Claude API."""

    VALID_TYPES = ["behavioral", "technical", "situational", "company_specific", "salary_negotiation"]
    VALID_DIFFICULTIES = ["easy", "medium", "hard"]

    # German interview culture classics
    GERMAN_CLASSICS = [
        "Wo siehst du dich in 5 Jahren?",
        "Was sind deine Stärken und Schwächen?",
        "Warum willst du bei uns arbeiten?",
        "Warum sollten wir dich einstellen?",
        "Erzähl uns etwas über dich.",
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def generate_questions(
        self,
        job_text: str,
        firma: str,
        position: str,
        user_skills: list[dict] | None = None,
        question_count: int = 12,
        retry_count: int = 3,
    ) -> list[dict]:
        """
        Generate interview questions based on job posting and user profile.

        Args:
            job_text: The text content of the job posting
            firma: Company name
            position: Job position title
            user_skills: Optional list of user skills for personalized questions
            question_count: Number of questions to generate (default 12, min 10, max 15)
            retry_count: Number of retries on failure

        Returns:
            List of question dictionaries with keys:
            - question_text: The interview question
            - question_type: One of behavioral, technical, situational, company_specific, salary_negotiation
            - difficulty: easy, medium, or hard
            - sample_answer: A suggested answer approach
        """
        # Ensure question count is within bounds
        question_count = max(10, min(15, question_count))

        prompt = self._create_generation_prompt(job_text, firma, position, user_skills, question_count)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.7,  # Slightly higher for creative variety
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                questions = self._parse_questions_response(response_text)

                # Ensure we have enough questions
                if len(questions) >= 10:
                    return questions[:15]  # Cap at 15

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        "Interview-Fragen Generierung fehlgeschlagen (Versuch %s/%s): %s", attempt + 1, retry_count, e
                    )
                    time.sleep(2)
                else:
                    logger.error("Interview-Fragen Generierung fehlgeschlagen nach %s Versuchen: %s", retry_count, e)
                    # Return fallback questions
                    return self._get_fallback_questions(firma, position)

        return self._get_fallback_questions(firma, position)

    def _create_generation_prompt(
        self, job_text: str, firma: str, position: str, user_skills: list[dict] | None, question_count: int
    ) -> str:
        """Create the prompt for interview question generation."""

        skills_section = ""
        if user_skills:
            skills_list = ", ".join([s.get("skill_name", "") for s in user_skills[:15] if s.get("skill_name")])
            skills_section = f"""
BEWERBER-SKILLS:
{skills_list}

Nutze diese Skills um personalisierte technische Fragen zu stellen, die auf die Erfahrung des Bewerbers eingehen.
"""

        return f"""Du bist ein erfahrener HR-Manager in Deutschland, der Interview-Fragen für Vorstellungsgespräche vorbereitet.

POSITION: {position}
UNTERNEHMEN: {firma}

STELLENANZEIGE:
{job_text[:5000]}
{skills_section}
Generiere {question_count} Interview-Fragen für ein deutsches Vorstellungsgespräch. Berücksichtige die deutsche Interview-Kultur:
- Informeller Ton, du-Form
- Direkte aber höfliche Fragen
- Fokus auf Qualifikationen und Berufserfahrung
- Typische deutsche Klassiker einbauen (z.B. "Wo siehst du dich in 5 Jahren?")

Für jede Frage gib an:

1. question_text: Die Interview-Frage auf Deutsch, in du-Form

2. question_type: Die Kategorie der Frage:
   - "behavioral": Verhaltensfragen über vergangene Erfahrungen ("Erzähl von einer Situation, wo...")
   - "technical": Fachliche Fragen zur Position und Skills
   - "situational": Hypothetische Szenarien ("Was würdest du tun, wenn...")
   - "company_specific": Fragen zum Unternehmen und zur Motivation ("Warum willst du bei uns...")
   - "salary_negotiation": Fragen zu Gehalt und Konditionen

3. difficulty: Schwierigkeitsgrad
   - "easy": Einfache Einstiegsfragen
   - "medium": Standard-Interviewfragen
   - "hard": Anspruchsvolle, tiefgehende Fragen

4. sample_answer: Eine Beispiel-Antwort-Strategie (2-3 Sätze), die dem Bewerber hilft sich vorzubereiten. Gib Tipps WIE man antworten sollte, nicht eine wortwörtliche Antwort.

WICHTIG:
- Antworte NUR mit einem JSON-Array. Keine anderen Texte.
- Mische verschiedene Fragentypen für ein realistisches Interview
- Beziehe Fragen auf die konkrete Stelle bei {firma}
- Mindestens 2-3 behavioral Fragen
- Mindestens 2-3 technical Fragen passend zur Position
- 1-2 Fragen zu Gehalt/Konditionen

Beispiel-Format:
[
  {{
    "question_text": "Wo siehst du dich beruflich in fünf Jahren?",
    "question_type": "behavioral",
    "difficulty": "medium",
    "sample_answer": "Zeige Ambition ohne unrealistisch zu wirken. Verknüpfe deine Ziele mit dem Unternehmen und der Position. Betone Lernbereitschaft und Entwicklungswünsche."
  }},
  {{
    "question_text": "Welche Erfahrungen hast du mit [Technologie X]?",
    "question_type": "technical",
    "difficulty": "medium",
    "sample_answer": "Nenne konkrete Projekte und Ergebnisse. Quantifiziere wenn möglich. Zeige kontinuierliches Lernen in diesem Bereich."
  }}
]

Generiere jetzt {question_count} Interview-Fragen als JSON-Array:"""

    def _parse_questions_response(self, response_text: str) -> list[dict[str, str]]:
        """Parse the Claude response into a list of question dictionaries."""
        text = response_text.strip()

        # Find JSON array bounds
        start_idx = text.find("[")
        end_idx = text.rfind("]")

        if start_idx == -1 or end_idx == -1:
            logger.warning("Keine JSON-Struktur in der Antwort gefunden")
            return []

        json_text = text[start_idx : end_idx + 1]

        try:
            questions = json.loads(json_text)

            # Validate and clean questions
            valid_questions = []
            for q in questions:
                if not isinstance(q, dict):
                    continue

                question_text = q.get("question_text", "").strip()
                question_type = q.get("question_type", "").strip().lower()
                difficulty = q.get("difficulty", "medium").strip().lower()
                sample_answer = q.get("sample_answer", "").strip()

                # Skip invalid entries
                if not question_text:
                    continue

                # Validate question type
                if question_type not in self.VALID_TYPES:
                    # Try to map common variations
                    type_mapping = {
                        "verhaltens": "behavioral",
                        "verhalten": "behavioral",
                        "technisch": "technical",
                        "fachlich": "technical",
                        "situations": "situational",
                        "hypothetisch": "situational",
                        "unternehmen": "company_specific",
                        "firma": "company_specific",
                        "motivation": "company_specific",
                        "gehalt": "salary_negotiation",
                        "salary": "salary_negotiation",
                        "konditionen": "salary_negotiation",
                    }
                    question_type = type_mapping.get(question_type, "behavioral")

                # Validate difficulty
                if difficulty not in self.VALID_DIFFICULTIES:
                    difficulty = "medium"

                valid_questions.append(
                    {
                        "question_text": question_text,
                        "question_type": question_type,
                        "difficulty": difficulty,
                        "sample_answer": sample_answer
                        or "Bereite eine konkrete Antwort mit Beispielen aus deiner Berufserfahrung vor.",
                    }
                )

            return valid_questions

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error: %s", e)
            return []

    def _get_fallback_questions(self, firma: str, position: str) -> list[dict[str, str]]:
        """Return fallback questions if API call fails."""
        return [
            {
                "question_text": "Erzähl uns etwas über dich.",
                "question_type": "behavioral",
                "difficulty": "easy",
                "sample_answer": "Fasse deinen Werdegang in 2-3 Minuten zusammen. Fokussiere auf relevante Erfahrungen für diese Position.",
            },
            {
                "question_text": f"Warum möchtest du bei {firma} arbeiten?",
                "question_type": "company_specific",
                "difficulty": "medium",
                "sample_answer": "Zeige, dass du dich über das Unternehmen informiert hast. Verknüpfe deine Ziele mit der Unternehmenskultur und Mission.",
            },
            {
                "question_text": "Was sind deine größten Stärken?",
                "question_type": "behavioral",
                "difficulty": "easy",
                "sample_answer": "Nenne 2-3 Stärken mit konkreten Beispielen. Wähle Stärken, die für die Position relevant sind.",
            },
            {
                "question_text": "Was ist deine größte Schwäche?",
                "question_type": "behavioral",
                "difficulty": "medium",
                "sample_answer": "Nenne eine echte Schwäche, die du aktiv verbesserst. Zeige Selbstreflexion und Entwicklungsbereitschaft.",
            },
            {
                "question_text": "Wo siehst du dich in fünf Jahren?",
                "question_type": "behavioral",
                "difficulty": "medium",
                "sample_answer": "Zeige Ambition und langfristiges Engagement. Verknüpfe deine Karriereziele mit dem Unternehmen.",
            },
            {
                "question_text": f"Welche Erfahrungen qualifizieren dich für die Position als {position}?",
                "question_type": "technical",
                "difficulty": "medium",
                "sample_answer": "Nenne 2-3 konkrete Erfahrungen und Erfolge aus bisherigen Positionen, die direkt auf die neue Rolle übertragbar sind.",
            },
            {
                "question_text": "Erzähl von einer herausfordernden Situation im Beruf und wie du diese gemeistert hast.",
                "question_type": "behavioral",
                "difficulty": "hard",
                "sample_answer": "Nutze die STAR-Methode: Situation, Task, Action, Result. Wähle ein Beispiel mit positivem Ausgang.",
            },
            {
                "question_text": "Wie gehst du mit Konflikten im Team um?",
                "question_type": "situational",
                "difficulty": "medium",
                "sample_answer": "Beschreibe deinen konstruktiven Ansatz zur Konfliktlösung. Betone Kommunikation und Kompromissbereitschaft.",
            },
            {
                "question_text": "Was weißt du über unser Unternehmen?",
                "question_type": "company_specific",
                "difficulty": "easy",
                "sample_answer": "Zeige, dass du recherchiert hast: Branche, Produkte, aktuelle Entwicklungen, Unternehmenskultur.",
            },
            {
                "question_text": "Was sind deine Gehaltsvorstellungen?",
                "question_type": "salary_negotiation",
                "difficulty": "hard",
                "sample_answer": "Nenne eine recherchierte Gehaltsspanne. Begründe mit deiner Erfahrung und Qualifikation. Zeige Verhandlungsbereitschaft.",
            },
            {
                "question_text": "Hast du Fragen an uns?",
                "question_type": "company_specific",
                "difficulty": "easy",
                "sample_answer": "Stelle 2-3 vorbereitete Fragen zur Rolle, zum Team oder zur Unternehmenskultur. Zeige echtes Interesse.",
            },
            {
                "question_text": "Wann könntest du bei uns anfangen?",
                "question_type": "salary_negotiation",
                "difficulty": "easy",
                "sample_answer": "Sei ehrlich bezüglich Kündigungsfristen. Zeige Flexibilität wenn möglich.",
            },
        ]
