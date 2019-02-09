# -*- coding: utf-8 -*-
import http.cookies as ck
import json

import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings

from packt.items import PacktBookItem


class BooklistSpider(scrapy.Spider):
    name = 'mybooks'
    allowed_domains = ['packtpub.com']
    start_urls = ['https://www.packtpub.com']

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
        print(response.headers.getlist('Set-Cookie'))
        if 'Sign Out' in response.text:
            print('Login successful.')
            cookie_text = str(response.request.headers['Cookie'], 'UTF-8')
            cookie = ck.SimpleCookie()
            cookie.load(cookie_text)
            access_tk = cookie['access_token_live'].value
            refresh_tk = cookie['refresh_token_live'].value
            headers = {'authorization': f'Bearer {access_tk}'}
            offset = 0
            meta = {'access_token': access_tk, 'refresh_token': refresh_tk, 'offset': offset}
            yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                              + f'&offset={offset}&limit=25',
                          headers=headers, meta=meta, callback=self.after_get_prod_list)
        else:
            print('Login Failed.')

    def after_get_prod_list(self, response):
        if response.status == 200:
            prod_list = json.loads(response.text)['data']
            next_offset = response.meta['offset']
            access_tk = response.meta['access_token']
            refresh_tk = response.meta['refresh_token']
            headers = {'authorization': f'Bearer {access_tk}'}
            for prod in prod_list:
                id = prod['productId']
                prod_name = prod['productName']
                meta = {'access_token': access_tk, 'refresh_token': refresh_tk,
                        'product_id': id, 'product_name': prod_name}
                yield Request(url=f'https://services.packtpub.com/products-v1/products/{id}/types',
                              headers=headers, meta=meta, callback=self.after_get_type)
            if len(prod_list) == 25:
                meta = {'access_token': access_tk, 'refresh_token': refresh_tk, 'offset': next_offset + 25}
                yield Request(url='https://services.packtpub.com/entitlements-v1/users/me/products?sort=createdAt:DESC'
                                  + f'&offset={next_offset}&limit=25',
                              headers=headers, meta=meta, callback=self.after_get_prod_list)

        else:
            print('Failed to get My Product data.')

    def after_get_type(self, response):
        if response.status == 200:
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
                              headers=headers, meta=meta, callback=self.after_get_real_dl_url)
        else:
            prod_name = response.meta['product_name']
            print(f'Failed to get resource type of {prod_name}.')

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
            print(f'Failed to get resource url of {prod_name}.')
