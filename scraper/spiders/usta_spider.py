# -*- coding: utf-8 -*-

import scrapy, itertools
from scraper.items import Player
from datetime import datetime

class UstaSpider(scrapy.Spider):
    name = 'usta'
    allowed_domains = ['ustanorcal.com']
    start_urls = ['https://www.ustanorcal.com/ntrpsearch.asp#goto']

    def parse(self, response):
        # extract select options for post request
        opt_keys, opt_values = [], []
        opts = response.xpath('//table')[-1].xpath('tr')[1:4]
        for iopt, opt in enumerate(opts):
            opt_keys.append(opt.xpath('td/select/@name').extract_first())
            opt_values.append(opt.xpath('td/select/option/@value')[1:].extract())
        # send post request for all options combinations
        for opt_combo in itertools.product(*opt_values):
            payload = dict(
                (opt_keys[iopt], opt)
                for iopt, opt in enumerate(opt_combo)
            )
            payload['show_matches_played'] = 'on'
            payload['submit'] = 'Submit'
            yield scrapy.http.FormRequest(
                self.start_urls[0], formdata=payload,
                callback=self.parse_players
            )
            break

    def parse_players(self, response):
        for row in response.xpath('//table')[-1].xpath('tr')[3:-2]:
            player = Player()
            columns = row.xpath('td')
            url = columns[0].xpath('a/@href').extract_first() # TODO follow
            player['_id'] = url.split('=')[-1]
            player['city'] = columns[1].xpath('text()').extract_first()
            rating = columns[4].xpath('text()').extract_first()
            player['rating_level'] = float(rating[:3])
            player['rating_type'] = rating[3:]
            player['age_group'] = columns[-2].xpath('text()').extract_first()
            player['matches_played'] = int(columns[-1].xpath('text()').extract_first())
            selection = response.xpath('//option[@selected]/@value').extract()
            player['area'], player['gender'] = selection[0], selection[1]
            name = columns[0].xpath('a/text()').extract_first().split(',')
            player['first_name'] = name[-1].strip().split()[0]
            player['last_name'] = name[0].strip()
            player['scraped_on'] = datetime.now()
            yield player
