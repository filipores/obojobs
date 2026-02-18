import json
import logging
import re

from openai import OpenAI

from config import config
from services.qwen_prompts import (
    FORBIDDEN_PHRASES,
    build_anschreiben_system_prompt,
    build_einleitung_system_prompt,
    create_details_extraction_prompt,
    create_extraction_prompt,
)
from services.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class QwenAPIClient:
    IGNORED_VALUES = {"keine angabe", "nicht vorhanden", "n/a", ""}

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.TOGETHER_API_KEY
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY nicht gesetzt")
        self.client = OpenAI(api_key=self.api_key, base_url=config.QWEN_API_BASE)
        self.model = config.QWEN_MODEL
        self.fast_model = config.QWEN_FAST_MODEL
        self.kimi_model = config.KIMI_MODEL
        self.max_tokens = config.QWEN_MAX_TOKENS
        self.temperature = config.QWEN_TEMPERATURE

    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def _call_api_with_retry(self, messages, max_tokens, temperature, model=None):
        """Send a chat completion request with automatic retry on failure."""
        return self._call_api(messages=messages, max_tokens=max_tokens, temperature=temperature, model=model)

    def _call_api_json(
        self, messages: list[dict], max_tokens: int, temperature: float, model: str | None = None
    ) -> dict:
        """Send a chat completion request expecting JSON response."""
        response = self.client.chat.completions.create(
            model=model or self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content.strip())

    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def _call_api_json_with_retry(self, messages, max_tokens, temperature, model=None):
        """Send a JSON chat completion request with automatic retry on failure."""
        return self._call_api_json(messages=messages, max_tokens=max_tokens, temperature=temperature, model=model)

    def extract_bewerbung_details(self, stellenanzeige_text: str, firma_name: str) -> dict:
        prompt = create_details_extraction_prompt(stellenanzeige_text, firma_name)

        try:
            data = self._call_api_json_with_retry(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                model=self.fast_model,
            )
            return self._normalize_extracted_details(data, firma_name)
        except Exception:
            logger.warning("Detail-Extraktion fehlgeschlagen, verwende Defaults")
            defaults = self._get_default_details(firma_name)
            defaults["warnings"] = [
                "Detail-Extraktion fehlgeschlagen. Position und Ansprechpartner wurden auf Standardwerte gesetzt."
            ]
            return defaults

    def extract_key_information(self, stellenanzeige_text: str) -> str | None:
        prompt = create_extraction_prompt(stellenanzeige_text)

        try:
            return self._call_api_with_retry(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3,
                model=self.fast_model,
            )
        except Exception as e:
            raise Exception(f"Informationsextraktion fehlgeschlagen: {e!s}") from e

    def generate_einleitung(
        self,
        cv_text: str,
        stellenanzeige_text: str,
        firma_name: str | None = None,
        zeugnis_text: str | None = None,
        details: dict[str, str] | None = None,
        use_extraction: bool = True,
        bewerber_vorname: str | None = None,
        user_skills: list | None = None,
    ) -> str | None:
        if details and details.get("stellenanzeige_kompakt"):
            stellenanzeige_text = details["stellenanzeige_kompakt"]
        elif use_extraction:
            logger.info("Extrahiere Kerninformationen aus Stellenanzeige...")
            stellenanzeige_text = self.extract_key_information(stellenanzeige_text)
            logger.info("Extraktion abgeschlossen (%d Zeichen)", len(stellenanzeige_text))

        position = details.get("position", "Softwareentwickler") if details else "Softwareentwickler"
        quelle = details.get("quelle", "eure Website") if details else "eure Website"

        system_prompt = build_einleitung_system_prompt(cv_text, position, quelle, bewerber_vorname, user_skills)

        if zeugnis_text:
            system_prompt += f"\n\n## ARBEITSZEUGNIS (LETZTE POSITION):\n{zeugnis_text[:1000]}"

        firma_info = f" (Firma: {firma_name})" if firma_name else ""
        user_prompt = f"""STELLENANZEIGE / FIRMENBESCHREIBUNG{firma_info}:
{stellenanzeige_text[:2000]}

Schreibe jetzt den Einleitungsabsatz basierend auf den Informationen aus dem Lebenslauf und der Stellenanzeige:"""

        try:
            einleitung = self._call_api_with_retry(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            if einleitung.startswith('"') and einleitung.endswith('"'):
                einleitung = einleitung[1:-1]
            return einleitung
        except Exception as e:
            raise Exception(f"Qwen API Fehler: {e!s}") from e

    def generate_anschreiben(
        self,
        cv_text: str,
        stellenanzeige_text: str,
        firma_name: str,
        position: str,
        ansprechpartner: str,
        quelle: str = "eure Website",
        zeugnis_text: str | None = None,
        bewerber_vorname: str | None = None,
        bewerber_name: str | None = None,
        user_skills: list | None = None,
        tonalitaet: str = "modern",
        details: dict | None = None,
    ) -> str | None:
        """Generate a complete cover letter body (greeting through closing).

        Unlike generate_einleitung() which only produces an intro paragraph,
        this generates the full letter body for direct use in PDF generation.

        API-level retries are handled by _call_api_with_retry. Forbidden phrases
        are removed via post-processing instead of re-generation.
        """
        # Use pre-extracted compact version if available
        if details and details.get("stellenanzeige_kompakt"):
            stellenanzeige_text = details["stellenanzeige_kompakt"]
        elif stellenanzeige_text and len(stellenanzeige_text) > 2000:
            stellenanzeige_text = self.extract_key_information(stellenanzeige_text)

        system_prompt = build_anschreiben_system_prompt(
            cv_text=cv_text,
            position=position,
            quelle=quelle,
            ansprechpartner=ansprechpartner,
            bewerber_vorname=bewerber_vorname,
            bewerber_name=bewerber_name,
            user_skills=user_skills,
            tonalitaet=tonalitaet,
        )

        if zeugnis_text:
            system_prompt += f"\n\n## ARBEITSZEUGNIS (LETZTE POSITION):\n{zeugnis_text[:1000]}"

        firma_info = f" (Firma: {firma_name})" if firma_name else ""
        user_prompt = f"""STELLENANZEIGE / FIRMENBESCHREIBUNG{firma_info}:
{stellenanzeige_text[:2000]}

Schreibe jetzt das vollständige Anschreiben (Anrede bis Grußformel):"""

        raw = self._call_api_with_retry(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=config.QWEN_ANSCHREIBEN_MAX_TOKENS,
            temperature=config.QWEN_ANSCHREIBEN_TEMPERATURE,
        )

        result = self._postprocess_anschreiben(raw)
        result = self._remove_forbidden_phrases(result)
        return result

    def generate_anschreiben_stream(
        self,
        cv_text: str,
        stellenanzeige_text: str,
        firma_name: str,
        position: str,
        ansprechpartner: str,
        quelle: str = "eure Website",
        zeugnis_text: str | None = None,
        bewerber_vorname: str | None = None,
        bewerber_name: str | None = None,
        user_skills: list | None = None,
        tonalitaet: str = "modern",
        details: dict | None = None,
        thinking_callback=None,
    ) -> str | None:
        """Generate a cover letter using Kimi K2.5 with streaming and reasoning.

        Together.xyz exposes Kimi's chain-of-thought via the `reasoning` API parameter.
        Reasoning tokens arrive in `delta.reasoning`, content in `delta.content`.

        No @retry_with_backoff — streaming responses cannot be retried mid-stream.
        """
        # Use pre-extracted compact version if available
        if details and details.get("stellenanzeige_kompakt"):
            stellenanzeige_text = details["stellenanzeige_kompakt"]
        elif stellenanzeige_text and len(stellenanzeige_text) > 2000:
            stellenanzeige_text = self.extract_key_information(stellenanzeige_text)

        system_prompt = build_anschreiben_system_prompt(
            cv_text=cv_text,
            position=position,
            quelle=quelle,
            ansprechpartner=ansprechpartner,
            bewerber_vorname=bewerber_vorname,
            bewerber_name=bewerber_name,
            user_skills=user_skills,
            tonalitaet=tonalitaet,
        )

        if zeugnis_text:
            system_prompt += f"\n\n## ARBEITSZEUGNIS (LETZTE POSITION):\n{zeugnis_text[:1000]}"

        firma_info = f" (Firma: {firma_name})" if firma_name else ""
        user_prompt = f"""STELLENANZEIGE / FIRMENBESCHREIBUNG{firma_info}:
{stellenanzeige_text[:2000]}

Schreibe jetzt das vollständige Anschreiben (Anrede bis Grußformel):"""

        try:
            response = self.client.chat.completions.create(
                model=self.kimi_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=config.KIMI_MAX_TOKENS,
                temperature=config.KIMI_TEMPERATURE,
                stream=True,
                extra_body={"reasoning": {"enabled": True}},
            )

            output_parts = []

            for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # Forward reasoning tokens via callback
                reasoning = getattr(delta, "reasoning", None)
                if reasoning and thinking_callback:
                    thinking_callback(reasoning)
                # Accumulate content tokens
                content = delta.content
                if content:
                    output_parts.append(content)

            result = "".join(output_parts)
            if not result.strip():
                logger.error("Kimi stream returned empty output")
                return None

            result = self._postprocess_anschreiben(result)
            result = self._remove_forbidden_phrases(result)
            return result

        except Exception as e:
            logger.error("Kimi streaming Fehler: %s", e)
            raise

    def chat_complete(self, messages: list[dict], max_tokens: int = 2000, temperature: float = 0.7) -> str:
        return self._call_api(messages=messages, max_tokens=max_tokens, temperature=temperature)

    # --- Private helpers ---

    def _call_api(self, messages: list[dict], max_tokens: int, temperature: float, model: str | None = None) -> str:
        """Send a chat completion request and return the stripped response text."""
        response = self.client.chat.completions.create(
            model=model or self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    def _normalize_extracted_details(self, data: dict, firma_name: str) -> dict:
        """Normalize JSON response from API into standard details dict."""
        defaults = self._get_default_details(firma_name)

        for key in ["ansprechpartner", "position", "quelle", "email"]:
            value = str(data.get(key, "")).strip()
            if value and value.lower() not in self.IGNORED_VALUES:
                if key == "position" and value.lower() == "initiativ":
                    continue
                defaults[key] = value

        if data.get("zusammenfassung"):
            defaults["stellenanzeige_kompakt"] = str(data["zusammenfassung"])

        return defaults

    def _get_default_details(self, firma_name: str) -> dict:
        return {
            "firma": firma_name,
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "position": "Softwareentwickler",
            "quelle": "eure Website",
            "email": "",
            "stellenanzeige_kompakt": "",
            "warnings": [],
        }

    def _postprocess_anschreiben(self, text: str) -> str:
        """Clean up AI-generated cover letter text."""
        # Remove preambles like "Hier ist das Anschreiben:" or "Gerne, hier..."
        preamble_patterns = [
            r"^(?:Hier ist|Gerne|Natürlich|Klar|Selbstverständlich)[^\n]*:\s*\n+",
            r"^```[^\n]*\n",
            r"\n```\s*$",
        ]
        for pattern in preamble_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Replace dashes used as punctuation (en-dash, em-dash)
        text = text.replace(" – ", ", ").replace(" — ", ", ")
        text = text.replace("–", ",").replace("—", ",")

        # Normalize excessive line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip surrounding quotes
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()

        return text

    def _remove_forbidden_phrases(self, text: str) -> str:
        """Remove sentences containing forbidden phrases from the text."""
        # Split into sentences by ". " or ".\n" while preserving paragraph structure
        paragraphs = text.split("\n")
        cleaned_paragraphs = []

        removed = []
        for paragraph in paragraphs:
            if not paragraph.strip():
                cleaned_paragraphs.append(paragraph)
                continue

            # Split paragraph into sentences
            sentences = re.split(r"(?<=\.)\s+", paragraph)
            kept = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                matched_phrases = [p for p in FORBIDDEN_PHRASES if p.lower() in sentence_lower]
                if matched_phrases:
                    removed.extend(matched_phrases)
                else:
                    kept.append(sentence)

            cleaned_paragraphs.append(" ".join(kept))

        if removed:
            logger.warning("Verbotene Phrasen entfernt: %s", removed)

        # Clean up empty paragraphs that resulted from removal
        result = "\n".join(cleaned_paragraphs)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()
