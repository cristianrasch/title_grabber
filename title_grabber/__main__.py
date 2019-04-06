#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import fileinput
from functools import lru_cache
import logging
import os
from pathlib import Path
import re
import shutil
import sys
import threading

from bs4 import BeautifulSoup
import requests

class TitleGrabber:
    URL_RE = re.compile('https?://\S+', re.I)
    URL_HEADER = 'url'
    PAGE_TIT_HEAD = 'page_title'
    ART_TIT_HEAD = 'article_title'
    HEADERS = (URL_HEADER, PAGE_TIT_HEAD, ART_TIT_HEAD)
    CONN_TO = float(os.environ.get('CONNECT_TIMEOUT', 10))
    READ_TO = float(os.environ.get('READ_TIMEOUT', 15))
    TIMEOUT = (CONN_TO, READ_TO)
    MAX_RETRIES = 3
    HTML_PARSER = 'html.parser'
    NEW_LINE_RE = re.compile('\n')
    WHITESPACE_RE = re.compile('\s{2,}')
    IS_WIN_PLAT = sys.platform.startswith('win')
    CSV_DIALECT = 'excel' if IS_WIN_PLAT else 'unix'

    def __init__(self, out_path):
        self.__out_path = out_path

        parent_path = Path(__file__).parent
        log_level = logging.DEBUG if os.environ.get('DEBUG') else logging.INFO
        self.logger = logging.getLogger(parent_path.stem)
        self.logger.setLevel(log_level)
        handler = logging.FileHandler(Path.cwd().joinpath(parent_path.with_suffix('.log').name),
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

                with ThreadPoolExecutor() as executor:
                    futures = []

                    for line in fileinput.input(files):
                        mo = self.URL_RE.search(line)
                        if not mo: continue

                        url = mo.group()
                        h = self.__processed_urls().get(url)
                        if h:
                            writer.writerow({ self.URL_HEADER: url,
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
            if tmp_path.exists():
                shutil.move(tmp_path, self.__out_path)


    def __build_csv_row_from(self, url):
        html = self.__get(url)
        if not html: return

        doc = BeautifulSoup(html, self.HTML_PARSER)
        page_tit_node = doc.select_one('title')
        page_tit = self.__clean_up_whitespace(page_tit_node) if page_tit_node else ''

        art_tit_node = doc.select_one('article h1') or doc.select_one('h1')
        art_tit = self.__clean_up_whitespace(art_tit_node) if art_tit_node else ''

        return { self.URL_HEADER: url, self.PAGE_TIT_HEAD: page_tit,
                 self.ART_TIT_HEAD: art_tit }


    def __clean_up_whitespace(self, tag):
        text = tag.string or tag.get_text()
        if not text: return ''

        text = text.strip()
        text = self.NEW_LINE_RE.sub(' ', text)
        return self.WHITESPACE_RE.sub(' ', text)


    def __get(self, url):
        retries = 0
        txt = None

        while txt is None and retries < self.MAX_RETRIES:
            try:
                res = requests.get(url, timeout=self.TIMEOUT)
            except requests.exceptions.Timeout:
                retries += 1
                self.logger.warning(f'[Thread: {threading.get_ident()}] GET {url} timed out [retry #{retries}]. Going to sleep for {retries} sec(s)')
                time.sleep(retries)
            else:
                if res.status_code == requests.codes.ok:
                    return res.text
                else:
                    break
            finally:
                self.logger.debug(f'[Thread: {threading.get_ident()}] GET {url} [{res.status_code}]')

        return txt


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
            page_t_h = self.PAGE_TIT_HEAD
            art_t_h = self.ART_TIT_HEAD

            return { r[url_h]: { page_t_h: r[page_t_h], art_t_h: r[art_t_h] }
                        for r in csv.DictReader(f, dialect=self.__csv_dialect())
                        if r[page_t_h] and r[art_t_h] }


if __name__ == '__main__':
    import argparse
    from pathlib import Path

    DEF_OUT_PATH = 'out.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', metavar='OUT_FILE',
                        help=f'Output file (defaults to {DEF_OUT_PATH})',
                        default='out.csv')
    parser.add_argument('files', metavar='FILES',
                        help="1 or more CSV files containing URLs (1 per line)",
                        nargs='*')
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    files = [Path(f).expanduser().resolve() for f in args.files]
    TitleGrabber(out_path)(files)