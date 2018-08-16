#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import unittest
import os
import glob
import pprint

sys.path.append('.')
sys.path.append('..')

from Config import Config
from PdfProcessor import PdfProcessor

class PdfProcessorTest(unittest.TestCase):

	def test_pdf_count_pages(self):
		"""Verifica la recuperación de la cantidad de páginas"""

		data = os.path.join(self._workpath,'data')
		pdffile = os.path.join(data,'4670.pdf')
		p = PdfProcessor(pdffile, self._cfg)
		self.assertEqual(p.pdf_count_pages(), 76)

	@classmethod
	def setUpClass(cls):
		cls._configfile = "pboletin.ini"
		cls._workpath = ""
		cls._cfg = Config()
		cls._load_config()

	@classmethod
	def tearDownClass(cls):
		pass

	@classmethod
	def _load_config(cls):
		cls._cfg.set_file(cls._configfile)
