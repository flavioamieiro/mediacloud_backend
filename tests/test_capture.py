#-*- coding:utf-8 -*-
__author__ = 'fccoelho'

import unittest
from capture import feedfinder, urlscanner, downloader


class FeedFinderTests(unittest.TestCase):
    def setUp(self):
        with open('data/URLS.txt') as f:
            self.urls = [s.strip() for s in f.readlines()]

    def test_get_page(self):
        page = feedfinder.get_page('https://www.google.com')
        self.assertIn('google', page)

    def test_isfeed(self):
        page = feedfinder.get_page('http://wikipedia.org')
        feed = feedfinder.get_page('http://www.engadget.com/rss.xml')
        self.assertEquals(feedfinder.isFeed(page), 0)
        self.assertEquals(feedfinder.isFeed(feed), 1)

    def test_find_on_single_page(self):
        fs = feedfinder.feeds(self.urls[0], all=True)
        self.assertNotEquals(fs, [], msg="feeds returned an empty list.")

class TestUrlScanner(unittest.TestCase):
    def test_scan(self):
        l = urlscanner.url_scanner('www.google.com', 1)
        self.assertEquals(l, ['http://www.google.com/robots.txt', 'http://www.google.com/',])

class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.d = downloader.RSSDownload('http://www.engadget.com/rss.xml')

    def tearDown(self):
        downloader.FEEDS.drop()
        downloader.ARTICLES.drop()

    def test_store_feed(self):
        self.d.parse()
        res = downloader.FEEDS.find({"title_detail.base": 'http://www.engadget.com/rss.xml'}, fields=["title_detail"])
        res = list(res)
        self.assertEquals(res[0]['title_detail']['base'], 'http://www.engadget.com/rss.xml')

    def test_store_articles(self):
        self.d.parse()
        res = downloader.ARTICLES.find().count()
        self.assertEquals(res, 25)


if __name__ == '__main__':
    unittest.main()