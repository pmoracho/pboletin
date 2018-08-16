#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Patricio Moracho <pmoracho@gmail.com>
#
# pboletin.py
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation. A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""
PdfProcessor
=============

Clase para el procesamiento de un página

"""

try:

	import sys
	import gettext
	import math
	import cv2 as cv
	import numpy as np
	import glob
	from operator import itemgetter
	# import pprint
	import itertools
	import os
	import argparse
	from progressbar import ProgressBar
	from progressbar import FormatLabel
	from progressbar import Percentage
	from progressbar import Bar
	from progressbar import RotatingMarker
	from progressbar import ETA
	import logging
	from configparser import ConfigParser
	import subprocess
	import tempfile
	import shutil
	import re
	from itertools import chain
	from itertools import groupby
	import statistics
	from PIL import Image
	from struct import *

except ImportError as err:
	modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
	print(_("No fue posible importar el modulo: %s") % modulename)
	sys.exit(-1)


class PdfProcessor():

	def __init__(self, pdffile, config, logging=None, force_page=None):

		self._inputpdffile = pdffile
		self._force_page = force_page
		self._logging = logging
		self._lista_actas = []
		self._total_actas = 0
		self._total_regions = 0
		self._cfg = config
		self._total_pages = self.pdf_count_pages()

	def loginfo(self,msg):
		if self._logging:
			self._logging.info(msg.replace("|", " "))

	def pdf_count_pages(self):
		self.loginfo("Get PDF info")
		cmdline = '{0} {1}'.format(self._cfg.pdfinfo_bin, self._inputpdffile)
		self.loginfo(cmdline)
		process = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
		out, err = process.communicate()
		rxcountpages = re.compile(self._cfg.rxcountpages, re.MULTILINE|re.DOTALL)
		m = re.findall(rxcountpages, out.decode('latin1'))

		return int(m[0]) if m else None

"""
	def process(self):


		loginfo("{0} has {1} pages".format(pdf_file, total_pages))

		if not force_page:
			if cfg.detect_export_pages:
				firstp = 1
				endp = total_pages 
			else:
				firstp = args.from_page if args.from_page else (cfg.ignore_first_pages+1)
				endp = args.to_page if args.to_page else (total_pages-cfg.ignore_last_pages)+1

			num_bars = (endp - firstp) + 1
		else:
			firstp = force_page
			endp = force_page
			num_bars = 1

		widgets = [FormatLabel(''), ' ', Percentage(), ' ', Bar('#'), ' ', ETA(), ' ', RotatingMarker()]
		bar = ProgressBar(widgets=widgets, maxval=num_bars)

		loginfo("Create temp dir")
		workpath = tempfile.mkdtemp()

		filename, _ = os.path.splitext(os.path.basename(pdf_file))
		outputpath = os.path.join(cfg.outputdir,filename)
		loginfo("Create outputp dir")
		os.makedirs(outputpath, exist_ok=True)

		loginfo("Extract PDF pages form {0}".format(pdf_file))
		maxz = len(str(total_pages))
		i=1

		for p in range(firstp,endp+1):

			loginfo("Extract page {0} of {1}".format(i,num_bars))
			cmdline = '{0} -png -f {3} -l {4} -r {5} {1} {2}/pagina'.format(
				cfg.pdftoppm_bin,
				pdf_file,
				workpath,
				p,
				p,
				cfg.resolution
			)
			loginfo(cmdline)
			with subprocess.Popen(cmdline, shell=True) as proc:
				pass

			cmdline = '{0} -q -c -f {3} -l {4} {1} {2}/pagina'.format(
				cfg.pdftohtml_bin,
				pdf_file,
				workpath,
				p,
				p
			)
			loginfo(cmdline)
			with subprocess.Popen(cmdline, shell=True) as proc:
				pass

			with open(os.path.join(workpath,'pagina-{0}.html'.format(str(p))), 'r', encoding="Latin1") as f:
				html = f.read()

			img_file = "pagina-{0}.png".format(str(p).zfill(maxz))
			img_file = os.path.join(workpath, img_file)

			actas = get_metadata(cfg,html)
			loginfo("Actas encontradas: {0}".format(str(actas)))

			if not cfg.detect_export_pages or (cfg.detect_export_pages and len(actas[2]) > 0) :

				last_acta = lista_actas[-1] if lista_actas else None

				lista_actas.extend([a[2] for a in actas[2]])
				total_actas = total_actas + (len(actas[2]) if actas is not None else 0)

				total_regions = total_regions + crop_regions(img_file, workpath, outputpath, last_acta=last_acta, metadata=actas)

				widgets[0] = FormatLabel('[Página {0} de {1}]'.format(i,num_bars))

			bar.update(i)
			i = i + 1

		loginfo("Remove temp dir")

		bar.finish()
		if args.debug_page:
			print(workpath)
		else:
			shutil.rmtree(workpath)

		actas_error=[]
		for a in lista_actas:
			f = os.path.join(outputpath,cfg.imgext[0],'{0}.{1}'.format(a,cfg.imgext[0]))
			if not os.path.isfile(f):
				actas_error.append(a)

		print("Total de actas               : {0}".format(total_actas))
		print("Total de regiones recortadas : {0}".format(total_regions))
		if actas_error:
			print("Actas no encontradas         : {0}".format(",".join(actas_error)))

		if force_page:
			print("Actas encontradas            : {0}".format(",".join(lista_actas)))

		loginfo("Finish process")
"""		
