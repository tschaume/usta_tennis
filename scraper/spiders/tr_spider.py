# -*- coding: utf-8 -*-

import scrapy, logging, re
from scraper.items import TrEntry
logger = logging.getLogger('tr')

class TrSpider(scrapy.Spider):
    name = 'tr'
    allowed_domains = ['tennisrecord.com']
    start_urls = ['http://www.tennisrecord.com/adult/ratingssection.aspx']

    def parse(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsdistrict')]"
        for url_obj in response.xpath(url_xpath):
            section = url_obj.xpath('text()').extract_first()
            url = url_obj.xpath('@href').extract_first()
            logger.info('section = {}'.format(section))
            logger.info('url = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_section)
            request.meta['section'] = section
            yield request
            break

    def parse_section(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsarea')]"
        for url_obj in response.xpath(url_xpath):
            district = url_obj.xpath('text()').extract_first()
            url = url_obj.xpath('@href').extract_first()
            logger.info('district = {}'.format(district))
            logger.info('url = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_district)
            request.meta['section'] = response.meta['section']
            request.meta['district'] = district
            yield request
            break

    def parse_district(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsgender')]"
        for url_obj in response.xpath(url_xpath):
            area = url_obj.xpath('text()').extract_first()
            url = url_obj.xpath('@href').extract_first()
            logger.info('area = {}'.format(area))
            logger.info('url = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_area)
            request.meta['section'] = response.meta['section']
            request.meta['district'] = response.meta['district']
            request.meta['area'] = area
            yield request
            break

    def parse_area(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsorderby')]"
        for url_obj in response.xpath(url_xpath):
            gender = url_obj.xpath('text()').extract_first()
            url = url_obj.xpath('@href').extract_first()
            logger.info('gender = {}'.format(gender))
            logger.info('url = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_gender)
            request.meta['section'] = response.meta['section']
            request.meta['district'] = response.meta['district']
            request.meta['area'] = response.meta['area']
            request.meta['gender'] = gender
            yield request
            break

    def parse_gender(self, response):
        url_xpath = "//a[text()='Estimated Dynamic Rating']/@href"
        url = response.xpath(url_xpath).extract_first()
        logger.info('url = {}'.format(url))
        request = scrapy.Request(response.urljoin(url), self.parse_ratings)
        request.meta['section'] = response.meta['section']
        request.meta['district'] = response.meta['district']
        request.meta['area'] = response.meta['area']
        request.meta['gender'] = response.meta['gender']
        yield request

    def parse_ratings(self, response):
        keys = []
        for idx, row in enumerate(response.xpath(
            '//table[2]/tr[2]/td/table/tr'
        )):
            if idx < 1:
                for td in row.xpath(
                    'td[string-length(normalize-space(text())) > 2]'
                ):
                    key = td.xpath(
                        "translate(normalize-space(), ' ', '')"
                    ).extract_first()
                    keys.append(re.sub('\d', '', key))
                logger.info('keys = {}'.format(keys))
            else:
                url_obj = row.xpath('td/a')
                name = url_obj.xpath('text()').extract_first()
                url = url_obj.xpath('@href').extract_first()
                logger.info('name = {}'.format(name))
                logger.info('url = {}'.format(url))
                entry = TrEntry()
                entry['section'] = response.meta['section']
                entry['district'] = response.meta['district']
                entry['area'] = response.meta['area']
                entry['gender'] = response.meta['gender']
                entry['name'] = name
                # TODO follow url for more player matches
                entry['ratings'] = {}
                for vidx, value in enumerate(row.xpath(
                    'td[string-length(normalize-space(text())) > 2]/text()'
                ).extract()):
                    try:
                        value = float(value)
                    except:
                        value = value.replace(' ', '')
                    entry['ratings'][keys[vidx+1]] = value
                yield entry
                break
