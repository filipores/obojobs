/**
 * Variable Descriptions
 *
 * Detailed explanations and real examples for template variables.
 * Used in VariableChip tooltips to educate users about each variable.
 */

export interface VariableDescription {
  title: string
  description: string
  example: string
  aiNote?: string
}

export const variableDescriptions: Record<string, VariableDescription> = {
  FIRMA: {
    title: 'Firmenname',
    description: 'Der Name des Unternehmens aus der Stellenanzeige. Wird automatisch aus den Jobdetails übernommen.',
    example: 'BMW Group',
  },

  POSITION: {
    title: 'Stellenbezeichnung',
    description: 'Die genaue Bezeichnung der Stelle. Wird direkt aus der Stellenanzeige übernommen.',
    example: 'Senior Software Engineer',
  },

  ANSPRECHPARTNER: {
    title: 'Ansprechpartner',
    description: 'Die persönliche Anrede mit Namen. Falls kein Name bekannt ist, wird eine neutrale Anrede verwendet.',
    example: 'Sehr geehrte Frau Schmidt',
  },

  QUELLE: {
    title: 'Jobquelle',
    description: 'Wo Sie die Stelle gefunden haben. Zeigt dem Arbeitgeber, dass Sie sich informiert haben.',
    example: 'LinkedIn',
  },

  EINLEITUNG: {
    title: 'Einleitung',
    description: 'Ein personalisierter Einstieg, der Ihre Qualifikationen mit den Anforderungen der Stelle verbindet.',
    example: 'Als erfahrener Full-Stack-Entwickler mit 5 Jahren Expertise in React und Node.js hat mich Ihre Suche nach jemandem, der innovative Webanwendungen entwickelt, sofort angesprochen.',
    aiNote: 'KI-generiert aus Ihrem Lebenslauf und der Stellenanzeige',
  },

  NAME: {
    title: 'Ihr Name',
    description: 'Ihr vollständiger Name aus den Profileinstellungen. Wird im Briefkopf und der Unterschrift verwendet.',
    example: 'Max Mustermann',
  },

  EMAIL: {
    title: 'E-Mail-Adresse',
    description: 'Ihre E-Mail-Adresse aus dem Profil. Wird im Briefkopf für die Kontaktdaten verwendet.',
    example: 'max.mustermann@email.de',
  },

  TELEFON: {
    title: 'Telefonnummer',
    description: 'Ihre Telefonnummer aus den Profileinstellungen. Wird im Briefkopf angezeigt.',
    example: '+49 170 1234567',
  },

  ADRESSE: {
    title: 'Straße und Hausnummer',
    description: 'Ihre Straßenadresse aus den Profileinstellungen. Wird im Briefkopf verwendet.',
    example: 'Musterstraße 42',
  },

  PLZ_ORT: {
    title: 'PLZ und Ort',
    description: 'Postleitzahl und Stadt aus den Profileinstellungen, automatisch zusammengesetzt.',
    example: '80331 München',
  },

  DATUM: {
    title: 'Aktuelles Datum',
    description: 'Das Datum der Bewerbungserstellung, automatisch im deutschen Format.',
    example: '06. Februar 2026',
  },

  WEBSEITE: {
    title: 'Website',
    description: 'Ihre persönliche Website oder Portfolio-URL aus den Profileinstellungen.',
    example: 'www.maxmustermann.de',
  },

  STADT: {
    title: 'Stadt',
    description: 'Ihre Stadt aus den Profileinstellungen. Wird z.B. für die Ortsangabe im Datum verwendet.',
    example: 'München',
  },

  KONTAKT_ZEILE: {
    title: 'Kontaktzeile',
    description: 'Telefon und E-Mail zusammengefasst. Leere Felder werden automatisch ausgelassen.',
    example: '+49 170 1234567 | max@email.de',
  },

  ORT_DATUM: {
    title: 'Ort und Datum',
    description: 'Stadt und Datum zusammengefasst. Falls keine Stadt hinterlegt ist, wird nur das Datum angezeigt.',
    example: 'München, 06. Februar 2026',
  },
}
