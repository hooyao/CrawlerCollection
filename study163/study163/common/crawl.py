from abc import abstractmethod


class CrawlStrategy:

    @classmethod
    def version(self):
        return "1.0"

    @abstractmethod
    def crawl(self, spider, request):
        raise NotImplementedError
