"""
Interview Evaluator Service - Evaluates interview answer responses using Claude API.
Provides feedback on structure, content, length, and STAR method compliance.
"""

import json
import time

from anthropic import Anthropic

from config import config


class InterviewEvaluator:
    """Service to evaluate interview answers and provide structured feedback."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def evaluate_answer(
        self,
        question_text: str,
        question_type: str,
        answer_text: str,
        position: str | None = None,
        firma: str | None = None,
        retry_count: int = 3,
    ) -> dict:
        """
        Evaluate an interview answer and provide structured feedback.

        Args:
            question_text: The interview question that was asked
            question_type: Type of question (behavioral, technical, situational, etc.)
            answer_text: The user's answer to evaluate
            position: Optional job position for context
            firma: Optional company name for context
            retry_count: Number of retries on failure

        Returns:
            Dictionary with feedback structure:
            - overall_score: Score from 0-100
            - overall_rating: Rating category (excellent, good, adequate, needs_improvement)
            - strengths: List of positive aspects
            - improvements: List of areas to improve
            - suggestion: Concrete improvement suggestion
            - star_analysis: STAR method analysis (for behavioral questions)
            - length_assessment: Feedback on answer length
            - structure_assessment: Feedback on answer structure
        """
        prompt = self._create_evaluation_prompt(question_text, question_type, answer_text, position, firma)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_evaluation_response(response_text, question_type)

            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"Antwort-Bewertung fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    print(f"Antwort-Bewertung fehlgeschlagen nach {retry_count} Versuchen: {str(e)}")
                    return self._get_fallback_evaluation(question_type)

        return self._get_fallback_evaluation(question_type)

    def _create_evaluation_prompt(
        self, question_text: str, question_type: str, answer_text: str, position: str | None, firma: str | None
    ) -> str:
        """Create the prompt for answer evaluation."""

        context_section = ""
        if position or firma:
            context_section = f"""
KONTEXT:
- Position: {position or "Nicht angegeben"}
- Unternehmen: {firma or "Nicht angegeben"}
"""

        star_section = ""
        if question_type == "behavioral":
            star_section = """
Für diese Verhaltensfrage, analysiere zusätzlich die STAR-Methode Komponenten:
- S (Situation): Hat der Bewerber eine konkrete Situation/Kontext beschrieben?
- T (Task): Wurde die Aufgabe/Herausforderung klar definiert?
- A (Action): Wurden die konkreten Handlungen beschrieben?
- R (Result): Wurde ein Ergebnis/Outcome genannt?

Gib für jede STAR-Komponente an:
- "present": true/false - Ist diese Komponente vorhanden?
- "quality": "strong"|"adequate"|"weak"|"missing" - Qualität der Komponente
- "feedback": Kurzes Feedback zu dieser Komponente
"""

        return f"""Du bist ein erfahrener HR-Coach und Interview-Trainer in Deutschland.
Bewerte die folgende Interview-Antwort eines Bewerbers und gib konstruktives Feedback.
{context_section}
INTERVIEW-FRAGE:
"{question_text}"

FRAGENTYP: {question_type}

ANTWORT DES BEWERBERS:
"{answer_text}"
{star_section}
Bewerte die Antwort nach folgenden Kriterien:

1. GESAMTBEWERTUNG (0-100 Punkte):
   - 80-100: Exzellent - Überzeugende, gut strukturierte Antwort
   - 60-79: Gut - Solide Antwort mit kleinen Verbesserungsmöglichkeiten
   - 40-59: Ausreichend - Grundlegende Antwort, aber deutliche Verbesserungen nötig
   - 0-39: Verbesserungswürdig - Antwort braucht wesentliche Überarbeitung

2. STÄRKEN: Was war gut an der Antwort? (2-3 Punkte)

3. VERBESSERUNGEN: Was könnte verbessert werden? (2-3 Punkte)

4. KONKRETER VORSCHLAG: Ein spezifischer Verbesserungsvorschlag für diese Antwort

5. LÄNGE: War die Antwort angemessen lang? (zu_kurz, angemessen, zu_lang)

6. STRUKTUR: War die Antwort gut strukturiert? (gut_strukturiert, teilweise_strukturiert, unstrukturiert)

