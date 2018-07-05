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

TO DO:
	- Try / catch pdftoppm
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
	from itertools import chain
	from itertools import groupby
	import statistics

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
										formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50)
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

def loginfo(msg):
	logging.info(msg.replace("|", " "))


class Config:

	def __init__(self, file=None):

		self.file = file
		self.config = ConfigParser()
		if self.file:
			self._load()

	def set_file(self, file):

		self.file = file
		if self.file:
			self._load()

	def _load(self):
		self.config.read(self.file)
		self.__dict__.update(dict(self.config.items("GLOBAL")))

		# np.array
		for e in ["linecolor_from" , "linecolor_to"]:
			self.__dict__[e] = np.array(list(map(int,self.__dict__[e].split(','))))

		# int
		for e in ["resolution", "artifact_min_size","ignore_first_pages","ignore_last_pages",
			"max_area", "min_area" ]:
			self.__dict__[e] = int(self.__dict__[e])

		# booleano
		for e in ["save_process_files"]:
			self.__dict__[e] = True if self.__dict__[e] == "True" else False

cfg = Config()


def crop_regions(filepath, workpath, outputpath, metadata=None):

	filename, _ = os.path.splitext(os.path.basename(filepath))
	############################################################################
	# Lectura inicial de la imagen
	############################################################################
	src = cv.imread(filepath)
	if src is None:
		print ('Error opening {0}!'.format(filepath))
		return -1

	height, width, channels = src.shape
	if cfg.save_process_files:
		cv.imwrite(os.path.join(workpath,'01.original.png'), src)

	############################################################################
	# Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
	############################################################################
	mask_bw_negative = cv.inRange(src, cfg.linecolor_from, cfg.linecolor_to)

	if cfg.save_process_files:
		cv.imwrite(os.path.join(workpath,'02.mask_bw_negative.png'), mask_bw_negative)

	############################################################################
	# Quito artefactos de hasta una cierta superficie
	############################################################################
	nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
	sizes = stats[1:, -1]
	nb_components = nb_components - 1
	clean_mask = np.zeros((output.shape[0], output.shape[1], 3), dtype = "uint8")

	for i in range(0, nb_components):
		if sizes[i] >= cfg.artifact_min_size:
			clean_mask[output == i + 1] = 255
	############################################################################

	original_con_lineas = np.copy(src)

	############################################################################
	# Remuevo las líneas para recortar luego sin estas
	############################################################################
	clean_mask = cv.cvtColor(clean_mask, cv.COLOR_BGR2GRAY)
	ret, clean_mask = cv.threshold(clean_mask, 10, 255, cv.THRESH_BINARY)

	height, width, channels = src.shape
	blank_image = np.zeros((height,width,3), np.uint8)
	blank_image = cv.bitwise_not(blank_image)

	# get first masked value (foreground)
	fg = cv.bitwise_or(blank_image, blank_image, mask=clean_mask)
	bg = cv.bitwise_or(src, src, mask=cv.bitwise_not(clean_mask))
	final = cv.bitwise_or(fg, bg)

	if cfg.save_process_files:
		cv.imwrite(os.path.join(workpath,'03.clean_mask.png'), clean_mask)
	
	if cfg.save_process_files:
		cv.imwrite(os.path.join(workpath,'04.original_sin_lineas.png'), final)
	############################################################################


	############################################################################
	# Engroso la máscara para no perder lineas rectas
	############################################################################
	kernel = np.ones((7,7),np.uint8)
	clean_mask_gray = cv.dilate(clean_mask,kernel,iterations = 1)

	############################################################################
	# Detección de líneas rectas y generación de máscara de recorte
	############################################################################
	height, width, channels = final.shape
	crop_mask = np.zeros((height,width,3), np.uint8)
	minLineLength = 240*(300/cfg.resolution)
	maxLineGap = 300*(300/cfg.resolution)
	thres = int(100*(300/cfg.resolution))
	rho=0.5
	linesP = cv.HoughLinesP(clean_mask_gray,rho, np.pi/180,thres,minLineLength=minLineLength,maxLineGap=maxLineGap)
	if linesP is not None:

		ll = [e[0] for e in np.array(linesP).tolist()]
		ll = process_lines(ll,cfg.resolution)
		for l in [e[1] for e in enumerate(ll)]:
			cv.line(original_con_lineas, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)
			cv.line(crop_mask, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)

	if cfg.save_process_files:
		cv.imwrite(os.path.join(workpath,'05.clean_mask_gray.png'), clean_mask_gray)
		cv.imwrite(os.path.join(workpath,'06.crop_mask.png'), crop_mask)
		cv.imwrite(os.path.join(workpath,'07.original_con_lineas.png'), original_con_lineas)

	############################################################################
	# En base a la mascara obtengo los rectangulos de interes
	############################################################################
	gray = cv.cvtColor(crop_mask, cv.COLOR_BGR2GRAY) # convert to grayscale
	retval, thresh_gray = cv.threshold(gray, thresh=1, maxval=255, type=cv.THRESH_BINARY_INV)
	image, contours, hierarchy = cv.findContours(thresh_gray,cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE )

	############################################################################
	# Recorto los rectangulos
	# Si las coordenadas de algun acta entran dentro de la zona de recorte
	# Bien! podemos asociar la zona con el número de acta
	############################################################################
	max_area = cfg.max_area * (300/cfg.resolution)
	min_area = cfg.min_area * (300/cfg.resolution)

	if metadata:
		(x, y, actas) = metadata
		relation = sum([height/y, width/x])/2

	i = 1
	contornos = []
	for cont in contours:
		x,y,w,h = cv.boundingRect(cont)
		area = w*h
		contornos.append((x,y,w,h,area))

	contornos.sort(key=lambda x: x[4])
	# pprint.pprint(contornos)
	for c in contornos[:-2]:
		x,y,w,h,area = c
		# print((x,y,w,h,area))
		if area < max_area and area > min_area :
			mx = x,y,w,h
			# pprint.pprint(mx)
			roi=final[y:y+h,x:x+w]

			acta = get_acta(actas, (x,y,x+w,y+h), relation)
			# acta = None
			if acta:
				cv.imwrite(os.path.join(outputpath,'{0}.{1}'.format(acta,cfg.imgext)), roi)
			else:
				cv.imwrite(os.path.join(outputpath,'{0}_crop_{1}.{2}'.format(filename,i,cfg.imgext)), roi)

			i = i + 1

	return i-1

