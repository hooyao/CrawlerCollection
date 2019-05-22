import logging
import os

from scrapy.spiders import Spider
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumSpider(Spider):

    browser: WebDriver

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.URL_TEMPLATE = 'http://{REMOTE_SELENIUM_ADDR}:4444/wd/hub'
        self.USE_REMOTE_SELENIUM = os.getenv('USE_REMOTE_SELENIUM', 'FALSE')
        self.REMOTE_SELENIUM_ADDR = os.getenv('REMOTE_SELENIUM_ADDR', '127.0.0.1')
        self.PAGE_LOAD_TIME_OUT = 30
        self.browser = self.get_selenium_driver()

    def parse(self, response):
        pass

    def closed(self, spider) -> None:
        logging.info("shut down selenium")
        self.browser.close()

    def get_selenium_driver(self) -> WebDriver:
        if self.USE_REMOTE_SELENIUM == 'TRUE':
            remote_selenium_url = self.URL_TEMPLATE.format(REMOTE_SELENIUM_ADDR=self.REMOTE_SELENIUM_ADDR)
            driver = webdriver.Remote(
                command_executor=remote_selenium_url,
                desired_capabilities=webdriver.DesiredCapabilities.CHROME,
            )
            driver.set_page_load_timeout(self.PAGE_LOAD_TIME_OUT)
            return driver
        else:
            return webdriver.Chrome()
