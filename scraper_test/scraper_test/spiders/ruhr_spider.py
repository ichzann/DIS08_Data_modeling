import scrapy
import json
from urllib.parse import urlencode

class RuhrSpider(scrapy.Spider):
    name = 'ruhr'
    allowed_domains = ['ruhrnachrichten.de']
    start_urls = ['https://www.ruhrnachrichten.de/dortmund']
    
    # Basis für die AJAX-Anfragen (mit allen identifizierten Platzhaltern)
    ajax_url_base = 'https://www.ruhrnachrichten.de/api/tns/more-articles/?offset={offset}&per_page={per_page}&order={order}&dateheading={dateheading}&tag={tag}&familytag={familytag}&immobilientag={immobilientag}&unternehmens_tag={unternehmens_tag}'

    # Konstanten, die aus dem ersten "Mehr Artikel" Button ausgelesen werden
    per_page_count = 50 # Standardwert, wird durch Button überschrieben
    last_params = {}

    def parse(self, response):
        
        # --- 1. DATEN VOM BUTTON AUSLESEN (Initialer AJAX-Setup) ---
        more_button = response.css('.load-more-button.teaser-bundle__more-button')
        
        if more_button:
            # Speichere die festen Parameter für alle zukünftigen Requests
            self.per_page_count = more_button.css('::attr(data-per-load)').get()
            
            # WICHTIG: Die data-last-param sind JSON und enthalten die Tags/Order-Parameter
            try:
                self.last_params = json.loads(more_button.css('::attr(data-last-param)').get())
            except (json.JSONDecodeError, TypeError):
                self.logger.error("Fehler beim Parsen der data-last-param. Verwende leeres Dict.")
                self.last_params = {}

            # Bestimme den initialen Offset (die Anzahl der bereits geladenen Artikel)
            initial_offset = len(response.css('article.teaser-bundle__item'))
            
            # Sende den ersten AJAX-Request und starte die Kette
            yield self.make_ajax_request(initial_offset)
            
        # --- 2. ARTIKEL VON DER STARTSEITE EXTRAHIEREN ---
        # Diese Artikel sind bereits im HTML enthalten und sollten zuerst verarbeitet werden.
        # Wichtig: Wähle den äußeren Container, der alle Artikel von der Startseite umschließt.
        for artikel in response.css('.teaser-bundle__item article'):
            # Gehe zum allgemeinen Link-Element für die URL
            link_element = artikel.css('a::attr(href)').get()
            
            yield {
                'titel': artikel.css('.teaser-title span.teaser__link::text').get().strip() if artikel.css('.teaser-title span.teaser__link::text').get() else 'N/A',
                # Korrigierter Selektor basierend auf deinem Screenshot ('teaser__sub-title')
                'untertitel': artikel.css('.teaser__sub-title::text').get().strip() if artikel.css('.teaser__sub-title::text').get() else 'N/A',
                'datum': artikel.css('.teaser__date::text').get().strip() if artikel.css('.teaser__date::text').get() else 'N/A',
                'link': response.urljoin(link_element) if link_element else 'N/A',
                'bild_url': artikel.css('img::attr(src)').get(),
            }


    def make_ajax_request(self, offset):
        # Fülle die Platzhalter in der ajax_url_base mit den extrahierten Werten
        url = self.ajax_url_base.format(
            offset=offset,
            per_page=self.per_page_count,
            # Verwende die persistenten Parameter aus dem initialen Button
            order=self.last_params.get('order', ''),
            dateheading=self.last_params.get('dateheading', ''),
            tag=self.last_params.get('tag', ''),
            familytag=self.last_params.get('familytag', ''),
            immobilientag=self.last_params.get('immobilientag', ''),
            unternehmens_tag=self.last_params.get('unternehmens_tag', '')
        )
        
        # Sende den Request an die API und speichere den aktuellen Offset
        return scrapy.Request(url, callback=self.parse_ajax_articles, meta={'offset': offset})

    def parse_ajax_articles(self, response):
        # --- 3. VERARBEITUNG DER AJAX-ANTWORT (Nachgeladene Artikel) ---
        
        # Die AJAX-Antwort sollte die reinen HTML-Blöcke der Artikel enthalten.
        # Wir suchen wieder nach den Artikel-Containern
        artikel_container = response.css('article.teaser-bundle__item')

        if not artikel_container:
            # STOPP: Wenn die API keine weiteren Artikel-HTML-Blöcke zurückgibt.
            self.logger.info(f"AJAX-Crawl beendet nach Offset {response.meta['offset']}: Keine Artikel mehr gefunden.")
            return

        # Scrape die neu geladenen Artikel
        for artikel in artikel_container:
            link_element = artikel.css('a::attr(href)').get()

            yield {
                'titel': artikel.css('.teaser-title span.teaser__link::text').get().strip() if artikel.css('.teaser-title span.teaser__link::text').get() else 'N/A',
                'untertitel': artikel.css('.teaser__sub-title::text').get().strip() if artikel.css('.teaser__sub-title::text').get() else 'N/A',
                'datum': artikel.css('.teaser__date::text').get().strip() if artikel.css('.teaser__date::text').get() else 'N/A',
                'link': response.urljoin(link_element) if link_element else 'N/A',
                'bild_url': artikel.css('img::attr(src)').get(),
            }

        # --- 4. NÄCHSTE AJAX-ANFRAGE SENDEN ---
        
        # Erhöhe den Offset um die Anzahl der gerade geladenen Artikel (per_page_count)
        current_offset = response.meta['offset']
        new_offset = current_offset + len(artikel_container)

        # Sende den nächsten Request
        yield self.make_ajax_request(new_offset)