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

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI', 'mongodb://localhost:27017'),
            mongo_db = crawler.settings.get('MONGO_DATABASE', 'usta')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        collection_name = inflect_engine.plural(type(item).__name__.lower())
        collection = self.db[collection_name]
        doc = dict(item)
        item_exists = bool(collection.find(doc).count() > 0)
        if item_exists:
            raise DropItem("Duplicate in {}:".format(collection_name))
        else:
            collection.insert(doc)
            return item
