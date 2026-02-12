import logging
import re
import time

from openai import OpenAI

from config import config
from services.qwen_prompts import (
    FORBIDDEN_PHRASES,
    build_anschreiben_system_prompt,
    build_einleitung_system_prompt,
    create_details_extraction_prompt,
    create_extraction_prompt,
)

logger = logging.getLogger(__name__)

RETRY_DELAY_SECONDS = 2


class QwenAPIClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.TOGETHER_API_KEY
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY nicht gesetzt")
        self.client = OpenAI(api_key=self.api_key, base_url=config.QWEN_API_BASE)
        self.model = config.QWEN_MODEL
        self.max_tokens = config.QWEN_MAX_TOKENS
        self.temperature = config.QWEN_TEMPERATURE

    def extract_bewerbung_details(
        self, stellenanzeige_text: str, firma_name: str, retry_count: int = 3
    ) -> dict[str, str]:
        prompt = create_details_extraction_prompt(stellenanzeige_text, firma_name)

        for attempt in range(retry_count):
            try:
                response = self._call_api(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3,
                )
                return self._parse_extracted_details(response, firma_name)
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        "Detail-Extraktion fehlgeschlagen (Versuch %d/%d): %s",
                        attempt + 1,
                        retry_count,
                        e,
                    )
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.warning("Detail-Extraktion fehlgeschlagen, verwende Defaults")
                    return self._get_default_details(firma_name)
        return None

    def extract_key_information(self, stellenanzeige_text: str, retry_count: int = 3) -> str:
        prompt = create_extraction_prompt(stellenanzeige_text)

        for attempt in range(retry_count):
            try:
                return self._call_api(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.3,
                )
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        "Extraktion fehlgeschlagen (Versuch %d/%d): %s",
                        attempt + 1,
                        retry_count,
                        e,
                    )
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise Exception(f"Informationsextraktion fehlgeschlagen: {e!s}") from e
        return None

    def generate_einleitung(
        self,
        cv_text: str,
        stellenanzeige_text: str,
        firma_name: str | None = None,
        zeugnis_text: str | None = None,
        details: dict[str, str] | None = None,
        use_extraction: bool = True,
        retry_count: int = 3,
        bewerber_vorname: str | None = None,
        user_skills: list | None = None,
    ) -> str:
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

        for attempt in range(retry_count):
            try:
                einleitung = self._call_api(
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
                if attempt < retry_count - 1:
                    logger.warning("API-Fehler (Versuch %d/%d): %s", attempt + 1, retry_count, e)
                    logger.info("Warte %d Sekunden vor erneutem Versuch...", RETRY_DELAY_SECONDS)
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise Exception(f"Qwen API Fehler nach {retry_count} Versuchen: {e!s}") from e
        return None

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
        retry_count: int = 3,
    ) -> str:
        """Generate a complete cover letter body (greeting through closing).

        Unlike generate_einleitung() which only produces an intro paragraph,
        this generates the full letter body for direct use in PDF generation.
        """
        # Use compact job description if available
        if stellenanzeige_text and len(stellenanzeige_text) > 2000:
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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(retry_count):
            try:
                raw = self._call_api(
                    messages=messages,
                    max_tokens=config.QWEN_ANSCHREIBEN_MAX_TOKENS,
                    temperature=config.QWEN_ANSCHREIBEN_TEMPERATURE,
                )
                result = self._postprocess_anschreiben(raw)

                # Check for forbidden phrases and retry with correction prompt
                violations = self._find_forbidden_phrases(result)
                if violations and attempt < retry_count - 1:
                    logger.warning(
                        "Verbotene Phrasen gefunden (Versuch %d/%d): %s",
                        attempt + 1,
                        retry_count,
                        violations,
                    )
                    phrases_str = ", ".join(f'"{p}"' for p in violations)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": f"Dein Text enthält verbotene Phrasen: {phrases_str}. "
                            "Schreibe das Anschreiben KOMPLETT NEU ohne diese Phrasen. "
                            "Formuliere die betroffenen Stellen völlig anders.",
                        },
                    ]
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue

                return result
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning("API-Fehler (Versuch %d/%d): %s", attempt + 1, retry_count, e)
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise Exception(f"Qwen API Fehler nach {retry_count} Versuchen: {e!s}") from e
        return None

    def chat_complete(self, messages: list[dict], max_tokens: int = 2000, temperature: float = 0.7) -> str:
        return self._call_api(messages=messages, max_tokens=max_tokens, temperature=temperature)

    def generate_email_text(
        self,
        position: str,
        ansprechperson: str,
        firma_name: str | None = None,
        attachments: list[str] | None = None,
        user_name: str | None = None,
        user_email: str | None = None,
        user_phone: str | None = None,
        user_city: str | None = None,
        user_website: str | None = None,
    ) -> str:
        """Generate personalized email text for job application"""
        if attachments is None:
            attachments = ["Anschreiben", "Lebenslauf"]

        position_text = f"die Position als {position}"
        if firma_name:
            position_text = f"die Position als {position} bei {firma_name}"

        name = user_name or "Ihr Name"
        signature_parts = [name]
        contact_line = " | ".join(filter(None, [user_city, user_phone]))
        if contact_line:
            signature_parts.append(contact_line)
        if user_email:
            signature_parts.append(user_email)
        if user_website:
            signature_parts.append(user_website)

        signature = "\n".join(signature_parts)

        return f"""{ansprechperson},

anbei finden Sie meine Bewerbungsunterlagen für {position_text}.

Ich freue mich auf Ihre Rückmeldung.

Mit freundlichen Grüßen
{signature}"""

    def generate_betreff(
        self, position: str, firma_name: str | None = None, style: str = "professional", user_name: str | None = None
    ) -> str:
        """Generate professional email subject line"""
        name = user_name or "Bewerber"
        if style == "professional":
            return f"Bewerbung als {position} - {name}" if firma_name else f"Bewerbung als {position}"
        if style == "informal":
            return f"Bewerbung: {position}"
        # formal style
        return (
            f"Bewerbung um die Position als {position} bei {firma_name}"
            if firma_name
            else f"Bewerbung um die Position als {position}"
        )

    # --- Private helpers ---

    def _call_api(self, messages: list[dict], max_tokens: int, temperature: float) -> str:
        """Send a chat completion request and return the stripped response text."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    def _parse_extracted_details(self, text: str, firma_name: str) -> dict[str, str]:
        details = {
            "firma": firma_name,
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "position": "Softwareentwickler",
            "quelle": "eure Website",
            "email": "",
            "stellenanzeige_kompakt": text,
        }

        ignored_values = {"keine angabe", "nicht vorhanden", "n/a"}

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("ANSPRECHPARTNER:"):
                anrede = line.replace("ANSPRECHPARTNER:", "").strip()
                if anrede and anrede.lower() not in ignored_values:
                    details["ansprechpartner"] = anrede
            elif line.startswith("POSITION:"):
                pos = line.replace("POSITION:", "").strip()
                if pos and pos.lower() not in ignored_values and pos.lower() != "initiativ":
                    details["position"] = pos
            elif line.startswith("QUELLE:"):
                quelle = line.replace("QUELLE:", "").strip()
                if quelle and quelle.lower() not in ignored_values:
                    details["quelle"] = quelle
            elif line.startswith("EMAIL:"):
                email = line.replace("EMAIL:", "").strip()
                if email and email.lower() not in ignored_values:
                    details["email"] = email

        return details

    def _get_default_details(self, firma_name: str) -> dict[str, str]:
        return {
            "firma": firma_name,
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "position": "Softwareentwickler",
            "quelle": "eure Website",
            "email": "",
            "stellenanzeige_kompakt": "",
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

    def _find_forbidden_phrases(self, text: str) -> list[str]:
        """Return list of forbidden phrases found in the text."""
        text_lower = text.lower()
        return [phrase for phrase in FORBIDDEN_PHRASES if phrase.lower() in text_lower]