def get_acta(actas, region, r):

	rx1, ry1, rx2, ry2 = region
	for x, y, numero in actas:
		if x*r >= rx1 and x*r <= rx2 and y*r >= ry1 and y*r <= ry2:
			return numero

	return None

def process_lines(lista, in_res):

	verticales = [l for l in lista if l[0] == l[2]]
	horizontales = [l for l in lista if l[1] == l[3]]

	xs = list(chain(*[(l[0], l[2]) for l in horizontales]))
	ys = list(chain(*[(l[1], l[3]) for l in horizontales]))

	min_x = min(xs) - 20
	max_x = max(xs) + 20
	min_y = min(ys)
	max_y = max(ys)

	############################################################################
	# Resolver el problema de falta de linea horizontal al final
	############################################################################
	bottom = int(3300*300/cfg.resolution)
	dif = bottom-max_y
	max_y = max_y if dif <= 50 else bottom

	############################################################################
	# Horizontales cercanas al bottom
	############################################################################
	for i,l in enumerate(horizontales):
		dif = bottom - l[1]
		if dif <= 50:
			horizontales[i][1] = bottom
			horizontales[i][3] = bottom

	newlista = horizontales
	newlista.extend(verticales)

	############################################################################
	# Bajo el recorte del top
	############################################################################
	for i, e in enumerate(newlista):
		newlista[i][1] = min_y+10 if e[1] == min_y else e[1] 
		newlista[i][3] = min_y+10 if e[3] == min_y else e[3]

	min_y = min_y + 10

	############################################################################
	# Agrego un recuadro
	############################################################################
	newlista.append([min_x, min_y, max_x, min_y])
	newlista.append([min_x, min_y, min_x, max_y])
	newlista.append([min_x, max_y, max_x, max_y])
	newlista.append([max_x, max_y, max_x, min_y])

	############################################################################
	# Simplificación de líneas
	############################################################################
	newlista = simplificar(simplificar(newlista, pair=1), pair=2)
	newlista = list(map(list,set(map(tuple,newlista))))

	############################################################################
	# Conectar lineas horizontales con las verticales
	############################################################################
	newlista = conectar_horizontales(newlista)
	newlista = conectar_verticales(newlista)

	return(newlista)

def simplificar(mylista, pair, level=5):

	xs = list(chain(*[(l[pair-1], l[pair+1]) for l in mylista]))
	xs.sort()

	lista = []

	for i,p in enumerate(xs):
		if i>0:
			if p - (xs[i-1]) <= level:
				lista.append((p,lista[i-1][1]))
			else:
				grupo = grupo + 1 
				lista.append((p,grupo))
		else:
			grupo = 1
			lista.append((p,grupo))

	px = dict(lista)
	aprox = {}
	for key, group in groupby(lista, key=lambda x: x[1]):
		aprox[key] = statistics.median_low(i for i, j in group)

	newlist = mylista[:]

	if pair == 1:
		for i,e in enumerate(newlist):
			newlist[i] = [aprox[px[e[0]]], e[1], aprox[px[e[2]]], e[3]]
	else:
		for i,e in enumerate(newlist):
			newlist[i] = [e[0], aprox[px[e[1]]], e[2], aprox[px[e[3]]]]

	return newlist

