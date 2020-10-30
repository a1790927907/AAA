# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

class SnygPipeline:
    def open_spider(self,spider):
        self.mongo = MongoClient('mongodb',27017)
        self.collection = self.mongo.suning.goods

    def process_item(self, item, spider):
        self.collection.insert(dict(item))
        return item

    def close_spider(self,spider):
        self.mongo.close()
        spider.queue_action.qclose()
