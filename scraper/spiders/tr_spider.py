# -*- coding: utf-8 -*-

import scrapy, logging, re, os, json
from scraper.items import TrEntry
from operator import itemgetter
from copy import deepcopy
from scraper.spiders.states import states
logger = logging.getLogger('tr')

class TrSpider(scrapy.Spider):
    name = 'tr'
    allowed_domains = ['tennisrecord.com', 'universaltennis.com']
    #start_urls = ['https://universaltennis.com/login']
    start_urls = ['https://www.myutr.com/login']
    #utr_url = 'https://universaltennis.com/search?type=player&query={}'
    #utr_url = 'https://universaltennis.com/mvc/search/azuresearch?search={}&top=10&skip=0&filter=(Type%20eq%20%27PLAYER%27)'
    utr_url = 'https://www.myutr.com/search?query=Joshua%20Duong&utrMin=1&utrMax=16&utrType=verified&utrFitPosition=6&type=players'

    def parse(self, response):
        print('LOGIN ...')
        return scrapy.FormRequest.from_response(
            response, formdata={
                'email': os.environ.get('UTR_USER'),
                'password': os.environ.get('UTR_PWD')
            },
            callback=self.after_login
        )

    def after_login(self, response):
        print('after_login ...')
        logger.info(response.body)
        if b"Please provide" in response.body:
            logger.error("UTR Login failed!")
            return
        logger.info("UTR Login succeeded!")
        #yield scrapy.Request(
        #    'http://www.tennisrecord.com/adult/ratingssection.aspx',
        #    self.parse_tr
        #)

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
        url_xpath = "//a[text()='Projected Year End Rating']/@href"
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
                if self.db['trentries'].find({'info.name': name}).count():
                    continue

                ratings = {}
                for vidx, value in enumerate(row.xpath(
                    'td[string-length(normalize-space(text())) > 0]/text()'
                ).extract()):
                    value = value.strip()
                    if vidx == 0:
                        ratings[keys[vidx]] = int(value) if value else 0
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

    def check_name(self, response, name):
        first_name, last_name = itemgetter(0,-1)(name.strip().lower().split())
        first_name_tr, last_name_tr = itemgetter(0,-1)(
            response.meta['info']['name'].lower().split()
        )
        return bool(last_name == last_name_tr and first_name.startswith(first_name_tr))

    def parse_utr(self, response):
        d = json.loads(response.body)
        utr_id = None
        for idx, result in enumerate(d['value']):
            country = result.get('LocationCountryCode', result.get('NationalityCode', ''))
            if country is not None and country.lower() == 'usa':
                state = result['LocationStateAbbr']
                if state is not None and states[state].lower() == response.meta['info']['state'].lower():
                    city = result['LocationCityName']
                    if city is not None and city.lower().replace('-', ' ') == response.meta['info']['city'].lower():
                        name = result['DisplayName']
                        if self.check_name(response, name):
                            utr_id = result['Id']
                            break

        if utr_id is None:
            entry = TrEntry()
            for k in ['info', 'tr']:
                entry[k] = deepcopy(response.meta[k])
            yield entry
            #result = d['value'][0]
            #name = result['DisplayName']
            #if not self.check_name(response, name):
            #    return
            #utr_id = result['Id']
        else:
            url = '/players/{}'.format(utr_id)
            request = scrapy.Request(response.urljoin(url), self.parse_profile)
            for k in ['info', 'tr']:
                request.meta[k] = deepcopy(response.meta[k])
            request.meta['utr'] = {'id': utr_id}
            yield request

    def parse_utr_legacy(self, response):
        results = response.xpath('//div[@class="inner-results"]')
        url = None
        for result in results:
            location = result.xpath('ul[2]/li[1]/text()').extract_first()
            if location is not None:
                location = location.lower().split(', ')
                if len(location) == 3:
                    city, state, country = location
                    if country == 'usa' and state == response.meta['info']['state'].lower() \
                       and city == response.meta['info']['city'].lower().replace('-', ' '):
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
