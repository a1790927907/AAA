# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SnygItem(scrapy.Item):
    # define the fields for your item here like:
    key_word = scrapy.Field()
    title = scrapy.Field()
    goods_url = scrapy.Field()
    goods_img = scrapy.Field()
    goods_price = scrapy.Field()
    goods_freight = scrapy.Field()
    good_comments_num = scrapy.Field()
    bad_comments_num = scrapy.Field()
    all_comments_num = scrapy.Field()
    good_rate = scrapy.Field()
    bad_rate = scrapy.Field()
    c_time = scrapy.Field()

