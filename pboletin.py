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
pboletin
========

Procesamiento de los boletines de marcas y patentes de Argentina

"""

__author__		= "Patricio Moracho <pmoracho@gmail.com>"
__appname__		= "pboletin"
__appdesc__		= "Procesamiento de boletines"
__license__		= 'GPL v3'
__copyright__	= "(c) 2018, %s" % (__author__)
__version__		= "1.0"
__date__		= "2018/06/02"


try:

	import sys
	import gettext
	from gettext import gettext as _
	gettext.textdomain('padrondl')

	def my_gettext(s):
		"""my_gettext: Traducir algunas cadenas de argparse."""
		current_dict = {
			'usage: ': 'uso: ',
			'optional arguments': 'argumentos opcionales',
			'show this help message and exit': 'mostrar esta ayuda y salir',
			'positional arguments': 'argumentos posicionales',
			'the following arguments are required: %s': 'los siguientes argumentos son requeridos: %s',
			'show program''s version number and exit': 'Mostrar la versión del programa y salir',
			'expected one argument': 'se espera un valor para el parámetro',
			'expected at least one argument': 'se espera al menos un valor para el parámetro'
		}

		if s in current_dict:
			return current_dict[s]
		return s

	gettext.gettext = my_gettext

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

def resource_path(relative):
	"""Obtiene un path, toma en consideración el uso de pyinstaller"""
	if hasattr(sys, "_MEIPASS"):
		return os.path.join(sys._MEIPASS, relative)
	return os.path.join(relative)

def expand_filename(filename):

	if '{desktop}' in filename:
		tmp = os.path.join(os.path.expanduser('~'), 'Desktop')
		filename = filename.replace('{desktop}', tmp)

	if '{tmpdir}' in filename:
		tmp = tempfile.gettempdir()
		filename = filename.replace('{tmpdir}', tmp)

	if '{tmpfile}' in filename:
		tmp = tempfile.mktemp()
		filename = filename.replace('{tmpfile}', tmp)

	return filename

def init_argparse():
	"""Inicializar parametros del programa."""
	cmdparser = argparse.ArgumentParser(prog=__appname__,
										description="%s\n%s\n" % (__appdesc__, __copyright__),
										epilog="",
										add_help=True,
										formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=45)
	)

	opciones = {	"pdffile": {
								"type": str,
								"nargs": '?',
								"action": "store",
								"help": _("Boletín en PDF a procesar")
					},
					"--version -v": {
								"action":	"version",
								"version":	__version__,
								"help":		_("Mostrar el número de versión y salir")
					},
					"--config -c": {
								"type": 	str,
								"action": 	"store",
								"dest": 	"configfile",
								"default":	None,
								"help":		_("Establecer el archivo de configuración del proceso de recorte. Por defecto se busca 'pboleti.ini'.")
					},
					"--debug-page -p": {
								"type": 	int,
								"action": 	"store",
								"dest": 	"debug_page",
								"default":	None,
								"help":		_("Establecer el proceso de una determinada página para debug.")
					},
					"--log-level -n": {
								"type": 	str,
								"action": 	"store",
								"dest": 	"loglevel",
								"default":	"info",
								"help":		_("Nivel de log")
					},
					"--input-path -i": {
								"type": 	str,
								"action": 	"store",
								"dest": 	"inputpath",
								"default":	None,
								"help":		_("Carpeta dónde se alojan los boletines en pdf a procesar")
					},
					"--log-file -l": {
								"type": 	str,
								"action": 	"store",
								"dest": 	"logfile",
								"default":	None,
								"help":		_("Archivo de log"),
								"metavar":  "file"
					},
					"--from-page -f": {
								"type": 	int,
								"action": 	"store",
								"dest": 	"from_page",
								"default":	None,
								"help":		_("Desde que página se procesará del PDF")
					},
					"--to-page -t": {
								"type": 	int,
								"action": 	"store",
								"dest": 	"to_page",
								"default":	None,
								"help":		_("Hasta que página se procesará del PDF")
					},
					"--quiet -q": {
								"action": 	"store_true",
								"dest": 	"quiet",
								"default":	False,
								"help":		_("Modo silencioso sin mostrar barra de progreso.")
					},
			}

	for key, val in opciones.items():
		args = key.split()
		kwargs = {}
		kwargs.update(val)
		cmdparser.add_argument(*args, **kwargs)

	return cmdparser

################################################################################
#  Cuerpo principal
################################################################################
if __name__ == "__main__":

	cmdparser = init_argparse()
	try:
		args = cmdparser.parse_args()

	except IOError as msg:
		cmdparser.error(str(msg))
		sys.exit(-1)

	# Definir el path de dónde obtener la configuración
	if not args.configfile:
		# determine if application is a script file or frozen exe
		if getattr(sys, 'frozen', False):
			application_path = os.path.dirname(sys.executable)
		elif __file__:
			application_path = os.path.dirname(__file__)

		configfile = resource_path(os.path.join(application_path, 'pboletin.ini'))
	else:
		configfile = args.configfile

	if args.pdffile:

		if args.logfile:
			log_level = getattr(logging, args.loglevel.upper(), None)
			logging.basicConfig(filename=args.logfile, level=log_level, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y/%m/%d %I:%M:%S', filemode='w')	

		try:
			loginfo("Config file: {0}".format(configfile))
			cfg.set_file(configfile)
		except IOError as msg:
			cmdparser.error(str(msg))
			sys.exit(-1)

		if args.debug_page:
			cfg.save_process_files = True

		if args.inputpath:
			cfg.inputdir = args.inputpath

		args.pdffile = os.path.join(cfg.inputdir, args.pdffile)
		loginfo("Proces PDF : {0}".format(args.pdffile))

	def __init__(self, 	config,
			  			pdffile=None, 
			  			logging=None):

		p = PdfProcessor( config=cfg,
				   		  pdffile=args.pdffile,
				   		  logging=logging)	

		def statusbar_start=(num_bars):
			widgets = [FormatLabel(''), ' ', Percentage(), ' ', Bar('#'), ' ', ETA(), ' ', RotatingMarker()]
			bar = ProgressBar(widgets=widgets, maxval=num_bars)

		def statusbar_update(i):
			bar.update(i)

		def statusbar_end():
			bar.finish()
	
		p.process(
			startfun=statusbar_start,
			statusfun=statusbar_update,
			endfun=statusbar_end
		)

	else:
		cmdparser.print_help()
