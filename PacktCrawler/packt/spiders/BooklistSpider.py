# -*- coding: utf-8 -*-
import http.cookies as ck
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
    start_urls = ['https://www.packtpub.com']

    pagination_size = 5

    def parse(self, response):
        settings = get_project_settings()
        request = scrapy.FormRequest.from_response(
            response,
            url='https://www.packtpub.com/',
            formdata={'email': settings.get('EMAIL'),
                      'password': settings.get('PASSWORD'),
                      'op': 'Login',
                      'form_build_id': 'form-95d37c613e0af5ed429ae7b2da3e8102',
                      'form_id': 'packt_user_login_form'
                      },
            callback=self.after_login

        )
        yield request

    def after_login(self, response):
        if 'Sign Out' in response.text:
            self.logger.info('Login successful.')
            cookie_text = str(response.request.headers['Cookie'], 'UTF-8')
            cookie = ck.SimpleCookie()
            cookie.load(cookie_text)
            access_tk = cookie['access_token_live'].value
            refresh_tk = cookie['refresh_token_live'].value
            headers = {'authorization': f'Bearer {access_tk}'}
            offset = 0
            meta = {'access_token': access_tk, 'refresh_token': refresh_tk, 'offset': offset}
            yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                              + f'&offset={offset}&limit={self.pagination_size}',
                          headers=headers, meta=meta, errback=self.handle_error, callback=self.after_get_prod_list)
        else:
            self.logger.error('Login Failed.')

    def after_get_prod_list(self, response):
        prod_list = json.loads(response.text)['data']
        cur_offset = response.meta['offset']
        access_tk = response.meta['access_token']
        refresh_tk = response.meta['refresh_token']
        headers = {'authorization': f'Bearer {access_tk}'}
        for prod in prod_list:
            id = prod['productId']
            prod_name = prod['productName']
            meta = {'access_token': access_tk, 'refresh_token': refresh_tk,
                    'product_id': id, 'product_name': prod_name}
            yield Request(url=f'https://services.packtpub.com/products-v1/products/{id}/types',
                          headers=headers, meta=meta,
                          errback=self.handle_error, callback=self.after_get_type)
        if len(prod_list) == self.pagination_size:
            meta = {'access_token': access_tk, 'refresh_token': refresh_tk,
                    'offset': cur_offset + self.pagination_size}
            yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                              + f'&offset={cur_offset + self.pagination_size}&limit={self.pagination_size}',
                          headers=headers, meta=meta,
                          errback=self.handle_error, callback=self.after_get_prod_list)

    def after_get_type(self, response):
        type_list = json.loads(response.text)['data'][0]['fileTypes']
        access_tk = response.meta['access_token']
        refresh_tk = response.meta['refresh_token']
        prod_name = response.meta['product_name']
        prod_id = response.meta['product_id']
        headers = {'authorization': f'Bearer {access_tk}'}
        for file_type in type_list:
            meta = {'access_token': access_tk, 'refresh_token': refresh_tk,
                    'product_id': id, 'product_name': prod_name, 'file_type': file_type}
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
                access_tk = ori_request.meta['access_token']
                refresh_tk = ori_request.meta['refresh_token']
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
        tokens = json.loads(response.text)['data']
        access_tk = tokens['access']
        refresh_tk = tokens['refresh']
        ori_request = response.meta['ori_request']
        ori_request.meta['access_token'] = access_tk
        ori_request.meta['refresh_token'] = refresh_tk
        ori_request.headers['authorization'] = f'Bearer {access_tk}'
        self.logger.error(f'Token refreshed to: {ori_request.meta}')
        yield ori_request
