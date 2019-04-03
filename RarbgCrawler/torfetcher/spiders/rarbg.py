# -*- coding: utf-8 -*-
import time
from typing import NewType

from scrapy import Request
from scrapy.http import HtmlResponse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.webkitgtk.webdriver import WebDriver

from torfetcher.common.SeleniumSpider import SeleniumSpider
from torfetcher.common.contants import CRAWL_STRATEGY_KEY, PAGE_LOG_KEY, PAGE_SEARCH_KW, PAGE_LOC_INDEX
from torfetcher.common.crawl import CrawlStrategy


class RarbgSpider(SeleniumSpider):
    name = 'rarbg'
    allowed_domains = ['rarbg.to']
    start_url = 'http://rarbg.to/'

    search_keywords = [
        'big bang theory'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crawler_strategy = RargbStrategy()

    def start_requests(self):
        self.logger.info(f'selenium is opening: {self.start_url}')
        try:
            self.browser.get(self.start_url)
            element = WebDriverWait(self.browser, 30).until(
                ec.visibility_of_element_located((By.LINK_TEXT, "TV Shows"))
            )
            #element = self.browser.find_element_by_link_text("TV Shows")
            href_dest = element.get_attribute('href')
            self.browser.get(href_dest)
            time.sleep(1)
            for keyword in self.search_keywords:
                self.browser.find_element_by_id('searchinput').send_keys("flash")
                self.browser.find_element_by_xpath("//button[@type='submit']").submit()
                page_param = f'&page=2'
                self.browser.current_url
                request = Request(self.start_url, dont_filter=True)
                request.meta[CRAWL_STRATEGY_KEY] = self.crawler_strategy
                request.meta[PAGE_LOG_KEY] = PAGE_LOC_INDEX
                request.meta[PAGE_SEARCH_KW] = keyword
                yield request


            # web_driver.execute_script("document.evaluate('//div[contains(@style,'z-index')]',document,null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.setAttribute('style', 'visibility: hidden;')")
            # web_driver.find_element_by_xpath("")
        except TimeoutException as e:
            print("Time out.")
            self.browser.execute_script('window.stop()')

    def parse(self, response):
        print("what")
        pass


class RargbStrategy(CrawlStrategy):

    def crawl(self, spider, request):

        web_driver_type = NewType('WebDriver', WebDriver)
        web_driver = web_driver_type(spider.browser)

        if request.meta[PAGE_LOG_KEY] == PAGE_LOC_INDEX:
            spider.logger.info('selenium is opening: %s' % request.url)
            try:
                index_url = request.url
                web_driver.get(index_url)
                time.sleep(1)
                element = web_driver.find_element_by_link_text("TV Shows")
                href_dest = element.get_attribute('href')
                web_driver.get(href_dest)
                time.sleep(1)
                web_driver.find_element_by_id('searchinput').send_keys("flash")
                web_driver.find_element_by_xpath("//button[@type='submit']").submit()

                # web_driver.execute_script("document.evaluate('//div[contains(@style,'z-index')]',document,null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.setAttribute('style', 'visibility: hidden;')")
                # web_driver.find_element_by_xpath("")
            except TimeoutException as e:
                print("Time out.")
                spider.browser.execute_script('window.stop()')
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding="utf-8", request=request)
        else:
            return None
