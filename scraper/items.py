# -*- coding: utf-8 -*-

import scrapy

class Team(scrapy.Item):
    id = scrapy.Field()
    year = scrapy.Field()
    season_id = scrapy.Field()
    season_name = scrapy.Field()
    league = scrapy.Field()
    league_url = scrapy.Field()
    gender = scrapy.Field()
    level = scrapy.Field()
    team = scrapy.Field()
    team_url = scrapy.Field()
    captain = scrapy.Field()
    captain_url = scrapy.Field()
    city = scrapy.Field()
    area = scrapy.Field()
    organization = scrapy.Field()
    organization_url = scrapy.Field()
    created = scrapy.Field()

class Player(scrapy.Item):
    id = scrapy.Field()
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

class TrEntry(scrapy.Item):
    info = scrapy.Field()
    tr = scrapy.Field()
    utr = scrapy.Field()

class TlinkEntry(scrapy.Item):
    info = scrapy.Field()

class TlinkPlayer(scrapy.Item):
    id = scrapy.Field()
    data = scrapy.Field()

class TlinkMatch(scrapy.Item):
    id = scrapy.Field()
    data = scrapy.Field()
