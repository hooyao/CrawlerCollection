import sys

from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from torfetcher.spiders.rarbg import RarbgSpider

configure_logging()
runner = CrawlerRunner(get_project_settings())


def main(*args):
    crawl()
    reactor.run()


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(RarbgSpider)
    reactor.stop()


if __name__ == '__main__':
    main(*sys.argv[1:])
