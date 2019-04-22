import csv
import os
from pathlib import Path
import tempfile
import unittest

from title_grabber.__main__ import TitleGrabber

class TitleGrabberTest(unittest.TestCase):
    def setUp(self):
        os.environ['TESTING'] = '1'
        self.out_path = Path('test_output.csv').resolve()
        self.title_grabber = TitleGrabber(dict(out_path=self.out_path))


    def tearDown(self):
        if self.out_path.exists(): self.out_path.unlink()


    def test_it_works_with_non_twitter_urls(self):
        src_url = 'https://www.jaylen.com.ar/'
        urls = ['123', src_url, 'abc', '!"#$%&']
        with tempfile.NamedTemporaryFile(mode='w') as f:
            lst_url_idx = len(urls) - 1
            for i, url in enumerate(urls):
                print(url, file=f, flush=i == lst_url_idx)

            self.title_grabber(files=[f.name])

        self.assertTrue(self.out_path.exists())
        res = []
        with self.out_path.open(newline='') as f:
            res = [r for r in csv.DictReader(f)]
        self.assertEqual(1, len(res))
        r = res[0]
        self.assertEqual(src_url, r[TitleGrabber.URL_HEADER])
        self.assertEqual(src_url, r[TitleGrabber.END_URL_HEADER])
        self.assertEqual('Jaylen Informática', r[TitleGrabber.PAGE_TIT_HEAD])
        self.assertEqual('Productos', r[TitleGrabber.ART_TIT_HEAD])

        self.assertFalse(len(list(Path('.').glob('*.tmp.csv'))))


    def test_it_works_with_t_co_urls(self):
        src_url = 'https://t.co/7VDzp24y9N'
        urls = [src_url]
        with tempfile.NamedTemporaryFile(mode='w') as f:
            lst_url_idx = len(urls) - 1
            for i, url in enumerate(urls):
                print(url, file=f, flush=i == lst_url_idx)

            self.title_grabber(files=[f.name])

        self.assertTrue(self.out_path.exists())
        res = []
        with self.out_path.open(newline='') as f:
            res = [r for r in csv.DictReader(f)]
        self.assertEqual(1, len(res))
        r = res[0]
        self.assertEqual(src_url, r[TitleGrabber.URL_HEADER])
        self.assertEqual(['https://startupmap.iamsterdam.com/dashboard',
                          'https://twitter.com/Startup_Adam'],
                         r[TitleGrabber.END_URL_HEADER].split(','))
        self.assertIn("A new report shows that startups have become Amsterdam's leading job growth engine",
                      r[TitleGrabber.PAGE_TIT_HEAD])
        self.assertEqual('Dealroom.co', r[TitleGrabber.ART_TIT_HEAD])

        self.assertFalse(len(list(Path('.').glob('*.tmp.csv'))))


    def test_it_works_with_twitter_com_urls(self):
        src_url = 'https://twitter.com/i/web/status/1116358879409995776'
        urls = [src_url]
        with tempfile.NamedTemporaryFile(mode='w') as f:
            lst_url_idx = len(urls) - 1
            for i, url in enumerate(urls):
                print(url, file=f, flush=i == lst_url_idx)

            self.title_grabber(files=[f.name])

        self.assertTrue(self.out_path.exists())
        res = []
        with self.out_path.open(newline='') as f:
            res = [r for r in csv.DictReader(f)]
        self.assertEqual(1, len(res))
        r = res[0]
        self.assertEqual(src_url, r[TitleGrabber.URL_HEADER])
        self.assertEqual(['https://twitter.com/cityblockhealth',
                          'https://twitter.com/cityblockhealth/status/1116351442460315649'],
                         r[TitleGrabber.END_URL_HEADER].split(','))
        self.assertIn('Cityblock Health has joined our global army of Health Transformers who are committed to improving the life and wellbeing of everyone in the world',
                      r[TitleGrabber.PAGE_TIT_HEAD])
        self.assertRegex(r[TitleGrabber.ART_TIT_HEAD], '\AStartUp Health')

        self.assertFalse(len(list(Path('.').glob('*.tmp.csv'))))
