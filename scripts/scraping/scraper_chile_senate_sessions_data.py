import scrapy
import locale
from datetime import datetime
import io

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import logging
from scrapy.http import Request
from scrapy.spider import BaseSpider

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
logging.propagate = False 
logging.getLogger("pdfminer").setLevel(logging.ERROR)
class SenadoSesionesScraper(BaseSpider):
    name = "senadosesiones_spider"
    def __init__(self,  *args, **kwargs):
        super(SenadoSesionesScraper, self).__init__(*args, **kwargs)
        
        self.BASE_URL = 'http://www.senado.cl/'
        self.PATH = './'
        
    def make_legislatura_url(self, legi):
        url = '{}appsenado/index.php?mo=sesionessala&ac=listado&listado=1&legi={}'.format(self.BASE_URL, legi)
        self.logger.info('Going to  %s', url)
        return url
    
    start_urls = ['http://www.senado.cl/appsenado/index.php?mo=sesionessala&ac=listado&listado=1&legi=161']

    def parse(self, response):
        ##Obtenemos todas las legislaturas y las mandamos al parser
        
        for legislatura in response.css("[name=legislaturas] > option ::attr(value)").extract():
            self.logger.info('Parseando la legislatura : %s', legislatura)
            for sesion in response.css(".seccion2 tr"):
                try:
                    Tipo = sesion.css("td:nth-child(2) ::text").extract()[0].strip().replace(' ', '_')
                    Fecha =  datetime.strptime(sesion.css("td:nth-child(3) ::text").extract()[0], "%A %d de %B de %Y").strftime("%Y%m%d")
                    PDF = sesion.css("td:nth-child(7) > a:nth-child(2) ::attr(href)").extract()[0]
                    self.logger.info('Parseaado  %s', PDF)
                    yield Request(self.BASE_URL + PDF, dont_filter=True, callback=self.save_pdf,
                                meta={
                                    'filename': '{legislatura}__{fecha}__{tipo}.pdf'.format(legislatura=legislatura, fecha=Fecha, tipo=Tipo)
                                        })
                except Exception as e:
                    self.logger.info(e)
                    pass
    def save_pdf(self, response):
            path = self.PATH + response.meta['filename']
            self.logger.info('Saving PDF %s', path)
            with open(path, 'wb') as f:
                f.write(response.body)
            self.logger.info('Extracting text from PDF %s', path)
            text = self.convert_pdf_to_txt(path)
            text_file = open(path + '.txt', "w")
            text_file.write(text)
            text_file.close()
    def convert_pdf_to_txt(self, path):
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                    password=password,
                                    caching=caching,
                                    check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        return text
