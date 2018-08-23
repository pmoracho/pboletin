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
Config
======

Clase para el procesamiento de la configuración

"""
try:

	import numpy as np
	from configparser import ConfigParser

except ImportError as err:
	modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
	print(_("No fue posible importar el modulo: %s") % modulename)
	sys.exit(-1)


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

		# lista
		for e in ["imgext"]:
			self.__dict__[e] = self.__dict__[e].split(',')

		# lista in
		for e in ["remove_pixels"]:
			self.__dict__[e] = list(map(int,self.__dict__[e].split(',')))

		# np.array
		for e in ["linecolor_from" , "linecolor_to"]:
			self.__dict__[e] = np.array(list(map(int,self.__dict__[e].split(','))))

		# floatr
		for e in ["line_rho"]:
			self.__dict__[e] = float(self.__dict__[e])

		# int
		for e in ["resolution", "artifact_min_size","ignore_first_pages", "ignore_last_pages",
			"max_area", "min_area", "jpg_compression", "h_line_gap", "v_line_gap", "line_min_length",
			"line_max_gap", "line_thres"]:
			self.__dict__[e] = int(self.__dict__[e])

		self.imgext = [e.lower() for e in self.imgext]

		# booleano
		for e in ["save_process_files"]:
			self.__dict__[e] = True if self.__dict__[e] == "True" else False

		self.compensation = self.resolution/300

	def __str__(self):
			
			parametros = (
				"line_min_length              : {0}".format(int(self.line_min_length*self.compensation)),
				"line_max_gap                 : {0}".format(int(self.line_max_gap*self.compensation)),
				"line_thres                   : {0}".format(int(self.line_thres*self.compensation)),
				"line_rho                     : {0}".format(self.line_rho),
				"resolution                   : {0}".format(self.resolution)
				)

			return "\n".join(parametros)
