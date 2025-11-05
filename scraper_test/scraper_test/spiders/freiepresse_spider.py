import scrapy
from urllib.parse import urlencode

class FreiePresseSpider(scrapy.Spider):
    name = 'freiepresse'
    allowed_domains = ['freiepresse.de']
    
    # Starte bei Seite 0. Die Paginierung wird im parse-Schritt angepasst.
    start_urls = ['https://www.freiepresse.de/archiv?page=0']
    
    # Zähler für die Paginierung
    page_number = 0

    def parse(self, response):
        
        # 🎯 Selektor für den Einzel-Artikel-Container (Der äußere <a>-Tag)
        # Dieser Tag hat die URL im href-Attribut.
        # Im Screenshot sichtbar: <a class="article-preview card article-preview--desktop ...">
        artikel_container = response.css('a.article-preview.card') 
        
        if not artikel_container:
            # STOPP: Wenn auf der aktuellen Seite keine Artikel mehr gefunden werden, beende den Crawl.
            self.logger.info(f"Keine Artikel mehr auf Seite {self.page_number} gefunden. Beende Crawl.")
            return

        for artikel in artikel_container:
            # Die Artikel-Daten extrahieren
            
            # 1. URL ist das href-Attribut des Containers selbst
            link_ziel = artikel.css('::attr(href)').get()
            
            # 2. Titel: Meistens in einem div mit dem Suffix __title
            titel = artikel.css('.article-preview__title::text').get()
            
            # 3. Teaser: Bestätigt durch deine Analyse
            teaser = artikel.css('.article-preview__teaser::text').get()
            
            # 4. Datum/Zeit: Der Lesbarkeits-Indikator (z.B. "2 min.") ist sichtbar
            lesezeit = artikel.css('.article-preview__readtime::text').get()

            yield {
                'titel': titel.strip() if titel else 'N/A',
                'link': response.urljoin(link_ziel) if link_ziel else 'N/A',
                'teaser': teaser.strip() if teaser else 'N/A',
                'lesezeit': lesezeit.strip() if lesezeit else 'N/A',
            }

        # 🔄 Paginierungs-Logik: Baue den Link zur nächsten Seite
        self.page_number += 1
        
        # Erstellt die URL für die nächste Seite, z.B. https://www.freiepresse.de/archiv?page=1
        naechste_seite_url = response.urljoin(f"/archiv?page={self.page_number}")
        
        # Folge der neuen URL und rufe dieselbe parse-Methode erneut auf
        yield response.follow(naechste_seite_url, callback=self.parse)