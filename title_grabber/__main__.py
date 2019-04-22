#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import fileinput
from functools import lru_cache
import itertools
import logging
from multiprocessing import cpu_count
import os
from pathlib import Path
import re
import shutil
import sys
import threading
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import requests

import title_grabber

class TitleGrabber:
    DEF_OUT_PATH = 'out.csv'
    CONN_TO = 10
    READ_TO = 15
    URL_RE = re.compile('https?://\S+', re.I)
    URL_HEADER = 'url'
    END_URL_HEADER = 'end_url'
    PAGE_TIT_HEAD = 'page_title'
    ART_TIT_HEAD = 'article_title'
    HEADERS = (URL_HEADER, END_URL_HEADER, PAGE_TIT_HEAD, ART_TIT_HEAD)
    MAX_RETRIES = 3
    MAX_REDIRECTS = 5
    HTML_PARSER = 'html.parser'
    NEW_LINE_RE = re.compile('\n')
    WHITESPACE_RE = re.compile('\s{2,}')
    IS_WIN_PLAT = sys.platform.startswith('win')
    CSV_DIALECT = 'excel' if IS_WIN_PLAT else 'unix'
    PARENT_PATH = Path(__file__).parent
    TWEET_PERMA_LINK_SEL = '.tweet.permalink-tweet'
    TWEET_TXT_SELS = ['.tweet-text', 'QuoteTweet']
    TWITTER_HOST = 'twitter.com'
    TWITTER_STATUS_RE = re.compile('/status/\d+\Z')
    TWITTER_URL_PREFIX = f'https://{TWITTER_HOST}'
    CSV_FIELD_SEP = ','

    def __init__(self, options):
        self.__options = options
        self.max_redirects = options.get('max_redirects', self.MAX_REDIRECTS)
        self.max_retries = options.get('max_retries', self.MAX_RETRIES)
        self.max_threads = options.get('max_threads', cpu_count())
        self.__out_path = options.get('out_path',
                                      Path(self.DEF_OUT_PATH).resolve())

        log_level = logging.DEBUG if options.get('debug') else logging.INFO
        self.logger = logging.getLogger(self.PARENT_PATH.stem)
        self.logger.setLevel(log_level)

        if os.environ.get('TESTING'):
            handler = logging.NullHandler()
        elif options.get('debug'):
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHandler(Path.cwd().joinpath(self.PARENT_PATH.with_suffix('.log').name),
                                          mode='w')

        handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                      datefmt='%m/%d/%Y %I:%M:%S %p')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


    def __call__(self, files):
        tmp_path = self.__out_path.with_suffix(f'.tmp{self.__out_path.suffix}')

        try:
            with tmp_path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS,
                                        dialect=self.__csv_dialect(),
                                        quoting=csv.QUOTE_ALL)
                writer.writeheader()

                with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                    futures = []

                    for line in fileinput.input(files):
                        mo = self.URL_RE.search(line)
                        if not mo: continue

                        url = mo.group()
                        h = self.__processed_urls().get(url)
                        if h:
                            writer.writerow({ self.URL_HEADER: url,
                                              self.END_URL_HEADER: h[self.END_URL_HEADER],
                                              self.PAGE_TIT_HEAD: h[self.PAGE_TIT_HEAD],
                                              self.ART_TIT_HEAD: h[self.ART_TIT_HEAD] })
                            continue

                        futures.append(executor.submit(self.__build_csv_row_from,
                                                       url))

                    for future in as_completed(futures):
                        try:
                            row = future.result()
                        except:
                            self.logger.exception(f'Error resolving future')
                        else:
                            if row: writer.writerow(row)
        finally:
            self.__session().close()
            if tmp_path.exists():
                shutil.move(tmp_path, self.__out_path)


    def __parse_end_url_from(self, doc):
        tweet_urls = []
        for tweet_txt_sel in self.TWEET_TXT_SELS:
            tweet_urls.extend((a['href'] for a in doc.select(f'{self.TWEET_PERMA_LINK_SEL} {tweet_txt_sel} a')))
        filter(None, tweet_urls)
        tweet_urls = set(tweet_urls)

        urls = []
        for url in tweet_urls:
            if self.URL_RE.match(url):
                res = self.__open_w_timeout(url)

                if res:
                    uri = urlparse(res.url)

                    if uri.netloc != self.TWITTER_HOST or self.TWITTER_STATUS_RE.search(uri.path):
                        urls.append(res.url)
                    continue

            urls.append(url)

        tweet_urls = [urljoin(self.TWITTER_URL_PREFIX, url) if url.startswith('/') else url for url in urls]

        tweet_urls = list(itertools.filterfalse(lambda url: urlparse(url).netloc == self.TWITTER_HOST and
                                                                urlparse(url).path.count('/') > 1 and not
                                                                self.TWITTER_STATUS_RE.search(url),
                                                tweet_urls))
        tweet_urls.sort()

        if tweet_urls: return self.CSV_FIELD_SEP.join(tweet_urls)


    def __build_csv_row_from(self, url):
        res = self.__read_w_timeout(url)
        if not res: return

        end_url, html = res
        if not html: return

        doc = BeautifulSoup(html, self.HTML_PARSER)

        e_url = self.__parse_end_url_from(doc)
        if e_url: end_url = e_url

        page_tit_node = doc.select_one('title')
        page_tit = self.__clean_up_whitespace(page_tit_node) if page_tit_node else ''

        art_tit_node = doc.select_one('article h1') or doc.select_one('h1')
        art_tit = self.__clean_up_whitespace(art_tit_node) if art_tit_node else ''

        return { self.URL_HEADER: url, self.END_URL_HEADER: end_url,
                 self.PAGE_TIT_HEAD: page_tit, self.ART_TIT_HEAD: art_tit }


    def __clean_up_whitespace(self, tag):
        text = tag.string or tag.get_text()
        if not text: return ''

        text = text.strip()
        text = self.NEW_LINE_RE.sub(' ', text)
        return self.WHITESPACE_RE.sub(' ', text)


    @lru_cache(maxsize=1)
    def __timeout(self):
        return (self.__options.get('connect_timeout', self.CONN_TO),
                self.__options.get('read_timeout', self.READ_TO))

    @lru_cache(maxsize=1)
    def __session(self):
        session = requests.Session();
        session.max_redirects = self.max_redirects
        return session


    def __open_w_timeout(self, url):
        retries = 0

        while retries < self.max_retries:
            try:
                res = self.__session().get(url, timeout=self.__timeout())
            except requests.exceptions.Timeout:
                retries += 1
                self.logger.warning(f'[Thread: {threading.get_ident()}] GET {url} timed out [retry #{retries}]. Going to sleep for {retries} sec(s)')
                time.sleep(retries)
            except requests.TooManyRedirects:
                self.logger.error(f'[Thread: {threading.get_ident()}] GET {url} resulted in more than {self.max_redirects} redirects')
                res = None
                break
            else:
                if res.status_code == requests.codes.ok:
                    return res
                else:
                    break
            finally:
                if res:
                    self.logger.debug(f'[Thread: {threading.get_ident()}] GET {url} [{res.status_code}]')


    def __read_w_timeout(self, url):
        res = self.__open_w_timeout(url)
        if res:
            return res.url, res.text


    @lru_cache(maxsize=1)
    def __csv_dialect(self):
        return self.CSV_DIALECT
        # if self.__out_path.exists():
        #     with self.__out_path.open(newline='') as f:
        #         return csv.Sniffer().sniff(f.read(1024))
        # else:
        #     return self.CSV_DIALECT


    @lru_cache(maxsize=1)
    def __processed_urls(self):
        if not self.__out_path.exists(): return {}

        with self.__out_path.open(newline='') as f:
            url_h = self.URL_HEADER
            end_url_h = self.END_URL_HEADER
            page_t_h = self.PAGE_TIT_HEAD
            art_t_h = self.ART_TIT_HEAD

            return { r[url_h]: { end_url_h: r[end_url_h], page_t_h: r[page_t_h],
                                 art_t_h: r[art_t_h] }
                        for r in csv.DictReader(f, dialect=self.__csv_dialect())
                        if r[page_t_h] and r[art_t_h] }


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    prog_name = TitleGrabber.PARENT_PATH.stem
    parser = argparse.ArgumentParser(prog=prog_name)
    parser.add_argument('-o', '--output', metavar='OUT_FILE', dest='out_path',
                        help=f'Output file (defaults to {TitleGrabber.DEF_OUT_PATH})',
                        default=TitleGrabber.DEF_OUT_PATH)
    parser.add_argument('--connect-timeout', metavar='TIMEOUT', type=float,
                        help=f'HTTP connect timeout. Defaults to the value of the CONNECT_TIMEOUT env var or {TitleGrabber.CONN_TO}',
                        default=float(os.environ.get('CONNECT_TIMEOUT',
                                                     TitleGrabber.CONN_TO)))
    parser.add_argument('--read-timeout', metavar='TIMEOUT', type=float,
                        help=f'HTTP read timeout. Defaults to the value of the READ_TIMEOUT env var or {TitleGrabber.READ_TO}',
                        default=float(os.environ.get('READ_TIMEOUT',
                                                     TitleGrabber.READ_TO)))
    parser.add_argument('--max-redirects', metavar='REDIRECTS', type=int,
                        help=f'Max. # of HTTP redirects to follow. Defaults to the value of the MAX_REDIRECTS env var or {TitleGrabber.MAX_REDIRECTS}',
                        default=float(os.environ.get('MAX_RETRIES',
                                                     TitleGrabber.MAX_RETRIES)))
    parser.add_argument('-r', '--max-retries', metavar='RETRIES', type=int,
                        help=f'Max. # of times to retry failed HTTP reqs. Defaults to the value of the MAX_RETRIES env var or {TitleGrabber.MAX_RETRIES}',
                        default=float(os.environ.get('MAX_RETRIES',
                                                     TitleGrabber.MAX_RETRIES)))
    parser.add_argument('-t', '--max-threads', metavar='THREADS', type=int,
                        help=f'Max. # of threads to use. Defaults to the value of the MAX_THREADS env var or the # of logical processors in the system ({cpu_count()})',
                        default=float(os.environ.get('MAX_THREADS',
                                                     cpu_count())))
    parser.add_argument('files', metavar='FILES',
                        help="1 or more CSV files containing URLs (1 per line)",
                        nargs='*')
    parser.add_argument('-d', '--debug',
                        help='Log to STDOUT instead of to a file in the CWD.  Defaults to the value of the DEBUG env var or False',
                        action='store_true',
                        default=os.environ.get('DEBUG'))
    parser.add_argument('-V', '--version',
                        help='Print program version and exit',
                        action='store_true')
    args = parser.parse_args()

    if args.version:
        print(f'{prog_name} version {title_grabber.version}')
        sys.exit(0)

    if not args.files:
        print('At least 1 input file is required!', file=sys.stderr)
        sys.exit(1)

    args.out_path = Path(args.out_path).expanduser().resolve()
    files = [Path(f).expanduser().resolve() for f in args.files]

    TitleGrabber(vars(args))(files)
