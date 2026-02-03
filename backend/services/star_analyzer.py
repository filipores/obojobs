"""
STAR Method Analyzer Service - Specialized feedback for behavioral interview questions.

Analyzes answers for STAR (Situation, Task, Action, Result) structure and provides
detailed improvement suggestions for each missing or weak component.
"""

import json
import time

from anthropic import Anthropic

from config import config


class STARAnalyzer:
    """Service to analyze interview answers for STAR method compliance."""

    STAR_COMPONENTS = ["situation", "task", "action", "result"]
    QUALITY_LEVELS = ["strong", "adequate", "weak", "missing"]

    # Detailed descriptions for each STAR component (German)
    COMPONENT_DESCRIPTIONS = {
        "situation": {
            "name": "Situation",
            "description": "Der Kontext oder Hintergrund der Erfahrung",
            "what_to_include": "Wo, wann, wer war beteiligt, was war die Ausgangslage",
            "example": "In meiner vorherigen Position als Projektmanager bei Firma X im Jahr 2022 standen wir vor einer kritischen Deadline...",
        },
        "task": {
            "name": "Aufgabe",
            "description": "Die spezifische Aufgabe oder Herausforderung, die Sie bewältigen mussten",
            "what_to_include": "Was war Ihre konkrete Verantwortung, was wurde von Ihnen erwartet",
            "example": "Meine Aufgabe war es, das Team zu reorganisieren und einen neuen Zeitplan zu erstellen, der das Projekt noch retten konnte.",
        },
        "action": {
            "name": "Handlung",
            "description": "Die konkreten Schritte, die Sie unternommen haben",
            "what_to_include": "Was haben SIE persönlich getan (nicht das Team), welche Methoden/Strategien haben Sie angewandt",
            "example": "Ich habe zunächst eine Bestandsaufnahme gemacht, dann priorisiert und schließlich tägliche Stand-ups eingeführt...",
        },
        "result": {
            "name": "Ergebnis",
            "description": "Das messbare Ergebnis Ihrer Handlungen",
            "what_to_include": "Konkrete Zahlen, Feedback, was Sie gelernt haben, wie es ausgegangen ist",
            "example": "Das Projekt wurde pünktlich abgeliefert, der Kunde war zufrieden, und wir haben den Folgeprozess für zukünftige Projekte übernommen.",
        },
    }

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def analyze_star(
        self,
        question_text: str,
        answer_text: str,
        position: str | None = None,
        firma: str | None = None,
        retry_count: int = 3,
    ) -> dict:
        """
        Perform detailed STAR method analysis on a behavioral interview answer.

        Args:
            question_text: The behavioral interview question
            answer_text: The user's answer to analyze
            position: Optional job position for context
            firma: Optional company name for context
            retry_count: Number of retries on API failure

        Returns:
            Dictionary with:
            - overall_star_score: 0-100 score for STAR compliance
            - components: Detailed analysis for each STAR component
            - improvement_suggestions: Specific suggestions for missing/weak components
            - improved_answer_example: Example of how to improve the answer
            - is_behavioral_suitable: Whether the answer suits a behavioral question
        """
        prompt = self._create_analysis_prompt(question_text, answer_text, position, firma)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_analysis_response(response_text)

            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"STAR-Analyse fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    print(f"STAR-Analyse fehlgeschlagen nach {retry_count} Versuchen: {str(e)}")
                    return self._get_fallback_analysis()

        return self._get_fallback_analysis()

    def _create_analysis_prompt(
        self, question_text: str, answer_text: str, position: str | None, firma: str | None
    ) -> str:
        """Create the prompt for STAR analysis."""
        context_section = ""
        if position or firma:
            context_section = f"""
KONTEXT:
- Position: {position or "Nicht angegeben"}
- Unternehmen: {firma or "Nicht angegeben"}
"""

        return f"""Du bist ein erfahrener Interview-Coach, spezialisiert auf die STAR-Methode für Verhaltens-Interviews.

Analysiere die folgende Antwort auf eine Verhaltensfrage und bewerte die Verwendung der STAR-Methode.
{context_section}
INTERVIEW-FRAGE:
"{question_text}"

ANTWORT DES BEWERBERS:
"{answer_text}"

Die STAR-Methode besteht aus:
- S (Situation): Der Kontext oder Hintergrund der Erfahrung
- T (Task/Aufgabe): Die spezifische Aufgabe oder Herausforderung
- A (Action/Handlung): Die konkreten Schritte, die der Bewerber unternommen hat
- R (Result/Ergebnis): Das messbare Ergebnis der Handlungen

Analysiere die Antwort und gib eine detaillierte Bewertung für JEDE Komponente:

Antworte NUR mit einem JSON-Objekt im folgenden Format:
{{
  "overall_star_score": <0-100>,
  "is_behavioral_suitable": <true/false>,
  "components": {{
    "situation": {{
      "present": <true/false>,
      "quality": "<strong|adequate|weak|missing>",
      "found_content": "Was in der Antwort als Situation identifiziert wurde (oder leer wenn missing)",
      "feedback": "Konkretes Feedback zu dieser Komponente",
      "improvement_tip": "Spezifischer Tipp zur Verbesserung dieser Komponente"
    }},
    "task": {{
      "present": <true/false>,
      "quality": "<strong|adequate|weak|missing>",
      "found_content": "...",
      "feedback": "...",
      "improvement_tip": "..."
    }},
    "action": {{
      "present": <true/false>,
      "quality": "<strong|adequate|weak|missing>",
      "found_content": "...",
      "feedback": "...",
      "improvement_tip": "..."
    }},
    "result": {{
      "present": <true/false>,
      "quality": "<strong|adequate|weak|missing>",
      "found_content": "...",
      "feedback": "...",
      "improvement_tip": "..."
    }}
  }},
  "improvement_suggestions": [
    "Konkrete Verbesserungsvorschläge für die gesamte Antwort..."
  ],
  "improved_answer_example": "Ein Beispiel wie die Antwort besser strukturiert werden könnte (2-3 Sätze pro STAR-Komponente)...",
  "general_feedback": "Allgemeines Feedback zur Antwort..."
}}

Qualitätskriterien:
- "strong": Komponente ist klar, spezifisch und detailliert
- "adequate": Komponente ist vorhanden, aber könnte detaillierter sein
- "weak": Komponente ist nur angedeutet oder sehr vage
- "missing": Komponente fehlt komplett

Gib jetzt das JSON-Objekt aus:"""

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse the Claude response into structured analysis."""
        text = response_text.strip()

        # Find JSON object bounds
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            print("Keine JSON-Struktur in der STAR-Analyse gefunden")
            return self._get_fallback_analysis()

        json_text = text[start_idx : end_idx + 1]

        try:
            analysis = json.loads(json_text)

            # Validate and ensure all required fields
            result = {
                "overall_star_score": min(100, max(0, analysis.get("overall_star_score", 50))),
                "is_behavioral_suitable": analysis.get("is_behavioral_suitable", True),
                "components": self._validate_components(analysis.get("components", {})),
                "improvement_suggestions": analysis.get("improvement_suggestions", [])[:5],
                "improved_answer_example": analysis.get("improved_answer_example", ""),
                "general_feedback": analysis.get("general_feedback", ""),
            }

            # Add component descriptions for frontend reference
            result["component_descriptions"] = self.COMPONENT_DESCRIPTIONS

            return result

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error in STAR-Analyse: {str(e)}")
            return self._get_fallback_analysis()

    def _validate_components(self, components_data: dict) -> dict:
        """Validate and clean component analysis data."""
        result = {}

        for component in self.STAR_COMPONENTS:
            comp_data = components_data.get(component, {})
            if not isinstance(comp_data, dict):
                comp_data = {}

            quality = comp_data.get("quality", "missing")
            if quality not in self.QUALITY_LEVELS:
                quality = "adequate" if comp_data.get("present", False) else "missing"

            result[component] = {
                "present": bool(comp_data.get("present", False)),
                "quality": quality,
                "found_content": str(comp_data.get("found_content", ""))[:500],
                "feedback": str(comp_data.get("feedback", ""))[:500],
                "improvement_tip": str(comp_data.get("improvement_tip", self._get_default_tip(component)))[:500],
            }

        return result

    def _get_default_tip(self, component: str) -> str:
        """Get default improvement tip for a component."""
        tips = {
            "situation": "Beschreiben Sie konkret: Wo arbeiteten Sie? Wann war das? Wer war beteiligt? Was war die Ausgangslage?",
            "task": "Erklären Sie genau: Was war Ihre spezifische Verantwortung? Was wurde von Ihnen erwartet?",
            "action": "Betonen Sie Ihre persönlichen Handlungen mit 'Ich habe...' statt 'Wir haben...'. Welche Schritte haben Sie unternommen?",
            "result": "Nennen Sie messbare Ergebnisse: Zahlen, Prozente, Zeitersparnis, Feedback vom Vorgesetzten oder Kunden.",
        }
        return tips.get(component, "Fügen Sie mehr Details zu dieser Komponente hinzu.")

    def _get_fallback_analysis(self) -> dict:
        """Return fallback analysis when API call fails."""
        return {
            "overall_star_score": 50,
            "is_behavioral_suitable": True,
            "components": {
                comp: {
                    "present": False,
                    "quality": "missing",
                    "found_content": "",
                    "feedback": "Automatische Analyse nicht verfügbar.",
                    "improvement_tip": self._get_default_tip(comp),
                }
                for comp in self.STAR_COMPONENTS
            },
            "improvement_suggestions": [
                "Strukturieren Sie Ihre Antwort nach der STAR-Methode: Situation, Aufgabe, Handlung, Ergebnis.",
                "Nennen Sie konkrete Beispiele aus Ihrer Berufserfahrung.",
                "Quantifizieren Sie Ihre Ergebnisse wenn möglich.",
            ],
            "improved_answer_example": "Detaillierte Analyse nicht verfügbar. Bitte versuchen Sie es erneut.",
            "general_feedback": "Automatische Bewertung konnte nicht durchgeführt werden.",
            "component_descriptions": self.COMPONENT_DESCRIPTIONS,
        }

    def get_component_descriptions(self) -> dict:
        """Return descriptions for all STAR components.

        Useful for displaying help text in the frontend.
        """
        return self.COMPONENT_DESCRIPTIONS
