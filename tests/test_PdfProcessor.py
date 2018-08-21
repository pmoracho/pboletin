#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import unittest
import os
import glob
import pprint
import tempfile

sys.path.append('.')
sys.path.append('..')

from Config import Config
from PdfProcessor import PdfProcessor

class PdfProcessorTest(unittest.TestCase):

	def test_pdf_count_pages(self):
		"""Verifica la recuperacion de la cantidad de paginas"""

		print(">>> Testing de la recuperación de la cantidad de paginas")
		data = os.path.join(self._workpath,'data')
		pdffile = os.path.join(data,'4670.pdf')
		p = PdfProcessor(self._cfg, pdffile)
		self.assertEqual(p.pdf_count_pages(), 76)

	def test_process(self):
		"""Verifica el proceso de un pdf completo"""

		print(">>> Testing del procesos completo de los pdf´s")
		tmppath = tempfile.mkdtemp()
		self._cfg.outputdir = tmppath
		data = os.path.join(self._workpath,'data')
		files = glob.glob(os.path.join(data,'*.pdf'))
		for pdffile in files:

			p = PdfProcessor(self._cfg, pdffile)
			p.process_pdf(
				startfun=lambda x:print("Total de paginas: {0}".format(x)),
				statusfun=lambda x, y:print("Procesando pagina {0} de {1}".format(x,y))
			)

		print(self._cfg.outputdir)


	def test_crop_regions(self):
		"""Verifica el proceso de crop de ciertas imagenes de referencia"""

		print(">>> Testing del crop de imagenes")
		data = os.path.join(self._workpath,'data')
		tmppath = tempfile.mkdtemp()

		outputpath = os.path.join(tmppath, 'crop')
		os.makedirs(outputpath, exist_ok=True)

		for ext in self._cfg.imgext:
			opath = os.path.join(outputpath, ext, "check")
			os.makedirs(opath,exist_ok=True)
		
		self._cfg.save_process_files = True

		p = PdfProcessor(self._cfg)

		files = glob.glob(os.path.join(data,'*.png'))
		for file in files:
			# print(file)
			p.crop_regions(file, tmppath, outputpath, last_acta=None, metadata=None)

	def test_get_metadata(self):
		"""Verifica la extraccion de las actas del html"""

		print(">>> Testing del proceso de los metadatos")
		test_data = {"data\\001.html": (892, 1262,
										[(107, 110, '3709500'),
										(107, 499, '3709501'),
										(107, 661, '3709583'),
										(107, 801, '3709504'),
										(109, 1071, '3709585'),
										(381, 110, '3709586'),
										(381, 240, '3709587'),
										(381, 369, '3709588'),
										(381, 499, '3709589'),
										(381, 866, '3709590'),
										(655, 110, '3709591'),
										(655, 251, '3709592'),
										(655, 391, '3709505'),
										(655, 521, '3709506')]),
					"data\\002.html": (892, 1262,
										[(109, 110, '3709988'),
										(655, 110, '3710247'),
										(655, 445, '3710248'),
										(655, 801, '3710249'),
										(381, 110, '3710241'),
										(381, 585, '3710242'),
										(381, 1082, '3710246')]),
					"data\\003.html": (892,	1262,
										[(94, 110, '3710474'),
										(94, 348, '3710480'),
										(94, 737, '3710481'),
										(97, 1071, '3710482'),
										(643, 110, '3710489'),
										(643, 240, '3710490'),
										(643, 369, '3710635'),
										(645, 920, '3710491'),
										(645, 1050, '3710492'),
										(368, 110, '3710483'),
										(368, 229, '3710631'),
										(368, 380, '3710633'),
										(368, 531, '3710484'),
										(371, 661, '3710485'),
										(368, 791, '3710486'),
										(368, 920, '3710487'),
										(368, 1061, '3710488')])
			   }
		
		p = PdfProcessor(self._cfg)
		data = os.path.join(self._workpath,'data')
		files = glob.glob(os.path.join(data,'*.html'))
		for file in files:
			with open(file, 'r', encoding="Latin1") as f:
				html = f.read()
				actas = p.get_metadata(html)
				# pprint.pprint(actas)
				self.assertEqual(test_data[file], actas)


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
