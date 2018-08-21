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
	from Config import Config

except ImportError as err:
	modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
	print(_("No fue posible importar el modulo: %s") % modulename)
	sys.exit(-1)


class PdfProcessor():

	def __init__(self, 	configfile,
			  			pdffile=None, 
			  			logging=None,
			  			debug_page=None):

		self._inputpdffile = pdffile
		self._logging = logging
		self._lista_actas = []
		self._total_actas = 0
		self._total_regions = 0
		self._force_page = debug_page if debug_page else None

		try:
			self._cfg = Config()
			self.loginfo("Config file: {0}".format(configfile))
			self._cfg.set_file(configfile)

		except IOError as msg:
			print("{0} not Found!".format(configfile))
			sys.exit(-1)
	
		if self._cfg.inputdir:
			self._inputpdffile = os.path.join(self._cfg.inputdir,self._inputpdffile)
			
		if self._inputpdffile:

			from pathlib import Path
			my_file = Path(self._inputpdffile)
			if not my_file.is_file():
				print("{0} not Found!".format(self._inputpdffile))
				sys.exit(-1)

			self._total_pages = self.pdf_count_pages()
			self.loginfo("{0} has {1} pages".format(self._inputpdffile, self._total_pages))

		if self._force_page:
			self._cfg.save_process_files = True

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

	def process_pdf(self,	
				 	startfun=None,
					statusfun=None,
			 		endfun=None,
			  		from_page=None, 
			  		to_page=None):

		if not self._force_page:
			if self._cfg.detect_export_pages:
				firstp = 1
				endp = self._total_pages 
			else:
				firstp = from_page if from_page else (self._cfg.ignore_first_pages+1)
				endp = to_page if to_page else (self._total_pages-self._cfg.ignore_last_pages)+1

			self._proc_pages = (endp - firstp) + 1
		else:
			firstp = self._force_page
			endp = self._force_page
			self._proc_pages = 1

		workpath = tempfile.mkdtemp()
		self.loginfo("Config file: {0}".format(self._cfg.file))
		self.loginfo("Create temp dir at: {0}".format(workpath))

		filename, _ = os.path.splitext(os.path.basename(self._inputpdffile))
		outputpath = os.path.join(self._cfg.outputdir,filename)
		self.loginfo("Create outputp path at {0}".format(outputpath))
		os.makedirs(outputpath, exist_ok=True)

		self.loginfo("Extract PDF pages form {0}".format(self._inputpdffile))
		maxz = len(str(self._total_pages))
		i=1

		############################################################################
		# Creamos las subcarpetas para guardar las imagenes por extensión
		############################################################################
		for ext in self._cfg.imgext:
			opath = os.path.join(outputpath, ext, "check")
			os.makedirs(opath,exist_ok=True)

		if startfun:
			startfun(self._proc_pages)

		for p in range(firstp, endp+1):

			self.loginfo("Extract page {0} of {1}".format(i,self._proc_pages))
			##############################################################################
			# Extración de página a png
			##############################################################################
			cmdline = '{0} -png -f {3} -l {4} -r {5} {1} {2}/pagina'.format(
				self._cfg.pdftoppm_bin,
				self._inputpdffile,
				workpath,
				p,
				p,
				self._cfg.resolution
			)
			self.loginfo(cmdline)
			with subprocess.Popen(cmdline, shell=True) as proc:
				pass

			##############################################################################
			# Extración de página a HTML
			##############################################################################
			cmdline = '{0} -q -c -f {3} -l {4} {1} {2}/pagina'.format(
				self._cfg.pdftohtml_bin,
				self._inputpdffile,
				workpath,
				p,
				p
			)
			self.loginfo(cmdline)
			with subprocess.Popen(cmdline, shell=True) as proc:
				pass

			##############################################################################
			# Lectura del contenido html
			##############################################################################
			with open(os.path.join(workpath,'pagina-{0}.html'.format(str(p))), 'r', encoding="Latin1") as f:
				html = f.read()

			img_file = "pagina-{0}.png".format(str(p).zfill(maxz))
			img_file = os.path.join(workpath, img_file)

			actas = self.get_metadata(html)
			self.loginfo("Actas encontradas: {0}".format(str(actas)))

			if not self._cfg.detect_export_pages or (self._cfg.detect_export_pages and len(actas[2]) > 0) :

				last_acta = self._lista_actas[-1] if self._lista_actas else None
				self._lista_actas.extend([a[2] for a in actas[2]])
				self._total_actas = self._total_actas + (len(actas[2]) if actas is not None else 0)
				self._total_regions = self._total_regions + self.crop_regions(img_file, workpath, outputpath, last_acta=last_acta, metadata=actas)

			if statusfun:
				statusfun(i, self._proc_pages)

			i = i + 1

		self.loginfo("Remove temp dir")
		if endfun:
			endfun()

	def get_metadata(self, html):
		"""get_metadata: extrae información del boletin en el PDF

		El boletin convertido de PDF -> HTML, se procesa con patrones
		regulares configurables en el INI para extraer la información
		necesaria de la página procesada:
			- Tamaño x, y de la página
			- # acta
			- Posición x,y del # acta en la página

		Args:
			html(str): Cadena completa html de la página a procesar.

		"""

		x, y = 1, 1
		rxactas = re.compile(self._cfg.rxpagedim, re.MULTILINE)
		t = re.findall(rxactas, html)
		if t:
			x,y = map(int,t[0])

		rxactas = re.compile(self._cfg.rxactas, re.MULTILINE)
		m = re.finditer(rxactas, html)

		if m:
			return (x, y, list( (int(e.group(2)),int(e.group(1)),e.group(3).replace('.','')) for e in m ))
		else:
			return None


	def crop_regions(self, filepath, workpath, outputpath, last_acta, metadata=None):

		filename, _ = os.path.splitext(os.path.basename(filepath))

		# El calculo de todo esta hecho sobre una base de 300 dpi
		# Hay que compensar si la resolucion es distinta
		self._cfg.compensation = (self._cfg.resolution/300)

		############################################################################
		# Lectura inicial de la imagen
		############################################################################
		src = cv.imread(filepath)
		if src is None:
			print ('Error opening {0}!'.format(filepath))
			return -1

		height, width, channels = src.shape

		############################################################################
		# Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
		############################################################################
		mask_bw_negative = cv.inRange(src, self._cfg.linecolor_from, self._cfg.linecolor_to)

		############################################################################
		# Quito artefactos de hasta una cierta superficie
		############################################################################
		nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
		sizes = stats[1:, -1]
		nb_components = nb_components - 1
		clean_mask = np.zeros((output.shape[0], output.shape[1], 3), dtype = "uint8")

		for i in range(0, nb_components):
			if sizes[i] >= self._cfg.artifact_min_size*self._cfg.compensation:
				clean_mask[output == i + 1] = 255
		############################################################################

		original_con_lineas = np.copy(src)
		final = src

		############################################################################
		# Engroso la máscara para no perder lineas rectas
		############################################################################
		clean_mask = cv.cvtColor(clean_mask, cv.COLOR_BGR2GRAY)
		ret, clean_mask = cv.threshold(clean_mask, 10, 255, cv.THRESH_BINARY)
		kernel = np.ones((7,7),np.uint8)
		clean_mask_gray = cv.dilate(clean_mask,kernel,iterations = 1)

		############################################################################
		# Detección de líneas rectas y generación de máscara de recorte
		############################################################################
		height, width, channels = final.shape
		crop_mask = np.zeros((height,width,3), np.uint8)
		minLineLength = int(self._cfg.line_min_length*self._cfg.compensation)
		maxLineGap = int(self._cfg.line_max_gap*self._cfg.compensation)
		thres = int(self._cfg.line_thres*self._cfg.compensation)
		rho=self._cfg.line_rho
		linesP = cv.HoughLinesP(clean_mask_gray,rho, np.pi/180,thres,minLineLength=minLineLength,maxLineGap=maxLineGap)
		if linesP is not None:

			ll = [e[0] for e in np.array(linesP).tolist()]
			ll = self.process_lines(ll)
			for l in [e[1] for e in enumerate(ll)]:
				cv.line(original_con_lineas, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)
				cv.line(crop_mask, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)

		if self._cfg.save_process_files:
			cv.imwrite(os.path.join(workpath,'01.original.png'), src)
			cv.imwrite(os.path.join(workpath,'02.mask_bw_negative.png'), mask_bw_negative)
			cv.imwrite(os.path.join(workpath,'03.clean_mask.png'), clean_mask)
			cv.imwrite(os.path.join(workpath,'04.clean_mask_gray.png'), clean_mask_gray)
			cv.imwrite(os.path.join(workpath,'05.crop_mask.png'), crop_mask)
			cv.imwrite(os.path.join(workpath,'06.original_con_lineas.png'), original_con_lineas)

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
		max_area = self._cfg.max_area * self._cfg.compensation
		min_area = self._cfg.min_area * self._cfg.compensation
		if metadata:
			(x, y, actas) = metadata
			relation = sum([height/y, width/x])/2
		else:
			actas = None

		i = 1
		contornos = []
		for cont in contours:
			x,y,w,h = cv.boundingRect(cont)
			area = w*h
			contornos.append((x,y,w,h,area))

		final = final.astype(np.uint8)

		remove = self._cfg.remove_pixels if self._cfg.remove_pixels else [0,0,0,0]
		contornos.sort(key=lambda x: x[4])

		adj = 3 # Para que no entren las líneas rectas
		for recorte in contornos[:-2]:
			x,y,w,h,area = recorte
			x=x+adj
			y=y+adj
			w=w-(adj*2)
			h=h-(adj*2)
			if area < max_area and area > min_area:

				acta = self.get_acta(actas, (x,y,x+w,y+h), relation) if actas else None
				roi = final[y:y+h,x:x+w]
				roi = self.get_main_area(roi, acta)
				file = self.save_crop(acta, roi, outputpath, filename, i, last_acta)
				if file:
					self.duplicate_file(file)
					i = i + 1

				pass
			
		return i-1

	def process_lines(self, lista):

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
		bottom = int(3300*(self._cfg.resolution/300))

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
		newlista = self.simplificar(self.simplificar(newlista, pair=1), pair=2)
		newlista = list(map(list,set(map(tuple,newlista))))

		############################################################################
		# Conectar lineas horizontales con las verticales
		############################################################################
		newlista = self.conectar_horizontales(newlista, int(self._cfg.h_line_gap*self._cfg.compensation))
		newlista = self.conectar_verticales(newlista, int(self._cfg.v_line_gap*self._cfg.compensation))

		return(newlista)


	def simplificar(self, mylista, pair, level=5):

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

	def conectar_horizontales(self, mylista, level=50):
	
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

	def conectar_verticales(self, mylista, level=50):
	
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


	def get_acta(self, actas, region, r):

		rx1, ry1, rx2, ry2 = region
		for x, y, numero in actas:
			if x*r >= rx1 and x*r <= rx2 and y*r >= ry1 and y*r <= ry2:
				return numero

		return None


	def get_main_area(self, img, acta):

		remove = self._cfg.remove_pixels if self._cfg.remove_pixels else [0,0,0,0]

		gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
		ret,thresh = cv.threshold(gray,127,255,cv.THRESH_BINARY_INV)
		kernel = np.ones((7,7),np.uint8)
		gray = cv.dilate(thresh,kernel,iterations = 1)
		im2, ctrs, hier = cv.findContours(gray.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
		l = [(t[0], t[1], t[0]+t[2], t[1]+t[3])  for t in [cv.boundingRect(ctr) for ctr in ctrs]]
		height, width, channels = img.shape
		
		if not l:
			# No hay zonas de interes posiblemente imagen en blanco
			l = [(0,0,width,height)]

		lmin = list(map(min, zip(*l)))
		lmax = list(map(max, zip(*l)))

		add = 3
		seguridad = (
			lmin[0]-add if lmin[0]-add > 0 else 0,
			lmin[1]-add if lmin[1]-add > 0 else 0,
			lmax[2]+add if lmax[2]+add < width else width,
			lmax[3]+add if lmax[3]+add < height else height
		)

		x1 = seguridad[0] if seguridad[0]<remove[0] else remove[0]
		y1 = seguridad[1] if seguridad[1]<remove[1] else remove[1]

		x2 = seguridad[2] if seguridad[2]>width-remove[2] else width-remove[2]
		y2 = seguridad[3] if seguridad[3]>height-remove[3] else height-remove[3]

		crop = (x1, y1, x2, y2)

		self.loginfo("Acta             : {0}".format(acta))
		self.loginfo("Recorte seguridad: {0}".format(str(seguridad)))
		self.loginfo("Recorte final    : {0}".format(str(crop)))
		
		roi = img[crop[1]:crop[1]+crop[3], crop[0]:crop[0]+crop[2]]
		return roi

	def save_crop(self, acta, crop, outputpath, boletin, index, last_acta):

		unique_colors = len(np.unique(crop.reshape(-1, crop.shape[2]), axis=0))
		compression = [int(cv.IMWRITE_JPEG_QUALITY), self._cfg.jpg_compression]
		fmerged = None
		ext_compat = 'jpg'

		if unique_colors <= 1:
			return None

		if not acta and last_acta:
			############################################################################################
			# Es un Merge
			############################################################################################
			last_file = os.path.join(outputpath, ext_compat,'{0}.{1}'.format(last_acta, ext_compat))
			last_img = cv.imread(last_file)			
			max_width = 0 # find the max width of all the images
			total_height = 0 # the total height of the images (vertical stacking)
			images = [last_img, crop]
			for img in images:
				if img.shape[1] > max_width:
					max_width = img.shape[1]
				total_height += img.shape[0]

			merged = np.zeros((total_height,max_width,3),dtype=np.uint8)
			merged.fill(255)

			current_y = 0 # keep track of where your current image was last placed in the y coordinate
			for image in images:
				merged[current_y:image.shape[0]+current_y,:image.shape[1],:] = image
				current_y += image.shape[0]

			unique_colors = len(np.unique(merged.reshape(-1, merged.shape[2]), axis=0))
			fmerged = os.path.join(outputpath, ext_compat, 'check', '{0}.merged.{1}'.format(last_acta, ext_compat))

			if unique_colors  <= 256:
				merged = cv.cvtColor(merged, cv.COLOR_BGR2GRAY)

			cv.imwrite(fmerged, merged, compression)
			self.add_resolution_to_jpg(fmerged,self._cfg.resolution)

			crop_file = os.path.join(outputpath, ext_compat,'{0}.{1}'.format(last_acta, ext_compat))
			# Muevo el file anterior a check
			shutil.move(crop_file, os.path.join(outputpath, ext_compat, 'check'))
			fmerged = os.path.join(outputpath, ext_compat, 'check', '{0}.merged.{1}'.format(last_acta, ext_compat))
			shutil.move(fmerged,crop_file)

		else:

			opath = os.path.join(outputpath, ext_compat)
			if acta:
				crop_file = os.path.join(opath,'{0}.{1}'.format(acta, ext_compat))
			else:
				crop_file = os.path.join(opath,'check','{0}_crop_{1}.{2}'.format(boletin, index, ext_compat))

			if unique_colors  <= 256:
				crop  = cv.cvtColor(crop, cv.COLOR_BGR2GRAY)

			cv.imwrite(crop_file, crop, compression)

		return crop_file


	def duplicate_file(self, file):

		for e in (e for e in self._cfg.imgext if e != 'jpg'):
			output = file.replace('jpg', e)
			Image.open(file).save(output)
			
		pass


	def add_resolution_to_jpg(self, filename, resolution):
		"""add_resolution_to_jpg: Agrega info de la resolución al archivo

		Debido a problemas a la hora de incrustar imagenes en el Word resulta
		necesario agregar al header del JPG la información de la resolución
		Vertical y horizontal, debido a que opencv no salva esta información.

		Args:
			filename (str): Path completo al archivo jpg
			resolution (int): Resolución

		Example:
			>>> add_resolution_to_jpg("c:\prueba.jpg", 150) # 150 dpi

		"""
		struct_fmt = '>6s5sHBHH'
		struct_len = calcsize(struct_fmt)

		with open(filename, "rb") as f:
			header = unpack(struct_fmt, f.read(struct_len))
			data = f.read()

		with open(filename, "wb") as f:
			f.write(pack(struct_fmt, header[0], header[1], header[2], header[3], resolution, resolution))
			f.write(data)