Antworte NUR mit einem JSON-Objekt im folgenden Format:
{{
  "overall_score": <0-100>,
  "overall_rating": "<excellent|good|adequate|needs_improvement>",
  "strengths": ["Stärke 1", "Stärke 2"],
  "improvements": ["Verbesserung 1", "Verbesserung 2"],
  "suggestion": "Konkreter Verbesserungsvorschlag...",
  "length_assessment": {{
    "rating": "<too_short|adequate|too_long>",
    "feedback": "Feedback zur Länge..."
  }},
  "structure_assessment": {{
    "rating": "<well_structured|partially_structured|unstructured>",
    "feedback": "Feedback zur Struktur..."
  }}{', "star_analysis": {...}' if question_type == "behavioral" else ""}
}}

{
            '''Für die STAR-Analyse (nur bei behavioral Fragen), füge hinzu:
"star_analysis": {
  "situation": {"present": true/false, "quality": "strong|adequate|weak|missing", "feedback": "..."},
  "task": {"present": true/false, "quality": "strong|adequate|weak|missing", "feedback": "..."},
  "action": {"present": true/false, "quality": "strong|adequate|weak|missing", "feedback": "..."},
  "result": {"present": true/false, "quality": "strong|adequate|weak|missing", "feedback": "..."}
}'''
            if question_type == "behavioral"
            else ""
        }

