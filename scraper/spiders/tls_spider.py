# -*- coding: utf-8 -*-

import scrapy, logging
from scraper.items import TlsEntry
logger = logging.getLogger('tls')

class TlsSpider(scrapy.Spider):
    name = 'tls'
    allowed_domains = ['tennisleaguestats.com']
    start_urls = ['http://tennisleaguestats.com']

    def parse(self, response):
        for url_obj in response.xpath('//p/a[@href]'):
            year = int(url_obj.xpath('text()').extract_first())
            url = url_obj.xpath('@href').extract_first()
            logger.info('year = {}'.format(year))
            logger.info('url = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_year)
            request.meta['year'] = year
            yield request

    def parse_year(self, response):
        for url_obj in response.xpath('//table/tr/td/a[@href]'):
            section = url_obj.xpath('text()').extract_first()
            logger.info('section = {}'.format(section))
            url = url_obj.xpath('@href').extract_first()
            request = scrapy.Request(response.urljoin(url), self.parse_section)
            request.meta['year'] = response.meta['year']
            request.meta['section'] = section
            yield request

    def parse_section(self, response):
        for url_obj in response.xpath('//p[@class="center"]/a[@href]'):
            area = url_obj.xpath('text()').extract_first()
            logger.info('area = {}'.format(area))
            url = url_obj.xpath('@href').extract_first()
            request = scrapy.Request(response.urljoin(url), self.parse_area)
            request.meta['year'] = response.meta['year']
            request.meta['section'] = response.meta['section']
            request.meta['area'] = area
            yield request

    def parse_area(self, response):
        for url in response.xpath('//table')[-1].xpath(
            'tr/td/a[contains(@href, "All") and contains(@href, "n.htm")]/@href'
        ).extract():
            request = scrapy.Request(response.urljoin(url), self.parse_list)
            request.meta['year'] = response.meta['year']
            request.meta['section'] = response.meta['section']
            request.meta['area'] = response.meta['area']
            yield request

    def parse_list(self, response):
        for row in response.xpath('//table')[-1].xpath(
            '//tr[contains(td/@class, "tdatlevel")]'
        ):
            name = row.xpath('td/a[@href]/text()').extract_first()
            cols = row.xpath('td/text()').extract()
            if name:
                entry = TlsEntry()
                entry['name'] = name
                entry['year'] = response.meta['year']
                entry['section'] = response.meta['section']
                entry['area'] = response.meta['area']
                entry['facility'] = cols[3]
                entry['level'] = cols[10] + cols[11]
            else:
                entry['league'] = cols[2]
                entry['flight'] = cols[3]
                entry['matches'] = {'W': int(cols[5]), 'L': int(cols[6])}
                entry['games'] = {'W': int(cols[7]), 'L': int(cols[8])}
                try:
                    entry['rating'] = float(cols[9])
                except ValueError:
                    continue
                yield entry
