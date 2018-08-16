#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import unittest
import os
import glob
import pprint

sys.path.append('.')
sys.path.append('..')

from pboletin import Config
from pboletin import get_metadata

class pboletinTest(unittest.TestCase):

	def test_get_metadata(self):
		"""Verifica la extraccion de las actas del html"""

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
		
		data = os.path.join(self._workpath,'data')
		files = glob.glob(os.path.join(data,'*.html'))
		for file in files:
			# print(file)
			with open(file, 'r', encoding="Latin1") as f:
				html = f.read()
				actas = get_metadata(self._cfg,html)
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
