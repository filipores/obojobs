"""Email formatting utilities for job applications."""


class EmailFormatter:
    """Generates email subjects and body text for job applications."""

    @staticmethod
    def generate_betreff(position, firma_name=None, style="professional", user_name=None):
        """Generate professional email subject line."""
        if style == "professional":
            name = user_name or "Bewerber"
            if firma_name:
                return f"Bewerbung als {position} - {name}"
            return f"Bewerbung als {position}"

        if style == "informal":
            return f"Bewerbung: {position}"

        # formal (default)
        if firma_name:
            return f"Bewerbung um die Position als {position} bei {firma_name}"
        return f"Bewerbung um die Position als {position}"

    @staticmethod
    def generate_email_text(
        position,
        ansprechperson,
        firma_name=None,
        attachments=None,
        user_name=None,
        user_email=None,
        user_phone=None,
        user_city=None,
        user_website=None,
    ):
        """Generate personalized email text for job application."""
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
