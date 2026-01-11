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
        <h1>Impressum</h1>
      </section>

      <!-- Content -->
      <section class="legal-content zen-card animate-fade-up" style="animation-delay: 100ms;">
        <div class="legal-section">
          <h2>Angaben gemäß § 5 TMG</h2>
          <p>
            <strong>[Ihr vollständiger Name]</strong><br>
            [Ihre Straße und Hausnummer]<br>
            [PLZ und Stadt]<br>
            Deutschland
          </p>
        </div>

        <div class="legal-section">
          <h2>Kontakt</h2>
          <p>
            E-Mail: <a href="mailto:kontakt@ihre-domain.de">kontakt@ihre-domain.de</a>
          </p>
        </div>

        <div class="legal-section">
          <h2>Umsatzsteuer-ID</h2>
          <p>
            Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
            [Ihre USt-ID, falls vorhanden, sonst diesen Abschnitt entfernen]
          </p>
        </div>

        <div class="legal-section">
          <h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
          <p>
            [Ihr vollständiger Name]<br>
            [Ihre Adresse]
          </p>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h2>Haftungsausschluss</h2>

          <h3>Haftung für Inhalte</h3>
          <p>
            Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen
            Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind
            wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte
            fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine
            rechtswidrige Tätigkeit hinweisen.
          </p>
          <p>
            Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach
            den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung
            ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung
            möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese
            Inhalte umgehend entfernen.
          </p>

          <h3>Haftung für Links</h3>
          <p>
            Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir
            keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine
            Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige
            Anbieter oder Betreiber der Seiten verantwortlich.
          </p>

          <h3>Urheberrecht</h3>
          <p>
            Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten
            unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung,
            Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes
            bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
          </p>
        </div>

        <div class="legal-section">
          <h2>Streitschlichtung</h2>
          <p>
            Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS)
            bereit: <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener">
            https://ec.europa.eu/consumers/odr/</a>
          </p>
          <p>
            Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
            Verbraucherschlichtungsstelle teilzunehmen.
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
