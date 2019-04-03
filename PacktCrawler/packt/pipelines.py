# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline


class PacktPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        req_list = []
        url = item['url'][0]
        file_type = item['file_type'][0]
        # headers = {'authorization': f'Bearer {access_tk}'}
        req = Request(url, priority=0)
        req.meta['book_name'] = item['title'][0]
        if file_type == 'code':
            req.meta['ext'] = 'code.zip'
        elif file_type == 'video':
            req.meta['ext'] = 'video.zip'
        else:
            req.meta['ext'] = file_type
        req_list.append(req)
        return req_list

    def file_path(self, request, response=None, info=None):
        book_name = request.meta['book_name']
        ext = request.meta['ext']
        return book_name + '/' + book_name + '.' + ext
