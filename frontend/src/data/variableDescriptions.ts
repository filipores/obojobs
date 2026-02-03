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
}
