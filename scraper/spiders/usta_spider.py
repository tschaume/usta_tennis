# -*- coding: utf-8 -*-

import scrapy, itertools, logging
from scraper.items import Player, Match
from datetime import datetime
logger = logging.getLogger('usta')

class UstaSpider(scrapy.Spider):
    name = 'usta'
    allowed_domains = ['ustanorcal.com']
    start_urls = [
        'https://www.ustanorcal.com/ntrpsearch.asp#goto',
        'https://www.ustanorcal.com/listdivisions.asp'
    ]
    area = 'eb' # set to None or '' to download all areas

    def parse(self, response):
        # extract select options for post request
        if 'ntrpsearch' in response.url:
            opt_keys, opt_values = [], []
            opts = response.xpath('//table')[-1].xpath('tr')[1:4]
            for iopt, opt in enumerate(opts):
                opt_keys.append(opt.xpath('td/select/@name').extract_first())
                opt_values.append(opt.xpath('td/select/option/@value')[1:].extract())
            # send post request for all options combinations
            for idx, opt_combo in enumerate(itertools.product(*opt_values)):
                if self.area and self.area not in opt_combo[0]: continue
                logger.info('players = {}'.format(opt_combo))
                payload = dict(
                    (opt_keys[iopt], opt)
                    for iopt, opt in enumerate(opt_combo)
                )
                payload['show_matches_played'] = 'on'
                payload['submit'] = 'Submit'
                yield scrapy.http.FormRequest(
                    response.url, formdata=payload,
                    callback=self.parse_players
                )
        elif 'listdivisions' in response.url:
            payload = {'seasonid': '192', 'submit1': ' GO '}
            yield scrapy.http.FormRequest(
                response.url, formdata=payload, callback=self.parse_league
            )

    def parse_players(self, response):
        no_players_found = response.xpath('//b[text()="No Players Found!"]')
        if not no_players_found:
            for row in response.xpath('//table')[-1].xpath('tr')[3:-2]:
                player = Player()
                columns = row.xpath('td')
                url = columns[0].xpath('a/@href').extract_first()
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
                yield player
        else:
            logger.info('No Players Found!')

    def parse_league(self, response):
        urls = response.xpath('//table')[2].xpath('tr/td/a/@href').extract()
        for idx, url in enumerate(urls):
            logger.info('league = {}'.format(url))
            yield scrapy.Request(response.urljoin(url), self.parse_teams)

    def parse_teams(self, response):
        table = response.xpath('//table[@class="DataList"]')
        rows = table.xpath(
            'tr[td//text()[contains(., "{}")]]'.format(self.area.upper())
        ) if self.area else table.xpath('tr')
        urls = rows.xpath('/td/a/@href[contains(., "teaminfo")]').extract()
        for idx, url in enumerate(urls):
            logger.info('team = {}'.format(url))
            yield scrapy.Request(response.urljoin(url), self.parse_team)

    def parse_team(self, response):
        urls = response.xpath('//td/a/@href[contains(.,"scorecard.asp")]').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), self.parse_match)

    def get_score(self, row):
        score = row.xpath('td')[3].xpath('text()').extract_first()
        return score.replace('-', '').split(',')

    def get_player_ids(self, row, bgcolor):
        ids = [
            int(url.split('=')[-1]) for url in row.xpath(
                'td[@bgcolor="{}"]/a/@href'.format(bgcolor)
            ).extract()
        ]
        if not ids:
            return None # player default
        return ids if len(ids) > 1 else ids[0]

    def get_match_results(self, row):
        return dict(
            winner = self.get_player_ids(row, '#FFFFCC'),
            loser = self.get_player_ids(row, 'white'),
            score = self.get_score(row)
        )

    def parse_match(self, response):
        match = Match()
        match['_id'] = int(response.url.split('?')[-1].split('&')[0].split('=')[1])
        tables = response.xpath('//table')
        match['date'] = datetime.strptime(
            tables[3].xpath('tr')[1].xpath('td/text()').extract_first(), '%m/%d/%y'
        )
        for mode in ['singles', 'doubles']:
            table_idx = 6 if mode == 'singles' else 8
            match[mode] = [
                self.get_match_results(row)
                for row in tables[table_idx].xpath('tr')[2:]
            ]
        yield match
