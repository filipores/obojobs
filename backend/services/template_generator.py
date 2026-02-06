"""Service for auto-generating default templates for users."""

from models import Template, db

DEFAULT_GERMAN_TEMPLATE = """{{NAME}}
{{ADRESSE}}
{{PLZ_ORT}}
{{TELEFON}} | {{EMAIL}}

{{FIRMA}}
z.Hd. {{ANSPRECHPARTNER}}

{{STADT}}, {{DATUM}}

Bewerbung als {{POSITION}}

{{ANSPRECHPARTNER}},

{{EINLEITUNG}}

Ich bin überzeugt, dass ich mit meiner Erfahrung und meinem Engagement einen wertvollen Beitrag zu {{FIRMA}} leisten kann. Gerne möchte ich Sie in einem persönlichen Gespräch von meiner Eignung überzeugen.

Über eine Einladung zu einem Vorstellungsgespräch würde ich mich sehr freuen.

Mit freundlichen Grüßen
{{NAME}}"""


def create_default_template(user_id: int) -> Template:
    """Create a default German Anschreiben template for a user.

    This is called automatically when a user tries to generate an application
    but has no templates configured.

    Args:
        user_id: The ID of the user to create the template for.

    Returns:
        The newly created Template object.
    """
    template = Template(
        user_id=user_id,
        name="Standard-Vorlage (automatisch erstellt)",
        content=DEFAULT_GERMAN_TEMPLATE,
        is_default=True,
        is_pdf_template=False,
    )

    db.session.add(template)
    db.session.commit()

    return template


def get_or_create_default_template(user_id: int) -> Template:
    """Get the user's default template, creating one if none exists.

    Args:
        user_id: The ID of the user.

    Returns:
        The user's default template (existing or newly created).
    """
    # First try to get the default template
    template = Template.query.filter_by(user_id=user_id, is_default=True).first()
    if template:
        return template

    # Then try to get any template
    template = Template.query.filter_by(user_id=user_id).first()
    if template:
        return template

    # No template exists, create the default one
    return create_default_template(user_id)
