# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings

from packt.items import PacktBookItem


class BooklistSpider(scrapy.Spider):
    name = 'mybooks'
    allowed_domains = ['packtpub.com']
    start_urls = ['https://account.packtpub.com/login']

    pagination_size = 5

    hard_coded_types = ['code', 'epub', 'mobi', 'pdf']

    tokens = {}

    settings = None

    def __init__(self, *a, **kw):
        super(BooklistSpider, self).__init__(*a, **kw)
        self.settings = get_project_settings()

    def parse(self, response):
        login_payload = {"username": self.settings.get('EMAIL'), "password": self.settings.get('PASSWORD')}
        yield Request(url='https://services.packtpub.com/auth-v1/users/tokens',
                      method='POST',
                      headers={'Accept': 'application/json',
                               'Content-Type': 'application/json'},
                      body=json.dumps(login_payload),
                      callback=self.after_login)

    def after_login(self, response):
        if response.status == 200:
            self.logger.info('Login successful.')
            self.tokens = json.loads(response.text)['data']
            access_tk = self.tokens['access']
            headers = {'authorization': f'Bearer {access_tk}'}
            offset = 0
            meta = {'offset': offset}
            yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                              + f'&offset={offset}&limit={self.pagination_size}',
                          headers=headers, meta=meta, errback=self.handle_error, callback=self.after_get_prod_list)
        else:
            self.logger.error('Login Failed.')

    def after_get_prod_list(self, response):
        prod_list = json.loads(response.text)['data']
        last_offset = response.meta['offset']
        access_tk = self.tokens['access']
        headers = {'authorization': f'Bearer {access_tk}'}
        for prod in prod_list:
            id = prod['productId']
            prod_name = prod['productName']
            headers = {'authorization': f'Bearer {access_tk}',
                       'Origin': 'https://account.packtpub.com',
                       'Referer': 'https://account.packtpub.com/account/products'}
            file_types = self.hard_coded_types[:]
            if 'Video' in prod_name:
                file_types.append('video')
            for file_type in file_types:
                meta = {'product_id': id, 'product_name': prod_name, 'file_type': file_type}
                yield Request(url=f'https://services.packtpub.com/products-v1/products/{id}/files/{file_type}',
                              headers=headers, meta=meta,
                              errback=self.handle_error, callback=self.after_get_real_dl_url)

        max_product_to_fetch = self.settings.get('MAX_PRODUCT_TO_FETCH', -1)
        cur_offset = last_offset + self.pagination_size
        if len(prod_list) == self.pagination_size and last_offset < max_product_to_fetch:
            meta = {'offset': cur_offset}
            yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                              + f'&offset={cur_offset}&limit={self.pagination_size}',
                          headers=headers, meta=meta,
                          errback=self.handle_error, callback=self.after_get_prod_list)

    # Deprecated not needed anymore
    def after_get_type(self, response):
        # type_list = json.loads(response.text)['data'][0]['fileTypes']
        access_tk = self.tokens['access']
        prod_name = response.meta['product_name']
        prod_id = response.meta['product_id']
        headers = {'authorization': f'Bearer {access_tk}',
                   'Origin': 'https://account.packtpub.com',
                   'Referer': 'https://account.packtpub.com/account/products'}
        file_types = self.hard_coded_types[:]
        if 'Video' in prod_name:
            file_types.append('video')
        for file_type in file_types:
            meta = {'product_id': id, 'product_name': prod_name, 'file_type': file_type}
            yield Request(url=f'https://services.packtpub.com/products-v1/products/{prod_id}/files/{file_type}',
                          headers=headers, meta=meta,
                          errback=self.handle_error, callback=self.after_get_real_dl_url)

    def after_get_real_dl_url(self, response):
        if response.status == 200:
            real_url = json.loads(response.text)['data']
            prod_name = response.meta['product_name']
            file_type = response.meta['file_type']
            loader = ItemLoader(item=PacktBookItem(), response=response)
            loader.add_value('title', prod_name)
            loader.add_value('url', real_url)
            loader.add_value('file_type', file_type)
            yield loader.load_item()
        else:
            prod_name = response.meta['product_name']
            self.logger.error(f'Failed to get resource url of {prod_name}.')

    def handle_error(self, failure):
        if failure.check(HttpError):
            # most likely token expired
            if failure.value.response.status == 401:
                ori_request = failure.request
                access_tk = self.tokens['access']
                refresh_tk = self.tokens['refresh']
                headers = {'authorization': f'Bearer {access_tk}', 'Content-Type': 'application/json'}
                meta = {'ori_request': ori_request}
                json_data = {'refresh': refresh_tk}
                yield Request(url='https://services.packtpub.com/auth-v1/users/me/tokens',
                              method='POST',
                              headers=headers,
                              meta=meta,
                              body=json.dumps(json_data),
                              callback=self.after_refresh_token)
        else:
            response = failure.value.response
            self.logger.error('Unknown error on %s', response.url)

    def after_refresh_token(self, response):
        self.tokens = json.loads(response.text)['data']
        access_tk = self.tokens['access']
        ori_request = response.meta['ori_request']
        ori_request.headers['authorization'] = f'Bearer {access_tk}'
        self.logger.error(f'Token refreshed to: {self.tokens}')
        yield ori_request
