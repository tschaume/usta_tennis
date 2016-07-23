# -*- coding: utf-8 -*-

import scrapy

class Player(scrapy.Item):
    _id = scrapy.Field()
    city = scrapy.Field()
    rating_level = scrapy.Field()
    rating_type = scrapy.Field()
    age_group = scrapy.Field()
    matches_played = scrapy.Field()
    gender = scrapy.Field()
    area = scrapy.Field()
    first_name = scrapy.Field()
    last_name = scrapy.Field()

class Match(scrapy.Item):
    _id = scrapy.Field()
    date = scrapy.Field()
    singles = scrapy.Field()
    doubles = scrapy.Field()

class TlsEntry(scrapy.Item):
    name = scrapy.Field()
    year = scrapy.Field()
    league = scrapy.Field()
    rating = scrapy.Field()
    area = scrapy.Field()
    section = scrapy.Field()
    facility = scrapy.Field()
    level = scrapy.Field()
    flight = scrapy.Field()
    matches = scrapy.Field()
    games = scrapy.Field()
