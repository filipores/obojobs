"""
Interview Generator Service - Generates interview questions based on job posting and user profile using Claude API.
"""

import json
import time

from anthropic import Anthropic

from config import config


class InterviewGenerator:
    """Service to generate interview questions for job applications using Claude API."""

    VALID_TYPES = ["behavioral", "technical", "situational", "company_specific", "salary_negotiation"]
    VALID_DIFFICULTIES = ["easy", "medium", "hard"]

    # German interview culture classics
    GERMAN_CLASSICS = [
        "Wo sehen Sie sich in 5 Jahren?",
        "Was sind Ihre Stärken und Schwächen?",
        "Warum wollen Sie bei uns arbeiten?",
        "Warum sollten wir Sie einstellen?",
        "Erzählen Sie uns etwas über sich.",
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
        retry_count: int = 3
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
                    print(f"Interview-Fragen Generierung fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    print(f"Interview-Fragen Generierung fehlgeschlagen nach {retry_count} Versuchen: {str(e)}")
                    # Return fallback questions
                    return self._get_fallback_questions(firma, position)

        return self._get_fallback_questions(firma, position)

    def _create_generation_prompt(
        self,
        job_text: str,
        firma: str,
        position: str,
        user_skills: list[dict] | None,
        question_count: int
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
- Formeller Ton, Sie-Form
- Direkte aber höfliche Fragen
- Fokus auf Qualifikationen und Berufserfahrung
- Typische deutsche Klassiker einbauen (z.B. "Wo sehen Sie sich in 5 Jahren?")

Für jede Frage gib an:

1. question_text: Die Interview-Frage auf Deutsch, in Sie-Form

2. question_type: Die Kategorie der Frage:
   - "behavioral": Verhaltensfragen über vergangene Erfahrungen ("Erzählen Sie von einer Situation, wo...")
   - "technical": Fachliche Fragen zur Position und Skills
   - "situational": Hypothetische Szenarien ("Was würden Sie tun, wenn...")
   - "company_specific": Fragen zum Unternehmen und zur Motivation ("Warum wollen Sie bei uns...")
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
    "question_text": "Wo sehen Sie sich beruflich in fünf Jahren?",
    "question_type": "behavioral",
    "difficulty": "medium",
    "sample_answer": "Zeigen Sie Ambition ohne unrealistisch zu wirken. Verknüpfen Sie Ihre Ziele mit dem Unternehmen und der Position. Betonen Sie Lernbereitschaft und Entwicklungswünsche."
  }},
  {{
    "question_text": "Welche Erfahrungen haben Sie mit [Technologie X]?",
    "question_type": "technical",
    "difficulty": "medium",
    "sample_answer": "Nennen Sie konkrete Projekte und Ergebnisse. Quantifizieren Sie wenn möglich. Zeigen Sie kontinuierliches Lernen in diesem Bereich."
  }}
]

Generiere jetzt {question_count} Interview-Fragen als JSON-Array:"""

    def _parse_questions_response(self, response_text: str) -> list[dict]:
        """Parse the Claude response into a list of question dictionaries."""
        text = response_text.strip()

        # Find JSON array bounds
        start_idx = text.find("[")
        end_idx = text.rfind("]")

        if start_idx == -1 or end_idx == -1:
            print("Keine JSON-Struktur in der Antwort gefunden")
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

                valid_questions.append({
                    "question_text": question_text,
                    "question_type": question_type,
                    "difficulty": difficulty,
                    "sample_answer": sample_answer or "Bereiten Sie eine konkrete Antwort mit Beispielen aus Ihrer Berufserfahrung vor.",
                })

            return valid_questions

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            return []

    def _get_fallback_questions(self, firma: str, position: str) -> list[dict]:
        """Return fallback questions if API call fails."""
        return [
            {
                "question_text": "Erzählen Sie uns etwas über sich.",
                "question_type": "behavioral",
                "difficulty": "easy",
                "sample_answer": "Fassen Sie Ihren Werdegang in 2-3 Minuten zusammen. Fokussieren Sie auf relevante Erfahrungen für diese Position."
            },
            {
                "question_text": f"Warum möchten Sie bei {firma} arbeiten?",
                "question_type": "company_specific",
                "difficulty": "medium",
                "sample_answer": "Zeigen Sie, dass Sie sich über das Unternehmen informiert haben. Verknüpfen Sie Ihre Ziele mit der Unternehmenskultur und Mission."
            },
            {
                "question_text": "Was sind Ihre größten Stärken?",
                "question_type": "behavioral",
                "difficulty": "easy",
                "sample_answer": "Nennen Sie 2-3 Stärken mit konkreten Beispielen. Wählen Sie Stärken, die für die Position relevant sind."
            },
            {
                "question_text": "Was ist Ihre größte Schwäche?",
                "question_type": "behavioral",
                "difficulty": "medium",
                "sample_answer": "Nennen Sie eine echte Schwäche, die Sie aktiv verbessern. Zeigen Sie Selbstreflexion und Entwicklungsbereitschaft."
            },
            {
                "question_text": "Wo sehen Sie sich in fünf Jahren?",
                "question_type": "behavioral",
                "difficulty": "medium",
                "sample_answer": "Zeigen Sie Ambition und langfristiges Engagement. Verknüpfen Sie Ihre Karriereziele mit dem Unternehmen."
            },
            {
                "question_text": f"Welche Erfahrungen qualifizieren Sie für die Position als {position}?",
                "question_type": "technical",
                "difficulty": "medium",
                "sample_answer": "Nennen Sie 2-3 konkrete Erfahrungen und Erfolge aus bisherigen Positionen, die direkt auf die neue Rolle übertragbar sind."
            },
            {
                "question_text": "Erzählen Sie von einer herausfordernden Situation im Beruf und wie Sie diese gemeistert haben.",
                "question_type": "behavioral",
                "difficulty": "hard",
                "sample_answer": "Nutzen Sie die STAR-Methode: Situation, Task, Action, Result. Wählen Sie ein Beispiel mit positivem Ausgang."
            },
            {
                "question_text": "Wie gehen Sie mit Konflikten im Team um?",
                "question_type": "situational",
                "difficulty": "medium",
                "sample_answer": "Beschreiben Sie Ihren konstruktiven Ansatz zur Konfliktlösung. Betonen Sie Kommunikation und Kompromissbereitschaft."
            },
            {
                "question_text": "Was wissen Sie über unser Unternehmen?",
                "question_type": "company_specific",
                "difficulty": "easy",
                "sample_answer": "Zeigen Sie, dass Sie recherchiert haben: Branche, Produkte, aktuelle Entwicklungen, Unternehmenskultur."
            },
            {
                "question_text": "Was sind Ihre Gehaltsvorstellungen?",
                "question_type": "salary_negotiation",
                "difficulty": "hard",
                "sample_answer": "Nennen Sie eine recherchierte Gehaltsspanne. Begründen Sie mit Ihrer Erfahrung und Qualifikation. Zeigen Sie Verhandlungsbereitschaft."
            },
            {
                "question_text": "Haben Sie Fragen an uns?",
                "question_type": "company_specific",
                "difficulty": "easy",
                "sample_answer": "Stellen Sie 2-3 vorbereitete Fragen zur Rolle, zum Team oder zur Unternehmenskultur. Zeigen Sie echtes Interesse."
            },
            {
                "question_text": "Wann könnten Sie bei uns anfangen?",
                "question_type": "salary_negotiation",
                "difficulty": "easy",
                "sample_answer": "Seien Sie ehrlich bezüglich Kündigungsfristen. Zeigen Sie Flexibilität wenn möglich."
            },
        ]
