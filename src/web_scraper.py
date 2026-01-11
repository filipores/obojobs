import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin, urlparse


class WebScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def fetch_job_posting(self, url: str) -> Dict[str, any]:
        """
        Fetched eine Stellenanzeige von einer URL und extrahiert Text + Links.

        Returns:
            Dict mit 'text', 'links', 'email_links', 'application_links'
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'html.parser')

            # Entferne Script/Style Tags
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Extrahiere Text
            text = soup.get_text(separator='\n', strip=True)

            # Bereinige Text (mehrfache Leerzeilen)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)

            # Extrahiere alle Links
            all_links = []
            email_links = []
            application_links = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text(strip=True)

                # Absolute URL
                absolute_url = urljoin(url, href)

                all_links.append({
                    'url': absolute_url,
                    'text': link_text
                })

                # Email Links
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0]
                    email_links.append({
                        'email': email,
                        'text': link_text
                    })

                # Bewerbungs-Links (Heuristik)
                if any(keyword in href.lower() or keyword in link_text.lower()
                       for keyword in ['bewerbung', 'apply', 'application', 'bewerben', 'job', 'karriere']):
                    application_links.append({
                        'url': absolute_url,
                        'text': link_text
                    })

            return {
                'text': clean_text,
                'all_links': all_links,
                'email_links': email_links,
                'application_links': application_links,
                'source_url': url
            }

        except requests.RequestException as e:
            raise Exception(f"Fehler beim Laden der URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der Seite: {str(e)}")

    def extract_company_name_from_url(self, url: str) -> str:
        """Versucht, Firmennamen aus URL zu extrahieren."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        company = domain.split('.')[0]
        return company.capitalize()