def conectar_horizontales(mylista, level=50):
  
  newlist = mylista[:]

  verticales = [l for l in mylista if l[0] == l[2]]
  horizontales = [l for l in mylista if l[1] == l[3]]
  
  xvert = {}
  for i in [l[0] for l in verticales]:
    for j in range(0, level):
      xvert[i+j] = i
      xvert[i-j] = i

  for i,l in enumerate(horizontales):
    horizontales[i][0] = xvert.get(horizontales[i][0],horizontales[i][0])
    horizontales[i][2] = xvert.get(horizontales[i][2],horizontales[i][2])
  
  return newlist

def conectar_verticales(mylista, level=50):
  
  newlist = mylista[:]

  verticales = [l for l in mylista if l[0] == l[2]]
  horizontales = [l for l in mylista if l[1] == l[3]]
  
  yvert = {}
  for i in [l[1] for l in horizontales]:
    for j in range(0, level):
      yvert[i+j] = i
      yvert[i-j] = i

  for i,l in enumerate(verticales):
    verticales[i][1] = yvert.get(verticales[i][1],verticales[i][1])
    verticales[i][3] = yvert.get(verticales[i][3],verticales[i][3])
  
  return newlist

def count_pages(filename):
	rxcountpages = re.compile(cfg.rxcountpages, re.MULTILINE|re.DOTALL)
	with open(filename,"rb") as f:
		data = f.read()
	return len(rxcountpages.findall(data.decode('latin1')))

def get_actas(html):

	x,y = 1, 1
	rxactas = re.compile(cfg.rxpagedim, re.MULTILINE)
	t = re.findall(rxactas, html)
	if t:
		x,y = map(int,t[0])

	rxactas = re.compile(cfg.rxactas, re.MULTILINE)
	m = re.finditer(rxactas, html)

	if m:
		return (x, y, list( (int(e.group(2)),int(e.group(1)),e.group(3)) for e in m ))
	else:
		return None

def process_pdf(pdf_file, force_page=None):

	lista_actas = []
	total_actas = 0
	total_regions = 0
	total_pages = count_pages(pdf_file)

	if not force_page:
		firstp = cfg.ignore_first_pages+1
		endp = (total_pages-cfg.ignore_last_pages)+1
		num_bars = (total_pages-cfg.ignore_last_pages-cfg.ignore_first_pages)
	else:
		firstp = force_page
		endp = force_page + 1
		num_bars = 1

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

	for p in range(firstp,endp):

		cmdline = '{0} -png -f {3} -l {4} -r {5} {1} {2}/pagina'.format(
			cfg.pdftoppm_bin,
			pdf_file,
			workpath,
			p,
			p,
			cfg.resolution
		)
		with subprocess.Popen(cmdline, shell=True) as proc:
			pass

		cmdline = '{0} -q -c -f {3} -l {4} {1} {2}/pagina'.format(
			cfg.pdftohtml_bin,
			pdf_file,
			workpath,
			p,
			p
		)
		with subprocess.Popen(cmdline, shell=True) as proc:
			pass

		with open(os.path.join(workpath,'pagina-{0}.html'.format(str(p))), 'r', encoding="Latin1") as f:
			html = f.read()

		img_file = "pagina-{0}.png".format(str(p).zfill(maxz))
		img_file = os.path.join(workpath, img_file)

		actas = get_actas(html)
		lista_actas.extend([a[2] for a in actas[2]])
		total_actas = total_actas + (len(actas[2]) if actas is not None else 0)

		total_regions = total_regions + crop_regions(img_file, workpath, outputpath, metadata=actas)

		widgets[0] = FormatLabel('[Página {0} de {1}]'.format(i,num_bars))
		loginfo("Extract page {0} of {1}".format(i,num_bars))
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
		if not os.path.isfile(os.path.join(outputpath,'{0}.{1}'.format(a,cfg.imgext))):
			actas_error.append(a)

	print("Total de actas               : {0}".format(total_actas))
	print("Total de regiones recortadas : {0}".format(total_regions))
	if actas_error:
		print("Actas no encontradas         : {0}".format(",".join(actas_error)))

	if force_page:
		print("Actas encontradas            : {0}".format(",".join(lista_actas)))

	loginfo("Finish process")


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

		cfg.set_file(configfile)
		process_pdf(args.pdffile, args.debug_page)
	else:
		cmdparser.print_help()
