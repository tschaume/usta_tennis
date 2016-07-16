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
    scraped_on = scrapy.Field()
    first_name = scrapy.Field()
    last_name = scrapy.Field()
