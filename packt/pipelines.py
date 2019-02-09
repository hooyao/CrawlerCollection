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
        access_tk = item['access_token'][0]
        refresh_tk = item['refresh_token'][0]
        url = item['url'][0]
        file_type = item['file_type'][0]
        # headers = {'authorization': f'Bearer {access_tk}'}
        meta = {'access_token': access_tk, 'refresh_token': refresh_tk}
        req = Request(url, meta=meta, priority=0)
        req.meta['book_name'] = item['title'][0]
        if file_type == 'code':
            req.meta['ext'] = 'zip'
        else:
            req.meta['ext'] = file_type
        req_list.append(req)
        return req_list

    def file_path(self, request, response=None, info=None):
        book_name = request.meta['book_name']
        ext = request.meta['ext']
        return book_name + '/' + book_name + '.' + ext
