import csv
from pathlib import Path
import unittest

from title_grabber.__main__ import TitleGrabber

class TitleGrabberTest(unittest.TestCase):
    URL = 'https://www.jaylen.com.ar/'

    def setUp(self):
        self.out_path = Path('test_output.csv').resolve()
        self.title_grabber = TitleGrabber(self.out_path)


    def tearDown(self):
        if self.out_path.exists(): self.out_path.unlink()


    def test_call(self):
        csv_files = Path(__file__).with_name('fixtures').glob('*.txt')
        self.title_grabber(files=csv_files)
        self.assertTrue(self.out_path.exists())

        res = []
        with self.out_path.open(newline='') as f:
            res = [r for r in csv.DictReader(f)]
        self.assertEqual(1, len(res))
        r = res[0]
        self.assertEqual(self.URL, r[TitleGrabber.URL_HEADER])
        self.assertEqual(self.URL, r[TitleGrabber.END_URL_HEADER])
        self.assertEqual('Jaylen Informática', r[TitleGrabber.PAGE_TIT_HEAD])
        self.assertEqual('Productos', r[TitleGrabber.ART_TIT_HEAD])

        self.assertFalse(len(list(Path('.').glob('*.tmp.csv'))))