Gib jetzt das JSON-Objekt aus:"""

    def _parse_evaluation_response(self, response_text: str, question_type: str) -> dict:
        """Parse the Claude response into a structured evaluation."""
        text = response_text.strip()

        # Find JSON object bounds
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            print("Keine JSON-Struktur in der Antwort gefunden")
            return self._get_fallback_evaluation(question_type)

        json_text = text[start_idx : end_idx + 1]

        try:
            evaluation = json.loads(json_text)

            # Validate and ensure all required fields
            result = {
                "overall_score": min(100, max(0, evaluation.get("overall_score", 50))),
                "overall_rating": evaluation.get("overall_rating", "adequate"),
                "strengths": evaluation.get("strengths", [])[:5],
                "improvements": evaluation.get("improvements", [])[:5],
                "suggestion": evaluation.get("suggestion", ""),
                "length_assessment": evaluation.get(
                    "length_assessment", {"rating": "adequate", "feedback": "Keine spezifische Bewertung verfügbar."}
                ),
                "structure_assessment": evaluation.get(
                    "structure_assessment",
                    {"rating": "partially_structured", "feedback": "Keine spezifische Bewertung verfügbar."},
                ),
            }

            # Validate overall_rating
            valid_ratings = ["excellent", "good", "adequate", "needs_improvement"]
            if result["overall_rating"] not in valid_ratings:
                # Map score to rating
                score = result["overall_score"]
                if score >= 80:
                    result["overall_rating"] = "excellent"
                elif score >= 60:
                    result["overall_rating"] = "good"
                elif score >= 40:
                    result["overall_rating"] = "adequate"
                else:
                    result["overall_rating"] = "needs_improvement"

            # Add STAR analysis for behavioral questions
            if question_type == "behavioral" and "star_analysis" in evaluation:
                result["star_analysis"] = self._validate_star_analysis(evaluation["star_analysis"])
            elif question_type == "behavioral":
                result["star_analysis"] = self._get_default_star_analysis()

            return result

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            return self._get_fallback_evaluation(question_type)

    def _validate_star_analysis(self, star_data: dict) -> dict:
        """Validate and clean STAR analysis data."""
        valid_qualities = ["strong", "adequate", "weak", "missing"]
        default_component = {"present": False, "quality": "missing", "feedback": "Keine Analyse verfügbar."}

        result = {}
        for component in ["situation", "task", "action", "result"]:
            comp_data = star_data.get(component, default_component)
            if not isinstance(comp_data, dict):
                comp_data = default_component

            quality = comp_data.get("quality", "missing")
            if quality not in valid_qualities:
                quality = "adequate" if comp_data.get("present", False) else "missing"

            result[component] = {
                "present": bool(comp_data.get("present", False)),
                "quality": quality,
                "feedback": str(comp_data.get("feedback", ""))[:500],
            }

        return result

    def _get_default_star_analysis(self) -> dict:
        """Return default STAR analysis when not provided."""
        return {
            "situation": {"present": False, "quality": "missing", "feedback": "Konnte nicht analysiert werden."},
            "task": {"present": False, "quality": "missing", "feedback": "Konnte nicht analysiert werden."},
            "action": {"present": False, "quality": "missing", "feedback": "Konnte nicht analysiert werden."},
            "result": {"present": False, "quality": "missing", "feedback": "Konnte nicht analysiert werden."},
        }

    def _get_fallback_evaluation(self, question_type: str) -> dict:
        """Return fallback evaluation when API call fails."""
        result = {
            "overall_score": 50,
            "overall_rating": "adequate",
            "strengths": [
                "Antwort wurde gegeben",
            ],
            "improvements": [
                "Detailliertere Analyse nicht verfügbar aufgrund eines technischen Problems",
            ],
            "suggestion": "Bitte versuchen Sie es erneut für eine detaillierte Bewertung.",
            "length_assessment": {"rating": "adequate", "feedback": "Automatische Bewertung nicht verfügbar."},
            "structure_assessment": {
                "rating": "partially_structured",
                "feedback": "Automatische Bewertung nicht verfügbar.",
            },
        }

        if question_type == "behavioral":
            result["star_analysis"] = self._get_default_star_analysis()

        return result

    def generate_interview_summary(
        self, answers: list[dict], position: str | None = None, firma: str | None = None, retry_count: int = 3
    ) -> dict:
        """
        Generate a summary of all interview answers.

        Args:
            answers: List of answer evaluations with question info
            position: Optional job position
            firma: Optional company name
            retry_count: Number of retries

        Returns:
            Dictionary with summary:
            - overall_score: Average score
            - overall_assessment: Text assessment
            - category_scores: Scores by question type
            - top_strengths: Best performing areas
            - priority_improvements: Key areas to work on
            - next_steps: Recommended next steps
        """
        if not answers:
            return {
                "overall_score": 0,
                "overall_assessment": "Keine Antworten zum Auswerten vorhanden.",
                "category_scores": {},
                "top_strengths": [],
                "priority_improvements": [],
                "next_steps": ["Beginnen Sie mit dem Mock-Interview um Feedback zu erhalten."],
            }

        # Calculate category scores
        category_scores = {}
        all_scores = []

        for answer in answers:
            score = answer.get("score", 50)
            all_scores.append(score)
            q_type = answer.get("question_type", "other")
            if q_type not in category_scores:
                category_scores[q_type] = []
            category_scores[q_type].append(score)

        # Calculate averages
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        for cat in category_scores:
            scores = category_scores[cat]
            category_scores[cat] = sum(scores) / len(scores) if scores else 0

        # Determine assessment
        if overall_score >= 80:
            assessment = "Ausgezeichnet! Sie haben das Mock-Interview sehr gut gemeistert."
        elif overall_score >= 60:
            assessment = (
                "Gut gemacht! Ihre Antworten zeigen eine solide Vorbereitung mit einigen Verbesserungsmöglichkeiten."
            )
        elif overall_score >= 40:
            assessment = "Ordentliche Leistung. Mit etwas mehr Vorbereitung können Sie sich deutlich verbessern."
        else:
            assessment = "Hier ist noch Übungsbedarf. Nutzen Sie die Verbesserungsvorschläge für die nächste Runde."

        # Collect strengths and improvements
        all_strengths = []
        all_improvements = []
        for answer in answers:
            all_strengths.extend(answer.get("strengths", []))
            all_improvements.extend(answer.get("improvements", []))

        # Deduplicate and limit
        top_strengths = list(dict.fromkeys(all_strengths))[:5]
        priority_improvements = list(dict.fromkeys(all_improvements))[:5]

        # Generate next steps
        next_steps = []
        if overall_score < 60:
            next_steps.append("Üben Sie die STAR-Methode für Verhaltensfragen.")
        if category_scores.get("technical", 100) < 60:
            next_steps.append("Bereiten Sie konkrete Beispiele für technische Fragen vor.")
        if category_scores.get("behavioral", 100) < 60:
            next_steps.append("Sammeln Sie mehr Beispiele aus Ihrer Berufserfahrung.")
        next_steps.append("Wiederholen Sie das Mock-Interview nach der Vorbereitung.")

        return {
            "overall_score": round(overall_score, 1),
            "overall_assessment": assessment,
            "category_scores": {k: round(v, 1) for k, v in category_scores.items()},
            "top_strengths": top_strengths,
            "priority_improvements": priority_improvements,
            "next_steps": next_steps[:4],
            "total_questions": len(answers),
        }
