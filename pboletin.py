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

+ Recorte automático de cada acta

"""

__author__		= "Patricio Moracho <pmoracho@gmail.com>"
__appname__		= "pboletin"
__appdesc__		= "Procesamiento de boletines"
__license__		= 'GPL v3'
__copyright__	= "(c) 2018, %s" % (__author__)
__version__		= "0.9"
__date__		= "2018/06/02"


try:

	import sys
	import gettext
	from gettext import gettext as _
	gettext.textdomain('padrondl')

	def _my_gettext(s):
		"""Traducir algunas cadenas de argparse."""
		current_dict = {'usage: ': 'uso: ',
						'optional arguments': 'argumentos opcionales',
						'show this help message and exit': 'mostrar esta ayuda y salir',
						'positional arguments': 'argumentos posicionales',
						'the following arguments are required: %s': 'los siguientes argumentos son requeridos: %s'}

		if s in current_dict:
			return current_dict[s]
		return s

	gettext.gettext = _my_gettext

	import math
	import cv2 as cv
	import numpy as np
	import glob
	from operator import itemgetter
	import pprint
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


except ImportError as err:
	modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
	print(_("No fue posible importar el modulo: %s") % modulename)
	sys.exit(-1)


# def init_argparse():
# 	"""Inicializar parametros del programa."""
# 	cmdparser = argparse.ArgumentParser(prog=__appname__,
# 										description="%s\n%s\n" % (__appdesc__, __copyright__),
# 										epilog="",
# 										add_help=True,
# 										formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50)
# 	)

# 	opciones = {	"padron": {
# 								"type": str,
# 								"nargs": '?',
# 								"action": "store",
# 								"help": _("Padrón a descargar")
# 					},
# 					"--version -v": {
# 								"action":	"version",
# 								"version":	__version__,
# 								"help":		_("Mostrar el número de versión y salir")
# 					},
# 					"--show-padrones -s": {
# 								"action":	"store_true",
# 								"dest":		"showpadrones",
# 								"default":	False,
# 								"help":		_("Verifciación completa. c: algoritmos de compresión, e: algoritmos de encriptación.")
# 					},
# 					"--output-path -o": {
# 								"type": 	str,
# 								"action": 	"store",
# 								"dest": 	"outputpath",
# 								"default":	None,
# 								"help":		_("Carpeta de outputh del padrón descargado.")
# 					},
# 					"--log-level -n": {
# 								"type": 	str,
# 								"action": 	"store",
# 								"dest": 	"loglevel",
# 								"default":	"info",
# 								"help":		_("Nivel de log")
# 					},
# 					"--quiet -q": {
# 								"action": 	"store_true",
# 								"dest": 	"quiet",
# 								"default":	False,
# 								"help":		_("Modo silencioso sin mostrar barra de progreso.")
# 					},
# 			}

# 	for key, val in opciones.items():
# 		args = key.split()
# 		kwargs = {}
# 		kwargs.update(val)
# 		cmdparser.add_argument(*args, **kwargs)

# 	return cmdparser


def loginfo(msg):
	logging.info(msg.replace("|", " "))


class Config:

	def __init__(self, file="pboletin.ini"):

		self.file = file
		self.config = ConfigParser()
		self.config.read(self.file)
		self.__dict__.update(dict(self.config.items("GLOBAL")))

		# np.array
		for e in ["linecolor_from" , "linecolor_to"]:
			self.__dict__[e] = np.array(list(map(int,self.__dict__[e].split(','))))

		# int
		for e in ["resolution", "artifact_min_size","ignore_first_pages","ignore_last_pages",
			"max_area", "min_area" ]:
			self.__dict__[e] = int(self.__dict__[e])

cfg = Config()

def crop_regions(filepath, workpath, outputpath):

	filename, _ = os.path.splitext(os.path.basename(filepath))

	############################################################################
	# Lectura inicial de la imagen
	############################################################################
	src = cv.imread(filepath)
	if src is None:
		print ('Error opening {0}!'.format(filepath))
		return -1

	############################################################################
	# Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
	############################################################################
	mask_bw_negative = cv.inRange(src, cfg.linecolor_from, cfg.linecolor_to)
	cv.imwrite(os.path.join(workpath,'mask_bw_negative.png'), mask_bw_negative)
	
	############################################################################
	# Quito artefactos de hasta una cierta superficie
	############################################################################
	nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
	sizes = stats[1:, -1]
	nb_components = nb_components - 1
	clean_mask = np.zeros((output.shape))

	for i in range(0, nb_components):
		if sizes[i] >= cfg.artifact_min_size:
			clean_mask[output == i + 1] = 255

	cv.imwrite(os.path.join(workpath,'clean_mask.png'), clean_mask)
	clean_mask = cv.imread(os.path.join(workpath,'clean_mask.png'))

	clean_mask_gray = cv.cvtColor(clean_mask,cv.COLOR_BGR2GRAY)
	cv.imwrite(os.path.join(workpath,'clean_mask_gray.png'), clean_mask_gray)

	############################################################################
	# Remuevo las líneas para recortar luego sin estas
	############################################################################
	cdstP = np.copy(src)
	cdstP = cv.bitwise_not(cdstP,cdstP,mask=clean_mask_gray)

	height, width, channels = cdstP.shape
	blank_image = np.zeros((height,width,3), np.uint8)

	in_res = cfg.resolution
	minLineLength = 300*(300/in_res)
	maxLineGap = 300*(300/in_res)
	thres = int(150*(300/in_res))
	rho=1
	linesP = cv.HoughLinesP(clean_mask_gray,rho, np.pi/180,thres,minLineLength = minLineLength,maxLineGap = maxLineGap)
	if linesP is not None:

		ll = [e[0] for e in np.array(linesP).tolist()]
		ll = process_lines(ll, in_res)
		for l in [e[1] for e in enumerate(ll)]:
			cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)
			cv.line(blank_image, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)

	cv.imwrite(os.path.join(workpath,'blank_image.png'), blank_image)
	cv.imwrite(os.path.join(workpath,'final.png'), cdstP)

	############################################################################
	# En bae a la mascara obtengo los rectanfulos de interes
	############################################################################
	gray = cv.cvtColor(blank_image, cv.COLOR_BGR2GRAY) # convert to grayscale
	retval, thresh_gray = cv.threshold(gray, thresh=1, maxval=255, \
                                   type=cv.THRESH_BINARY_INV)

	cv.imwrite(os.path.join(workpath,'thresh_gray.png'), thresh_gray)

	image, contours, hierarchy = cv.findContours(thresh_gray,cv.RETR_CCOMP , \
									cv.CHAIN_APPROX_SIMPLE )

	############################################################################
	# Recorto los rectangulos
	############################################################################
	max_area = cfg.max_area * (cfg.resolution/300) 
	min_area = cfg.min_area * (cfg.resolution/300) 
	
	i = 1
	for cont in contours:
		x,y,w,h = cv.boundingRect(cont)
		area = w*h
		if area < max_area and area > min_area:
			mx = x,y,w,h
			# pprint.pprint(mx)
			roi=src[y:y+h,x:x+w]
			cv.imwrite(os.path.join(outputpath,'{0}_crop_{1}.png'.format(filename,i)), roi)
			i = i + 1

def process_lines(lista, in_res):

	top = int(240*in_res/300)
	left= int(80*in_res/300)
	# bottom = int(3260*in_res/300)
	# right = int(2300*in_res/300)

	############################################################################
	# Establezco el valor de y minímo para que caiga debajo de la recta
	# horizontal del titulo de página
	############################################################################
	lista = [[left if l[0]-(left*2) < left else l[0],
			  l[1] if l[1] > top else top,
		      left if l[2]-(left*2) < left else l[2],
		      l[3] if l[3] > top else top]
			  for l in lista]

	############################################################################
	# Agregago el recuadro completo de la pagina
	############################################################################
	puntos=[(l[0],l[1]) for l in lista]
	puntos.extend([(l[2],l[3]) for l in lista])

	min_x = min([x for x,y in puntos]) - 50
	min_y = min([y for x,y in puntos])
	max_x = max([x for x,y in puntos]) + 50
	max_y = max([y for x,y in puntos])

	lista.append([min_x, min_y, max_x, min_y])
	lista.append([min_x, min_y, min_x, max_y])
	lista.append([min_x, max_y, max_x, max_y])
	lista.append([max_x, max_y, max_x, min_y])

	############################################################################
	# Simplifico las líneas
	############################################################################
	# level = 55
	# aprox = {0:{}, 1:{}}

	# for i in (0,1):
	# 	valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in lista])), ()))
	# 	print(valor)
	# 	for e in valor:
	# 		if e not in aprox[i]:
	# 			aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})


	# for i,e in enumerate(lista):
	# 	lista[i][0] = aprox[0][e[0]]
	# 	lista[i][1] = aprox[1][e[1]]
	# 	lista[i][2] = aprox[0][e[2]]
	# 	lista[i][3] = aprox[1][e[3]]


	############################################################################
	# Simplifico las líneas
	############################################################################
	level = 55
	aprox = {0:{}, 1:{}}

	i = 0
	valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in lista])), ()))
	for e in valor:
		if e not in aprox[i]:
			aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})


	for i,e in enumerate(lista):
		lista[i][0] = aprox[0][e[0]]
		lista[i][2] = aprox[0][e[2]]


	############################################################################
	# Ordeno y me quedo con las líneas no repetidas
	############################################################################
	lista.sort()
	lista = list(e for e,_ in itertools.groupby(lista))

	return(lista)

def remove_lines(lista, maxtop, maxbottom):

	lista = [l for l in lista if l[0] > maxtop and not (l[0] > maxbottom and l[2] > maxbottom)]


def add_box(lista, top, bottom, right, left):

	puntos=[(l[0],l[1]) for l in lista]
	puntos.extend([(l[2],l[3]) for l in lista])

	min_x = min([x for x,y in puntos]) - 50
	min_y = min([y for x,y in puntos])
	max_x = max([x for x,y in puntos]) + 50
	max_y = max([y for x,y in puntos])

	lista.append([min_x, min_y, max_x, min_y])
	lista.append([min_x, min_y, min_x, max_y])
	lista.append([min_x, max_y, max_x, max_y])
	lista.append([max_x, max_y, max_x, min_y])


def simplificar(mylista, level=5):

	aprox = {0:{}, 1:{}}

	for i in (0,1):
		valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in mylista])), ()))
		for e in valor:
			if e not in aprox[i]:
				aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})

	for i,e in enumerate(mylista):
		mylista[i][0] = aprox[0][e[0]]
		mylista[i][1] = aprox[1][e[1]]
		mylista[i][2] = aprox[0][e[2]]
		mylista[i][3] = aprox[1][e[3]]


rxcountpages = re.compile(r"/Type\s*/Page([^s]|$)", re.MULTILINE|re.DOTALL)
def count_pages(filename):
	with open(filename,"rb") as f:
		data = f.read()
	return len(rxcountpages.findall(data.decode('latin1')))

def process_pdf(pdf_file):

	print()
	total_pages = count_pages(pdf_file)
	num_bars = (total_pages-cfg.ignore_last_pages-cfg.ignore_first_pages)
	widgets = [FormatLabel(''), ' ', Percentage(), ' ', Bar('#'), ' ', ETA(), ' ', RotatingMarker()]
	bar = ProgressBar(widgets=widgets, maxval=num_bars)

	loginfo("Create temp dir")
	workpath = tempfile.mkdtemp()
	outputpath = os.path.join(cfg.outputdir,pdf_file)
	loginfo("Create outputp dir")
	os.makedirs(outputpath, exist_ok=True)

	loginfo("Extract PDF pages form {0}".format(pdf_file))
	maxz = len(str(total_pages))
	i=1
	for p in range(cfg.ignore_first_pages+1,(total_pages-cfg.ignore_last_pages)+1):

		cmdline = '{0} -png -f {3} -l {4} -r {5} {1} {2}/pagina'.format(
			cfg.pdftoppm_bin, 
			pdf_file, 
			workpath,
			p, 
			p,
			cfg.resolution
		)
		with subprocess.Popen(cmdline) as proc:
			pass

		img_file = "pagina-{0}.png".format(str(p).zfill(maxz))
		img_file = os.path.join(workpath, img_file)

		crop_regions(img_file, workpath, outputpath)

		widgets[0] = FormatLabel('[Página {0} de {1}]'.format(i,num_bars))
		loginfo("Extract page {0} of {1}".format(i,num_bars))
		bar.update(i)
		i = i + 1

	loginfo("Remove temp dir")
	shutil.rmtree(workpath)
	bar.finish()

	loginfo("Finish process)


def main(argv):

	pdf_file = argv[0] if len(argv) > 0 else "./boletines/4589_3_.pdf"
	process_pdf(pdf_file)
	return 0

if __name__ == "__main__":
	main(sys.argv[1:])
	pass
