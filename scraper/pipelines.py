# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo, inflect
from scrapy.exceptions import DropItem

inflect_engine = inflect.engine()

class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.names_seen = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI', 'mongodb://localhost:27017'),
            mongo_db = crawler.settings.get('MONGO_DATABASE', 'usta')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        spider.db = self.db

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        collection_name = inflect_engine.plural(type(item).__name__.lower())
        self.db[collection_name].insert(dict(item))
        return item
        #name = item.get('info', {}).get('name', None)
        #if name is not None and name in self.names_seen:
        #    raise DropItem("Duplicate name found: %s" % name)
        #else:
        #    if name is not None:
        #        self.names_seen.add(name)
        #    collection_name = inflect_engine.plural(type(item).__name__.lower())
        #    self.db[collection_name].insert(dict(item))
        #    return item
