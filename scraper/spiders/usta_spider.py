# -*- coding: utf-8 -*-

import sys
import scrapy, itertools, logging
from scraper.items import Player, Match, Team
from datetime import datetime
logger = logging.getLogger('usta')

root_url = "https://www.ustanorcal.com"
seasons = {
    "249": "2019 Adult 18 - 45 Team Singles League",
    "257": "2020 Adult 18 & Over",
    "253": "2020 Adult 40 & Over",
    "256": "2020 Adult 65 & Over",
    "246": "2020 Mixed 40 & Over ",
    "251": "2020 Mixed 55 & Over",
    "247": "2020 Reno/Tahoe Adult 40",
    "228": "2018 18-39 Team Singles League",
    "230": "2018 Adult 70 & Over",
    "239": "2019 Adult 18 & Over",
    "237": "2019 Adult 18-39 League",
    "234": "2019 Adult 40 & Over",
    "243": "2019 Adult 55 & Over",
    "238": "2019 Adult 65 & Over",
    "245": "2019 Adult 70 & Over ",
    "242": "2019 Mixed 18 & Over ",
    "227": "2019 Mixed 40 & Over",
    "236": "2019 Mixed 55 & Over",
    "212": "2017 Adult 70 & Over",
    "221": "2018 Adult 18 & Over",
    "216": "2018 Adult 18 - 39 League",
    "218": "2018 Adult 40 & Over ",
    "224": "2018 Adult 55 & Over",
    "220": "2018 Adult 65 & Over",
    "225": "2018 Mixed 18 & Over",
    "210": "2018 Mixed 40 & Over",
    "219": "2018 Mixed 55 & Over ",
    "198": "2016 Adult 70 & Over ",
    "197": "2016 Mixed 55 & Over ",
    "204": "2017 Adult 18 & Over ",
    "201": "2017 Adult 40 & Over ",
    "206": "2017 Adult 55 & Over",
    "203": "2017 Adult 65 & Over ",
    "215": "2017 Mens 2.5+ Pilot",
    "205": "2017 Mixed 18 & Over ",
    "202": "2017 Mixed 40 & Over ",
    "213": "2017 Mixed 70 & Over",
    "184": "2015 Adult 70 & Over",
    "183": "2015 Mixed 55 & Over",
    "192": "2016 Adult 18 & Over ",
    "188": "2016 Adult 40 & Over",
    "195": "2016 Adult 55 & Over",
    "190": "2016 Adult 65 & Over",
    "194": "2016 Mixed 18 & Over ",
    "189": "2016 Mixed 40 & Over",
    "168": "2014 Mixed 55 & Over ",
    "177": "2015 Adult 18 & Over",
    "172": "2015 Adult 40 & Over",
    "179": "2015 Adult 55 & Over",
    "176": "2015 Adult 65 & Over",
    "180": "2015 Mixed 18 & Over ",
    "173": "2015 Mixed 40 & Over",
    "145": "2013 Mixed 40 & Over",
    "158": "2014 Adult 18 & Over",
    "152": "2014 Adult 40 & Over ",
    "153": "2014 Adult 55 & Over",
    "155": "2014 Adult 65 & Over",
    "167": "2014 Adult 70 & Over ",
    "163": "2014 Mixed Doubles 18 & Over",
    "164": "2014 Mixed Doubles 40 & Over",
    "131": "2012 Super Senior 70 League",
    "141": "2013 Adult 18 & Over",
    "138": "2013 Adult 40 & Over",
    "142": "2013 Adult 55 & Over",
    "140": "2013 Adult 65 & Over",
    "148": "2013 Adult 70 & Over",
    "144": "2013 Mixed 18 & Over",
    "139": "2013 Mixed 55 & Over",
}

class UstaSpider(scrapy.Spider):
    name = 'usta'
    allowed_domains = ['ustanorcal.com']
    start_urls = [
        #'https://www.ustanorcal.com/ntrpsearch.asp#goto',
        'https://www.ustanorcal.com/listdivisions.asp'
    ]
    area = '' # set to None or '' to download all areas

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
            for season_id in seasons.keys():
                payload = {'seasonid': season_id, 'submit1': ' GO '}
                request = scrapy.http.FormRequest(
                    response.url, formdata=payload, callback=self.parse_league
                )
                request.meta["season_id"] = season_id
                yield request

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
        tables = response.xpath('//table')
        if len(tables) < 3:
            return
        levels = tables[2].xpath('tr/td/a')
        for idx, level in enumerate(levels):
            url = level.xpath('@href').extract_first()
            level_name = level.xpath('text()').extract_first()
            league, gender, ntrp = level_name.rsplit(' ', 2)
            year = league.split(' ', 1)[0]
            logger.info('league = {}'.format(url))
            request = scrapy.Request(response.urljoin(url), self.parse_teams)
            request.meta["season_id"] = response.meta["season_id"]
            request.meta["year"] = year
            request.meta["league"] = league
            request.meta["league_url"] = f"{root_url}/{url}"
            request.meta["gender"] = gender[0]
            request.meta["level"] = ntrp
            yield request

    def parse_teams(self, response):
        table = response.xpath('//table[@class="DataList"]')
        rows = table.xpath(
            'tr[td//text()[contains(., "{}")]]'.format(self.area.upper())
        ) if self.area else table.xpath('tr')
        urls = rows.xpath('td/a/@href[contains(., "teaminfo")]').extract()
        ids = [int(u.split('=')[-1]) for u in urls]
        #for idx, url in enumerate(urls):
        #    logger.info('team = {}'.format(url))
        #    yield scrapy.Request(response.urljoin(url), self.parse_team)
        header = list(filter(None, [
            c.split()[0].lower() for c in rows[0].xpath('td//text()').extract()
        ]))
        looking = "Looking"
        idx_map = [0, 1, 4]
        for i, row in zip(ids, rows[1:]):
            columns = row.xpath('td//text()').extract()
            links = {
                header[idx_map[j]]: l
                for j, l in enumerate(row.xpath('td/a/@href').extract())
            }
            if looking in columns:
                columns.remove(looking)
            team = Team()
            team["year"] = response.meta["year"]
            team["league"] = response.meta["league"]
            team["league_url"] = response.meta["league_url"]
            team["gender"] = response.meta["gender"]
            team["level"] = response.meta["level"]
            team["id"] = i
            season_id = response.meta["season_id"]
            team["season_id"] = season_id
            team["season_name"] = seasons[season_id].strip()
            clean_columns = list(filter(None, [c.strip() for c in columns]))
            for key, col in zip(header, clean_columns):
                team[key] = col
                link = links.get(key)
                if link:
                    team[f"{key}_url"] = f"{root_url}/{link}"
            yield team


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
