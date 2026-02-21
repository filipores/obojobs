<template>
  <div class="legal-page">
    <div class="container container-md">
      <!-- Header -->
      <section class="page-header animate-fade-up">
        <router-link to="/" class="back-link">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Zurück
        </router-link>
        <h1>Datenschutzerklärung</h1>
      </section>

      <!-- Content -->
      <section class="legal-content zen-card animate-fade-up" style="animation-delay: 100ms;">

        <div class="legal-section">
          <h2>1. Datenschutz auf einen Blick</h2>

          <h3>Allgemeine Hinweise</h3>
          <p>
            Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit deinen
            personenbezogenen Daten passiert, wenn du diese Website besuchst. Personenbezogene
            Daten sind alle Daten, mit denen du persönlich identifiziert werden kannst.
          </p>

          <h3>Datenerfassung auf dieser Website</h3>
          <p>
            <strong>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</strong><br>
            Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber.
            Dessen Kontaktdaten kannst du dem Impressum dieser Website entnehmen.
          </p>
          <p>
            <strong>Wie erfassen wir deine Daten?</strong><br>
            Deine Daten werden zum einen dadurch erhoben, dass du uns diese mitteilst.
            Hierbei kann es sich z.B. um Daten handeln, die du bei der Registrierung eingibst.
            Andere Daten werden automatisch beim Besuch der Website durch unsere IT-Systeme erfasst.
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>2. Hosting</h2>
          <p>
            Wir hosten die Inhalte unserer Website bei folgendem Anbieter:
          </p>
          <h3>Hetzner</h3>
          <p>
            Anbieter ist die Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen
            (nachfolgend Hetzner). Wenn du unsere Website besuchst, erfasst Hetzner
            verschiedene Logfiles inklusive deiner IP-Adressen.
          </p>
          <p>
            Details entnimmst du der Datenschutzerklärung von Hetzner:
            <a href="https://www.hetzner.com/de/rechtliches/datenschutz" target="_blank" rel="noopener">
              https://www.hetzner.com/de/rechtliches/datenschutz
            </a>
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>3. Allgemeine Hinweise und Pflichtinformationen</h2>

          <h3>Datenschutz</h3>
          <p>
            Die Betreiber dieser Seiten nehmen den Schutz deiner persönlichen Daten sehr ernst.
            Wir behandeln deine personenbezogenen Daten vertraulich und entsprechend den
            gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.
          </p>

          <h3>Hinweis zur verantwortlichen Stelle</h3>
          <p>
            Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:<br><br>
            {{ legal.company_name }}<br>
            {{ legal.company_address }}<br>
            {{ legal.company_postal_code }} {{ legal.company_city }}<br>
            E-Mail: <a :href="'mailto:' + legal.company_email">{{ legal.company_email }}</a>
          </p>

          <h3>Speicherdauer</h3>
          <p>
            Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer
            genannt wurde, verbleiben deine personenbezogenen Daten bei uns, bis der Zweck
            für die Datenverarbeitung entfällt. Wenn du ein berechtigtes Löschersuchen
            geltend machst oder eine Einwilligung zur Datenverarbeitung widerrufst, werden
            deine Daten gelöscht, sofern wir keine anderen rechtlich zulässigen Gründe für
            die Speicherung deiner personenbezogenen Daten haben.
          </p>

          <h3>Rechtsgrundlagen der Verarbeitung</h3>
          <p>Wir verarbeiten deine Daten auf folgenden Rechtsgrundlagen:</p>
          <ul>
            <li><strong>Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)</strong> - Google OAuth, E-Mail-Kontoverknüpfung</li>
            <li><strong>Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)</strong> - Kontoverwaltung, KI-gestützte Bewerbungserstellung, Zahlungsabwicklung</li>
            <li><strong>Art. 6 Abs. 1 lit. f DSGVO (Berechtigtes Interesse)</strong> - Technische Nutzungsdaten, Sicherheitsmaßnahmen, Fehlerbehebung</li>
          </ul>

          <h3>Deine Rechte</h3>
          <p>Du hast jederzeit das Recht:</p>
          <ul>
            <li><strong>Auskunft</strong> (Art. 15 DSGVO) - über deine bei uns gespeicherten Daten zu erhalten</li>
            <li><strong>Berichtigung</strong> (Art. 16 DSGVO) - unrichtige Daten korrigieren zu lassen</li>
            <li><strong>Löschung</strong> (Art. 17 DSGVO) - deine Daten löschen zu lassen</li>
            <li><strong>Einschränkung</strong> (Art. 18 DSGVO) - die Verarbeitung einzuschränken</li>
            <li><strong>Widerspruch</strong> (Art. 21 DSGVO) - der Verarbeitung zu widersprechen</li>
            <li><strong>Datenportabilität</strong> (Art. 20 DSGVO) - deine Daten in einem gängigen Format zu erhalten</li>
          </ul>
          <p>
            Zur Ausübung deiner Rechte kontaktiere uns bitte unter
            <a :href="'mailto:' + legal.company_email">{{ legal.company_email }}</a>.
          </p>

          <h3>Beschwerderecht bei einer Aufsichtsbehörde</h3>
          <p>
            Wenn du der Ansicht bist, dass die Verarbeitung deiner personenbezogenen Daten
            gegen die DSGVO verstößt, hast du das Recht, dich bei einer Datenschutz-Aufsichtsbehörde
            zu beschweren. Du kannst dich insbesondere an die Aufsichtsbehörde deines
            üblichen Aufenthaltsortes, deines Arbeitsplatzes oder unseres Firmensitzes wenden.
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>4. Datenerfassung auf dieser Website</h2>

          <h3>Registrierung und Benutzerkonto</h3>
          <p>
            Wenn du dich auf unserer Website registrierst, speichern wir folgende Daten:
          </p>
          <ul>
            <li>E-Mail-Adresse</li>
            <li>Passwort (verschlüsselt gespeichert)</li>
            <li>Vollständiger Name</li>
            <li>Telefonnummer (optional)</li>
            <li>Adresse (optional, für Bewerbungsschreiben)</li>
          </ul>
          <p>
            Diese Daten werden zur Bereitstellung unseres Dienstes benötigt und auf Grundlage
            von Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) verarbeitet.
          </p>

          <h3>Erstellte Bewerbungen</h3>
          <p>
            Die über unsere Plattform generierten Bewerbungen (Anschreiben, ATS-Analysen,
            Interviewfragen) werden in deinem Benutzerkonto gespeichert, bis du diese
            eigenständig löschst oder dein Konto löschen lässt. Die Verarbeitung erfolgt
            auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).
          </p>

          <h3>Nutzungsdaten</h3>
          <p>
            Bei der Nutzung unserer Plattform erfassen wir automatisch technische Daten
            wie IP-Adresse, Browsertyp, Betriebssystem und Zeitpunkt des Zugriffs.
            Diese Daten werden auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO
            (berechtigtes Interesse) zur Sicherstellung des Betriebs und zur
            Fehlerbehebung verarbeitet.
          </p>

          <h3>Hochgeladene Dokumente</h3>
          <p>
            Du kannst Dokumente (Lebensläufe, Zeugnisse) hochladen. Diese werden auf unserem
            Server gespeichert und nur für die Erstellung deiner Bewerbungen verwendet.
            Die Dokumente werden nicht an Dritte weitergegeben (außer an die unten genannten
            Dienste zur Verarbeitung).
          </p>

          <h3>Cookies und Local Storage</h3>
          <p>
            Wir verwenden keine Tracking-Cookies. Wir speichern ausschließlich folgende
            Daten im Local Storage deines Browsers:
          </p>
          <ul>
            <li>Authentifizierungs-Token (JWT) zur Identifizierung deiner Session</li>
            <li>Spracheinstellung (Deutsch/Englisch)</li>
            <li>Theme-Einstellung (Hell-/Dunkelmodus)</li>
          </ul>
          <p>
            Diese Daten enthalten keine personenbezogenen Informationen und dienen
            ausschließlich der Funktionalität der Website.
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>5. Externe Dienste</h2>

          <h3>Anthropic (Claude API)</h3>
          <p>
            Für die KI-gestützte Generierung von Bewerbungstexten nutzen wir die API von
            Anthropic, PBC (USA). Dabei werden folgende Daten übermittelt:
          </p>
          <ul>
            <li>Inhalte deiner hochgeladenen Dokumente (zur Textgenerierung)</li>
            <li>Informationen zur Stellenanzeige</li>
          </ul>
          <p>
            Anthropic verarbeitet diese Daten auf Servern in den USA. Es besteht ein
            angemessenes Datenschutzniveau gemäß EU-US Data Privacy Framework.
          </p>
          <p>
            Datenschutzerklärung von Anthropic:
            <a href="https://www.anthropic.com/privacy" target="_blank" rel="noopener">
              https://www.anthropic.com/privacy
            </a>
          </p>

          <h3>Stripe</h3>
          <p>
            Für Zahlungen nutzen wir Stripe, Inc. (USA). Bei der Zahlung werden deine
            Zahlungsdaten direkt an Stripe übermittelt und dort verarbeitet. Wir
            speichern keine vollständigen Kreditkartendaten auf unseren Servern.
            Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO
            (Vertragserfüllung).
          </p>
          <p>
            Datenschutzerklärung von Stripe:
            <a href="https://stripe.com/privacy" target="_blank" rel="noopener">
              https://stripe.com/privacy
            </a>
          </p>

          <h3>Google OAuth</h3>
          <p>
            Du kannst dich optional über dein Google-Konto bei uns anmelden. Dabei
            werden dein Name und deine E-Mail-Adresse von Google an uns übermittelt.
            Wir speichern keine Google-Passwörter. Die Verarbeitung erfolgt auf
            Grundlage von Art. 6 Abs. 1 lit. a DSGVO (Einwilligung).
          </p>
          <p>
            Datenschutzerklärung von Google:
            <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">
              https://policies.google.com/privacy
            </a>
          </p>

          <h3>Gmail und Outlook (E-Mail-Versand)</h3>
          <p>
            Du kannst optional dein Gmail- oder Outlook-Konto verbinden, um Bewerbungen
            direkt per E-Mail zu versenden. Dabei werden OAuth-Zugangstokens verschlüsselt
            auf unserem Server gespeichert. Wir greifen ausschließlich zum Versenden deiner
            Bewerbungen auf dein E-Mail-Konto zu. Die Verarbeitung erfolgt auf Grundlage
            von Art. 6 Abs. 1 lit. a DSGVO (Einwilligung). Du kannst die Verbindung
            jederzeit in deinen Kontoeinstellungen widerrufen.
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>6. Speicherdauer und Datenlöschung</h2>
          <p>
            Deine Kontodaten (Name, E-Mail, Passwort) werden gespeichert, bis du dein
            Konto löschen lässt. Deine Bewerbungen und hochgeladenen Dokumente werden
            gespeichert, bis du diese eigenständig löschst oder dein Konto löschen lässt.
          </p>
          <p>
            Du kannst dein Konto jederzeit löschen lassen. Kontaktiere uns dazu
            per E-Mail an <a :href="'mailto:' + legal.company_email">{{ legal.company_email }}</a>.
            Bei der Kontolöschung werden alle deine personenbezogenen Daten,
            hochgeladenen Dokumente und erstellten Bewerbungen unwiderruflich gelöscht.
          </p>
          <p>
            Ausgenommen sind Daten, die wir aus gesetzlichen Gründen aufbewahren müssen
            (z.B. Rechnungsdaten für steuerliche Zwecke - 10 Jahre gemäß § 147 AO).
          </p>
        </div>

        <div class="legal-footer">
          <p class="last-updated">Stand: Februar 2026</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useLegalInfo } from '@/composables/useLegalInfo.js'

const { legal } = useLegalInfo()
</script>
