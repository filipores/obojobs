import time

from anthropic import Anthropic

from config import config


class ClaudeAPIClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE

    def extract_bewerbung_details(
        self, stellenanzeige_text: str, firma_name: str, retry_count: int = 3
    ) -> dict[str, str]:
        prompt = self._create_details_extraction_prompt(stellenanzeige_text, firma_name)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=500, temperature=0.3, messages=[{"role": "user", "content": prompt}]
                )
                extracted_text = response.content[0].text.strip()
                return self._parse_extracted_details(extracted_text, firma_name)
            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"Detail-Extraktion fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    print("⚠ Detail-Extraktion fehlgeschlagen, verwende Defaults")
                    return self._get_default_details(firma_name)

    def _parse_extracted_details(self, text: str, firma_name: str) -> dict[str, str]:
        details = {
            "firma": firma_name,
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "position": "Softwareentwickler",
            "quelle": "eure Website",
            "email": "",
            "stellenanzeige_kompakt": text,
        }

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("ANSPRECHPARTNER:"):
                anrede = line.replace("ANSPRECHPARTNER:", "").strip()
                if anrede and anrede.lower() not in ["keine angabe", "nicht vorhanden", "n/a"]:
                    details["ansprechpartner"] = anrede
            elif line.startswith("POSITION:"):
                pos = line.replace("POSITION:", "").strip()
                if pos and pos.lower() not in ["keine angabe", "initiativ", "n/a"]:
                    details["position"] = pos
            elif line.startswith("QUELLE:"):
                quelle = line.replace("QUELLE:", "").strip()
                if quelle and quelle.lower() not in ["keine angabe", "nicht vorhanden", "n/a"]:
                    details["quelle"] = quelle
            elif line.startswith("EMAIL:"):
                email = line.replace("EMAIL:", "").strip()
                if email and email.lower() not in ["keine angabe", "nicht vorhanden", "n/a"]:
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

    def extract_key_information(self, stellenanzeige_text: str, retry_count: int = 3) -> str:
        prompt = self._create_extraction_prompt(stellenanzeige_text)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=400, temperature=0.3, messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"Extraktion fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    raise Exception(f"Informationsextraktion fehlgeschlagen: {str(e)}") from e

    def generate_einleitung(
        self,
        cv_text: str,
        stellenanzeige_text: str,
        firma_name: str | None = None,
        zeugnis_text: str | None = None,
        details: dict[str, str] | None = None,
        use_extraction: bool = True,
        retry_count: int = 3,
    ) -> str:
        if details and details.get("stellenanzeige_kompakt"):
            stellenanzeige_text = details["stellenanzeige_kompakt"]
        elif use_extraction:
            print("  → Extrahiere Kerninformationen aus Stellenanzeige...")
            stellenanzeige_text = self.extract_key_information(stellenanzeige_text)
            print(f"  → Extraktion abgeschlossen ({len(stellenanzeige_text)} Zeichen)")

        position = details.get("position", "Softwareentwickler") if details else "Softwareentwickler"
        quelle = details.get("quelle", "eure Website") if details else "eure Website"

        system_blocks = self._create_cached_system_blocks(cv_text, zeugnis_text, position, quelle)
        user_prompt = self._create_user_prompt(stellenanzeige_text, firma_name)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_blocks,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                einleitung = response.content[0].text.strip()
                if einleitung.startswith('"') and einleitung.endswith('"'):
                    einleitung = einleitung[1:-1]
                return einleitung
            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"API-Fehler (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    print("Warte 2 Sekunden vor erneutem Versuch...")
                    time.sleep(2)
                else:
                    raise Exception(f"Claude API Fehler nach {retry_count} Versuchen: {str(e)}") from e

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

    def _create_cached_system_blocks(self, cv_text: str, zeugnis_text: str | None, position: str, quelle: str) -> list:
        system_blocks = []

        instructions = f"""Du bist ein professioneller Bewerbungsschreiber. Deine Aufgabe ist es, einen kurzen, prägnanten Einleitungsabsatz für ein Anschreiben zu verfassen.

KONTEXT:
- Position: {position}
- Quelle: {quelle}

WICHTIGE ANFORDERUNGEN:
- Der Absatz soll 2-4 Sätze lang sein
- Locker und authentisch formulieren (wie Filip schreibt: "hiermit bewerbe ich mich initiativ bei euch als...")
- Bezug nehmen auf: Position, wie Filip auf das Unternehmen aufmerksam wurde (Quelle), warum er interessiert ist
- OHNE Anrede beginnen (das steht schon im Template)
- Den Firmennamen NICHT wiederholen (steht schon in der Anrede)
- Authentisch und individuell klingen
- Auf die Qualifikationen aus dem Lebenslauf Bezug nehmen
- Locker, aber professionell ("bei euch" statt "bei Ihnen")
- keine Bindestriche verwenden

Schreibe NUR den Einleitungsabsatz (2-4 Sätze) im lockeren, authentischen Stil von Filip. Beginne direkt mit dem Text, ohne Anrede."""

        system_blocks.append({"type": "text", "text": instructions, "cache_control": {"type": "ephemeral"}})

        system_blocks.append(
            {
                "type": "text",
                "text": f"LEBENSLAUF DES BEWERBERS:\n{cv_text[:2000]}",
                "cache_control": {"type": "ephemeral"},
            }
        )

        if zeugnis_text:
            system_blocks.append(
                {
                    "type": "text",
                    "text": f"ARBEITSZEUGNIS (LETZTE POSITION):\n{zeugnis_text[:1000]}",
                    "cache_control": {"type": "ephemeral"},
                }
            )

        return system_blocks

    def generate_email_text(
        self, position: str, ansprechperson: str, firma_name: str = None, attachments: list = None
    ) -> str:
        """Generate personalized email text for job application"""
        if attachments is None:
            # Note: Arbeitszeugnis is optional - caller should pass it explicitly if available
            attachments = ["Anschreiben", "Lebenslauf", "Bachelorzeugnis"]

        # Add company context if available
        position_text = f"die Position als {position}"
        if firma_name:
            position_text = f"die Position als {position} bei {firma_name}"

        return f"""{ansprechperson},

anbei finden Sie meine Bewerbungsunterlagen für {position_text}.

Ich freue mich auf Ihre Rückmeldung.

Mit freundlichen Grüßen
Filip Ores

Hamburg | +49 15254112096
filip.ores@hotmail.com
filipores.com"""

    def generate_betreff(self, position: str, firma_name: str = None, style: str = "professional") -> str:
        """Generate professional email subject line"""
        if style == "professional":
            return f"Bewerbung als {position} - Filip Ores" if firma_name else f"Bewerbung als {position}"
        if style == "informal":
            return f"Bewerbung: {position}"
        # formal style
        return (
            f"Bewerbung um die Position als {position} bei {firma_name}"
            if firma_name
            else f"Bewerbung um die Position als {position}"
        )

    def _create_user_prompt(self, stellenanzeige_text: str, firma_name: str | None) -> str:
        firma_info = f" (Firma: {firma_name})" if firma_name else ""
        return f"""STELLENANZEIGE / FIRMENBESCHREIBUNG{firma_info}:
{stellenanzeige_text[:2000]}

Schreibe jetzt den Einleitungsabsatz basierend auf den Informationen aus dem Lebenslauf und der Stellenanzeige:"""
