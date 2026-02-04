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
            Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren
            personenbezogenen Daten passiert, wenn Sie diese Website besuchen. Personenbezogene
            Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.
          </p>

          <h3>Datenerfassung auf dieser Website</h3>
          <p>
            <strong>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</strong><br>
            Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber.
            Dessen Kontaktdaten können Sie dem Impressum dieser Website entnehmen.
          </p>
          <p>
            <strong>Wie erfassen wir Ihre Daten?</strong><br>
            Ihre Daten werden zum einen dadurch erhoben, dass Sie uns diese mitteilen.
            Hierbei kann es sich z.B. um Daten handeln, die Sie bei der Registrierung eingeben.
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
            (nachfolgend Hetzner). Wenn Sie unsere Website besuchen, erfasst Hetzner
            verschiedene Logfiles inklusive Ihrer IP-Adressen.
          </p>
          <p>
            Details entnehmen Sie der Datenschutzerklärung von Hetzner:
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
            Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst.
            Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend den
            gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.
          </p>

          <h3>Hinweis zur verantwortlichen Stelle</h3>
          <p>
            Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:<br><br>
            Filip Ores<br>
            Hamburg<br>
            E-Mail: filip.ores@hotmail.com
          </p>

          <h3>Speicherdauer</h3>
          <p>
            Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer
            genannt wurde, verbleiben Ihre personenbezogenen Daten bei uns, bis der Zweck
            für die Datenverarbeitung entfällt. Wenn Sie ein berechtigtes Löschersuchen
            geltend machen oder eine Einwilligung zur Datenverarbeitung widerrufen, werden
            Ihre Daten gelöscht, sofern wir keine anderen rechtlich zulässigen Gründe für
            die Speicherung Ihrer personenbezogenen Daten haben.
          </p>

          <h3>Ihre Rechte</h3>
          <p>Sie haben jederzeit das Recht:</p>
          <ul>
            <li>Auskunft über Ihre bei uns gespeicherten Daten zu erhalten</li>
            <li>Diese Daten berichtigen oder löschen zu lassen</li>
            <li>Die Verarbeitung einzuschränken</li>
            <li>Der Verarbeitung zu widersprechen</li>
            <li>Ihre Daten in einem gängigen Format zu erhalten (Datenportabilität)</li>
          </ul>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>4. Datenerfassung auf dieser Website</h2>

          <h3>Registrierung und Benutzerkonto</h3>
          <p>
            Wenn Sie sich auf unserer Website registrieren, speichern wir folgende Daten:
          </p>
          <ul>
            <li>E-Mail-Adresse</li>
            <li>Passwort (verschlüsselt gespeichert)</li>
            <li>Vollständiger Name</li>
          </ul>
          <p>
            Diese Daten werden zur Bereitstellung unseres Dienstes benötigt und auf Grundlage
            von Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) verarbeitet.
          </p>

          <h3>Hochgeladene Dokumente</h3>
          <p>
            Sie können Dokumente (Lebensläufe, Zeugnisse) hochladen. Diese werden auf unserem
            Server gespeichert und nur für die Erstellung Ihrer Bewerbungen verwendet.
            Die Dokumente werden nicht an Dritte weitergegeben (außer an die unten genannten
            Dienste zur Verarbeitung).
          </p>

          <h3>Cookies und Local Storage</h3>
          <p>
            Wir verwenden keine Tracking-Cookies. Für die Authentifizierung speichern wir
            einen JWT-Token im Local Storage Ihres Browsers. Dieser Token enthält keine
            persönlichen Daten und dient ausschließlich der Identifizierung Ihrer Session.
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
            <li>Inhalte Ihrer hochgeladenen Dokumente (zur Textgenerierung)</li>
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
            Für Zahlungen nutzen wir Stripe, Inc. (USA). Bei der Zahlung werden Ihre
            Zahlungsdaten direkt an Stripe übermittelt und dort verarbeitet. Wir
            speichern keine vollständigen Kreditkartendaten auf unseren Servern.
          </p>
          <p>
            Datenschutzerklärung von Stripe:
            <a href="https://stripe.com/privacy" target="_blank" rel="noopener">
              https://stripe.com/privacy
            </a>
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>6. Datenlöschung</h2>
          <p>
            Sie können Ihr Konto jederzeit löschen lassen. Kontaktieren Sie uns dazu per
            E-Mail. Bei der Kontolöschung werden alle Ihre personenbezogenen Daten,
            hochgeladenen Dokumente und erstellten Bewerbungen unwiderruflich gelöscht.
          </p>
          <p>
            Ausgenommen sind Daten, die wir aus gesetzlichen Gründen aufbewahren müssen
            (z.B. Rechnungsdaten für steuerliche Zwecke - 10 Jahre).
          </p>
        </div>

        <div class="legal-footer">
          <p class="last-updated">Stand: Januar 2026</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
// Static page - styles defined in assets/styles.css under .legal-page
</script>
