# -*- coding: utf-8 -*-

import scrapy, logging, re, os, json
from scraper.items import TlinkEntry
logger = logging.getLogger('tlink')

class TlinkSpider(scrapy.Spider):
    name = 'tlink'
    start_urls = [
        'http://tennislink.usta.com/leagues/reports/NTRP/SearchResults.aspx?'
        'Search=TreeNode&update=1&NationalNodeID=4920768&CYear=2017&'
        'SectionNodeID=4920779&DistrictNodeID=4920842&SubDistrictNodeID=4921014&'
        'DivisionNodeID=&FlightNodeID=&GenderCode={}&NTRPRating={}'.format(
            gender, rating
        ) for gender in ['M', 'F'] for rating in [
            '{:.1f}'.format(x/10.) for x in range(30, 60, 5)
        ]
    ]

    def parse(self, response):
        rows = '//table[@id="DataGrid1"]/tr'
        keys = None
        for irow, row in enumerate(response.xpath(rows)):
            if not irow:
                keys = [
                    col.lower().replace(' ', '_')
                    for col in row.xpath('td/text()').extract()
                ]
            else:
                cols = row.xpath('td/descendant-or-self::*/text()').extract()
                cols[0] = ' '.join(cols[0].strip().split(', ')[::-1])
                d = dict(zip(keys, cols))
                query = {'info.name': d['name'], 'info.year_end_rating_date': d['year_end_rating_date']}
                if self.db['tlinkentries'].find(query).count():
                    continue
                entry = TlinkEntry()
                entry['info'] = d
                yield entry
