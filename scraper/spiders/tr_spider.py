# -*- coding: utf-8 -*-

import scrapy, logging, re, os
from scraper.items import TrEntry
from operator import itemgetter
from copy import deepcopy
from scraper.spiders.states import states
logger = logging.getLogger('tr')

class TrSpider(scrapy.Spider):
    name = 'tr'
    allowed_domains = ['tennisrecord.com', 'universaltennis.com']
    start_urls = ['https://universaltennis.com/login']
    utr_url = 'https://universaltennis.com/search?type=player&query={}'

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response, formdata={
                'Email': os.environ.get('UTR_USER'),
                'Password': os.environ.get('UTR_PWD')
            },
            callback=self.after_login
        )

    def after_login(self, response):
        if b"Please provide" in response.body:
            logger.error("UTR Login failed!")
            return
        logger.info("UTR Login succeeded!")
        yield scrapy.Request(
            'http://www.tennisrecord.com/adult/ratingssection.aspx',
            self.parse_tr
        )

    def parse_tr(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsdistrict')]"
        for url_obj in response.xpath(url_xpath):
            section = url_obj.xpath('text()').extract_first()
            if section != 'No California':
                continue
            url = url_obj.xpath('@href').extract_first()
            logger.info('section = {}'.format(section))
            request = scrapy.Request(response.urljoin(url), self.parse_section)
            request.meta['info'] = {'section': section}
            yield request

    def parse_section(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsarea')]"
        for url_obj in response.xpath(url_xpath):
            district = url_obj.xpath('text()').extract_first()
            if district != 'No. California':
                continue
            url = url_obj.xpath('@href').extract_first()
            logger.info('district = {}'.format(district))
            request = scrapy.Request(response.urljoin(url), self.parse_district)
            request.meta['info'] = deepcopy(response.meta['info'])
            request.meta['info']['district'] = district
            yield request

    def parse_district(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsgender')]"
        for url_obj in response.xpath(url_xpath):
            area = url_obj.xpath('text()').extract_first()
            #if area not in [
            #    'East Bay', 'Diablo North', 'Diablo South', 'Sacramento', 'San Francisco'
            #]:
            #    continue
            url = url_obj.xpath('@href').extract_first()
            logger.info('area = {}'.format(area))
            request = scrapy.Request(response.urljoin(url), self.parse_area)
            request.meta['info'] = deepcopy(response.meta['info'])
            request.meta['info']['area'] = area
            yield request

    def parse_area(self, response):
        url_xpath = "//a[starts-with(@href, '/adult/ratingsorderby')]"
        for url_obj in response.xpath(url_xpath):
            gender = url_obj.xpath('text()').extract_first()
            url = url_obj.xpath('@href').extract_first()
            logger.info('gender = {}'.format(gender))
            request = scrapy.Request(response.urljoin(url), self.parse_gender)
            request.meta['info'] = deepcopy(response.meta['info'])
            request.meta['info']['gender'] = gender
            yield request

    def parse_gender(self, response):
        url_xpath = "//a[text()='Estimated Dynamic Rating']/@href"
        url = response.xpath(url_xpath).extract_first()
        request = scrapy.Request(response.urljoin(url), self.parse_ratings)
        request.meta['info'] = deepcopy(response.meta['info'])
        yield request

    def parse_ratings(self, response):
        keys = ['place']
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
            else:
                url_obj = row.xpath('td/a')
                name = url_obj.xpath('text()').extract_first()
                logger.info('name = {}'.format(name))
                if self.db['trentries'].find({'info.name': name}).count():
                    logger.info('{} already in DB!'.format(name))
                    continue

                ratings = {}
                for vidx, value in enumerate(row.xpath(
                    'td[string-length(normalize-space(text())) > 0]/text()'
                ).extract()):
                    value = value.strip()
                    if vidx == 0:
                        ratings[keys[vidx]] = int(value)
                    else:
                        try:
                            value = float(value)
                        except:
                            value = value.replace(' ', '')
                        ratings[keys[vidx+1]] = value

                if 'EstimatedDynamic' not in ratings:
                    break

                url = url_obj.xpath('@href').extract_first()
                request = scrapy.Request(response.urljoin(url), self.parse_match_history)
                request.meta['info'] = deepcopy(response.meta['info'])
                request.meta['info']['name'] = name
                request.meta['tr'] = ratings
                yield request

    def parse_match_history(self, response):
        city, state = response.xpath(
            '//div[@class="wrapper_center"]/div[1]/text()[normalize-space()]'
        ).extract_first().strip().split('\n')[0].strip()[1:-1].split(', ')
        leagues = response.xpath(
            '//div[@class="wrapper_center"]/table[2]/tr/td[2]/text()'
        ).extract()[1:-1]

        if not city or not state or not leagues:
            return

        name = response.meta['info']['name']
        utr_name = '%20'.join(itemgetter(0,-1)(name.split()))
        request = scrapy.Request(
            self.utr_url.format(utr_name), self.parse_utr
        )
        for k in ['info', 'tr']:
            request.meta[k] = deepcopy(response.meta[k])
        request.meta['info'].update(
            {'city': city, 'state': states[state], 'leagues': leagues}
        )
        yield request

    def parse_utr(self, response):
        results = response.xpath('//div[@class="inner-results"]')
        url = None
        for result in results:
            location = result.xpath('ul[2]/li[1]/text()').extract_first()
            if location is not None:
                location = location.split(', ')
                if len(location) == 3:
                    city, state, country = location
                    if country == 'USA' and state == response.meta['info']['state'] \
                       and city == response.meta['info']['city']:
                        atag = result.xpath('h3/a')
                        name = atag.xpath('text()').extract_first()
                        first_name, last_name = itemgetter(0,-1)(name.strip().lower().split())
                        first_name_tr, last_name_tr = itemgetter(0,-1)(
                            response.meta['info']['name'].lower().split()
                        )
                        if last_name == last_name_tr and first_name.startswith(first_name_tr):
                            url = atag.xpath('@href').extract_first()
                            break

        if url is not None:
            request = scrapy.Request(response.urljoin(url), self.parse_profile)
            for k in ['info', 'tr']:
                request.meta[k] = deepcopy(response.meta[k])
            request.meta['utr'] = {'id': int(url.split('/')[-1])}
            yield request
        else:
            entry = TrEntry()
            for k in ['info', 'tr']:
                entry[k] = deepcopy(response.meta[k])
            yield entry

    def parse_profile(self, response):

        def convert_float(s):
            try:
                return float(s)
            except ValueError:
                return s

        ratings = [convert_float(r) for r in response.xpath(
                '//div[@class="player-profile__rating-val-inner"]/div/strong/text()'
        ).extract()[:2]]

        statuses = [s.strip().split()[0] for s in response.xpath(
            '//div[@class="player-profile__rating-status"]/text()[normalize-space()]'
        ).extract()[:2]]

        progresses = []
        for detail in response.xpath(
            '//div[@class="player-profile__status-detail"]'
        )[:2]:
            progress = detail.xpath(
                'div[@class="player-profile__status-title"]/text()'
            ).extract_first()
            if progress is not None:
                try:
                    progress = float(progress.split()[-1][:-1])/100
                except:
                    pass
            progresses.append(progress)

        entry = TrEntry()
        for k in ['info', 'tr', 'utr']:
            entry[k] = deepcopy(response.meta[k])
        keys = ['rating', 'status', 'progress']
        for k, l in zip(
            ['singles', 'doubles'], zip(ratings, statuses, progresses)
        ):
            entry['utr'][k] = dict(zip(keys, l))

        yield entry
