import hashlib
import sys
import pymongo
import logging
import settings
import datetime
import requests

from goose import Goose
from bs4 import BeautifulSoup
from downloader import compress_content, detect_language
from logging.handlers import RotatingFileHandler


###########################
#  Setting up Logging
###########################

logger = logging.getLogger("Estadao")
logger.setLevel(logging.DEBUG)

# create stream handler and set level to debug
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('/tmp/mediacloud_estadao.log',
                          maxBytes=5e6,
                          backupCount=3)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to stream_handler
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add stream_handler to logger
logger.addHandler(stream_handler)  # uncomment for console output of messages
logger.addHandler(file_handler)

client = pymongo.MongoClient(settings.MONGOHOST, 27017)
mcdb = client.MCDB
ARTICLES = mcdb.articles  # Article Collection

CATEGORIES = (u'politica', u'economia', u'internacional', u'esportes',
                  u'sao-paulo', u'cultura', u'opiniao', u'alias', u'brasil',
                  u'ciencia', u'educacao', u'saude', u'sustentabilidade',
                  u'viagem')

def find_articles(category, page=1):
    """Get the urls of last news and its categories
       :param category: the category of the news (politica, economia,
                        internacional, esportes, sao-paulo, cultura)
       :param page: the page number of last news
       :type category: string
       :type page: integer
       :return: last news with its categories
       :rtype: list()
    """

    if category not in CATEGORIES:
        raise ValueError("Category value not accepted.")

    INDEX_URL = "http://{0}.estadao.com.br/ultimas/{1}".format(category, page)

    index = requests.get(INDEX_URL).content
    soup = BeautifulSoup(index)
    news_index = soup.findAll("div", {"class":"listadesc"})
    news_urls = [url.contents[1]['href'] for url in news_index]
    return news_urls

def extract_published_time(url, soup):
    """ Get the news published datetime

    :param soup: object with news html page
    :type soup: BeautifulSoup object
    :return: news published datetime
    :rtype: string
    """

    MONTHS = {u"janeiro": u"Jan", u"fevereiro": u"Fev", u"mar\xe7o": u"Mar",
                u"abril": u"Apr", u"maio": u"May", u"junho": u"Jun", u"julho":
                u"Jul", u"agosto": u"Aug", u"setembro": u"Sep", u"outubro":
                u"Oct", u"novembro": u"Nov", u"dezembro": u"Dec"
             }
    try:
        date = soup.findAll("p", {"class":"data"})[0]
    except IndexError:
        try:
            date = soup.findAll("span", {"class":"data"})[0]
        except IndexError:
            logger.error('wrong date tags')
            return datetime.datetime.today()

    try:
        date = date.text.strip().split()
        date[1] = date[1].lower()
        date[1] = MONTHS[date[1]]

        if "estadao.com.br/noticias/" in url:
            date = date[0:3] + date[4:6]
            date[3] = date[3][0:2]

        elif "estadao.com.br/blogs/" in url:
            date[3] = date[4][0:2]
            date[4] = date[4][3:5]
    except ValueError:
        logger.error('wrong data extraction')
        return datetime.datetime.today()

    date = '-'.join(date)

    try:
        published_time = datetime.datetime.strptime(date, '%d-%b-%Y-%H-%M')
    except ValueError:
        logger.error('wrong published time format. ')
        return datetime.datetime.today()

    if published_time is None:
        logger.error("The published time is None")
        return datetime.datetime.today()

    return published_time

def extract_title(article):
    """ Extract the news title.
    """

    try:
        title = article.title
    except Exception as ex:
        template = "An exception of type {0} occured during extraction of news title. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.exception(message)
        return None
    if title is None:
        logger.error("The news title is None")
    return title

def extract_content(article):
    """ Extract relevant information about news page
    """

    try:
        body_content = article.cleaned_text
    except Exception as ex:
        template = "An exception of type {0} occured during extraction of news content. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.exception(message)
        return None
    if body_content is None:
        logger.error("The news content is None")
    return body_content

def download_article(url):
    """ Download the html content of a news page

    :param url: news page's url
    :type url: string
    :return: news page's content
    :rtype: requests.models.Response
    """

    article = { 'link': url, 'source': 'crawler_estadao' }
    logger.info("Downloading article: {0}".format(url))

    try:
        response = requests.get(url, timeout=30)
    except Exception as ex:
        logger.exception("Failed to fetch {0}".format(url))
        return None

    extractor = Goose({'use_meta_language': False, 'target_language':'pt'})
    news = extractor.extract(url=url)
    soup = BeautifulSoup(response.text)

    article['link_content'] = compress_content(response.text)
    article['compressed'] = True
    article['language'] = detect_language(response.text)
    article['title'] = extract_title(news)
    article['body_content'] = extract_content(news)
    article['published_time'] = extract_published_time(url, soup)

    return article

if __name__ == '__main__':
    for category in CATEGORIES:
        for url in find_articles(category):
            exists = list(ARTICLES.find(
                {"link_sha1": hashlib.sha1(url).hexdigest()}))
            if not exists:
                article = download_article(url)
                if article['body_content'] is None:
                    continue
                ARTICLES.insert(article, w=1)

