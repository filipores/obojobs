import logging
import time

from openai import OpenAI

from config import config

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
        prompt = self._create_details_extraction_prompt(stellenanzeige_text, firma_name)

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

    def extract_key_information(self, stellenanzeige_text: str, retry_count: int = 3) -> str:
        prompt = self._create_extraction_prompt(stellenanzeige_text)

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

        system_prompt = self._build_einleitung_system_prompt(cv_text, position, quelle, bewerber_vorname, user_skills)

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

    def _create_details_extraction_prompt(self, stellenanzeige_text: str, firma_name: str) -> str:
        return f"""Extrahiere folgende Informationen aus dieser Stellenanzeige für eine Bewerbung:

STELLENANZEIGE:
{stellenanzeige_text}

Extrahiere präzise folgende Informationen:

1. ANSPRECHPARTNER: Wenn ein konkreter Name genannt wird (z.B. "Frau Schmidt", "Herr Müller"), gib "Sehr geehrte/r [Name]" zurück. Wenn kein Name vorhanden ist, gib "Sehr geehrte Damen und Herren" zurück.

2. POSITION: Die Stellenbezeichnung/Position (z.B. "Fullstack Developer", "Frontend Engineer"). Falls keine konkrete Position genannt wird, gib "Softwareentwickler" zurück.

3. QUELLE: Wo wurde die Anzeige gefunden/wo ist das Unternehmen präsent? (z.B. "LinkedIn", "eure Website", "StepStone"). Falls nicht erkennbar, gib "eure Website" zurück.

4. EMAIL: Die E-Mail-Adresse für Bewerbungen (z.B. "bewerbung@firma.de", "jobs@company.com"). Falls keine E-Mail-Adresse erkennbar ist, gib "keine Angabe" zurück.

5. Danach: Schreibe eine kompakte Zusammenfassung der wichtigsten Infos (Firma, Branche, Kernaufgaben, Skills) in Stichpunkten.

WICHTIG: Formatiere deine Antwort genau so:

ANSPRECHPARTNER: [Anrede]
POSITION: [Position]
QUELLE: [Quelle]
EMAIL: [E-Mail oder "keine Angabe"]

[Kompakte Zusammenfassung in Stichpunkten]

Extrahiere jetzt die Informationen:"""

    def _create_extraction_prompt(self, stellenanzeige_text: str) -> str:
        return f"""Extrahiere die wichtigsten Informationen aus dieser Stellenanzeige. Fokussiere dich auf das Wesentliche.

STELLENANZEIGE:
{stellenanzeige_text}

Extrahiere folgende Informationen in kompakter Form:
1. Firmenname und Branche
2. Position/Stellenbezeichnung (falls vorhanden)
3. Kernaufgaben und Tätigkeitsbereich (max. 3-4 Punkte)
4. Wichtigste Anforderungen/Skills (max. 3-4)
5. Besonderheiten des Unternehmens (Kultur, Arbeitsweise, Projekte)

WICHTIG: Fasse dich sehr kurz. Keine langen Beschreibungen. Nur die Kernfakten.
Schreibe die Extraktion in Stichpunkten oder kurzen Sätzen:"""

    def _build_einleitung_system_prompt(
        self,
        cv_text: str,
        position: str,
        quelle: str,
        bewerber_vorname: str | None = None,
        user_skills: list | None = None,
    ) -> str:
        # Skills section - dynamic based on user_skills
        if user_skills:
            skills_list = ", ".join(skill.skill_name for skill in user_skills)
            skills_section = f"- Die Skills im CV sind: {skills_list}"
        else:
            skills_section = "- Lies die Skills direkt aus dem Lebenslauf"

        # Persona personalization
        if bewerber_vorname:
            persona = f"Schreibe wie {bewerber_vorname}: locker, authentisch, 'bei euch' statt 'bei Ihnen'"
            stil_schluss = f"im Stil von {bewerber_vorname}"
        else:
            persona = "Schreibe locker und authentisch: 'bei euch' statt 'bei Ihnen'"
            stil_schluss = "im lockeren, authentischen Stil"

        return f"""Du schreibst den Einleitungsabsatz eines Bewerbungsanschreibens. Nur diesen einen Absatz, nicht das ganze Anschreiben.

## KONTEXT:
- Position: {position}
- Quelle: {quelle}

## LEBENSLAUF:
{cv_text[:2000]}

## KRITISCHE REGEL — FAKTENTREUE:
- Nenne NUR Skills, Tools und Erfahrungen die EXAKT im Lebenslauf stehen
- ERFINDE KEINE Kenntnisse. Wenn ein Skill nicht im CV steht, erwähne ihn NICHT
- Beispiele für VERBOTENE Erfindungen: React, Angular, Spring Boot, Python, C++, XSLT, Kubernetes — wenn es nicht im CV steht, NICHT verwenden
{skills_section}
- Wenn die Stelle Skills fordert die nicht im CV stehen: Sage ehrlich dass du dich einarbeiten willst, statt die Skills zu erfinden
- Lieber eine ehrliche Lücke als eine erfundene Qualifikation
- KEINE Pflegeerfahrung, Laborerfahrung oder andere fachfremde Erfahrung erfinden

## POSITION KORREKT EXTRAHIEREN:
- Lies die EXAKTE Positionsbezeichnung aus der Stellenanzeige
- Verwende den genauen Titel, nicht eine vereinfachte Version
- FALSCH: "Softwareentwickler" wenn die Stelle "Junior Frontend Developer" heißt
- RICHTIG: Den exakten Titel aus der Anzeige übernehmen

## REGELN:

### Was der Absatz enthalten MUSS:
- 2-4 Sätze, nicht mehr
- Warum du dich auf DIESE Stelle bei DIESER Firma bewirbst (nicht generisch)
- Ein konkreter Bezug zu deinem CV (eine spezifische Erfahrung oder Skill)

### Was der Absatz NICHT enthalten darf:
- KEINE Anrede (steht bereits im Template davor)
- KEINE Aufzählung von Skills (das kommt später im Anschreiben)
- KEINE Bindestriche, Gedankenstriche oder Spiegelstriche verwenden
- KEINE Zeilenumbrüche innerhalb des Absatzes — schreibe einen fließenden Absatz

### VERBOTENE ZEICHEN:
- Das Zeichen "–" (Gedankenstrich/En-Dash) ist VERBOTEN
- Das Zeichen "—" (Em-Dash) ist VERBOTEN
- Das Zeichen "-" als Satzzeichen ist VERBOTEN (als Bindestrich in Wörtern wie "Full-Stack" ist es OK)
- Verwende stattdessen Kommas, Punkte oder Semikolons

### VERBOTENE PHRASEN (NIEMALS verwenden):
- "Hiermit bewerbe ich mich" — das ist der langweiligste Einstieg überhaupt
- "mit großem Interesse"
- "hochmotiviert"
- "hat meine Aufmerksamkeit geweckt"
- "vielfältige Herausforderungen"
- "bin ich der ideale Kandidat"
- "freue mich auf die Herausforderung"
- "in einem dynamischen Umfeld"
- "meine Leidenschaft für"
- "hat mich sofort angesprochen"
- "genau die Mischung aus"
- "spricht mich besonders an"
- "reizt mich besonders"
- "passt genau zu meinen Erfahrungen"
- "technische Tiefe"
- "Lösungskompetenz"
- "praktische Erfahrung mitbringen"

### Ton & Authentizität:
- {persona}
- NICHT wie ein Sprachmodell, das "professionelle Bewerbungstexte" generiert
- Echte Menschen schreiben unperfekt: Mal ein kurzer Satz, mal ein längerer
- Echte Menschen wiederholen nicht dieselbe Satzstruktur in jedem Satz
- Jeder Satz soll einen eigenen Gedanken transportieren
- Variiere den Satzanfang (nicht jeder Satz mit "Ich" oder "Mit meiner")

### AI-TYPISCHE MUSTER (VERMEIDE):
- Immer gleiche Satzstruktur: "Bei X habe ich Y gemacht und dabei Z gelernt"
- Glatte Übergänge die zu perfekt klingen: "genau die Mischung aus", "spricht mich besonders an"
- Abstrakte Zusammenfassungen: "technische Tiefe und eigenständige Umsetzung"
- Jedes Erlebnis klingt gleich aufregend und positiv — echte Menschen sind konkreter
- Alles wirkt wie ein logischer Beweis statt wie ein persönlicher Text
- STATTDESSEN: Sei konkret. Nenne ein echtes Projekt, ein echtes Tool, eine echte Situation.

## AUSGABE:
Schreibe NUR den Einleitungsabsatz {stil_schluss}. Keine Anrede, keine Erklärung, kein "Hier ist...".
Beginne direkt mit dem ersten Satz. Ein fließender Absatz, KEINE Zeilenumbrüche.
Der Text darf KEINE Bindestriche als Satzzeichen enthalten."""
