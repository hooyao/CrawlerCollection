# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class PacktBookItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    title = Field()
    author = Field()
    cover_url = Field()
    price = Field()
    order_ref = Field()
    order_date = Field()
    url = Field()
    file_type = Field()
    files = Field()
